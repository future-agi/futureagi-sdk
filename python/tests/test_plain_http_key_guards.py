"""Requests that carry API keys over plain http://.

Every case sends one request from one client to a listener on the loopback interface and reads what
reached each listener: the connection count and the number of bytes that hold the marker key. Names
such as ``api.futureagi.com`` resolve to the loopback interface through a lookup shim, so no case
reaches a real host.

Rules under test:

* HTTPS is permitted;
* the SDK's own transports send plain HTTP to loopback directly;
* a request carrying a key to a named Future AGI host requires HTTPS;
* a request carrying a key to another non-loopback host over plain HTTP requires opt-in and a direct route;
* requests without a key are permitted.
"""

from __future__ import annotations

import asyncio
import base64
import secrets
import socket
import threading
import time

import httpx
import pytest
import requests
from requests_futures.sessions import FuturesSession

from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from fi.errors import (
    ConfigurationError,
    InsecureHttpRefusedError,
    KeyedProxyRefusedError,
    KeyedRedirectRefusedError,
)
from fi.gateway import AgentCCError, AsyncGateway, Gateway
from fi.gateway._utils import check_valid_key, health_check
from fi.platform import AsyncClient, Client

KEY = "fikey-" + secrets.token_hex(12)
SECRET = "fisec-" + secrets.token_hex(12)
SHIM_NAMES = {"api.futureagi.com", "plain.example.test"}
NAMED_HOSTS = ["api.futureagi.com", "plain.example.test"]
CODE = "insecure_http_origin"
PROXY_VARS = ("HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy", "HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy")


def _marker_forms(*values: str) -> list[bytes]:
    forms = []
    for value in values:
        raw = value.encode()
        forms.append(raw)
        forms.append(base64.b64encode(raw))
        forms.append(base64.b64encode(raw + b":"))
        forms.append(base64.b64encode(b"user:" + raw))
    return forms


class Sink:
    """A listener on the loopback interface that records connections and the raw bytes it receives."""

    def __init__(self, family: int = socket.AF_INET) -> None:
        self.connections = 0
        self.raw = b""
        self._lock = threading.Lock()
        self._sock = socket.socket(family, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("::1" if family == socket.AF_INET6 else "127.0.0.1", 0))
        self._sock.listen(32)
        self.port = self._sock.getsockname()[1]
        self._stop = False
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        self._sock.settimeout(0.1)
        while not self._stop:
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            with self._lock:
                self.connections += 1
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket) -> None:
        conn.settimeout(0.4)
        data = b""
        try:
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
            with self._lock:
                self.raw += data
            if data.startswith(b"CONNECT"):
                conn.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
                try:
                    more = conn.recv(65536)
                except OSError:
                    more = b""
                with self._lock:
                    self.raw += more
            else:
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}")
        except OSError:
            pass
        finally:
            conn.close()

    def marker_bytes(self) -> int:
        time.sleep(0.15)
        with self._lock:
            raw = self.raw
        return sum(raw.count(form) for form in _marker_forms(KEY, SECRET))

    def close(self) -> None:
        self._stop = True
        self._sock.close()


class Net:
    def __init__(self, target: Sink, proxy: Sink) -> None:
        self.target, self.proxy = target, proxy

    def report(self) -> str:
        return (
            f"target: {self.target.connections} connections, {self.target.marker_bytes()} marker bytes; "
            f"proxy: {self.proxy.connections} connections, {self.proxy.marker_bytes()} marker bytes"
        )

    def nothing_sent(self) -> None:
        assert (self.target.connections, self.target.marker_bytes(), self.proxy.connections, self.proxy.marker_bytes()) == (
            0, 0, 0, 0,
        ), self.report()

    def delivered_direct(self) -> None:
        assert self.target.marker_bytes() > 0, self.report()
        assert (self.proxy.connections, self.proxy.marker_bytes()) == (0, 0), self.report()

    def direct_or_refused(self, exc: BaseException | None) -> None:
        """Where 0.8.1 sends direct and 0.9.0 refuses before a connection (a caller's proxied session or client, or a
        constructor argument 0.9.0 does not take): no byte reaches the proxy, and the key reaches the target only direct."""
        assert (self.proxy.connections, self.proxy.marker_bytes()) == (0, 0), self.report()
        if self.target.marker_bytes() == 0:
            assert exc is not None, self.report()
            self.nothing_sent()


@pytest.fixture(autouse=True)
def net(monkeypatch):
    for name in PROXY_VARS + ("FI_ALLOW_INSECURE_HTTP",):
        monkeypatch.delenv(name, raising=False)
    original = socket.getaddrinfo

    def shim(host, *args, **kwargs):
        name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
        if isinstance(name, str) and name in SHIM_NAMES:
            host = "127.0.0.1"
        return original(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", shim)
    target, proxy = Sink(), Sink()
    yield Net(target, proxy)
    target.close()
    proxy.close()


def use_proxy(monkeypatch, net: Net, *, names=("HTTP_PROXY",), no_proxy: str | None = None) -> None:
    for name in names:
        monkeypatch.setenv(name, f"http://127.0.0.1:{net.proxy.port}")
    if no_proxy is not None:
        monkeypatch.setenv("NO_PROXY", no_proxy)


# ---------------------------------------------------------------------------------------------
# senders: each sends one keyed request to ``base`` and returns the error it raised, if any
# ---------------------------------------------------------------------------------------------


def _attempt(call):
    try:
        call()
    except Exception as exc:  # the transport may fail on the listener's reply; the refusal is what is read
        return exc
    return None


def legacy(base: str, *, headers=None, default_headers=None, session=None, **kwargs):
    client = HttpClient(
        base_url=base,
        session=session,
        default_headers={"X-Api-Key": KEY, "X-Secret-Key": SECRET} if default_headers is None else default_headers,
        **kwargs,
    )

    def send():
        config = RequestConfig(method=HttpMethod.GET, url=base + "/v1/ping", headers=headers or {}, retry_attempts=1, timeout=3)
        client.request(config)

    return _attempt(send)


def platform_sync(base: str, **kwargs):
    # 0.9.0 judges the base URL when the client is built, so building it is part of the attempt.
    return _attempt(lambda: Client(api_key=KEY, secret_key=SECRET, base_url=base, max_retries=0, timeout=3, **kwargs)
                    .request("GET", "/v1/ping", unwrap=None))


def platform_async(base: str, **kwargs):
    async def run():
        client = AsyncClient(api_key=KEY, secret_key=SECRET, base_url=base, max_retries=0, timeout=3, **kwargs)
        try:
            await client.request("GET", "/v1/ping", unwrap=None)
        finally:
            await client.aclose()

    return _attempt(lambda: asyncio.run(run()))


def gateway_sync(base: str, **kwargs):
    call = kwargs.pop("call", None)
    send = call or (lambda gw: gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}]))
    return _attempt(lambda: send(Gateway(api_key=KEY, base_url=base, max_retries=0, timeout=3, **kwargs)))


def gateway_async(base: str, **kwargs):
    call = kwargs.pop("call", None)

    async def run():
        client = AsyncGateway(api_key=KEY, base_url=base, max_retries=0, timeout=3, **kwargs)
        try:
            if call:
                await call(client)
            else:
                await client.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        finally:
            await client.aclose()

    return _attempt(lambda: asyncio.run(run()))


def gateway_health(base: str, **kwargs):
    return health_check(api_key=KEY, base_url=base, timeout=3)


def gateway_key_check(base: str, **kwargs):
    return check_valid_key(KEY, base)


SENDERS = {
    "http-client": legacy,
    "platform-sync": platform_sync,
    "platform-async": platform_async,
    "gateway-sync": gateway_sync,
    "gateway-async": gateway_async,
}
HELPERS = {"gateway-health-check": gateway_health, "gateway-key-check": gateway_key_check}
ALL_SENDERS = {**SENDERS, **HELPERS}
OPT_IN_ARG = {name: fn for name, fn in ALL_SENDERS.items() if name not in HELPERS}


# The 0.9.0 classes for the refusals 0.8.1 raised as ValueError or AgentCCError with insecure_http_origin.
REFUSAL_CLASSES = (ConfigurationError, InsecureHttpRefusedError, KeyedProxyRefusedError, KeyedRedirectRefusedError)
REFUSAL_CODES = (CODE, "INSECURE_HTTP_REFUSED", "KEYED_PROXY_REFUSED", "KEYED_REDIRECT_REFUSED")


def refused(exc: BaseException | None, *classes: type, code: str = CODE) -> None:
    assert exc is not None, "no error was raised"
    if ValueError in classes or AgentCCError in classes:
        classes = classes + REFUSAL_CLASSES
        codes = (code,) + REFUSAL_CODES
    else:
        codes = (code,)
    if len(codes) > 1 and (isinstance(exc, httpx.InvalidURL) or (isinstance(exc, TypeError) and "allow_insecure_http" in str(exc))):
        # 0.9.0 stops before a request exists: httpx does not read the URL, or the 0.9.0 platform or gateway client
        # takes no allow_insecure_http argument. The callers assert 0 connections and 0 marker bytes first.
        assert KEY not in str(exc) and SECRET not in str(exc)
        return
    assert isinstance(exc, classes), f"{type(exc).__name__}: {exc}"
    found = getattr(exc, "code", None)
    if found is None and callable(getattr(exc, "get_error_code", None)):
        found = exc.get_error_code()
    assert found in codes, f"code: {found!r}"
    assert KEY not in str(exc) and SECRET not in str(exc)


def assert_named_host_refusal(result, sender: str, host: str) -> None:
    if sender == "gateway-health-check":
        assert result["status"] == "error"
        text = result["error"]
        assert "Credentials are not sent over http://" in text and "FI_ALLOW_INSECURE_HTTP" in text
        assert KEY not in text and SECRET not in text
    elif sender == "gateway-key-check":
        assert result is False
    elif host == "api.futureagi.com":
        refused(result, InsecureHttpRefusedError, code="INSECURE_HTTP_REFUSED")
    else:
        refused(result, ConfigurationError)


EXPECTED = {
    "http-client": (ValueError,),
    "platform-sync": (ValueError,),
    "platform-async": (ValueError,),
    "gateway-sync": (AgentCCError,),
    "gateway-async": (AgentCCError,),
    "gateway-health-check": (AgentCCError,),
    "gateway-key-check": (AgentCCError,),
}

sender_names = pytest.mark.parametrize("sender", list(ALL_SENDERS))
checked_senders = pytest.mark.parametrize("sender", list(SENDERS))
named_hosts = pytest.mark.parametrize("host", NAMED_HOSTS)


# ---------------------------------------------------------------------------------------------
# plain http to a host that is not loopback: refused before any connection
# ---------------------------------------------------------------------------------------------


@sender_names
@named_hosts
def test_keyed_plain_http_to_named_host_is_refused(net, sender, host):
    exc = ALL_SENDERS[sender](f"http://{host}:{net.target.port}")
    net.nothing_sent()
    assert_named_host_refusal(exc, sender, host)


@sender_names
@named_hosts
@pytest.mark.parametrize("variable", [("HTTP_PROXY",), ("ALL_PROXY",), ("http_proxy", "all_proxy")])
def test_keyed_plain_http_with_environment_proxy_reaches_no_sink(monkeypatch, net, sender, host, variable):
    use_proxy(monkeypatch, net, names=variable)
    exc = ALL_SENDERS[sender](f"http://{host}:{net.target.port}")
    net.nothing_sent()
    assert_named_host_refusal(exc, sender, host)


@sender_names
@named_hosts
def test_opt_in_by_environment_requires_an_eligible_host_and_sends_directly(monkeypatch, net, sender, host):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"))
    result = ALL_SENDERS[sender](f"http://{host}:{net.target.port}")
    if host == "api.futureagi.com":
        net.nothing_sent()
        assert_named_host_refusal(result, sender, host)
    else:
        net.delivered_direct()


@pytest.mark.parametrize("value", ["true", "yes", "0", "", "2", " 1", "1 "])
@pytest.mark.parametrize("sender", ["http-client", "platform-sync", "gateway-sync"])
def test_opt_in_environment_accepts_only_the_exact_value(monkeypatch, net, sender, value):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", value)
    ALL_SENDERS[sender](f"http://plain.example.test:{net.target.port}")
    net.nothing_sent()


@pytest.mark.parametrize("sender", list(OPT_IN_ARG))
@named_hosts
def test_opt_in_argument_sends_directly_past_environment_proxy(monkeypatch, net, sender, host):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"))
    exc = ALL_SENDERS[sender](f"http://{host}:{net.target.port}", allow_insecure_http=True)
    net.direct_or_refused(exc)


@pytest.mark.parametrize("value", [False, 0, "1", "true", 1])
@pytest.mark.parametrize("sender", ["http-client", "platform-sync", "gateway-sync"])
def test_opt_in_argument_accepts_only_true(net, sender, value):
    ALL_SENDERS[sender](f"http://plain.example.test:{net.target.port}", allow_insecure_http=value)
    net.nothing_sent()


@pytest.mark.parametrize("sender", ["http-client", "platform-sync", "gateway-sync"])
def test_opt_in_argument_false_wins_over_environment(monkeypatch, net, sender):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    ALL_SENDERS[sender](f"http://plain.example.test:{net.target.port}", allow_insecure_http=False)
    net.nothing_sent()


# ---------------------------------------------------------------------------------------------
# loopback hosts: sent directly
# ---------------------------------------------------------------------------------------------


@sender_names
@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_keyed_plain_http_to_loopback_is_sent_directly_past_environment_proxy(monkeypatch, net, sender, host):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"), no_proxy="")
    ALL_SENDERS[sender](f"http://{host}:{net.target.port}")
    net.delivered_direct()


@sender_names
def test_keyed_plain_http_to_loopback_without_proxy_is_delivered(net, sender):
    ALL_SENDERS[sender](f"http://127.0.0.1:{net.target.port}")
    net.delivered_direct()


@pytest.mark.parametrize("sender", ["http-client", "platform-sync", "platform-async", "gateway-sync", "gateway-async"])
def test_keyed_plain_http_to_ipv6_loopback_is_sent_directly_past_environment_proxy(monkeypatch, net, sender):
    try:
        v6 = Sink(socket.AF_INET6)
    except OSError:
        pytest.skip("no IPv6 loopback")
    try:
        use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"), no_proxy="")
        SENDERS[sender](f"http://[::1]:{v6.port}")
        assert v6.marker_bytes() > 0
        assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), net.report()
    finally:
        v6.close()


# ---------------------------------------------------------------------------------------------
# hosts written with ideographic or fullwidth dots are a bad base URL
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("written", ["127。0。0。1", "127．0．0．1", "127｡0｡0｡1", "localhost。"])
@pytest.mark.parametrize("opted_in", [False, True])
@pytest.mark.parametrize("sender", list(SENDERS))
def test_keyed_plain_http_to_host_with_ideographic_dots_is_refused(monkeypatch, net, sender, written, opted_in):
    if opted_in:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    exc = SENDERS[sender](f"http://{written}:{net.target.port}")
    net.nothing_sent()
    refused(exc, *EXPECTED[sender])


# ---------------------------------------------------------------------------------------------
# HTTPS and requests without a key
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("sender", ["http-client", "platform-sync", "gateway-sync"])
@named_hosts
def test_https_is_not_refused_and_still_uses_the_environment_proxy(monkeypatch, net, sender, host):
    use_proxy(monkeypatch, net, names=("HTTPS_PROXY", "ALL_PROXY"))
    exc = ALL_SENDERS[sender](f"https://{host}:{net.target.port}")
    assert net.proxy.connections >= 1, net.report()
    assert net.proxy.marker_bytes() == 0, net.report()
    assert getattr(exc, "code", None) != CODE


@pytest.mark.parametrize("sender", ["http-client", "platform-sync", "gateway-sync"])
def test_https_without_proxy_is_not_refused(net, sender):
    exc = ALL_SENDERS[sender](f"https://plain.example.test:{net.target.port}")
    assert getattr(exc, "code", None) != CODE
    assert net.target.marker_bytes() == 0


@named_hosts
def test_request_without_a_key_is_unchanged(monkeypatch, net, host):
    use_proxy(monkeypatch, net)
    exc = legacy(f"http://{host}:{net.target.port}", default_headers={}, session=FuturesSession())
    assert exc is None or getattr(exc, "code", None) != CODE
    assert net.proxy.connections == 1, net.report()
    assert net.target.connections == 0


@named_hosts
def test_request_without_a_key_and_without_proxy_is_delivered(net, host):
    exc = legacy(f"http://{host}:{net.target.port}", default_headers={"Accept": "application/json"})
    assert exc is None
    assert net.target.connections == 1


@pytest.mark.parametrize("headers", [{"Authorization": "Token abc"}, {"X-Request-Id": "r1"}, {"Cookie": "session=abc"}])
def test_authorization_is_refused_and_noncredential_headers_use_the_proxy(monkeypatch, net, headers):
    use_proxy(monkeypatch, net)
    exc = legacy(f"http://plain.example.test:{net.target.port}", default_headers=headers, session=FuturesSession())
    if "Authorization" in headers:
        net.nothing_sent()
        refused(exc, ConfigurationError)
    else:
        assert exc is None or getattr(exc, "code", None) != CODE
        assert net.proxy.connections == 1, net.report()


# ---------------------------------------------------------------------------------------------
# how a key enters: the headers of the request as prepared
# ---------------------------------------------------------------------------------------------

PLAIN = "plain.example.test"


def basic(value: str) -> str:
    return "Basic " + base64.b64encode(value.encode()).decode()


HEADER_FORMS = {
    "dict-default-api-key": dict(default_headers={"X-Api-Key": KEY}),
    "dict-default-secret-key": dict(default_headers={"X-Secret-Key": SECRET}),
    "dict-default-lower-case": dict(default_headers={"x-api-key": KEY}),
    "dict-default-upper-case": dict(default_headers={"X-API-KEY": KEY}),
    "dict-default-padded-name": dict(default_headers={"X-Api-Key ": KEY}),
    "dict-default-underscore-name": dict(default_headers={"X_Api_Key": KEY}),
    "dict-default-bytes-name": dict(default_headers={b"X-Api-Key": KEY.encode()}),
    "dict-default-bytes-underscore-name": dict(default_headers={b"x_secret_key": SECRET.encode()}),
    "dict-default-bearer": dict(default_headers={"Authorization": f"Bearer {KEY}"}),
    "dict-default-bearer-lower-case": dict(default_headers={"authorization": f"bearer {KEY}"}),
    "dict-default-basic": dict(default_headers={"Authorization": basic(KEY)}),
    "dict-default-basic-pair": dict(default_headers={"Authorization": basic(f"{KEY}:{SECRET}")}),
    "dict-per-call-api-key": dict(default_headers={}, headers={"X-Api-Key": KEY}),
    "dict-per-call-padded-name": dict(default_headers={}, headers={"X-Api-Key ": KEY}),
    "dict-per-call-bearer": dict(default_headers={}, headers={"Authorization": f"Bearer {KEY}"}),
    "dict-per-call-bytes-name": dict(default_headers={}, headers={b"X-Api-Key": KEY.encode()}),
    "pairs-default": dict(default_headers=[("X-Api-Key", KEY)]),
    "pairs-per-call": dict(default_headers={}, headers=[("X-Api-Key", KEY)]),
}


@pytest.mark.parametrize("form", list(HEADER_FORMS))
def test_http_client_header_forms_are_refused(net, form):
    exc = legacy(f"http://{PLAIN}:{net.target.port}", **HEADER_FORMS[form])
    net.nothing_sent()
    if not form.startswith("pairs"):
        refused(exc, ConfigurationError)


@pytest.mark.parametrize("form", list(HEADER_FORMS))
def test_http_client_header_forms_reach_no_proxy(monkeypatch, net, form):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"))
    legacy(f"http://{PLAIN}:{net.target.port}", **HEADER_FORMS[form])
    net.nothing_sent()


@pytest.mark.parametrize("form", [f for f in HEADER_FORMS if not f.startswith("pairs")])
def test_http_client_header_forms_to_loopback_are_sent_directly(monkeypatch, net, form):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"), no_proxy="")
    legacy(f"http://127.0.0.1:{net.target.port}", **HEADER_FORMS[form])
    net.delivered_direct()


def test_session_authentication_hook_that_adds_a_key_is_refused(net):
    def hook(request):
        request.headers["X-Api-Key"] = KEY
        return request

    session = FuturesSession()
    session.auth = hook
    exc = legacy(f"http://{PLAIN}:{net.target.port}", session=session, default_headers={})
    net.nothing_sent()
    refused(exc, ConfigurationError)


def test_session_authentication_hook_that_adds_a_bearer_is_refused(monkeypatch, net):
    class Bearer(requests.auth.AuthBase):
        def __call__(self, request):
            request.headers["Authorization"] = f"Bearer {KEY}"
            return request

    use_proxy(monkeypatch, net)
    session = FuturesSession()
    session.auth = Bearer()
    exc = legacy(f"http://{PLAIN}:{net.target.port}", session=session, default_headers={})
    net.nothing_sent()
    refused(exc, ConfigurationError)


def test_caller_session_with_authentication_and_proxy_is_refused_for_loopback(monkeypatch, net):
    class Bearer(requests.auth.AuthBase):
        def __call__(self, request):
            request.headers["Authorization"] = f"Bearer {KEY}"
            return request

    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"), no_proxy="")
    session = FuturesSession()
    session.auth = Bearer()
    exc = legacy(f"http://127.0.0.1:{net.target.port}", session=session, default_headers={})
    net.nothing_sent()
    refused(exc, KeyedProxyRefusedError, code="KEYED_PROXY_REFUSED")


@pytest.mark.parametrize("name,value", [("X-Api-Key", KEY), ("x-secret-key", SECRET), ("Authorization", f"Bearer {KEY}")], ids=["api-key", "secret-key", "bearer"])
def test_session_headers_that_hold_a_key_are_refused(net, name, value):
    session = FuturesSession()
    session.headers[name] = value
    exc = legacy(f"http://{PLAIN}:{net.target.port}", session=session, default_headers={})
    net.nothing_sent()
    refused(exc, ConfigurationError)


@pytest.mark.parametrize("name,value", [("X-Api-Key", KEY), ("Authorization", f"Bearer {KEY}")], ids=["api-key", "bearer"])
def test_session_headers_that_hold_a_key_reach_no_proxy(monkeypatch, net, name, value):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"))
    session = FuturesSession()
    session.headers[name] = value
    legacy(f"http://{PLAIN}:{net.target.port}", session=session, default_headers={})
    net.nothing_sent()


def test_caller_session_with_credential_headers_and_proxy_is_refused_for_loopback(monkeypatch, net):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"), no_proxy="")
    session = FuturesSession()
    session.headers["X-Api-Key"] = KEY
    exc = legacy(f"http://127.0.0.1:{net.target.port}", session=session, default_headers={})
    net.nothing_sent()
    refused(exc, KeyedProxyRefusedError, code="KEYED_PROXY_REFUSED")


def test_wrapped_session_headers_are_judged(net):
    inner = requests.Session()
    inner.headers["X-Api-Key"] = KEY
    exc = legacy(f"http://{PLAIN}:{net.target.port}", session=FuturesSession(session=inner), default_headers={})
    net.nothing_sent()
    refused(exc, ConfigurationError)


@pytest.mark.parametrize("cookie_name", ["X-Api-Key", "x_secret_key"])
def test_cookie_that_holds_a_key_is_refused(net, cookie_name):
    session = FuturesSession()
    session.cookies.set(cookie_name, KEY, domain=PLAIN, path="/")
    exc = legacy(f"http://{PLAIN}:{net.target.port}", session=session, default_headers={})
    net.nothing_sent()
    refused(exc, ValueError)


def test_cookie_header_that_holds_a_key_is_refused(net):
    exc = legacy(f"http://{PLAIN}:{net.target.port}", default_headers={"Cookie": f"x-api-key={KEY}; theme=dark"})
    net.nothing_sent()
    refused(exc, ValueError)


def test_cookie_that_holds_a_key_to_loopback_is_sent_directly(monkeypatch, net):
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "ALL_PROXY"), no_proxy="")
    session = FuturesSession()
    session.cookies.set("X-Api-Key", KEY, domain="127.0.0.1", path="/")
    exc = legacy(f"http://127.0.0.1:{net.target.port}", session=session, default_headers={})
    net.direct_or_refused(exc)


def test_caller_session_with_explicit_proxy_is_refused_for_loopback(net):
    session = FuturesSession()
    session.proxies = {"http": f"http://127.0.0.1:{net.proxy.port}"}
    exc = legacy(f"http://127.0.0.1:{net.target.port}", session=session)
    net.nothing_sent()
    refused(exc, KeyedProxyRefusedError, code="KEYED_PROXY_REFUSED")


def test_session_proxies_setting_with_opt_in_is_not_used(net):
    session = FuturesSession()
    session.proxies = {"http": f"http://127.0.0.1:{net.proxy.port}", "all": f"http://127.0.0.1:{net.proxy.port}"}
    exc = legacy(f"http://{PLAIN}:{net.target.port}", session=session, allow_insecure_http=True)
    net.direct_or_refused(exc)


def test_session_proxies_setting_without_opt_in_is_refused(net):
    session = FuturesSession()
    session.proxies = {"http": f"http://127.0.0.1:{net.proxy.port}"}
    exc = legacy(f"http://{PLAIN}:{net.target.port}", session=session)
    net.nothing_sent()
    refused(exc, ConfigurationError)


def test_redirect_from_a_keyed_loopback_request_is_not_followed_to_another_host(net):
    class Redirect(Sink):
        def _handle(self, conn):
            conn.settimeout(0.4)
            data = conn.recv(65536)
            with self._lock:
                self.raw += data
            conn.sendall(
                f"HTTP/1.1 302 Found\r\nLocation: http://{PLAIN}:{net.target.port}/x\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".encode()
            )
            conn.close()

    redirecting = Redirect()
    try:
        legacy(f"http://127.0.0.1:{redirecting.port}")
        assert redirecting.marker_bytes() > 0
        assert (net.target.connections, net.target.marker_bytes()) == (0, 0), net.report()
    finally:
        redirecting.close()


# ---------------------------------------------------------------------------------------------
# platform client headers and gateway headers
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("make", [
    lambda: {"default_headers": [("X-Api-Key", KEY)]},
    lambda: {"default_headers": {"Authorization": f"Bearer {KEY}"}},
    lambda: {"default_headers": {"x_api_key": KEY}},
    lambda: {"default_headers": {b"X-Api-Key": KEY.encode()}},
])
@pytest.mark.parametrize("sender", ["platform-sync", "platform-async"])
def test_platform_default_headers_that_hold_a_key_are_refused(monkeypatch, net, sender, make):
    use_proxy(monkeypatch, net)
    SENDERS[sender](f"http://{PLAIN}:{net.target.port}", **make())
    net.nothing_sent()


def test_platform_per_call_headers_that_hold_a_key_are_refused(net):
    from fi.platform import RequestOptions

    client = Client(api_key=KEY, secret_key=SECRET, base_url=f"http://{PLAIN}:{net.target.port}", max_retries=0, timeout=3)
    exc = _attempt(lambda: client.request("GET", "/v1/ping", unwrap=None, options=RequestOptions(headers={"Authorization": f"Bearer {KEY}"})))
    net.nothing_sent()
    refused(exc, ConfigurationError)


@pytest.mark.parametrize("headers", [
    [("X-Api-Key", KEY)],
    [("Authorization", f"Bearer {KEY}")],
    {"Authorization": f"Bearer {KEY}"},
    {"X-Api-Key": KEY},
], ids=["pairs-api-key", "pairs-bearer", "dict-bearer", "dict-api-key"])
def test_gateway_chat_extra_headers_are_refused(monkeypatch, net, headers):
    use_proxy(monkeypatch, net)
    exc = gateway_sync(
        f"http://{PLAIN}:{net.target.port}",
        call=lambda gw: gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}], extra_headers=headers),
    )
    net.nothing_sent()
    refused(exc, AgentCCError)


@pytest.mark.parametrize("headers", [[("X-Api-Key", KEY)], [("Authorization", f"Bearer {KEY}")]], ids=["pairs-api-key", "pairs-bearer"])
def test_gateway_embeddings_extra_headers_are_refused(net, headers):
    exc = gateway_sync(
        f"http://{PLAIN}:{net.target.port}",
        call=lambda gw: gw.embeddings.create(model="m", input="hi", extra_headers=headers),
    )
    net.nothing_sent()
    refused(exc, AgentCCError)


@pytest.mark.parametrize("headers", [[("X-Api-Key", KEY)], [("Authorization", f"Bearer {KEY}")], {"x_api_key": KEY}], ids=["pairs-api-key", "pairs-bearer", "dict-underscore-name"])
@pytest.mark.parametrize("sender", ["gateway-sync", "gateway-async"])
def test_gateway_default_headers_are_refused(monkeypatch, net, sender, headers):
    use_proxy(monkeypatch, net)
    SENDERS[sender](f"http://{PLAIN}:{net.target.port}", default_headers=headers)
    net.nothing_sent()


# ---------------------------------------------------------------------------------------------
# a client the caller supplies
# ---------------------------------------------------------------------------------------------


def test_gateway_with_a_proxied_http_client_is_not_sent_through_the_proxy(net):
    client = httpx.Client(proxy=f"http://127.0.0.1:{net.proxy.port}")
    exc = gateway_sync(f"http://{PLAIN}:{net.target.port}", http_client=client, allow_insecure_http=True)
    net.direct_or_refused(exc)


def test_gateway_with_a_proxied_http_client_without_opt_in_sends_nothing(net):
    client = httpx.Client(proxy=f"http://127.0.0.1:{net.proxy.port}")
    exc = gateway_sync(f"http://{PLAIN}:{net.target.port}", http_client=client)
    net.nothing_sent()
    refused(exc, AgentCCError)


def test_gateway_with_a_proxied_http_client_to_loopback_is_not_sent_through_the_proxy(net):
    client = httpx.Client(proxy=f"http://127.0.0.1:{net.proxy.port}")
    gateway_sync(f"http://127.0.0.1:{net.target.port}", http_client=client)
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), net.report()


def test_platform_with_a_proxied_http_client_is_not_sent_through_the_proxy(net):
    client = httpx.Client(proxy=f"http://127.0.0.1:{net.proxy.port}")
    exc = platform_sync(f"http://{PLAIN}:{net.target.port}", http_client=client)
    net.nothing_sent()
    refused(exc, ConfigurationError)


def test_async_gateway_with_a_proxied_http_client_sends_nothing_through_the_proxy(net):
    async def run():
        client = httpx.AsyncClient(proxy=f"http://127.0.0.1:{net.proxy.port}")
        gw = AsyncGateway(api_key=KEY, base_url=f"http://{PLAIN}:{net.target.port}", http_client=client, max_retries=0)
        try:
            await gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        finally:
            await client.aclose()

    exc = _attempt(lambda: asyncio.run(run()))
    net.nothing_sent()
    refused(exc, AgentCCError)


def test_gateway_streaming_request_is_refused(net):
    def stream(gw):
        for _ in gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}], stream=True):
            pass

    exc = gateway_sync(f"http://{PLAIN}:{net.target.port}", call=stream)
    net.nothing_sent()
    refused(exc, AgentCCError)


def test_error_text_names_the_setting_and_holds_no_key(net):
    for sender in SENDERS:
        exc = SENDERS[sender](f"http://{PLAIN}:{net.target.port}")
        text = str(exc)
        assert "FI_ALLOW_INSECURE_HTTP" in text, f"{sender}: {text}"
        assert KEY not in text and SECRET not in text
    net.nothing_sent()


# ---------------------------------------------------------------------------------------------
# redirects, adapters and in-process transports
# ---------------------------------------------------------------------------------------------


class _Redirecting(Sink):
    def __init__(self, location: str) -> None:
        self._location = location
        super().__init__()

    def _handle(self, conn):
        conn.settimeout(0.4)
        data = conn.recv(65536)
        with self._lock:
            self.raw += data
        conn.sendall(f"HTTP/1.1 302 Found\r\nLocation: {self._location}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".encode())
        conn.close()


@pytest.mark.parametrize("sender", ["gateway-sync", "gateway-async"])
def test_gateway_client_that_follows_redirects_does_not_follow_one_to_another_host(net, sender):
    redirecting = _Redirecting(f"http://{PLAIN}:{net.target.port}/x")
    try:
        if sender == "gateway-sync":
            client = httpx.Client(follow_redirects=True)
            gateway_sync(f"http://127.0.0.1:{redirecting.port}", http_client=client, default_headers={"X-Api-Key": KEY})
        else:
            async def run():
                client = httpx.AsyncClient(follow_redirects=True)
                gw = AsyncGateway(api_key=KEY, base_url=f"http://127.0.0.1:{redirecting.port}", http_client=client, max_retries=0)
                try:
                    await gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
                finally:
                    await client.aclose()

            _attempt(lambda: asyncio.run(run()))
        assert redirecting.marker_bytes() > 0
        assert (net.target.connections, net.target.marker_bytes()) == (0, 0), net.report()
    finally:
        redirecting.close()


def test_redirect_from_https_to_plain_http_host_is_refused_before_it_is_followed(net):
    class Adapter(requests.adapters.HTTPAdapter):
        def send(self, request, **kwargs):
            response = requests.Response()
            response.status_code = 302
            response.headers["Location"] = f"http://{PLAIN}:{net.target.port}/x"
            response.url = request.url
            response.request = request
            return response

    session = FuturesSession()
    session.mount("https://", Adapter())
    exc = legacy("https://api.futureagi.com", session=session)
    net.nothing_sent()
    assert isinstance(exc, KeyedRedirectRefusedError)
    assert exc.get_error_code() == "KEYED_REDIRECT_REFUSED"
    assert KEY not in str(exc) and SECRET not in str(exc)


def test_custom_adapter_that_may_use_a_proxy_is_refused_for_loopback(net):
    class ProxyAdapter(requests.adapters.HTTPAdapter):
        def send(self, request, **kwargs):
            kwargs["proxies"] = {"http": f"http://127.0.0.1:{net.proxy.port}"}
            return super().send(request, **kwargs)

    session = FuturesSession()
    session.mount("http://", ProxyAdapter())
    legacy(f"http://127.0.0.1:{net.target.port}", session=session)
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), net.report()


@pytest.mark.parametrize("separator", ["\t", "  ", " \t "])
def test_authorization_scheme_separated_by_whitespace_is_refused(monkeypatch, net, separator):
    use_proxy(monkeypatch, net)
    exc = legacy(f"http://{PLAIN}:{net.target.port}", default_headers={"Authorization": "Bearer" + separator + KEY})
    net.nothing_sent()
    refused(exc, ValueError)


def test_in_process_transport_is_accepted_for_loopback():
    def app(environ, start_response):
        start_response("200 OK", [("Content-Type", "application/json")])
        return [b"{}"]

    client = httpx.Client(transport=httpx.WSGITransport(app=app))
    exc = platform_sync("http://127.0.0.1", http_client=client)
    assert getattr(exc, "code", None) != CODE
