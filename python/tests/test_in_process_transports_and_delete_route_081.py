from __future__ import annotations

import asyncio
import json
import socket
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import httpx
import pytest
from fi.gateway import AgentCC, AsyncAgentCC
from fi.platform import AsyncClient, Client
from fi.prompt import Prompt

KEY = "test-key-marker-1"
SECRET = "test-secret-marker-1"
CUSTOM_HOST = "selfhosted.example"
FUTURE_AGI_HOST = "api.futureagi.com"
IDN_HOST = "b\u00fccher.example"  # a host written with a non-ASCII character
NAME = "route-probe"
TEMPLATE_ID = "00000000-0000-0000-0000-000000000001"
LOOKUP = ("GET", f"/model-hub/prompt-labels/get-by-name/?name={NAME}")
DELETE = ("DELETE", f"/model-hub/prompt-templates/{TEMPLATE_ID}/")
PROMPT_REPLIES = {
    LOOKUP: {"result": {"id": TEMPLATE_ID, "name": NAME, "version": "v1"}},
    DELETE: {"status": True},
}
PAYLOAD = {
    "object": "list",
    "data": [{"id": "handler-model", "object": "model", "created": 1, "owned_by": "test"}],
}
CLIENTS = (Client, AsyncClient, AgentCC, AsyncAgentCC)
ASYNC_CLIENTS = (AsyncClient, AsyncAgentCC)
TRANSPORT_CASES = [
    (client_type, kind)
    for client_type in CLIENTS
    for kind in ("mock", "asgi" if client_type in ASYNC_CLIENTS else "wsgi")
]


def _is_gateway(client_type):
    return client_type in (AgentCC, AsyncAgentCC)


def _path(client_type):
    return "/v1/models" if _is_gateway(client_type) else "/ping"


def _exchange(client_type, url, transport):
    options = dict(api_key=KEY, base_url=url, max_retries=0, timeout=2)
    gateway = _is_gateway(client_type)
    if not gateway:
        options["secret_key"] = SECRET

    async def run_async():
        async with httpx.AsyncClient(transport=transport) as http:
            async with client_type(http_client=http, **options) as client:
                if gateway:
                    return (await client.models.list()).model_dump()
                return await client.request("GET", _path(client_type))

    if client_type in ASYNC_CLIENTS:
        return asyncio.run(run_async())
    with httpx.Client(transport=transport) as http:
        with client_type(http_client=http, **options) as client:
            return client.models.list().model_dump() if gateway else client.request("GET", _path(client_type))


def _in_process_transport(kind, record):
    body = json.dumps(PAYLOAD).encode()

    def mock(request):
        record(request.method, request.url.host, request.url.path, request.headers)
        return httpx.Response(200, json=PAYLOAD)

    def wsgi(environ, start_response):
        headers = httpx.Headers({
            name[5:].replace("_", "-"): value
            for name, value in environ.items()
            if name.startswith("HTTP_")
        })
        record(environ["REQUEST_METHOD"], headers["Host"], environ["PATH_INFO"], headers)
        start_response("200 OK", [("Content-Type", "application/json")])
        return [body]

    async def asgi(scope, receive, send):
        headers = httpx.Headers(scope["headers"])
        record(scope["method"], headers["Host"], scope["path"], headers)
        await send({"type": "http.response.start", "status": 200,
                    "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": body})

    if kind == "mock":
        return httpx.MockTransport(mock)
    if kind == "wsgi":
        return httpx.WSGITransport(wsgi)
    return httpx.ASGITransport(asgi)


class _ConnectingMock(httpx.MockTransport):
    def __init__(self, handler, port):
        super().__init__(handler)
        self.port = port

    def handle_request(self, request):
        self.handler(request)
        target = request.url.copy_with(host="127.0.0.1", port=self.port)
        with httpx.Client(trust_env=False, timeout=2) as client:
            return client.request(request.method, target, headers=request.headers)

    async def handle_async_request(self, request):
        self.handler(request)
        target = request.url.copy_with(host="127.0.0.1", port=self.port)
        async with httpx.AsyncClient(trust_env=False, timeout=2) as client:
            return await client.request(request.method, target, headers=request.headers)


class _Handler(BaseHTTPRequestHandler):
    def _respond(self):
        request = (self.command, self.path)
        self.server.requests.append(request)
        payload = self.server.replies.get(request)
        body = json.dumps(payload if payload is not None else {"error": "unexpected route"}).encode()
        self.send_response(200 if payload is not None else 404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_DELETE = _respond

    def log_message(self, *_):
        pass


class _Listener(ThreadingHTTPServer):
    def __init__(self, replies):
        super().__init__(("127.0.0.1", 0), _Handler)
        self.replies = replies
        self.requests = []
        self.connections = 0

    def get_request(self):
        connection, address = super().get_request()
        self.connections += 1
        return connection, address


@contextmanager
def _listen(replies):
    with _Listener(replies) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join()


@pytest.fixture(autouse=True)
def _isolate_http(monkeypatch):
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    for name in (
        "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS", "FI_API_KEY", "FI_SECRET_KEY",
        "FI_GATEWAY_API_KEY", "AGENTCC_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    getaddrinfo = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        if host in (CUSTOM_HOST, FUTURE_AGI_HOST, CUSTOM_HOST.encode(), FUTURE_AGI_HOST.encode()):
            host = "127.0.0.1"
        return getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)


@pytest.mark.parametrize("host", [CUSTOM_HOST, FUTURE_AGI_HOST, IDN_HOST], ids=["custom", "future-agi", "idn"])
@pytest.mark.parametrize("client_type,kind", TRANSPORT_CASES,
                         ids=[f"{cls.__name__}-{kind}" for cls, kind in TRANSPORT_CASES])
def test_item3_exact_in_process_transport_returns_handler_response(client_type, kind, host):
    calls = []

    def record(method, host, path, headers):
        if _is_gateway(client_type):
            keyed = headers.get("Authorization") == f"Bearer {KEY}"
        else:
            keyed = headers.get("X-Api-Key") == KEY and headers.get("X-Secret-Key") == SECRET
        calls.append((method, host, path, keyed))

    transport = _in_process_transport(kind, record)
    assert _exchange(client_type, f"http://{host}", transport) == PAYLOAD
    sent_host = httpx.URL(f"http://{host}/").raw_host.decode("ascii")  # the A-label httpx sends
    assert calls in ([("GET", host, _path(client_type), True)], [("GET", sent_host, _path(client_type), True)])


@pytest.mark.parametrize("client_type", CLIENTS, ids=lambda cls: cls.__name__)
def test_item3_connecting_mock_subclass_still_refused(client_type):
    from fi.errors import InsecureHttpRefusedError

    calls = []
    with _listen({("GET", _path(client_type)): PAYLOAD}) as sink:
        transport = _ConnectingMock(calls.append, sink.server_port)
        with pytest.raises(InsecureHttpRefusedError):
            _exchange(client_type, f"http://{FUTURE_AGI_HOST}", transport)
        assert calls == []
        assert sink.connections == 0
        assert sink.requests == []


def _delete_template(host, port):
    return Prompt.delete_template_by_name(
        NAME,
        fi_api_key=KEY,
        fi_secret_key=SECRET,
        fi_base_url=f"http://{host}:{port}",
        allow_insecure_http=True,
    )


def test_item4_delete_template_by_name_uses_label_lookup_then_delete():
    with _listen(PROMPT_REPLIES) as server:
        assert _delete_template(CUSTOM_HOST, server.server_port) is True
        assert server.requests == [LOOKUP, DELETE]


def test_item4_delete_template_by_name_still_refuses_future_agi_http():
    from fi.errors import InsecureHttpRefusedError

    with _listen(PROMPT_REPLIES) as server:
        with pytest.raises(InsecureHttpRefusedError):
            _delete_template(FUTURE_AGI_HOST, server.server_port)
        assert server.connections == 0
        assert server.requests == []


@pytest.mark.parametrize("client_type,kind", TRANSPORT_CASES,
                         ids=[f"{cls.__name__}-{kind}" for cls, kind in TRANSPORT_CASES])
def test_item3_exact_in_process_transport_reads_an_https_non_ascii_host_as_sent(client_type, kind):
    calls = []
    transport = _in_process_transport(kind, lambda method, host, path, headers: calls.append((method, host, path)))
    assert _exchange(client_type, f"https://{IDN_HOST}", transport) == PAYLOAD
    sent_host = httpx.URL(f"https://{IDN_HOST}/").raw_host.decode("ascii")
    assert calls in ([("GET", IDN_HOST, _path(client_type))], [("GET", sent_host, _path(client_type))])
