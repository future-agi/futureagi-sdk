"""Keyed requests through authentication hooks, retries, redirects, caller transports and helpers.

Listeners run on the loopback interface; ``plain.example.test`` and ``api.futureagi.com`` resolve to them through
the lookup shim of ``test_plain_http_key_guards`` (its ``net`` fixture applies here too), so no case reaches a
real host. Each case reads the connection count and the number of bytes holding the marker key at each listener.
"""

from __future__ import annotations

import asyncio
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest
import requests
from requests_futures.sessions import FuturesSession

from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from fi.gateway import AgentCCError, APIStatusError, AsyncGateway, Gateway
from fi.gateway._utils import check_valid_key, health_check
from fi.platform import Client
from tests.test_plain_http_key_guards import CODE, KEY, PLAIN, SECRET, _attempt, _marker_forms, net, refused  # noqa: F401

KEYED = {"X-Api-Key": KEY, "X-Secret-Key": SECRET}


class Site:
    """An HTTP listener on 127.0.0.1 that answers from ``route(method, path)`` and records what reached it."""

    def __init__(self, route) -> None:
        self.requests: list[tuple[str, str]] = []
        self.connections = 0
        self.raw = b""
        site = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def _answer(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                with site._lock:
                    site.requests.append((self.command, self.path))
                    site.raw += self.requestline.encode() + b"\r\n" + bytes(self.headers) + body
                status, headers, payload = route(self.command, self.path)
                self.send_response(status)
                for name, value in headers.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(payload)
                self.close_connection = True

            do_GET = do_POST = do_PATCH = do_DELETE = do_PUT = _answer

        class Server(ThreadingHTTPServer):
            daemon_threads = True

            def process_request(self, request, client_address):
                with site._lock:
                    site.connections += 1
                super().process_request(request, client_address)

        self._lock = threading.Lock()
        self._server = Server(("127.0.0.1", 0), Handler)
        self.port = self._server.server_address[1]
        self.base = f"http://127.0.0.1:{self.port}"
        threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

    def marker_bytes(self) -> int:
        time.sleep(0.1)
        with self._lock:
            raw = self.raw
        return sum(raw.count(form) for form in _marker_forms(KEY, SECRET))

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def sites():
    made: list[Site] = []

    def make(route) -> Site:
        made.append(Site(route))
        return made[-1]

    yield make
    for site in made:
        site.close()


def ok(body: bytes = b"{}"):
    return 200, {"Content-Type": "application/json"}, body


def send(client: HttpClient, url: str, *, method: HttpMethod = HttpMethod.GET, retry_attempts: int = 1, **extra):
    return client.request(RequestConfig(method=method, url=url, retry_attempts=retry_attempts, retry_delay=0, timeout=3, **extra))


class Counted(requests.auth.AuthBase):
    """Authentication that counts its calls and returns ``headers_for(call)`` added to the request."""

    def __init__(self, headers_for) -> None:
        self.calls = 0
        self.headers_for = headers_for

    def __call__(self, request):
        self.calls += 1
        request.headers.update(self.headers_for(self.calls))
        return request


class Closing:
    """A loopback listener that closes every connection without answering, so each attempt fails."""

    def __init__(self) -> None:
        import socket

        self.connections = 0
        self.raw = b""
        self._sock = socket.socket()
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(16)
        self._sock.settimeout(0.05)
        self.port = self._sock.getsockname()[1]
        self._stop = False
        threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self) -> None:
        while not self._stop:
            try:
                conn, _ = self._sock.accept()
            except OSError:
                continue
            self.connections += 1
            conn.settimeout(0.3)
            try:
                self.raw += conn.recv(65536)
            except OSError:
                pass
            conn.close()

    def marker_bytes(self) -> int:
        time.sleep(0.1)
        return sum(self.raw.count(form) for form in _marker_forms(KEY, SECRET))

    def close(self) -> None:
        self._stop = True
        self._sock.close()


# ---------------------------------------------------------------------------------------------
# authentication runs once per attempt, and the request it prepared is the one judged and sent
# ---------------------------------------------------------------------------------------------


def test_session_authentication_runs_once_per_attempt(sites):
    site = sites(lambda method, path: ok())
    auth = Counted(lambda call: {})
    session = FuturesSession()
    session.auth = auth
    send(HttpClient(base_url=site.base, session=session), site.base + "/v1/ping")
    assert auth.calls == 1
    assert site.requests == [("GET", "/v1/ping")]


def test_session_authentication_runs_once_per_attempt_across_retries():
    closing = Closing()
    try:
        auth = Counted(lambda call: {})
        session = FuturesSession()
        session.auth = auth
        base = f"http://127.0.0.1:{closing.port}"
        with pytest.raises(Exception):
            send(HttpClient(base_url=base, session=session), base + "/v1/ping", retry_attempts=3)
        assert auth.calls == 3
    finally:
        closing.close()


@pytest.mark.parametrize("added", ["api-key", "bearer"])
def test_authentication_that_adds_a_key_on_its_second_call_sends_no_key_to_a_named_host(net, added):
    header = {"api-key": {"X-Api-Key": KEY}, "bearer": {"Authorization": f"Bearer {KEY}"}}[added]
    auth = Counted(lambda call: header if call >= 2 else {})
    session = FuturesSession()
    session.auth = auth
    base = f"http://{PLAIN}:{net.target.port}"
    _attempt(lambda: send(HttpClient(base_url=base, session=session), base + "/v1/ping"))
    assert auth.calls == 1
    assert (net.target.marker_bytes(), net.proxy.connections) == (0, 0), net.report()


def test_callable_authentication_that_adds_a_key_on_its_second_call_sends_no_key_to_a_named_host(net):
    calls = []

    def auth(request):
        calls.append(1)
        if len(calls) >= 2:
            request.headers["Authorization"] = f"Bearer {KEY}"
        return request

    session = FuturesSession()
    session.auth = auth
    base = f"http://{PLAIN}:{net.target.port}"
    _attempt(lambda: send(HttpClient(base_url=base, session=session), base + "/v1/ping"))
    assert len(calls) == 1
    assert net.target.marker_bytes() == 0, net.report()


def test_authentication_that_adds_a_key_on_a_retry_is_refused_on_that_attempt(monkeypatch):
    import socket

    original = socket.getaddrinfo

    def shim(host, *args, **kwargs):
        return original("127.0.0.1" if host == PLAIN else host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", shim)
    closing = Closing()
    try:
        auth = Counted(lambda call: {"X-Api-Key": KEY} if call >= 2 else {})
        session = FuturesSession()
        session.auth = auth
        base = f"http://{PLAIN}:{closing.port}"
        exc = _attempt(lambda: send(HttpClient(base_url=base, session=session), base + "/v1/ping", retry_attempts=3))
        assert closing.marker_bytes() == 0
        assert closing.connections == 1
        assert auth.calls == 2
        refused(exc, ValueError)
    finally:
        closing.close()


def test_authentication_error_is_raised_and_nothing_is_sent(net):
    class Boom(Exception):
        pass

    calls = []

    def auth(request):
        calls.append(1)
        if len(calls) == 1:
            raise Boom("authentication failed")
        request.headers["X-Api-Key"] = KEY
        return request

    session = FuturesSession()
    session.auth = auth
    base = f"http://{PLAIN}:{net.target.port}"
    exc = _attempt(lambda: send(HttpClient(base_url=base, session=session), base + "/v1/ping"))
    assert isinstance(exc, Boom), repr(exc)
    net.nothing_sent()


# ---------------------------------------------------------------------------------------------
# redirects of keyed https requests
# ---------------------------------------------------------------------------------------------


class RedirectingAdapter(requests.adapters.HTTPAdapter):
    """Answers every https request with ``status`` and ``Location: location`` and counts the requests."""

    def __init__(self, location: str, status: int = 302) -> None:
        super().__init__()
        self.location, self.status, self.sent = location, status, []

    def send(self, request, **kwargs):
        self.sent.append(request.method)
        response = requests.Response()
        response.status_code = self.status
        response.headers["Location"] = self.location
        response.url = request.url
        response.request = request
        response._content = b""
        response.raw = None
        return response


LOCATION_FORMS = {
    "tab-in-scheme": "http\t://{host}/x",
    "leading-control": "\x01http://{host}/x",
    "leading-space": " http://{host}/x",
    "newline-in-scheme": "ht\ntp://{host}/x",
    "tab-in-authority": "http://{host}\t/x",
    "leading-delete": "\x7fhttp://{host}/x",
}


@pytest.mark.parametrize("form", list(LOCATION_FORMS))
def test_redirect_location_with_control_characters_is_refused(net, form):
    adapter = RedirectingAdapter(LOCATION_FORMS[form].format(host=f"{PLAIN}:{net.target.port}"))
    session = FuturesSession()
    session.mount("https://", adapter)
    exc = _attempt(lambda: send(HttpClient(base_url="https://api.futureagi.com", default_headers=KEYED, session=session), "https://api.futureagi.com/v1/ping"))
    net.nothing_sent()
    refused(exc, ValueError)


@pytest.mark.parametrize("method", [HttpMethod.GET, HttpMethod.POST])
def test_refused_redirect_is_not_retried(net, method):
    adapter = RedirectingAdapter(f"http://{PLAIN}:{net.target.port}/x")
    session = FuturesSession()
    session.mount("https://", adapter)
    client = HttpClient(base_url="https://api.futureagi.com", default_headers=KEYED, session=session)
    exc = _attempt(lambda: send(client, "https://api.futureagi.com/v1/ping", method=method, retry_attempts=3, json={"a": 1}))
    assert adapter.sent == [method.value]
    net.nothing_sent()
    refused(exc, ValueError)


def test_redirect_of_a_request_keyed_by_session_authentication_is_refused(net):
    class ApiKey(requests.auth.AuthBase):
        def __call__(self, request):
            request.headers["X-Api-Key"] = KEY
            return request

    adapter = RedirectingAdapter(f"http://{PLAIN}:{net.target.port}/x")
    session = FuturesSession()
    session.mount("https://", adapter)
    session.auth = ApiKey()
    exc = _attempt(lambda: send(HttpClient(base_url="https://api.futureagi.com", session=session), "https://api.futureagi.com/v1/ping"))
    net.nothing_sent()
    refused(exc, ValueError)


def test_opted_in_redirect_from_https_to_plain_http_is_delivered_directly(net):
    adapter = RedirectingAdapter(f"http://{PLAIN}:{net.target.port}/x")
    session = FuturesSession()
    session.mount("https://", adapter)
    client = HttpClient(base_url="https://api.futureagi.com", default_headers=KEYED, session=session, allow_insecure_http=True)
    exc = _attempt(lambda: send(client, "https://api.futureagi.com/v1/ping"))
    assert exc is None, repr(exc)
    net.delivered_direct()


def test_opted_in_redirect_from_https_that_an_environment_proxy_would_carry_is_refused(monkeypatch, net):
    monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{net.proxy.port}")
    adapter = RedirectingAdapter(f"http://{PLAIN}:{net.target.port}/x")
    session = FuturesSession()
    session.mount("https://", adapter)
    client = HttpClient(base_url="https://api.futureagi.com", default_headers=KEYED, session=session, allow_insecure_http=True)
    exc = _attempt(lambda: send(client, "https://api.futureagi.com/v1/ping"))
    net.nothing_sent()
    refused(exc, ValueError)


@pytest.mark.parametrize("name", ["X-Api-Key", "X-Secret-Key"])
def test_redirect_that_picks_up_a_key_cookie_from_the_session_is_refused(net, name):
    adapter = RedirectingAdapter(f"http://{PLAIN}:{net.target.port}/x")
    session = FuturesSession()
    session.mount("https://", adapter)
    session.cookies.set(name, KEY, domain=PLAIN)
    exc = _attempt(lambda: send(HttpClient(base_url="https://api.futureagi.com", session=session), "https://api.futureagi.com/v1/ping"))
    net.nothing_sent()
    refused(exc, ValueError)


def test_redirect_that_picks_up_netrc_credentials_is_refused(monkeypatch, net, tmp_path):
    netrc = tmp_path / "netrc"
    netrc.write_text(f"machine {PLAIN}\nlogin user\npassword {KEY}\n")
    netrc.chmod(0o600)
    monkeypatch.setenv("NETRC", str(netrc))
    adapter = RedirectingAdapter(f"http://{PLAIN}:{net.target.port}/x")
    session = FuturesSession()
    session.mount("https://", adapter)
    exc = _attempt(lambda: send(HttpClient(base_url="https://api.futureagi.com", session=session), "https://api.futureagi.com/v1/ping"))
    net.nothing_sent()
    refused(exc, ValueError)


def test_challenge_response_session_authentication_completes(monkeypatch, sites):
    """``HTTPDigestAuth`` answers a 401 challenge through the response hook it registers; the hook runs."""
    site = sites(lambda method, path: (401, {"WWW-Authenticate": 'Digest realm="r", nonce="n1", qop="auth"'}, b""))
    challenges = []
    original = requests.auth.HTTPDigestAuth.handle_401

    def handle_401(self, r, **kwargs):
        challenges.append(r.status_code)
        return original(self, r, **kwargs)

    monkeypatch.setattr(requests.auth.HTTPDigestAuth, "handle_401", handle_401)
    session = FuturesSession()
    session.auth = requests.auth.HTTPDigestAuth("user", "pass")
    send(HttpClient(base_url=site.base, session=session), site.base + "/v1/ping")
    assert challenges == [401]
    assert len(site.requests) == 2


# ---------------------------------------------------------------------------------------------
# redirects of keyed plain-http requests to loopback or opted-in hosts
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_loopback_redirect_within_the_origin_is_followed(sites, status):
    site = sites(lambda method, path: ok() if path == "/final" else (status, {"Location": "/final"}, b""))
    response = send(HttpClient(base_url=site.base, default_headers=KEYED), site.base + "/v1/ping")
    assert response.status_code == 200
    assert site.requests == [("GET", "/v1/ping"), ("GET", "/final")]


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_loopback_redirect_to_a_named_plain_http_host_is_refused(net, sites, status):
    site = sites(lambda method, path: (status, {"Location": f"http://{PLAIN}:{net.target.port}/x"}, b""))
    exc = _attempt(lambda: send(HttpClient(base_url=site.base, default_headers=KEYED), site.base + "/v1/ping"))
    assert len(site.requests) == 1
    net.nothing_sent()
    refused(exc, ValueError)


def test_opted_in_redirect_is_followed_directly_past_environment_proxy(monkeypatch, net, sites):
    monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{net.proxy.port}")
    monkeypatch.setenv("ALL_PROXY", f"http://127.0.0.1:{net.proxy.port}")
    monkeypatch.setenv("NO_PROXY", "")
    site = sites(lambda method, path: (302, {"Location": f"http://{PLAIN}:{net.target.port}/x"}, b""))
    client = HttpClient(base_url=site.base, default_headers=KEYED, allow_insecure_http=True)
    _attempt(lambda: send(client, site.base + "/v1/ping"))
    net.delivered_direct()


def _kb(base: str, **kwargs):
    from fi.kb.client import KnowledgeBase

    return KnowledgeBase(fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base, **kwargs)


KB_ID = "00000000-0000-4000-8000-000000000001"
KB_PATH = "/model-hub/knowledge-base/"
KB_LIST_PATH = "/model-hub/knowledge-base/list/"


def _kb_route(status: int):
    def route(method, path):
        if path.startswith(KB_LIST_PATH):
            return ok(b'{"result": {"table_data": [{"id": "%s", "name": "docs"}]}}' % KB_ID.encode())
        if path == KB_PATH:
            return status, {"Location": "/moved" + KB_PATH}, b""
        if path == "/moved" + KB_PATH:
            return ok(b'{"status": true, "result": {"kb_id": "%s", "kb_name": "docs", "id": "%s", "name": "docs"}}' % (KB_ID.encode(), KB_ID.encode()))
        return 404, {}, b""

    return route


@pytest.mark.parametrize("status", [307, 308])
def test_knowledge_base_create_follows_a_loopback_redirect(sites, status):
    site = sites(_kb_route(status))
    kb = _kb(site.base).create_kb(name="docs")
    assert str(kb.kb.id) == KB_ID
    assert site.requests == [("POST", KB_PATH), ("POST", "/moved" + KB_PATH)]


@pytest.mark.parametrize("status", [307, 308])
def test_knowledge_base_update_follows_a_loopback_redirect(sites, status, tmp_path):
    (tmp_path / "notes.txt").write_text("notes")
    site = sites(_kb_route(status))
    kb = _kb(site.base, kb_name="docs").update_kb(kb_name="docs", new_name="docs", file_paths=[str(tmp_path / "notes.txt")])
    assert str(kb.kb.id) == KB_ID
    assert [entry for entry in site.requests if not entry[1].startswith(KB_LIST_PATH)] == [("PATCH", KB_PATH), ("PATCH", "/moved" + KB_PATH)]


def test_knowledge_base_create_redirect_to_a_named_plain_http_host_is_refused(net, sites):
    site = sites(lambda method, path: (307, {"Location": f"http://{PLAIN}:{net.target.port}{KB_PATH}"}, b""))
    exc = _attempt(lambda: _kb(site.base).create_kb(name="docs"))
    net.nothing_sent()
    refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# knowledge base errors and uploads
# ---------------------------------------------------------------------------------------------


def test_knowledge_base_by_name_reports_the_refusal(net):
    exc = _attempt(lambda: _kb(f"http://{PLAIN}:{net.target.port}", kb_name="docs"))
    net.nothing_sent()
    refused(exc, ValueError)


def test_knowledge_base_delete_reports_the_refusal(net):
    exc = _attempt(lambda: _kb(f"http://{PLAIN}:{net.target.port}").delete_kb(kb_ids=KB_ID))
    net.nothing_sent()
    refused(exc, ValueError)


def test_knowledge_base_upload_is_judged_without_the_client_session(sites):
    class Wrapping(requests.adapters.HTTPAdapter):
        pass

    session = FuturesSession()
    session.mount("http://", Wrapping())
    site = sites(_kb_route(307))
    kb = _kb(site.base, session=session).create_kb(name="docs")
    assert str(kb.kb.id) == KB_ID


# ---------------------------------------------------------------------------------------------
# transports a caller supplies
# ---------------------------------------------------------------------------------------------


class DirectSubclass(httpx.HTTPTransport):
    pass


class AsyncDirectSubclass(httpx.AsyncHTTPTransport):
    pass


class Answering(httpx.BaseTransport):
    """A transport with no connection pool and no inner transport."""

    def handle_request(self, request):
        return httpx.Response(200, json={})


class Routing(httpx.BaseTransport):
    """Holds its transports in a dict and sends through the first."""

    def __init__(self, routes) -> None:
        self.routes = routes

    def handle_request(self, request):
        return next(iter(self.routes.values())).handle_request(request)


def _platform(base, transport):
    client = Client(api_key=KEY, secret_key=SECRET, base_url=base, max_retries=0, timeout=3, http_client=httpx.Client(transport=transport))
    return _attempt(lambda: client.request("GET", "/v1/ping", unwrap=None))


def _gateway(base, transport):
    gw = Gateway(api_key=KEY, base_url=base, max_retries=0, timeout=3, http_client=httpx.Client(transport=transport))
    return _attempt(lambda: gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}]))


SENDS = {"platform": _platform, "gateway": _gateway}


@pytest.mark.parametrize("sender", list(SENDS))
def test_http_transport_subclass_is_accepted_for_loopback(net, sender):
    exc = SENDS[sender](f"http://127.0.0.1:{net.target.port}", DirectSubclass())
    assert getattr(exc, "code", None) != CODE, repr(exc)
    net.delivered_direct()


def test_async_http_transport_subclass_is_accepted_for_loopback(net):
    async def run():
        client = httpx.AsyncClient(transport=AsyncDirectSubclass())
        gw = AsyncGateway(api_key=KEY, base_url=f"http://127.0.0.1:{net.target.port}", http_client=client, max_retries=0, timeout=3)
        try:
            await gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        finally:
            await client.aclose()

    exc = _attempt(lambda: asyncio.run(run()))
    assert getattr(exc, "code", None) != CODE, repr(exc)
    net.delivered_direct()


@pytest.mark.parametrize("sender", list(SENDS))
def test_transport_without_pool_or_inner_transport_is_accepted_for_loopback(sender):
    exc = SENDS[sender]("http://127.0.0.1:9", Answering())
    assert getattr(exc, "code", None) != CODE, repr(exc)


@pytest.mark.parametrize("sender", list(SENDS))
def test_transport_holding_a_proxy_beside_a_direct_transport_is_refused(net, sender):
    routes = {"direct": httpx.HTTPTransport(), "proxied": httpx.HTTPTransport(proxy=f"http://127.0.0.1:{net.proxy.port}")}
    exc = SENDS[sender](f"http://127.0.0.1:{net.target.port}", Routing(routes))
    net.nothing_sent()
    refused(exc, AgentCCError if sender == "gateway" else ValueError)


# ---------------------------------------------------------------------------------------------
# gateway redirects and helpers
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("status", [301, 302, 307])
def test_gateway_redirect_response_is_a_status_error(sites, status):
    site = sites(lambda method, path: (status, {"Location": "/elsewhere"}, b""))
    gw = Gateway(api_key=KEY, base_url=site.base, max_retries=0, timeout=3)
    with pytest.raises(APIStatusError) as caught:
        gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
    assert caught.value.status_code == status


def test_gateway_redirect_response_to_a_stream_is_a_status_error(sites):
    site = sites(lambda method, path: (302, {"Location": "/elsewhere"}, b""))
    gw = Gateway(api_key=KEY, base_url=site.base, max_retries=0, timeout=3)
    with pytest.raises(APIStatusError) as caught:
        for _ in gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}], stream=True):
            pass
    assert caught.value.status_code == 302


def test_async_gateway_redirect_response_is_a_status_error(sites):
    site = sites(lambda method, path: (301, {"Location": "/elsewhere"}, b""))

    async def run():
        gw = AsyncGateway(api_key=KEY, base_url=site.base, max_retries=0, timeout=3)
        try:
            await gw.chat.completions.create(model="m", messages=[{"role": "user", "content": "hi"}])
        finally:
            await gw.aclose()

    with pytest.raises(APIStatusError) as caught:
        asyncio.run(run())
    assert caught.value.status_code == 301


def test_check_valid_key_reports_the_refusal(net):
    with pytest.raises(AgentCCError) as caught:
        check_valid_key(KEY, f"http://{PLAIN}:{net.target.port}")
    net.nothing_sent()
    refused(caught.value, AgentCCError)


def test_health_check_reports_the_refusal(net):
    with pytest.raises(AgentCCError) as caught:
        health_check(api_key=KEY, base_url=f"http://{PLAIN}:{net.target.port}", timeout=3)
    net.nothing_sent()
    refused(caught.value, AgentCCError)


def test_mock_client_with_a_named_plain_http_base_url_answers(net):
    from fi.gateway.testing import create_mock_client

    client = create_mock_client(responses={"/v1/models": {"object": "list", "data": []}}, base_url=f"http://{PLAIN}")
    client.models.list()
    net.nothing_sent()


# ---------------------------------------------------------------------------------------------
# hosts the opt-in does not unlock
# ---------------------------------------------------------------------------------------------


HOSTS_NOT_UNLOCKED = {
    "userinfo": "user@" + PLAIN,
    "percent": "plain%2eexample.test",
    "non-ascii": "plain.exämple.test",
    "trailing-dot": "localhost.",
    "short-ipv4": "127.1",
    "hex-ipv4": "0x7f.0.0.1",
    "octal-ipv4": "0177.0.0.1",
}


@pytest.mark.parametrize("form", list(HOSTS_NOT_UNLOCKED))
@pytest.mark.parametrize("sender", ["http-client", "platform-sync", "gateway-sync"])
def test_opt_in_does_not_unlock_hosts_written_ambiguously(monkeypatch, net, sender, form):
    from tests.test_plain_http_key_guards import EXPECTED, SENDERS

    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    exc = SENDERS[sender](f"http://{HOSTS_NOT_UNLOCKED[form]}:{net.target.port}")
    net.nothing_sent()
    refused(exc, *EXPECTED[sender])


class HoldsClient(httpx.BaseTransport):
    def __init__(self, client) -> None:
        self.client = client

    def handle_request(self, request):
        return self.client._transport_for_url(request.url).handle_request(request)


class Slotted(httpx.BaseTransport):
    __slots__ = ("inner",)

    def __init__(self, inner) -> None:
        self.inner = inner

    def handle_request(self, request):
        return self.inner.handle_request(request)


@pytest.mark.parametrize("holder", ["client", "slots", "nested"])
@pytest.mark.parametrize("sender", list(SENDS))
def test_proxy_held_deeper_inside_a_custom_transport_is_refused(net, sender, holder):
    proxied = httpx.HTTPTransport(proxy=f"http://127.0.0.1:{net.proxy.port}")
    transport = {
        "client": lambda: HoldsClient(httpx.Client(proxy=f"http://127.0.0.1:{net.proxy.port}")),
        "slots": lambda: Slotted(proxied),
        "nested": lambda: Routing({"group": [httpx.HTTPTransport(), {"inner": proxied}]}),
    }[holder]()
    exc = SENDS[sender](f"http://127.0.0.1:{net.target.port}", transport)
    net.nothing_sent()
    refused(exc, AgentCCError if sender == "gateway" else ValueError)
