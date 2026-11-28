import inspect
import json
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Optional
from urllib.parse import parse_qs, urlsplit

import pytest

from fi.errors import ConfigurationError, InsecureHttpRefusedError
from fi.prompt import Prompt
from fi.prompt.cache import PromptCache
from fi.utils.routes import Routes
from tests.test_plain_http_key_guards import PROXY_VARS

KEY = "test-key-marker-1"
SECRET = "test-secret-marker-1"
NAME = "transport-probe"
TEMPLATE_ID = "00000000-0000-0000-0000-000000000001"
CUSTOM = "prompts.example.test"
FUTURE_AGI = "api.futureagi.com"

POSITIONAL = inspect.Parameter.POSITIONAL_OR_KEYWORD
KEYWORD = inspect.Parameter.KEYWORD_ONLY
CREDENTIAL_PARAMS = ("fi_api_key", "fi_secret_key", "fi_base_url")
SIGNATURES = {
    "list_templates": ((), POSITIONAL),
    "delete_template_by_name": (("name",), POSITIONAL),
    "get_template_by_name": (("name", "label", "version"), POSITIONAL),
    "assign_label_to_template_version": (("template_name", "version", "label"), KEYWORD),
    "remove_label_from_template_version": (("template_name", "version", "label"), KEYWORD),
    "set_default_version": (("template_name", "version"), KEYWORD),
    "get_template_labels": (("template_name", "template_id"), KEYWORD),
}
LABEL_ARGS = {"template_name": NAME, "version": "v1", "label": "staging"}
CALLS = [
    ("list_templates", (), {}, 1),
    ("delete_template_by_name", (NAME,), {}, 2),
    ("get_template_by_name", (NAME,), {}, 2),
    pytest.param("get_template_by_name", (NAME,), {"label": "staging"}, 2, id="get_template_by_name_with_label"),
    ("assign_label_to_template_version", (), LABEL_ARGS, 4),
    ("remove_label_from_template_version", (), LABEL_ARGS, 4),
    ("set_default_version", (), {"template_name": NAME, "version": "v1"}, 1),
    ("get_template_labels", (), {"template_name": NAME}, 1),
]


class PromptHandler(BaseHTTPRequestHandler):
    def _reply(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.keys.append((self.headers.get("X-Api-Key"), self.headers.get("X-Secret-Key")))
        url = urlsplit(self.path)
        route = url.path.lstrip("/")
        status = 200
        if "search" in parse_qs(url.query):
            payload = {"results": [{"id": TEMPLATE_ID, "name": NAME}]}
        elif route == Routes.get_template_version_history.value:
            payload = {"results": [{"id": "version-id", "template_version": "v1"}]}
        elif route == Routes.prompt_labels.value:
            payload = {"results": [{"id": "label-id", "name": "staging"}]}
        elif route in (Routes.get_template_by_name.value, Routes.prompt_label_get_by_name.value):
            if self.server.lookup_unavailable:
                status = 503
            payload = {"result": {"id": TEMPLATE_ID, "name": NAME, "version": "v1"}}
        else:
            payload = {"status": True}
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = do_DELETE = _reply

    def log_message(self, *_):
        pass


class PromptServer(HTTPServer):
    def __init__(self, address):
        super().__init__((address, 0), PromptHandler)
        self.connections = 0
        self.keys = []
        self.lookup_unavailable = False

    def get_request(self):
        conn, address = super().get_request()
        self.connections += 1
        return conn, address


@pytest.fixture
def endpoint(monkeypatch, host):
    for name in (*PROXY_VARS, "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("fi.prompt.client.prompt_cache", PromptCache(max_workers=0))
    address = "127.0.0.1" if host == "127.0.0.1" else "127.0.0.2"
    getaddrinfo = socket.getaddrinfo

    def resolve(name, *args, **kwargs):
        if name in (CUSTOM, FUTURE_AGI):
            name = address
        return getaddrinfo(name, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    with PromptServer(address) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        try:
            yield server, dict(
                fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=f"http://{host}:{server.server_port}"
            )
        finally:
            server.shutdown()
            thread.join()


@pytest.mark.parametrize("method", SIGNATURES)
def test_published_parameter_position_and_kind(method):
    leading, kind = SIGNATURES[method]
    params = inspect.signature(getattr(Prompt, method)).parameters
    assert tuple(params) == (*leading, *CREDENTIAL_PARAMS, "allow_insecure_http")
    assert all(params[name].kind == kind for name in (*leading, *CREDENTIAL_PARAMS))
    opt_in = params["allow_insecure_http"]
    assert opt_in.kind == KEYWORD
    assert opt_in.default is None
    assert opt_in.annotation == Optional[bool]


@pytest.mark.parametrize("method,args,kwargs,requests", CALLS, ids=[
    entry[0] if isinstance(entry, tuple) else entry.id for entry in CALLS
])
@pytest.mark.parametrize(
    "host,opt_in,env,refusal",
    [
        ("127.0.0.1", True, None, None),
        (CUSTOM, True, None, None),
        (CUSTOM, None, "1", None),
        (CUSTOM, False, "1", ConfigurationError),
        (FUTURE_AGI, True, None, InsecureHttpRefusedError),
    ],
    ids=["loopback", "custom-opt-in", "environment-opt-in", "custom-opt-out", "future-agi"],
)
def test_classmethod_transport(endpoint, monkeypatch, method, args, kwargs, requests, opt_in, env, refusal):
    server, auth = endpoint
    if env is not None:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", env)
    call = getattr(Prompt, method)
    if refusal:
        with pytest.raises(refusal) as error:
            call(*args, **kwargs, **auth, allow_insecure_http=opt_in)
        assert error.value.code == (
            "INSECURE_HTTP_REFUSED" if refusal is InsecureHttpRefusedError else "insecure_http_origin"
        )
        assert server.connections == 0
        assert server.keys == []
    else:
        result = call(*args, **kwargs, **auth, allow_insecure_http=opt_in)
        if isinstance(result, Prompt):
            try:
                result.list_labels()
            finally:
                result.close()
        assert server.keys == [(KEY, SECRET)] * requests


@pytest.mark.parametrize("host", [CUSTOM])
@pytest.mark.parametrize("stale", [False, True], ids=["fresh", "stale"])
def test_cached_prompt_preserves_opt_in(endpoint, monkeypatch, stale):
    server, auth = endpoint
    if stale:
        monkeypatch.setattr("fi.prompt.client.prompt_cache._ttl_sec", -1)
    Prompt.get_template_by_name(NAME, label="staging", **auth, allow_insecure_http=True).close()
    server.lookup_unavailable = stale
    prompt = Prompt.get_template_by_name(NAME, label="staging", **auth, allow_insecure_http=True)
    try:
        assert str(prompt.template.id) == TEMPLATE_ID
        prompt.list_labels()
    finally:
        prompt.close()
    assert server.keys == [(KEY, SECRET)] * (3 if stale else 2)

    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    before = server.connections
    with pytest.raises(ConfigurationError) as error:
        Prompt.get_template_by_name(NAME, label="staging", **auth, allow_insecure_http=False)
    assert error.value.code == "insecure_http_origin"
    assert server.connections == before
