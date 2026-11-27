"""One client in the process, with one tenant's keys: the keys each SDK sender puts on the wire.

Each case builds one client for one tenant (keys given as arguments, or read from ``FI_API_KEY`` and
``FI_SECRET_KEY``) against a listener on 127.0.0.1, sends through one SDK path, and reads the requests that
reached the listener. An environment proxy points at the proxy listener of ``test_plain_http_key_guards``,
whose lookup shim also applies here, so no case reaches a real host. The marker keys are made in each case, and
each assertion message prints, for every listener, the number of bytes holding each tenant's markers.

Rules under test:

* each request a sender makes carries ``X-Api-Key`` and ``X-Secret-Key`` with the tenant's values;
* keys given as arguments win over the environment;
* a client built without one or both keys raises ``MissingAuthError`` with code
  ``MISSING_FI_CLIENT_AUTHENTICATION`` and names the key that is missing;
* the client holds ``_fi_api_key``, ``_fi_secret_key`` and ``_default_headers`` with the tenant's values.
"""

from __future__ import annotations

import contextlib
import json
import secrets
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pytest

from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.client import Client
from fi.datasets.dataset import Dataset, LRUCache
from fi.kb.client import KnowledgeBase
from fi.prompt.client import Prompt
from fi.prompt.types import PromptTemplate
from fi.utils.errors import MissingAuthError
from tests.test_plain_http_key_guards import _marker_forms, net, use_proxy  # noqa: F401

AUTH_CODE = "MISSING_FI_CLIENT_AUTHENTICATION"
ENV_NAMES = ("FI_API_KEY", "FI_SECRET_KEY")
DATASET = "single-client-probe"
KB_ID = "00000000-0000-4000-8000-0000000000a1"
PROMPT_ID = "00000000-0000-4000-8000-0000000000b1"
PING_PATH = "/v1/ping"
NAMES_PATH = "/model-hub/develops/get-datasets-names/"
KB_PATH = "/model-hub/knowledge-base/"
KB_LIST_PATH = "/model-hub/knowledge-base/list/"
PROMPT_BY_NAME_PATH = "/model-hub/prompt-labels/get-by-name/"
PROMPT_LIST_PATH = "/model-hub/prompt-templates/"


def tenant(letter: str) -> Tuple[str, str]:
    """A pair of marker keys for one tenant, made fresh for each call."""
    return "fikey-" + letter + "-" + secrets.token_hex(10), "fisec-" + letter + "-" + secrets.token_hex(10)


def _route(method: str, path: str) -> dict:
    if path == NAMES_PATH:
        return {"result": {"datasets": [{"datasetId": str(uuid.uuid4()), "name": DATASET, "modelType": "GenerativeLLM"}]}}
    if path == KB_LIST_PATH:
        return {"result": {"table_data": [{"id": KB_ID, "name": "docs"}]}}
    if path == KB_PATH:
        return {"status": True, "result": {"kb_id": KB_ID, "kb_name": "docs", "id": KB_ID, "name": "docs"}}
    if path == PROMPT_BY_NAME_PATH:
        return {"result": {"id": PROMPT_ID, "name": "probe", "prompt_config": []}}
    if path == PROMPT_LIST_PATH:
        return {"results": []}
    return {"status": True, "result": {}}


class Desk:
    """An HTTP/1.1 listener on 127.0.0.1 that answers each SDK route with a small JSON body and keeps each
    request: method, path, the two key headers and the raw bytes."""

    def __init__(self) -> None:
        self.requests: List[Tuple[str, str, Optional[str], Optional[str]]] = []
        self.raw = b""
        self._lock = threading.Lock()
        desk = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def _answer(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                path = urlparse(self.path).path
                with desk._lock:
                    desk.requests.append((self.command, path, self.headers.get("X-Api-Key"), self.headers.get("X-Secret-Key")))
                    desk.raw += self.requestline.encode() + b"\r\n" + bytes(self.headers) + body
                payload = json.dumps(_route(self.command, path)).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(payload)
                self.close_connection = True

            do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _answer

        class Server(ThreadingHTTPServer):
            daemon_threads = True

        self._server = Server(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

    def bytes_of(self, *values: str) -> int:
        time.sleep(0.1)
        with self._lock:
            raw = self.raw
        return sum(raw.count(form) for form in _marker_forms(*values))

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


def _count(raw: bytes, *values: str) -> int:
    return sum(raw.count(form) for form in _marker_forms(*values))


def _report(desk: Desk, net, tenants: Dict[str, Tuple[str, str]]) -> str:  # noqa: F811
    time.sleep(0.1)
    sinks = {"listener": desk.raw, "proxy": net.proxy.raw, "named-target": net.target.raw}
    parts = []
    for sink, raw in sinks.items():
        counts = ", ".join(f"tenant {name}: {_count(raw, *keys)} marker bytes" for name, keys in tenants.items())
        parts.append(f"{sink} ({counts})")
    parts.append(f"proxy connections: {net.proxy.connections}; listener requests: {[r[:2] for r in desk.requests]}")
    return "; ".join(parts)


@contextlib.contextmanager
def _scene(monkeypatch, net):  # noqa: F811
    """A listener, an environment proxy set to the proxy listener, no key variables and an empty dataset cache."""
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    use_proxy(monkeypatch, net)
    monkeypatch.setattr(Dataset, "_dataset_instance_cache", LRUCache(capacity=100))
    desk = Desk()
    try:
        yield desk
    finally:
        desk.close()


class CustomAuth(APIKeyAuth):
    """A caller's own subclass of ``APIKeyAuth``."""


def _ping(client) -> None:
    client.request(RequestConfig(method=HttpMethod.GET, url=client._base_url + PING_PATH, retry_attempts=1, retry_delay=0, timeout=5))


def _notes(tmp_path) -> str:
    path = tmp_path / "notes.txt"
    path.write_text("notes")
    return str(path)


# Each sender builds one client with ``keys`` (``fi_api_key`` / ``fi_secret_key``, possibly empty) and sends
# through one SDK path; the second item is the path the request reaches.
SENDERS = {
    "api-key-auth-request": (lambda base, keys, tmp: _ping(APIKeyAuth(fi_base_url=base, **keys)), PING_PATH),
    "api-key-auth-subclass-request": (lambda base, keys, tmp: _ping(CustomAuth(fi_base_url=base, **keys)), PING_PATH),
    "fi-client-request": (lambda base, keys, tmp: _ping(Client(fi_base_url=base, **keys)), PING_PATH),
    "kb-create-upload": (
        lambda base, keys, tmp: KnowledgeBase(fi_base_url=base, **keys).create_kb(name="docs", file_paths=[_notes(tmp)]),
        KB_PATH,
    ),
    "kb-update-upload": (
        lambda base, keys, tmp: KnowledgeBase(kb_name="docs", fi_base_url=base, **keys).update_kb(
            kb_name="docs", new_name="docs", file_paths=[_notes(tmp)]
        ),
        KB_PATH,
    ),
    "dataset-get-config": (lambda base, keys, tmp: Dataset.get_dataset_config(DATASET, fi_base_url=base, **keys), NAMES_PATH),
    "prompt-list-templates": (lambda base, keys, tmp: Prompt.list_templates(fi_base_url=base, **keys), PROMPT_LIST_PATH),
    "prompt-template-by-name": (
        lambda base, keys, tmp: Prompt(template=PromptTemplate(name="probe"), fi_base_url=base, **keys),
        PROMPT_BY_NAME_PATH,
    ),
}
senders = pytest.mark.parametrize("sender", list(SENDERS), ids=list(SENDERS))


def _check_sent(desk: Desk, net, sender: str, key: str, secret: str, tenants: Dict[str, Tuple[str, str]]) -> None:  # noqa: F811
    report = _report(desk, net, tenants)
    path = SENDERS[sender][1]
    assert any(entry[1] == path for entry in desk.requests), f"no request reached {path}; {report}"
    for method, at, api_key, secret_key in desk.requests:
        assert (api_key, secret_key) == (key, secret), f"{method} {at} carried other key headers; {report}"
    assert desk.bytes_of(key, secret) > 0, report
    assert (_count(net.proxy.raw, key, secret), net.proxy.connections, _count(net.target.raw, key, secret)) == (0, 0, 0), report


# ---------------------------------------------------------------------------------------------
# keys given as arguments
# ---------------------------------------------------------------------------------------------


@senders
def test_keys_given_as_arguments_are_sent_by_each_sender(monkeypatch, net, tmp_path, sender):  # noqa: F811
    key, secret = tenant("a")
    with _scene(monkeypatch, net) as desk:
        SENDERS[sender][0](desk.base, {"fi_api_key": key, "fi_secret_key": secret}, tmp_path)
        _check_sent(desk, net, sender, key, secret, {"a": (key, secret)})


# ---------------------------------------------------------------------------------------------
# keys read from FI_API_KEY and FI_SECRET_KEY
# ---------------------------------------------------------------------------------------------


@senders
def test_keys_from_the_environment_are_sent_by_each_sender(monkeypatch, net, tmp_path, sender):  # noqa: F811
    key, secret = tenant("a")
    with _scene(monkeypatch, net) as desk:
        monkeypatch.setenv("FI_API_KEY", key)
        monkeypatch.setenv("FI_SECRET_KEY", secret)
        SENDERS[sender][0](desk.base, {}, tmp_path)
        _check_sent(desk, net, sender, key, secret, {"a": (key, secret)})


# ---------------------------------------------------------------------------------------------
# keys given as arguments win over the environment
# ---------------------------------------------------------------------------------------------


@senders
def test_keys_given_as_arguments_win_over_the_environment(monkeypatch, net, tmp_path, sender):  # noqa: F811
    key, secret = tenant("a")
    env_key, env_secret = tenant("e")
    tenants = {"a (arguments)": (key, secret), "e (environment)": (env_key, env_secret)}
    with _scene(monkeypatch, net) as desk:
        monkeypatch.setenv("FI_API_KEY", env_key)
        monkeypatch.setenv("FI_SECRET_KEY", env_secret)
        SENDERS[sender][0](desk.base, {"fi_api_key": key, "fi_secret_key": secret}, tmp_path)
        _check_sent(desk, net, sender, key, secret, tenants)
        assert desk.bytes_of(env_key, env_secret) == 0, _report(desk, net, tenants)


@pytest.mark.parametrize("given", ["api-key", "secret-key"])
def test_one_key_given_as_an_argument_wins_and_the_other_is_read_from_the_environment(monkeypatch, net, given):  # noqa: F811
    key, secret = tenant("a")
    env_key, env_secret = tenant("e")
    tenants = {"a (arguments)": (key, secret), "e (environment)": (env_key, env_secret)}
    with _scene(monkeypatch, net) as desk:
        monkeypatch.setenv("FI_API_KEY", env_key)
        monkeypatch.setenv("FI_SECRET_KEY", env_secret)
        if given == "api-key":
            client, expected = Client(fi_api_key=key, fi_base_url=desk.base), (key, env_secret)
        else:
            client, expected = Client(fi_secret_key=secret, fi_base_url=desk.base), (env_key, secret)
        _ping(client)
        report = _report(desk, net, tenants)
        assert [entry[2:] for entry in desk.requests] == [expected], report
        assert (client._fi_api_key, client._fi_secret_key) == expected, report


# ---------------------------------------------------------------------------------------------
# missing keys
# ---------------------------------------------------------------------------------------------


CLIENTS = {
    "api-key-auth": APIKeyAuth,
    "api-key-auth-subclass": CustomAuth,
    "fi-client": Client,
    "kb": KnowledgeBase,
    "dataset": Dataset,
    "prompt": Prompt,
}
clients = pytest.mark.parametrize("kind", list(CLIENTS), ids=list(CLIENTS))

# (api key present, secret key present, source of the present keys)
MISSING = {
    "api-key-missing-secret-as-argument": (False, True, "arguments"),
    "api-key-missing-secret-from-environment": (False, True, "environment"),
    "secret-key-missing-api-key-as-argument": (True, False, "arguments"),
    "secret-key-missing-api-key-from-environment": (True, False, "environment"),
    "both-keys-missing": (False, False, "arguments"),
}


@clients
@pytest.mark.parametrize("case", list(MISSING), ids=list(MISSING))
def test_missing_keys_raise_missing_auth_error_naming_the_missing_key(monkeypatch, net, kind, case):  # noqa: F811
    key, secret = tenant("a")
    has_key, has_secret, source = MISSING[case]
    with _scene(monkeypatch, net) as desk:
        present = {}
        if has_key:
            present["FI_API_KEY"] = key
        if has_secret:
            present["FI_SECRET_KEY"] = secret
        kwargs = {}
        if source == "environment":
            for name, value in present.items():
                monkeypatch.setenv(name, value)
        else:
            kwargs = {{"FI_API_KEY": "fi_api_key", "FI_SECRET_KEY": "fi_secret_key"}[name]: value for name, value in present.items()}
        with pytest.raises(MissingAuthError) as caught:
            CLIENTS[kind](fi_base_url=desk.base, **kwargs)
        error = caught.value
        report = _report(desk, net, {"a": (key, secret)})
        assert error.get_error_code() == AUTH_CODE, f"{error!r}; {report}"
        assert (error.missing_api_key, error.missing_secret_key) == (not has_key, not has_secret), f"{error!r}; {report}"
        message = str(error)
        assert ("'fi_api_key'" in message.split("Missing:")[-1]) == (not has_key), message
        assert ("'fi_secret_key'" in message.split("Missing:")[-1]) == (not has_secret), message
        assert key not in message and secret not in message and key not in repr(error) and secret not in repr(error), message
        assert desk.requests == [], report
        assert (desk.bytes_of(key, secret), net.proxy.connections, net.target.connections) == (0, 0, 0), report


# ---------------------------------------------------------------------------------------------
# the attributes the SDK reads
# ---------------------------------------------------------------------------------------------


@clients
@pytest.mark.parametrize("source", ["arguments", "environment"])
def test_client_holds_the_tenant_keys_in_its_private_attributes(monkeypatch, net, kind, source):  # noqa: F811
    key, secret = tenant("a")
    with _scene(monkeypatch, net) as desk:
        if source == "environment":
            monkeypatch.setenv("FI_API_KEY", key)
            monkeypatch.setenv("FI_SECRET_KEY", secret)
            client = CLIENTS[kind](fi_base_url=desk.base)
        else:
            client = CLIENTS[kind](fi_api_key=key, fi_secret_key=secret, fi_base_url=desk.base)
        report = _report(desk, net, {"a": (key, secret)})
        assert client._fi_api_key == key, report
        assert client._fi_secret_key == secret, report
        assert client._default_headers == {"X-Api-Key": key, "X-Secret-Key": secret}, report
        assert client._base_url == desk.base, report
