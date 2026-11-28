"""Check the released platform clients' HTTP opt-in on loopback listeners."""

from __future__ import annotations

import asyncio
import inspect
import socket
import threading
from contextlib import ExitStack, nullcontext
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
import pytest

from fi.errors import (
    ConfigurationError,
    InsecureHttpRefusedError,
    KeyedProxyRefusedError,
    KeyedRedirectRefusedError,
)
from fi.platform import AsyncClient, Client

KEY = "test-key-marker-1"
SECRET = "test-secret-marker-1"
CUSTOM_HOST = "platform.example.test"
FUTURE_AGI_HOST = "api.futureagi.com"
MODES = pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])


class _Site(HTTPServer):
    def __init__(self, address):
        super().__init__((address, 0), _Handler)
        self.connections = 0
        self.requests = []
        self.location = None

    def get_request(self):
        conn, address = super().get_request()
        self.connections += 1
        conn.settimeout(2)
        return conn, address

    def url(self, host=None):
        return f"http://{host or self.server_address[0]}:{self.server_port}"

    def assert_received_keys(self):
        assert self.connections == 1
        assert len(self.requests) == 1
        assert self.requests[0]["X-Api-Key"] == KEY
        assert self.requests[0]["X-Secret-Key"] == SECRET

    def assert_no_connection(self):
        headers = b"".join(request.as_bytes() for request in self.requests)
        assert KEY.encode() not in headers and SECRET.encode() not in headers
        assert self.connections == 0


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.requests.append(self.headers)
        if self.server.location:
            self.send_response(302)
            self.send_header("Location", self.server.location)
        else:
            self.send_response(204)
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_CONNECT = do_GET

    def log_message(self, *args):
        pass


@pytest.fixture
def site(monkeypatch):
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    monkeypatch.delenv("REQUEST_METHOD", raising=False)
    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    original = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        name = host.decode("ascii") if isinstance(host, bytes) else host
        return original("127.0.0.2" if name in (CUSTOM_HOST, FUTURE_AGI_HOST) else host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)

    with ExitStack() as stack:
        def start(address="127.0.0.2"):
            server = stack.enter_context(_Site(address))
            thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
            thread.start()
            stack.callback(thread.join)
            stack.callback(server.shutdown)
            return server

        yield start


def _request(asynchronous, base_url, allow_insecure_http, http_options=None):
    options = dict(api_key=KEY, secret_key=SECRET, base_url=base_url, max_retries=0, timeout=2,
                   allow_insecure_http=allow_insecure_http)
    if not asynchronous:
        with (nullcontext() if http_options is None else httpx.Client(**http_options)) as http:
            with Client(http_client=http, **options) as client:
                return client.request("GET", "/ping")

    async def run():
        async with (nullcontext() if http_options is None else httpx.AsyncClient(**http_options)) as http:
            async with AsyncClient(http_client=http, **options) as client:
                return await client.request("GET", "/ping")

    return asyncio.run(run())


@pytest.mark.parametrize("client_class", [Client, AsyncClient])
def test_released_keyword_signature(client_class):
    parameters = inspect.signature(client_class.__init__).parameters
    parameter = parameters["allow_insecure_http"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is None
    assert list(parameters)[-2:] == ["http_client", "allow_insecure_http"]


@MODES
@pytest.mark.parametrize("option", [True, False, None])
def test_loopback_call_with_released_keyword(site, asynchronous, option):
    target = site("127.0.0.1")
    assert _request(asynchronous, target.url(), option) is None
    target.assert_received_keys()


@MODES
@pytest.mark.parametrize(("option", "env", "allowed"), [
    (True, None, True),
    (False, "1", False),
    ("1", "1", False),
    (None, "1", True),
    (None, None, False),
])
def test_named_host_opt_in(site, monkeypatch, asynchronous, option, env, allowed):
    target = site()
    if env is not None:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", env)
    url = target.url(CUSTOM_HOST)
    if allowed:
        assert _request(asynchronous, url, option) is None
        target.assert_received_keys()
    else:
        with pytest.raises(ConfigurationError) as caught:
            _request(asynchronous, url, option)
        assert caught.value.code == "insecure_http_origin"
        target.assert_no_connection()


@MODES
def test_opt_in_does_not_allow_http_to_future_agi(site, asynchronous):
    target = site()
    with pytest.raises(InsecureHttpRefusedError):
        _request(asynchronous, target.url(FUTURE_AGI_HOST), True)
    target.assert_no_connection()


@MODES
@pytest.mark.parametrize("routing", ["env", "proxy", "mount"])
def test_opt_in_does_not_allow_http_via_proxy(site, monkeypatch, asynchronous, routing):
    target, proxy = site(), site("127.0.0.1")
    if routing == "env":
        monkeypatch.setenv("HTTP_PROXY", proxy.url())
        options = {"trust_env": True}
    elif routing == "proxy":
        options = {"proxy": proxy.url()}
    else:
        transport = httpx.AsyncHTTPTransport if asynchronous else httpx.HTTPTransport
        options = {"mounts": {"http://": transport(proxy=proxy.url())}, "trust_env": False}
    with pytest.raises(KeyedProxyRefusedError):
        _request(asynchronous, target.url(CUSTOM_HOST), True, options)
    proxy.assert_no_connection()
    target.assert_no_connection()


@MODES
def test_sdk_transport_uses_direct_route_with_proxy_environment(site, monkeypatch, asynchronous):
    target, proxy = site(), site("127.0.0.1")
    monkeypatch.setenv("HTTP_PROXY", proxy.url())
    assert _request(asynchronous, target.url(CUSTOM_HOST), True) is None
    target.assert_received_keys()
    proxy.assert_no_connection()


@MODES
@pytest.mark.parametrize("option", [True, False])
def test_opt_in_applies_to_merged_httpx_base_url(site, monkeypatch, asynchronous, option):
    target = site()
    options = {"base_url": target.url(CUSTOM_HOST), "trust_env": False}
    if option:
        assert _request(asynchronous, "/", option, options) is None
        target.assert_received_keys()
    else:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
        with pytest.raises(ConfigurationError) as caught:
            _request(asynchronous, "/", option, options)
        assert caught.value.code == "insecure_http_origin"
        target.assert_no_connection()


@MODES
def test_opt_in_does_not_allow_cross_origin_redirect(site, asynchronous):
    target, redirector = site(), site("127.0.0.1")
    redirector.location = target.url(CUSTOM_HOST) + "/ping"
    with pytest.raises(KeyedRedirectRefusedError):
        _request(asynchronous, redirector.url(), True, {"follow_redirects": True, "trust_env": False})
    redirector.assert_received_keys()
    target.assert_no_connection()
