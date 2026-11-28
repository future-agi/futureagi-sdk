"""Gateway HTTP opt-in compatibility with local request and connection records."""

from __future__ import annotations

import inspect
import socket
import threading
from contextlib import AsyncExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from fi.errors import KeyedProxyRefusedError
from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC, AsyncGateway, Gateway
from fi.gateway._redirect_error import GatewayRedirectRefusedError

KEY = "test-key-marker-1"
AUTH = f"Bearer {KEY}"
NAMED = "gateway.example.test"
FUTURE_AGI = "api.futureagi.com"
AUDIO = b"test-audio"


class Listener(ThreadingHTTPServer):
    def __init__(self, host, *, location=None):
        super().__init__((host, 0), Handler)
        self.connections = 0
        self.requests = []
        self.headers_received = b""
        self.location = location

    def get_request(self):
        connection = super().get_request()
        self.connections += 1
        return connection

    def url(self, host=None):
        return f"http://{host or self.server_address[0]}:{self.server_port}"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.server.requests.append((self.path, self.headers.get("Authorization")))
        self.server.headers_received += self.headers.as_bytes()
        status, content_type, body = 200, "application/json", b'{"object":"list","data":[]}'
        if self.server.location:
            status, body = 307, b""
        elif self.path == "/v1/chat/completions":
            content_type, body = "text/event-stream", b"data: [DONE]\n\n"
        elif self.path == "/v1/audio/speech":
            content_type, body = "audio/mpeg", AUDIO
        self.send_response(status)
        if self.server.location:
            self.send_header("Location", self.server.location)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = respond


@pytest.fixture
def listen(monkeypatch):
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    getaddrinfo = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        name = host.decode("ascii") if isinstance(host, bytes) else host
        if name in {NAMED, FUTURE_AGI}:
            host = "127.0.0.2"
        return getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    listeners = []

    def start(host="127.0.0.2", **kwargs):
        listener = Listener(host, **kwargs)
        thread = threading.Thread(target=listener.serve_forever, args=(0.01,), daemon=True)
        thread.start()
        listeners.append((listener, thread))
        return listener

    yield start
    for listener, thread in listeners:
        listener.shutdown()
        thread.join()
        listener.server_close()


@pytest.fixture(params=(AgentCC, AsyncAgentCC, Gateway, AsyncGateway), ids=lambda cls: cls.__name__)
def client_type(request):
    return request.param


async def _call(client, resource):
    if resource == "models":
        result = client.models.list()
    elif resource == "speech":
        result = client.audio.speech.create(model="m", input="hello", voice="v")
    else:
        result = client.chat.completions.create(
            model="m", messages=[{"role": "user", "content": "hello"}], stream=True,
        )
    if inspect.isawaitable(result):
        result = await result
    if resource == "stream":
        return [chunk async for chunk in result] if hasattr(result, "__aiter__") else list(result)
    return result


async def _exchange(client_type, url, enabled, *, resource="models", proxy=None, copy=None):
    async_client = issubclass(client_type, AsyncAgentCC)
    async with AsyncExitStack() as stack:
        async def use(client):
            if async_client:
                return await stack.enter_async_context(client)
            return stack.enter_context(client)

        options = {}
        if proxy is not None:
            client_cls = httpx.AsyncClient if async_client else httpx.Client
            options["http_client"] = await use(client_cls(**proxy))
        client = await use(client_type(
            api_key=KEY, base_url=url, allow_insecure_http=enabled,
            timeout=2, max_retries=0, **options,
        ))
        if copy == "after-request":
            await _call(client, "models")
        if copy:
            client = await use(client.with_options(timeout=1))
        return await _call(client, resource)


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [True, False, None])
async def test_loopback_with_explicit_option(client_type, listen, enabled):
    target = listen("127.0.0.1")
    assert (await _exchange(client_type, target.url(), enabled)).data == []
    assert target.connections == 1
    assert target.requests == [("/v1/models", AUTH)]


@pytest.mark.asyncio
@pytest.mark.parametrize(("enabled", "env", "allowed"), [
    (True, None, True), (False, "1", False), (None, "1", True), (None, None, False),
    ("1", "1", False),
])
async def test_option_precedes_environment(client_type, listen, monkeypatch, enabled, env, allowed):
    if env is not None:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", env)
    target = listen()
    if allowed:
        assert (await _exchange(client_type, target.url(NAMED), enabled)).data == []
        assert target.connections == 1
        assert target.requests == [("/v1/models", AUTH)]
    else:
        with pytest.raises(AgentCCError) as refusal:
            await _exchange(client_type, target.url(NAMED), enabled)
        assert refusal.value.get_error_code() == "insecure_http_origin"
        assert target.connections == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(("resource", "path", "body", "copy"), [
    ("stream", "/v1/chat/completions", [], "before-request"),
    ("speech", "/v1/audio/speech", AUDIO, "after-request"),
])
async def test_copies_preserve_opt_in_for_streams_and_raw_bytes(client_type, listen, resource, path, body, copy):
    target = listen()
    assert await _exchange(client_type, target.url(NAMED), True, resource=resource, copy=copy) == body
    earlier = [("/v1/models", AUTH)] if copy == "after-request" else []
    assert target.connections == len(earlier) + 1
    assert target.requests == [*earlier, (path, AUTH)]


@pytest.mark.asyncio
async def test_copy_preserves_opt_out(client_type, listen, monkeypatch):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    target = listen()
    with pytest.raises(AgentCCError) as refusal:
        await _exchange(client_type, target.url(NAMED), False, copy="before-request")
    assert refusal.value.get_error_code() == "insecure_http_origin"
    assert target.connections == 0


@pytest.mark.asyncio
async def test_opt_in_does_not_permit_future_agi_http(client_type, listen):
    target = listen()
    with pytest.raises(AgentCCError, match="Future AGI host"):
        await _exchange(client_type, target.url(FUTURE_AGI), True)
    assert target.connections == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["environment", "explicit", "mount"])
async def test_opt_in_refuses_a_proxy_route(client_type, listen, monkeypatch, route):
    target, proxy = listen(), listen("127.0.0.1")
    if route == "environment":
        monkeypatch.setenv("HTTP_PROXY", proxy.url())
        options = {"trust_env": True}
    elif route == "explicit":
        options = {"proxy": proxy.url()}
    else:
        transport = httpx.AsyncHTTPTransport if issubclass(client_type, AsyncAgentCC) else httpx.HTTPTransport
        options = {"mounts": {"http://": transport(proxy=proxy.url())}}
    with pytest.raises(KeyedProxyRefusedError):
        await _exchange(client_type, target.url(NAMED), True, proxy=options)
    assert (target.connections, proxy.connections) == (0, 0)
    assert KEY.encode() not in proxy.headers_received


@pytest.mark.asyncio
async def test_sdk_transport_sends_directly_with_environment_proxy_set(client_type, listen, monkeypatch):
    target, proxy = listen(), listen("127.0.0.1")
    monkeypatch.setenv("HTTP_PROXY", proxy.url())
    assert (await _exchange(client_type, target.url(NAMED), True)).data == []
    assert (target.connections, proxy.connections) == (1, 0)
    assert target.requests == [("/v1/models", AUTH)]
    assert KEY.encode() not in proxy.headers_received


@pytest.mark.asyncio
async def test_opt_in_does_not_permit_keyed_cross_origin_redirect(client_type, listen):
    target = listen("127.0.0.1")
    redirect = listen(location=target.url() + "/v1/models")
    with pytest.raises(GatewayRedirectRefusedError):
        await _exchange(client_type, redirect.url(NAMED), True, proxy={"follow_redirects": True})
    assert (redirect.connections, target.connections) == (1, 0)
    assert redirect.requests == [("/v1/models", AUTH)]
