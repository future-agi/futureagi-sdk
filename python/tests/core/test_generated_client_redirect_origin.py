"""The generated ``AuthenticatedClient`` with ``follow_redirects=True`` keeps its token on its own origin, whatever
header carries it. Origin A (a loopback listener) answers the first request with a 302 to origin B, another loopback
listener on a different port, so a different origin; B counts the connections it accepts and the token bytes in what it
reads. B receives 0 bytes of the token for every header name and prefix, sync and async, and for an https origin that
redirects to plain http on the same host. The client may stop at the 302 or raise a ``FutureAGIError`` that does not
carry the token; either way B reads no byte of it.

The chosen behaviour for a redirect to a path on the same origin: the client follows it and sends the token there too.

The token is generated per test with ``secrets.token_hex``; every listener is on 127.0.0.1 and no other host is dialed.
"""

from __future__ import annotations

import secrets
import shutil
import ssl
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from fi.errors import FutureAGIError
from fi.generated.openapi_client import AuthenticatedClient

HEADER_NAMES = ["Authorization", "X-Api-Key", "X-Fi-Token"]
PREFIXES = ["", "Bearer"]
LANDED = "/landed-after-the-redirect"


class Listener:
    """A loopback HTTP listener; it answers ``/start`` with a 302 to ``location`` and anything else with 200, and
    keeps the raw bytes of every request it reads."""

    def __init__(self, location: str | None = None, tls: ssl.SSLContext | None = None) -> None:
        self.location = location
        self.requests: list[tuple[str, bytes]] = []
        self.connections = 0
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def setup(self) -> None:
                super().setup()
                outer.connections += 1

            def do_GET(self) -> None:
                length = int(self.headers.get("content-length") or 0)
                body = self.rfile.read(length) if length else b""
                outer.requests.append((self.path, self.raw_requestline + str(self.headers).encode("latin-1") + body))
                if self.path == "/start" and outer.location is not None:
                    self.send_response(302)
                    self.send_header("Location", outer.location)
                else:
                    self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args) -> None:
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        if tls is not None:
            self._server.socket = tls.wrap_socket(self._server.socket, server_side=True)
        self.port = self._server.server_address[1]
        scheme = "https" if tls is not None else "http"
        self.origin = f"{scheme}://127.0.0.1:{self.port}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def token_bytes(self, token: str) -> int:
        return sum(raw.count(token.encode()) for _, raw in self.requests) * len(token)

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def token() -> str:
    return secrets.token_hex(24)


@pytest.fixture
def target():
    listener = Listener()
    yield listener
    listener.close()


@pytest.fixture
def plain_origin(target):
    listener = Listener(location=f"{target.origin}{LANDED}")
    yield listener
    listener.close()


@pytest.fixture
def same_origin():
    listener = Listener(location=LANDED)
    yield listener
    listener.close()


@pytest.fixture
def tls_files(tmp_path):
    if shutil.which("openssl") is None:
        pytest.skip("the openssl command line tool is needed for the https origin")
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key), "-out", str(cert),
         "-days", "2", "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"],
        check=True, capture_output=True,
    )
    server = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server.load_cert_chain(str(cert), str(key))
    client = ssl.create_default_context(cafile=str(cert))
    return server, client


@pytest.fixture
def tls_origin(target, tls_files):
    listener = Listener(location=f"{target.origin}{LANDED}", tls=tls_files[0])
    yield listener
    listener.close()


def _client(origin: Listener, token: str, header: str, prefix: str, verify: ssl.SSLContext | bool = True) -> AuthenticatedClient:
    return AuthenticatedClient(
        base_url=origin.origin, token=token, prefix=prefix, auth_header_name=header,
        follow_redirects=True, verify_ssl=verify, timeout=30.0,
    )


def _send(origin: Listener, token: str, header: str, prefix: str, verify: ssl.SSLContext | bool = True) -> None:
    try:
        with _client(origin, token, header, prefix, verify) as client:
            client.get_httpx_client().get("/start")
    except FutureAGIError as error:
        assert token not in str(error)


async def _send_async(origin: Listener, token: str, header: str, prefix: str) -> None:
    try:
        async with _client(origin, token, header, prefix) as client:
            await client.get_async_httpx_client().get("/start")
    except FutureAGIError as error:
        assert token not in str(error)


def _assert_origin_got_it_and_target_did_not(origin: Listener, target: Listener, token: str) -> None:
    assert origin.requests and origin.requests[0][0] == "/start"
    assert token.encode() in origin.requests[0][1]
    assert target.token_bytes(token) == 0, (
        f"the other origin read {target.token_bytes(token)} token bytes over {target.connections} connection(s)"
    )


@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("header", HEADER_NAMES)
def test_token_header_is_not_sent_to_another_origin_after_a_redirect(plain_origin, target, token, header, prefix):
    _send(plain_origin, token, header, prefix)
    _assert_origin_got_it_and_target_did_not(plain_origin, target, token)


@pytest.mark.anyio
@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("header", HEADER_NAMES)
async def test_async_token_header_is_not_sent_to_another_origin_after_a_redirect(
    plain_origin, target, token, header, prefix
):
    await _send_async(plain_origin, token, header, prefix)
    _assert_origin_got_it_and_target_did_not(plain_origin, target, token)


@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("header", HEADER_NAMES)
def test_token_header_is_not_sent_over_plain_http_after_an_https_redirect_on_the_same_host(
    tls_origin, tls_files, target, token, header, prefix
):
    _send(tls_origin, token, header, prefix, verify=tls_files[1])
    _assert_origin_got_it_and_target_did_not(tls_origin, target, token)


@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("header", HEADER_NAMES)
def test_token_header_follows_a_redirect_to_a_path_on_the_same_origin(same_origin, token, header, prefix):
    with _client(same_origin, token, header, prefix) as client:
        assert client.get_httpx_client().get("/start").status_code == 200
    assert [path for path, _ in same_origin.requests] == ["/start", LANDED]
    expected = (f"{prefix} {token}" if prefix else token).encode()
    assert all(f"{header}: ".encode() + expected in raw for _, raw in same_origin.requests)


@pytest.mark.anyio
@pytest.mark.parametrize("header", HEADER_NAMES)
async def test_async_token_header_follows_a_redirect_to_a_path_on_the_same_origin(same_origin, token, header):
    async with _client(same_origin, token, header, "Bearer") as client:
        assert (await client.get_async_httpx_client().get("/start")).status_code == 200
    assert [path for path, _ in same_origin.requests] == ["/start", LANDED]
    assert all(token.encode() in raw for _, raw in same_origin.requests)
