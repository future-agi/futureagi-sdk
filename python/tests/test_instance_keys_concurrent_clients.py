"""Clients of eight tenants, built at the same time on eight threads, each send their own keys.

For every sender type below, each round builds one client per tenant on eight threads that a
``threading.Barrier`` releases together, with a very short thread switch interval while they are built, and then
has each client send one request to a listener on 127.0.0.1. Every tenant has its own key pair and its own path
segment in the base URL, so each received request is attributed to a tenant by its path. The bytes of a request
attributed to a tenant hold that tenant's key markers and no other tenant's.

Senders: ``APIKeyAuth`` through ``HttpClient.request``, the KB client (``create_kb`` and ``update_kb``) with a file
upload, ``Dataset`` (an instance ``delete`` and the ``get_dataset_config`` class method), ``Prompt`` (an instance
``delete`` and the ``list_templates`` class method), ``Annotation``, ``AnnotationQueue``, ``fi.platform.Client``
and ``fi.gateway.Gateway`` (which sends its ``api_key`` only).
"""

from __future__ import annotations

import json
import secrets
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import pytest

from fi.annotations.annotation import Annotation
from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.datasets.dataset import Dataset, LRUCache
from fi.datasets.types import DatasetConfig
from fi.gateway import Gateway
from fi.kb.client import KnowledgeBase
from fi.kb.types import KnowledgeBaseConfig
from fi.platform import Client
from fi.prompt.client import Prompt
from fi.prompt.types import PromptTemplate
from fi.queues.client import AnnotationQueue
from fi.utils.routes import Routes
from fi.utils.types import ModelTypes
from tests.test_plain_http_key_guards import _marker_forms, net  # noqa: F401

LETTERS = "abcdefgh"
ROUNDS = 20
# an httpx-based client takes far longer to build under the short switch interval, so these run fewer rounds
HTTPX_ROUNDS = 6
ENV_NAMES = (
    "FI_API_KEY",
    "FI_SECRET_KEY",
    "FI_BASE_URL",
    "FI_WORKSPACE_ID",
    "FI_GATEWAY_API_KEY",
    "AGENTCC_API_KEY",
    "FI_GATEWAY_URL",
    "AGENTCC_BASE_URL",
)


class Tenant:
    """One tenant: a key pair and a path segment, all distinct from those of every other tenant."""

    def __init__(self, letter: str) -> None:
        self.letter = letter
        self.key = f"fikey-{letter}-{secrets.token_hex(10)}"
        self.secret = f"fisec-{letter}-{secrets.token_hex(10)}"
        self.tag = f"tenant-{letter}-{secrets.token_hex(4)}"
        self.forms = _marker_forms(self.key, self.secret)

    def marker_bytes(self, raw: bytes) -> int:
        return sum(raw.count(form) for form in self.forms)


class TenantSite:
    """An HTTP/1.1 listener on 127.0.0.1 that answers every request with JSON and records, per request, its path
    and its raw bytes (request line, headers and body)."""

    def __init__(self) -> None:
        self.received: List[Tuple[str, bytes]] = []
        self._lock = threading.Lock()
        site = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def __getattr__(self, name):
                if name.startswith("do_"):
                    return self._answer
                raise AttributeError(name)

            def _answer(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                raw = self.requestline.encode() + b"\r\n" + bytes(self.headers) + body
                with site._lock:
                    site.received.append((self.path, raw))
                payload = json.dumps(_reply(self.path)).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(payload)
                self.close_connection = True

        class Server(ThreadingHTTPServer):
            daemon_threads = True

        self._server = Server(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

    def snapshot(self) -> List[Tuple[str, bytes]]:
        time.sleep(0.1)
        with self._lock:
            return list(self.received)

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


def _reply(target: str) -> Dict[str, Any]:
    """The answer to a request for ``target``: the dataset-names lookup gets one dataset of the name searched for,
    the KB route gets a KB id and name, a chat completion gets an empty completion, and any other path gets an empty successful envelope."""
    parsed = urlparse(target)
    if parsed.path.endswith("/" + Routes.dataset_names.value):
        name = parse_qs(parsed.query).get("search_text", ["dataset"])[0]
        return {"result": {"datasets": [{"datasetId": str(uuid.uuid4()), "name": name, "modelType": "GenerativeLLM"}]}}
    if parsed.path.endswith("/" + Routes.knowledge_base.value):
        kb_id = str(uuid.uuid4())
        return {"status": True, "result": {"kb_id": kb_id, "kb_name": "docs", "id": kb_id, "name": "docs", "file_ids": []}}
    if parsed.path.endswith("/chat/completions"):
        return {"id": "completion", "object": "chat.completion", "created": 0, "model": "m", "choices": []}
    return {"status": True, "result": {}}


# ---------------------------------------------------------------------------------------------
# senders: ``build`` runs on the barrier threads and returns the client (or ``None`` for a class method that
# builds its own client and sends at once); ``send`` runs afterwards and sends one request with that client
# ---------------------------------------------------------------------------------------------


class Sender:
    def __init__(
        self,
        build: Callable[[Tenant, str, Dict[str, Any]], Any],
        send: Optional[Callable[[Any, Tenant, Dict[str, Any]], Any]] = None,
        rounds: int = ROUNDS,
    ) -> None:
        self.build = build
        self.send = send
        self.rounds = rounds


def _http_client_send(client: APIKeyAuth, tenant: Tenant, ctx: Dict[str, Any]) -> None:
    client.request(RequestConfig(method=HttpMethod.GET, url=client._base_url + "/v1/ping", retry_attempts=1, timeout=5))


def _kb_build(tenant: Tenant, base: str, ctx: Dict[str, Any]) -> KnowledgeBase:
    return KnowledgeBase(fi_api_key=tenant.key, fi_secret_key=tenant.secret, fi_base_url=base)


def _kb_update_build(tenant: Tenant, base: str, ctx: Dict[str, Any]) -> KnowledgeBase:
    kb = _kb_build(tenant, base, ctx)
    kb.kb = KnowledgeBaseConfig(id=str(uuid.uuid4()), name="docs-" + tenant.letter)
    return kb


def _dataset_build(tenant: Tenant, base: str, ctx: Dict[str, Any]) -> Dataset:
    config = DatasetConfig(id=uuid.uuid4(), name="dataset-" + tenant.letter, model_type=ModelTypes.GENERATIVE_LLM)
    return Dataset(dataset_config=config, fi_api_key=tenant.key, fi_secret_key=tenant.secret, fi_base_url=base)


def _dataset_get_config(tenant: Tenant, base: str, ctx: Dict[str, Any]) -> None:
    Dataset.get_dataset_config(
        "dataset-" + tenant.letter + "-" + str(ctx["round"]), fi_api_key=tenant.key, fi_secret_key=tenant.secret, fi_base_url=base
    )


def _prompt_build(tenant: Tenant, base: str, ctx: Dict[str, Any]) -> Prompt:
    template = PromptTemplate(id=uuid.uuid4(), name="prompt-" + tenant.letter)
    return Prompt(template=template, fi_api_key=tenant.key, fi_secret_key=tenant.secret, fi_base_url=base)


def _prompt_list_templates(tenant: Tenant, base: str, ctx: Dict[str, Any]) -> None:
    Prompt.list_templates(fi_api_key=tenant.key, fi_secret_key=tenant.secret, fi_base_url=base)


def _platform_build(tenant: Tenant, base: str, ctx: Dict[str, Any]) -> Client:
    return Client(api_key=tenant.key, secret_key=tenant.secret, base_url=base, max_retries=0, timeout=5)


def _gateway_build(tenant: Tenant, base: str, ctx: Dict[str, Any]) -> Gateway:
    return Gateway(api_key=tenant.key, base_url=base, max_retries=0, timeout=5)


def _gateway_send(client: Gateway, tenant: Tenant, ctx: Dict[str, Any]) -> None:
    client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])


SENDERS: Dict[str, Sender] = {
    "http-client-request": Sender(
        lambda t, base, ctx: APIKeyAuth(fi_api_key=t.key, fi_secret_key=t.secret, fi_base_url=base), _http_client_send
    ),
    "kb-create-with-file": Sender(_kb_build, lambda kb, t, ctx: kb.create_kb(name="docs-" + t.letter, file_paths=[ctx["file"]])),
    "kb-update-with-file": Sender(_kb_update_build, lambda kb, t, ctx: kb.update_kb(kb_name="docs-" + t.letter, file_paths=[ctx["file"]])),
    "dataset-instance-delete": Sender(_dataset_build, lambda ds, t, ctx: ds.delete()),
    "dataset-get-config-class-method": Sender(_dataset_get_config),
    "prompt-instance-delete": Sender(_prompt_build, lambda prompt, t, ctx: prompt.delete()),
    "prompt-list-templates-class-method": Sender(_prompt_list_templates),
    "annotation-list-projects": Sender(
        lambda t, base, ctx: Annotation(fi_api_key=t.key, fi_secret_key=t.secret, fi_base_url=base),
        lambda client, t, ctx: client.list_projects(),
    ),
    "annotation-queue-list-queues": Sender(
        lambda t, base, ctx: AnnotationQueue(fi_api_key=t.key, fi_secret_key=t.secret, fi_base_url=base),
        lambda client, t, ctx: client.list_queues(),
    ),
    "platform-client-account-whoami": Sender(_platform_build, lambda client, t, ctx: client.account.whoami(), HTTPX_ROUNDS),
    "gateway-chat-completion": Sender(_gateway_build, _gateway_send, HTTPX_ROUNDS),
}


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------


def _build_round(sender: Sender, tenants: List[Tenant], site: TenantSite, ctx: Dict[str, Any]) -> Tuple[List[Any], List[str]]:
    """Build one client per tenant on threads released together, with a short switch interval."""
    barrier = threading.Barrier(len(tenants))
    built: List[Any] = [None] * len(tenants)
    errors: List[str] = []

    def work(index: int) -> None:
        tenant = tenants[index]
        try:
            barrier.wait(timeout=15)
            built[index] = sender.build(tenant, f"{site.base}/{tenant.tag}", ctx)
        except Exception as exc:  # a failure after the request was sent is read from the listener
            errors.append(f"build {tenant.letter}: {_brief(exc)}")

    threads = [threading.Thread(target=work, args=(index,), daemon=True) for index in range(len(tenants))]
    interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
    finally:
        sys.setswitchinterval(interval)
    return built, errors


def _brief(exc: BaseException) -> str:
    first = (str(exc).splitlines() or [""])[0]
    return f"{type(exc).__name__}: {first[:160]}"


def _close(client: Any) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def _counts(received: List[Tuple[str, bytes]], tenants: List[Tenant]):
    """Per receiving tenant: its request count and the bytes holding each tenant's key markers; also the paths
    of requests attributed to no tenant."""
    by_tag = {tenant.tag: tenant for tenant in tenants}
    requests_of = {tenant.letter: 0 for tenant in tenants}
    table = {tenant.letter: {other.letter: 0 for other in tenants} for tenant in tenants}
    stray: List[str] = []
    for path, raw in received:
        segment = urlparse(path).path.split("/")[1] if path.startswith("/") else ""
        owner = by_tag.get(segment)
        if owner is None:
            stray.append(path)
            continue
        requests_of[owner.letter] += 1
        for other in tenants:
            table[owner.letter][other.letter] += other.marker_bytes(raw)
    return requests_of, table, stray


def _report(name: str, rounds: int, tenants: List[Tenant], requests_of, table, stray: List[str], errors: List[str]) -> str:
    lines = [
        f"sender {name}: bytes holding each tenant's key markers (columns) in the requests attributed to each "
        f"tenant (rows), over {rounds} rounds; n = requests received",
        "tenant     n " + " ".join(f"{t.letter:>7}" for t in tenants),
    ]
    for tenant in tenants:
        row = table[tenant.letter]
        lines.append(f"{tenant.letter:>6} {requests_of[tenant.letter]:>5} " + " ".join(f"{row[t.letter]:>7}" for t in tenants))
    if stray:
        lines.append(f"requests attributed to no tenant: {len(stray)} (first: {stray[:3]})")
    if errors:
        lines.append(f"errors raised to the caller: {len(errors)} (first: {errors[:3]})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------
# cases
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", list(SENDERS), ids=list(SENDERS))
def test_each_tenant_client_built_on_concurrent_threads_sends_only_its_own_keys(monkeypatch, tmp_path, name):
    site = TenantSite()
    try:
        _run_sender(monkeypatch, tmp_path, site, name)
    finally:
        site.close()


def _run_sender(monkeypatch, tmp_path, site: TenantSite, name: str) -> None:
    for variable in ENV_NAMES:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(Dataset, "_dataset_instance_cache", LRUCache(capacity=1000))
    upload = tmp_path / "notes.txt"
    upload.write_text("notes for the upload")
    sender = SENDERS[name]
    tenants = [Tenant(letter) for letter in LETTERS]
    errors: List[str] = []

    for round_number in range(sender.rounds):
        ctx = {"file": str(upload), "round": round_number}
        built, build_errors = _build_round(sender, tenants, site, ctx)
        errors.extend(build_errors)
        if sender.send is None:
            continue
        for tenant, client in zip(tenants, built):
            if client is None:
                continue
            try:
                sender.send(client, tenant, ctx)
            except Exception as exc:  # a failure after the request was sent is read from the listener
                errors.append(f"send {tenant.letter}: {_brief(exc)}")
            finally:
                _close(client)

    requests_of, table, stray = _counts(site.snapshot(), tenants)
    report = _report(name, sender.rounds, tenants, requests_of, table, stray, errors)

    assert not stray, report
    assert all(requests_of[t.letter] == sender.rounds for t in tenants), report
    for tenant in tenants:
        row = table[tenant.letter]
        assert row[tenant.letter] > 0, report
        assert all(row[other.letter] == 0 for other in tenants if other is not tenant), report
    # every call completes against the listener's replies
    assert not errors, report
