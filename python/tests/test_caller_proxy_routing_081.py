"""Keyed plain HTTP follows the proxy selection of the caller's sending client."""

from __future__ import annotations

import asyncio
import socket
import threading
from contextlib import ExitStack, contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest
import requests
from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.gateway import AgentCC
from fi.platform import AsyncClient, Client
from requests_futures.sessions import FuturesSession

KEY = "test-api-key-proxy-route-marker"
SECRET = "test-secret-key-proxy-route-marker"
GATEWAY_KEY = "sk-agentcc-test-proxy-route-marker"
LOOPBACK = "127.0.0.1"
OPT_IN = "direct.example.test"
MODELS = {"object": "list", "data": []}


class Sink(ThreadingHTTPServer):
    def __init__(self):
        super().__init__((LOOPBACK, 0), Handler)
        self.connections = 0
        self.requests = []
        self.marker_count = 0

    def get_request(self):
        connection = super().get_request()
        self.connections += 1
        return connection

    def url(self, host=LOOPBACK):
        return f"http://{host}:{self.server_port}"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self):
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        header_bytes = self.headers.as_bytes()
        self.server.marker_count += sum(
            header_bytes.count(key.encode()) for key in (KEY, SECRET, GATEWAY_KEY)
        )
        self.server.requests.append(
            (
                self.command,
                self.path,
                self.headers.get("X-Api-Key"),
                self.headers.get("X-Secret-Key"),
                self.headers.get("Authorization"),
            )
        )
        # A CONNECT is recorded but does not open a tunnel.
        status, body = (
            (502, b"{}")
            if self.command == "CONNECT"
            else (200, b'{"object":"list","data":[]}')
        )
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_CONNECT = respond


@pytest.fixture
def sinks(monkeypatch, tmp_path):
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    monkeypatch.delenv("REQUEST_METHOD", raising=False)
    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)
    monkeypatch.setenv("NETRC", str(tmp_path / "empty-netrc"))
    getaddrinfo = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        if host in (OPT_IN, OPT_IN.encode()):
            host = LOOPBACK
        return getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    with ExitStack() as stack:

        def start():
            sink = stack.enter_context(Sink())
            thread = threading.Thread(
                target=sink.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
            )
            thread.start()
            stack.callback(thread.join)
            stack.callback(sink.shutdown)
            return sink

        yield start(), start()


def _platform_options(url, http_client):
    return {
        "api_key": KEY,
        "secret_key": SECRET,
        "base_url": url,
        "http_client": http_client,
        "max_retries": 0,
        "timeout": 2,
    }


async def _send_async_platform(url, trust_env):
    async with (
        httpx.AsyncClient(trust_env=trust_env) as caller,
        AsyncClient(**_platform_options(url, caller)) as client,
    ):
        return await client.request("GET", "/probe", unwrap=None)


def _send_api_key_auth(url, session):
    client = APIKeyAuth(
        fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=url, session=session
    )
    response = client.request(
        RequestConfig(
            method=HttpMethod.GET, url=url + "/probe", retry_attempts=1, timeout=2
        )
    )
    assert response.status_code == 200
    return response.json()


def _send(sender, url, trust_env):
    if sender == "platform-async":
        return asyncio.run(_send_async_platform(url, trust_env))
    if sender == "api-key-auth":
        # A bare requests.Session checks the route on the wire: 0.8.1 sends the same one request direct, then raises
        # AttributeError reading the answer; the FuturesSession form below matches 0.8.1 end to end.
        with requests.Session() as caller:
            caller.trust_env = trust_env
            return _send_api_key_auth(url, caller)
    if sender == "api-key-auth-futures":
        with requests.Session() as inner, FuturesSession(session=inner) as caller:
            inner.trust_env = trust_env
            return _send_api_key_auth(url, caller)
    with httpx.Client(trust_env=trust_env) as caller:
        if sender == "agentcc":
            with AgentCC(
                api_key=GATEWAY_KEY,
                base_url=url,
                http_client=caller,
                max_retries=0,
                timeout=2,
            ) as client:
                return client.models.list().data
        with Client(**_platform_options(url, caller)) as client:
            return client.request("GET", "/probe", unwrap=None)


def _assert_no_request(sink):
    assert sink.requests == []
    assert sink.marker_count == 0
    assert sink.connections == 0


@contextmanager
def _expect_proxy_refusal(target, proxy):
    from fi.errors import KeyedProxyRefusedError

    try:
        with pytest.raises(KeyedProxyRefusedError):
            yield
    finally:
        _assert_no_request(target)
        _assert_no_request(proxy)


def _assert_received_directly(target, proxy, sender):
    _assert_no_request(proxy)
    assert target.connections == 1
    if sender == "agentcc":
        assert target.requests == [
            ("GET", "/v1/models", None, None, f"Bearer {GATEWAY_KEY}")
        ]
        assert target.marker_count == 1
    else:
        assert target.requests == [("GET", "/probe", KEY, SECRET, None)]
        assert target.marker_count == 2


@pytest.mark.parametrize(
    "sender", ["platform-sync", "platform-async", "agentcc", "api-key-auth", "api-key-auth-futures"]
)
@pytest.mark.parametrize("host", [LOOPBACK, OPT_IN], ids=["loopback", "opt-in"])
@pytest.mark.parametrize("trust_env", [False, True], ids=["ignore-env", "trust-env"])
@pytest.mark.parametrize(
    "use_env_proxy", [False, True], ids=["proxy-unset", "proxy-set"]
)
def test_item1_caller_proxy_selection(
    sinks, monkeypatch, sender, host, trust_env, use_env_proxy
):
    target, proxy = sinks
    if host == OPT_IN:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    if use_env_proxy:
        monkeypatch.setenv("HTTP_PROXY", proxy.url())
    url = target.url(host)
    if trust_env and use_env_proxy:
        with _expect_proxy_refusal(target, proxy):
            _send(sender, url, trust_env)
    else:
        assert _send(sender, url, trust_env) == ([] if sender == "agentcc" else MODELS)
        _assert_received_directly(target, proxy, sender)


@pytest.mark.parametrize("workers", [None, 1], ids=["default-workers", "one-worker"])
@pytest.mark.parametrize(
    "route", ["outer-proxy", "inner-proxy", "unwrapped-proxy", "outer-env-proxy"]
)
def test_item2_futures_effective_proxy_selection(sinks, monkeypatch, workers, route):
    target, proxy = sinks
    with ExitStack() as stack:
        options = {} if workers is None else {"max_workers": workers}
        if route != "unwrapped-proxy":
            inner = stack.enter_context(requests.Session())
            inner.trust_env = False
            options["session"] = inner
        outer = stack.enter_context(FuturesSession(**options))
        outer.trust_env = route == "outer-env-proxy"
        if route == "outer-env-proxy":
            monkeypatch.setenv("HTTP_PROXY", proxy.url())
        elif route == "inner-proxy":
            inner.proxies = {"http": proxy.url()}
        else:
            outer.proxies = {"http": proxy.url()}
        if route in ("inner-proxy", "unwrapped-proxy"):
            with _expect_proxy_refusal(target, proxy):
                _send_api_key_auth(target.url(), outer)
        else:
            assert _send_api_key_auth(target.url(), outer) == MODELS
            _assert_received_directly(target, proxy, "api-key-auth")


def test_item2_a_proxy_manager_cached_by_an_unkeyed_send_does_not_refuse_a_direct_send(sinks):
    target, proxy = sinks
    with requests.Session() as inner, FuturesSession(session=inner) as outer:
        inner.trust_env = False
        inner.get(target.url() + "/warmup", proxies={"http": proxy.url()}, timeout=2)  # unkeyed, through the proxy
        proxy.requests.clear()
        proxy.connections = 0
        target.requests.clear()
        target.connections = 0
        assert _send_api_key_auth(target.url(), outer) == MODELS
        _assert_received_directly(target, proxy, "api-key-auth")


class _ForwardingFuturesSession(FuturesSession):
    def request(self, *args, **kwargs):
        return super().request(*args, **kwargs)


@pytest.mark.parametrize("proxied", ["outer", "outer-env", "outer-with-inner-hook", "inner"])
def test_item2_a_forwarding_futures_session_is_judged_by_the_session_that_sends(sinks, monkeypatch, proxied):
    target, proxy = sinks
    with requests.Session() as inner, _ForwardingFuturesSession(session=inner) as outer:
        inner.trust_env = outer.trust_env = False
        if proxied == "outer-env":  # only the outer session reads the environment, and it sends nothing
            outer.trust_env = True
            monkeypatch.setenv("HTTP_PROXY", proxy.url())
        else:
            (inner if proxied == "inner" else outer).proxies = {"http": proxy.url()}
        if proxied == "outer-with-inner-hook":
            inner.hooks["response"].append(lambda response, **_: response)
        if proxied == "inner":
            with _expect_proxy_refusal(target, proxy):
                _send_api_key_auth(target.url(), outer)
        else:
            assert _send_api_key_auth(target.url(), outer) == MODELS
            _assert_received_directly(target, proxy, "api-key-auth")
