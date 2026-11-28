"""fi.platform Client/AsyncClient and HttpClient (the SDK's session, a caller's requests.Session and FuturesSession)
follow a 301, 302, 303, 307 or 308 on the origin of the request (scheme, host and port), as futureagi 0.8.1 follows it,
with the 0.8.1 method and body rules, and each hop is judged as any request. A redirect to another scheme on the same
host (https to http included), another host or another port is refused and nothing is sent there; a chain that leaves
the origin is refused at its first hop off it and does not come back to the first origin; a 300 is not followed; a
sixth redirect in a row is refused after six sends. Loopback listeners and planted marker keys only."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import ssl
import threading
import time
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from itertools import pairwise

import httpx
import pytest
import requests
from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from fi.platform import APIConnectionError, AsyncClient, Client
from requests_futures.sessions import FuturesSession

MAX_HOPS = 5
TIMEOUT = 1.0
HOST = "127.0.0.1"
KEY = "mk-redirect-081-a17c"
SECRET = "ms-redirect-081-b28d"
MARKERS = (KEY.encode(), SECRET.encode())
BODY = {"payload": "redirect-body"}
LANDED = b'{"status": true, "result": {"ok": 1}}'
PLATFORM = ("platform_sync", "platform_async")
CALLER_SESSIONS = ("httpclient_requests", "httpclient_futures")
CLIENTS = (*PLATFORM, "httpclient_sdk", *CALLER_SESSIONS)


@dataclass(frozen=True)
class Hit:
    method: str
    path: str
    scheme: str
    body: bytes
    marker_bytes: int
    key_headers_match: bool

    @property
    def body_length(self):
        return len(self.body)


class Origin(ThreadingHTTPServer):
    def __init__(self, host=HOST, tls=None):
        super().__init__((host, 0), Handler)
        self.routes: dict[str, tuple[int, str]] = {}
        self.hits: list[Hit] = []
        self.tls = tls
        self.port = self.server_address[1]
        self.http = f"http://{host}:{self.port}"
        self.https = f"https://{host}:{self.port}"

    def process_request_thread(self, request, client_address):
        request.settimeout(TIMEOUT)
        if self.tls is not None:
            try:
                # Both schemes use this port; record HTTP requests as well as TLS requests.
                if request.recv(1, socket.MSG_PEEK) == b"\x16":
                    request = self.tls.wrap_socket(request, server_side=True)
            except OSError:
                self.shutdown_request(request)
                return
        super().process_request_thread(request, client_address)


class Handler(BaseHTTPRequestHandler):
    server: Origin
    protocol_version = "HTTP/1.1"

    def _answer(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        wire = self.raw_requestline + self.headers.as_bytes() + body
        self.server.hits.append(Hit(
            method=self.command,
            path=self.path,
            scheme="https" if isinstance(self.connection, ssl.SSLSocket) else "http",
            body=body,
            marker_bytes=sum(wire.count(marker) * len(marker) for marker in MARKERS),
            key_headers_match=(self.headers.get("X-Api-Key"), self.headers.get("X-Secret-Key")) == (KEY, SECRET),
        ))
        location = None
        if self.path in self.server.routes:
            status, location = self.server.routes[self.path]
            payload = b""
        elif self.path == "/landed":
            status, payload = 200, LANDED
        else:
            status, payload = 404, b""
        self.send_response(status)
        if location is not None:
            self.send_header("Location", location)
        if payload:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        if payload and self.command != "HEAD":
            self.wfile.write(payload)

    do_GET = do_POST = do_PUT = do_HEAD = _answer

    def log_message(self, *args):
        pass


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "FI_EXTRA_HEADERS", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
        monkeypatch.delenv(name, raising=False)
        monkeypatch.delenv(name.lower(), raising=False)
    monkeypatch.setenv("NETRC", str(tmp_path / "empty-netrc"))
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "empty-login.json"))
    monkeypatch.setenv("FI_RUN_DIR", str(tmp_path / "runs"))


@pytest.fixture
def origins():
    def start(host=HOST, tls=None):
        server = stack.enter_context(Origin(host, tls))
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        thread.start()
        stack.callback(thread.join, 1)
        stack.callback(server.shutdown)
        return server

    with ExitStack() as stack:
        yield start


@pytest.fixture
def tls_contexts(tmp_path, monkeypatch):
    x509 = pytest.importorskip("cryptography.x509", reason="The loopback TLS cases need a test certificate")
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, HOST)])
    generated = datetime.fromtimestamp(time.time(), tz=timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(generated - timedelta(days=1))
        .not_valid_after(generated + timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(HOST))]), critical=False)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    cert_file, key_file = tmp_path / "test-cert.pem", tmp_path / "test-key.pem"
    cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_file.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption(),
    ))
    server = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server.load_cert_chain(cert_file, key_file)
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(cert_file))
    return server, ssl.create_default_context(cafile=str(cert_file))


def _keyed_redirect_error():
    from fi.errors import KeyedRedirectRefusedError

    return KeyedRedirectRefusedError


def _send(client_kind, base, method, *, verify=None):
    # fi.Client and fi.AsyncClient are the fi.platform exports under test.
    body = None if method == "HEAD" else BODY
    if client_kind in PLATFORM:
        kwargs = {"api_key": KEY, "secret_key": SECRET, "base_url": base, "timeout": TIMEOUT, "max_retries": 0}
        if client_kind == "platform_sync":
            with ExitStack() as stack:
                if verify is not None:
                    kwargs["http_client"] = stack.enter_context(httpx.Client(verify=verify, trust_env=False))
                with Client(**kwargs) as client:
                    return client.request(method, "/start", body=body)

        async def run():
            if verify is None:
                async with AsyncClient(**kwargs) as client:
                    return await client.request(method, "/start", body=body)
            async with (
                httpx.AsyncClient(verify=verify, trust_env=False) as http,
                AsyncClient(http_client=http, **kwargs) as client,
            ):
                return await client.request(method, "/start", body=body)

        return asyncio.run(run())

    if client_kind == "httpclient_requests":
        session = requests.Session()
    elif client_kind == "httpclient_futures":
        session = FuturesSession(max_workers=1)
    else:
        session = None
    client = APIKeyAuth(fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base, session=session)
    try:
        return client.request(RequestConfig(
            method=HttpMethod(method), url=base + "/start", json=body, timeout=TIMEOUT, retry_attempts=1,
        ))
    finally:
        client.close()


def _assert_landed(result):
    if isinstance(result, requests.Response):
        assert result.status_code == 200
        assert result.json() == {"status": True, "result": {"ok": 1}}
    else:
        assert result == {"ok": 1}


def _assert_hits(origin, paths, *, scheme="http"):
    assert [hit.path for hit in origin.hits] == paths
    for hit in origin.hits:
        assert hit.scheme == scheme
        assert hit.marker_bytes == sum(map(len, MARKERS))
        assert hit.key_headers_match


def _assert_two_hops(origin, method, sent_body, next_method, next_body):
    _assert_hits(origin, ["/start", "/landed"])
    first, second = origin.hits
    assert first.method == method
    assert (first.body_length > 0) is sent_body
    assert second.method == next_method
    assert second.body == (first.body if next_body else b"")


@pytest.mark.parametrize("client_kind", CLIENTS)
@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_follow_status(status, client_kind, origins):
    origin = origins()
    origin.routes["/start"] = (status, "/landed")
    _assert_landed(_send(client_kind, origin.http, "POST"))
    preserve = status in (307, 308)
    _assert_two_hops(origin, "POST", True, "POST" if preserve else "GET", preserve)


@pytest.mark.parametrize("client_kind", CLIENTS)
@pytest.mark.parametrize("status", [301, 302, 303])
def test_follow_status_with_put(status, client_kind, origins):
    origin = origins()
    origin.routes["/start"] = (status, "/landed")
    _assert_landed(_send(client_kind, origin.http, "PUT"))
    platform = client_kind in PLATFORM
    next_method = "GET" if status == 303 or (status == 302 and not platform) else "PUT"
    _assert_two_hops(origin, "PUT", True, next_method, platform and status != 303)


@pytest.mark.parametrize("client_kind", PLATFORM)
def test_follow_303_with_head(client_kind, origins):
    origin = origins()
    origin.routes["/start"] = (303, "/landed")
    _assert_landed(_send(client_kind, origin.http, "HEAD"))
    _assert_two_hops(origin, "HEAD", False, "GET", False)


@pytest.mark.parametrize("client_kind", CLIENTS)
def test_follow_absolute_location(client_kind, origins):
    origin = origins()
    origin.routes["/start"] = (307, origin.http + "/landed")
    _assert_landed(_send(client_kind, origin.http, "POST"))
    _assert_two_hops(origin, "POST", True, "POST", True)


@pytest.mark.parametrize("client_kind", CLIENTS)
def test_follow_explicit_and_implicit_default_port(client_kind, origins, monkeypatch):
    origin = origins()
    origin.routes["/start"] = (308, f"http://{HOST}:80/landed")
    # Map only this loopback socket's port, leaving both URL spellings intact for the clients.
    def connect_at_test_port(connect):
        def connect_local(sock, address):
            if address == (HOST, 80):
                address = (HOST, origin.port)
            return connect(sock, address)

        return connect_local

    for name in ("connect", "connect_ex"):
        monkeypatch.setattr(socket.socket, name, connect_at_test_port(getattr(socket.socket, name)))
    _assert_landed(_send(client_kind, f"http://{HOST}", "POST"))
    _assert_two_hops(origin, "POST", True, "POST", True)


def _chain(origin, redirects):
    paths = ["/start", *(f"/hop/{index}" for index in range(1, redirects)), "/landed"]
    origin.routes.update({source: (307, target) for source, target in pairwise(paths)})
    return paths


@pytest.mark.parametrize("client_kind", CLIENTS)
def test_follow_five_redirects(client_kind, origins):
    origin = origins()
    paths = _chain(origin, MAX_HOPS)
    _assert_landed(_send(client_kind, origin.http, "POST"))
    _assert_hits(origin, paths)
    assert origin.hits[0].body
    assert all(hit.method == "POST" and hit.body == origin.hits[0].body for hit in origin.hits)


@pytest.mark.parametrize("client_kind", CLIENTS)
@pytest.mark.parametrize("case", ["other_host", "other_port", "return_to_a", "local_hop_then_return_to_a"])
def test_refused_cross_origin(case, client_kind, origins):
    a = origins()
    b = origins("127.0.0.2" if case == "other_host" else HOST)
    target = b.http + "/landed"
    expected = ["/start"]
    if case in ("return_to_a", "local_hop_then_return_to_a"):
        target = b.http + "/back"
        b.routes["/back"] = (302, a.http + "/landed")
    if case == "local_hop_then_return_to_a":
        a.routes.update({"/start": (302, "/x"), "/x": (302, target)})
        expected.append("/x")
    else:
        a.routes["/start"] = (302, target)
    with pytest.raises(_keyed_redirect_error()):
        _send(client_kind, a.http, "POST")
    assert b.hits == []
    _assert_hits(a, expected)


@pytest.mark.parametrize("client_kind", CLIENTS)
def test_refused_300_with_location(client_kind, origins):
    origin = origins()
    origin.routes["/start"] = (300, "/landed")
    if client_kind in CALLER_SESSIONS:
        # A caller's session returns the 300 answer, not followed (0.8.1 did not follow a 300 either).
        response = _send(client_kind, origin.http, "POST")
        assert response.status_code == 300
    else:
        with pytest.raises(_keyed_redirect_error()):
            _send(client_kind, origin.http, "POST")
    _assert_hits(origin, ["/start"])


@pytest.mark.parametrize("client_kind", CLIENTS)
@pytest.mark.parametrize("scheme", ["http", "https"], ids=["http_to_https", "https_to_http"])
def test_refused_scheme_change(scheme, client_kind, origins, tls_contexts):
    server_tls, client_tls = tls_contexts
    origin = origins(tls=server_tls)
    base, target = (origin.http, origin.https) if scheme == "http" else (origin.https, origin.http)
    origin.routes["/start"] = (302, target + "/landed")
    with pytest.raises(_keyed_redirect_error()):
        _send(client_kind, base, "POST", verify=client_tls)
    _assert_hits(origin, ["/start"], scheme=scheme)


@pytest.mark.parametrize("client_kind", CLIENTS)
def test_refused_hop_limit(client_kind, origins):
    origin = origins()
    paths = _chain(origin, MAX_HOPS + 1)
    if client_kind in PLATFORM:
        with pytest.raises(APIConnectionError, match="more than 5 redirects"):
            _send(client_kind, origin.http, "POST")
    else:
        with pytest.raises(requests.TooManyRedirects, match="Exceeded 5 redirects"):
            _send(client_kind, origin.http, "POST")
    _assert_hits(origin, paths[:-1])


@pytest.mark.parametrize("client_kind", CLIENTS)
def test_follow_on_an_https_origin(client_kind, origins, tls_contexts):
    server_tls, client_tls = tls_contexts
    origin = origins(tls=server_tls)
    origin.routes["/start"] = (307, origin.https + "/landed")
    _assert_landed(_send(client_kind, origin.https, "POST", verify=client_tls))
    _assert_hits(origin, ["/start", "/landed"], scheme="https")


@pytest.mark.parametrize("client_kind", CLIENTS)
@pytest.mark.parametrize("scheme", ["http", "https"], ids=["http_to_https", "https_to_http"])
def test_refused_scheme_change_after_a_followed_hop(scheme, client_kind, origins, tls_contexts):
    # The first hop stays on the origin and is followed; the second names the other scheme on the same host and port
    # and is refused: nothing goes out over it.
    server_tls, client_tls = tls_contexts
    origin = origins(tls=server_tls)
    base, other = (origin.http, origin.https) if scheme == "http" else (origin.https, origin.http)
    origin.routes.update({"/start": (302, "/x"), "/x": (307, other + "/landed")})
    with pytest.raises(_keyed_redirect_error()):
        _send(client_kind, base, "POST", verify=client_tls)
    _assert_hits(origin, ["/start", "/x"], scheme=scheme)
