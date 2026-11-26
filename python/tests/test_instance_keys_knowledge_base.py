"""KB uploads (``fi.kb``) from one client while other clients with other keys exist in the process.

Two tenants, A and B, each hold their own marker keys, generated per case. Client A is a ``KnowledgeBase``
created first; client B is created second, with B's keys, as another ``KnowledgeBase``, a ``fi.client.Client``,
a ``fi.datasets.Dataset`` or an ``APIKeyAuth`` built directly (as the ``fi.prompt`` class methods do). Then A
uploads a file through ``create_kb`` or ``update_kb``, and B sends a request of its own.

Each client talks to its own HTTP listener on 127.0.0.1, so requests go direct. Every case counts, at each
listener (A's site, B's site, and the ``net`` target and proxy listeners of ``test_plain_http_key_guards``),
the bytes holding each tenant's markers, and every assertion message prints those counts. A's site holds
A's markers and none of B's; B's site holds B's markers and none of A's; the ``net`` listeners hold none.
"""

from __future__ import annotations

import contextlib
import secrets
import threading
from typing import Dict, Iterator, Tuple

import pytest

from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.client import Client
from fi.datasets import Dataset
from fi.kb.client import KnowledgeBase
from fi.kb.types import KnowledgeBaseConfig
from tests.test_keyed_request_paths import Site
from tests.test_plain_http_key_guards import _marker_forms, net  # noqa: F401

KB_ID = "00000000-0000-4000-8000-0000000000a1"
KB_PATH = "/model-hub/knowledge-base/"
KB_LIST_PATH = "/model-hub/knowledge-base/list/"
KEY_ATTRIBUTES = ("_fi_api_key", "_fi_secret_key")
CLASSES = (APIKeyAuth, KnowledgeBase, Client, Dataset)
_MISSING = object()


class Tenant:
    """A tenant's marker keys, distinct for every tenant and every case."""

    def __init__(self, letter: str) -> None:
        self.letter = letter
        self.key = f"fikey-{letter.lower()}-" + secrets.token_hex(10)
        self.secret = f"fisec-{letter.lower()}-" + secrets.token_hex(10)

    def count(self, raw: bytes) -> int:
        """The number of bytes in ``raw`` that hold this tenant's markers, raw or base64."""
        return sum(raw.count(form) * len(form) for form in _marker_forms(self.key, self.secret))


def _route(method: str, path: str) -> Tuple[int, Dict[str, str], bytes]:
    body = b'{"status": true, "result": {"kb_id": "%s", "kb_name": "docs", "id": "%s", "name": "docs", "file_ids": []}}' % (
        KB_ID.encode(),
        KB_ID.encode(),
    )
    if path.startswith(KB_LIST_PATH):
        return 200, {"Content-Type": "application/json"}, b'{"result": {"table_data": [{"id": "%s", "name": "docs"}]}}' % KB_ID.encode()
    if path == KB_PATH and method != "GET":
        return 200, {"Content-Type": "application/json"}, body
    return 200, {"Content-Type": "application/json"}, b"{}"


def _raw(listener) -> bytes:
    lock = getattr(listener, "_lock", None) or threading.Lock()
    with lock:
        return bytes(listener.raw)


class Scene:
    """The two tenants, the listeners and the per-tenant marker byte counts at each listener."""

    def __init__(self, net, site_a: Site, site_b: Site) -> None:
        self.a, self.b = Tenant("A"), Tenant("B")
        self.listeners = {"site-a": site_a, "site-b": site_b, "net-target": net.target, "net-proxy": net.proxy}

    def counts(self) -> Dict[str, Dict[str, int]]:
        return {
            name: {"A": self.a.count(_raw(listener)), "B": self.b.count(_raw(listener))}
            for name, listener in self.listeners.items()
        }

    def report(self, counts: Dict[str, Dict[str, int]]) -> str:
        return "per-tenant marker bytes: " + "; ".join(
            f"{name}: A={value['A']} B={value['B']}" for name, value in counts.items()
        )

    def check(self, label: str) -> None:
        """A's site holds A's markers only, B's site holds B's markers only, the ``net`` listeners hold none."""
        counts = self.counts()
        message = f"{label}: {self.report(counts)}"
        assert counts["site-a"]["A"] > 0, message
        assert counts["site-a"]["B"] == 0, message
        assert counts["site-b"]["B"] > 0, message
        assert counts["site-b"]["A"] == 0, message
        for name in ("net-target", "net-proxy"):
            assert counts[name] == {"A": 0, "B": 0}, message


@contextlib.contextmanager
def scene(net, monkeypatch) -> Iterator[Scene]:
    """Two listeners and two tenants, with FI_API_KEY and FI_SECRET_KEY unset. The key attributes the client
    classes hold on the class itself, if any, are put back as they were when the case ends."""
    monkeypatch.delenv("FI_API_KEY", raising=False)
    monkeypatch.delenv("FI_SECRET_KEY", raising=False)
    saved = {(cls, name): cls.__dict__.get(name, _MISSING) for cls in CLASSES for name in KEY_ATTRIBUTES}
    site_a, site_b = Site(_route), Site(_route)
    try:
        yield Scene(net, site_a, site_b)
    finally:
        site_a.close()
        site_b.close()
        for (cls, name), value in saved.items():
            if value is _MISSING:
                if name in cls.__dict__:
                    delattr(cls, name)
            else:
                setattr(cls, name, value)


def _notes(tmp_path, letter: str) -> str:
    path = tmp_path / f"notes-{letter.lower()}.txt"
    path.write_text(f"notes for tenant {letter}")
    return str(path)


def _kb_with_keys(tenant: Tenant, base: str, monkeypatch, source: str) -> KnowledgeBase:
    """A ``KnowledgeBase`` for ``tenant``: keys passed as arguments, or read from FI_API_KEY and FI_SECRET_KEY."""
    if source == "arguments":
        return KnowledgeBase(fi_api_key=tenant.key, fi_secret_key=tenant.secret, fi_base_url=base)
    monkeypatch.setenv("FI_API_KEY", tenant.key)
    monkeypatch.setenv("FI_SECRET_KEY", tenant.secret)
    try:
        return KnowledgeBase(fi_base_url=base)
    finally:
        monkeypatch.delenv("FI_API_KEY", raising=False)
        monkeypatch.delenv("FI_SECRET_KEY", raising=False)


def _upload(kb: KnowledgeBase, operation: str, path: str) -> None:
    """Upload ``path`` from ``kb`` through ``create_kb`` or ``update_kb``."""
    if operation == "create":
        kb.create_kb(name="docs", file_paths=[path])
    elif operation == "update-cached":
        kb.kb = KnowledgeBaseConfig(id=KB_ID, name="docs")
        kb.update_kb(kb_name="docs", file_paths=[path])
    elif operation == "update-after-create":
        kb.create_kb(name="docs")
        kb.update_kb(kb_name="docs", new_name="docs", file_paths=[path])
    else:
        raise AssertionError(operation)
    assert kb.kb is not None and str(kb.kb.id) == KB_ID


def _ping(client: APIKeyAuth, base: str) -> None:
    client.request(RequestConfig(method=HttpMethod.GET, url=base + "/v1/ping", retry_attempts=1, retry_delay=0, timeout=3))


OPERATIONS = pytest.mark.parametrize("operation", ["create", "update-cached", "update-after-create"])


# ---------------------------------------------------------------------------------------------
# B is a second KnowledgeBase
# ---------------------------------------------------------------------------------------------


@OPERATIONS
@pytest.mark.parametrize("b_keys", ["arguments", "environment"], ids=["b-keys-as-arguments", "b-keys-from-environment"])
def test_kb_upload_from_a_sends_a_keys_when_a_second_kb_client_b_exists(net, monkeypatch, tmp_path, operation, b_keys):
    with scene(net, monkeypatch) as s:
        site_a, site_b = s.listeners["site-a"], s.listeners["site-b"]
        kb_a = KnowledgeBase(fi_api_key=s.a.key, fi_secret_key=s.a.secret, fi_base_url=site_a.base)
        kb_b = _kb_with_keys(s.b, site_b.base, monkeypatch, b_keys)

        _upload(kb_a, operation, _notes(tmp_path, "A"))
        counts = s.counts()
        message = f"after A's {operation} upload: {s.report(counts)}"
        assert counts["site-a"]["A"] > 0, message
        assert counts["site-a"]["B"] == 0, message

        _upload(kb_b, operation, _notes(tmp_path, "B"))
        s.check(f"after A's and B's {operation} uploads")


@pytest.mark.parametrize("operation", ["create", "update-cached"])
def test_kb_uploads_from_a_and_b_in_turn_each_send_their_own_keys(net, monkeypatch, tmp_path, operation):
    with scene(net, monkeypatch) as s:
        site_a, site_b = s.listeners["site-a"], s.listeners["site-b"]
        kb_a = KnowledgeBase(fi_api_key=s.a.key, fi_secret_key=s.a.secret, fi_base_url=site_a.base)
        kb_b = KnowledgeBase(fi_api_key=s.b.key, fi_secret_key=s.b.secret, fi_base_url=site_b.base)
        for _ in range(2):
            _upload(kb_b, operation, _notes(tmp_path, "B"))
            _upload(kb_a, operation, _notes(tmp_path, "A"))
        s.check(f"after alternating {operation} uploads from B and A")


# ---------------------------------------------------------------------------------------------
# B is a client of another class, or APIKeyAuth built directly
# ---------------------------------------------------------------------------------------------


def _client_b(kind: str, tenant: Tenant, base: str) -> APIKeyAuth:
    if kind == "client":
        return Client(fi_api_key=tenant.key, fi_secret_key=tenant.secret, fi_base_url=base)
    if kind == "dataset":
        return Dataset(fi_api_key=tenant.key, fi_secret_key=tenant.secret, fi_base_url=base)
    if kind == "api-key-auth":
        return APIKeyAuth(fi_api_key=tenant.key, fi_secret_key=tenant.secret, fi_base_url=base)
    raise AssertionError(kind)


@OPERATIONS
@pytest.mark.parametrize("kind", ["client", "dataset", "api-key-auth"])
def test_kb_upload_from_a_sends_a_keys_when_a_client_b_of_another_class_exists(net, monkeypatch, tmp_path, operation, kind):
    with scene(net, monkeypatch) as s:
        site_a, site_b = s.listeners["site-a"], s.listeners["site-b"]
        kb_a = KnowledgeBase(fi_api_key=s.a.key, fi_secret_key=s.a.secret, fi_base_url=site_a.base)
        client_b = _client_b(kind, s.b, site_b.base)

        _upload(kb_a, operation, _notes(tmp_path, "A"))
        counts = s.counts()
        message = f"after A's {operation} upload with B as {kind}: {s.report(counts)}"
        assert counts["site-a"]["A"] > 0, message
        assert counts["site-a"]["B"] == 0, message

        _ping(client_b, site_b.base)
        s.check(f"after A's {operation} upload and a request from B as {kind}")
