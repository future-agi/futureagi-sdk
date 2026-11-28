"""0.8.1 send counts and recipients for answers the HTTP library cannot finish reading, and gateway origin variables.

- An unreadable redirect location or a short response body produces an error without repeating the keyed request.
- A short response body at the end of a same-origin redirect chain does not repeat either request.
- With ``FI_GATEWAY_URL`` (or ``AGENTCC_BASE_URL``) and ``FI_GATEWAY_BASE_URL`` both set, the gateway clients send to the
  0.8.1 variable's origin; 0.8.1 did not read ``FI_GATEWAY_BASE_URL``.
- The gateway resource modules expose the names 0.8.1 exposed.
"""

from __future__ import annotations

import asyncio
import socket
import threading

import pytest
import requests
from requests_futures.sessions import FuturesSession

from fi.api.auth import HttpClient
from fi.api.types import HttpMethod, RequestConfig
from tests.test_plain_http_key_guards import PROXY_VARS

KEY = "test-key-marker-answered-1"
GATEWAY_KEY = "sk-agentcc-test-marker-answered-1"


class RawSink:
    """A loopback listener that records requests, with an optional reply per path."""

    def __init__(self, reply: bytes, *, routes: dict[bytes, bytes] | None = None) -> None:
        self.reply = reply
        self.routes = routes or {}
        self.requests: list[bytes] = []
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(16)
        self.port = self.sock.getsockname()[1]
        self._stop = False
        threading.Thread(target=self._serve, daemon=True).start()

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def _serve(self) -> None:
        while not self._stop:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            with conn, conn.makefile("rb") as stream:
                conn.settimeout(3)
                try:
                    request_line = stream.readline()
                    if not request_line:
                        continue
                    data = request_line
                    content_length = 0
                    for line in stream:
                        data += line
                        if line.lower().startswith(b"content-length:"):
                            content_length = int(line.split(b":", 1)[1])
                        if line == b"\r\n":
                            # Consume the request body so closing the socket does not reset the connection.
                            data += stream.read(content_length)
                            break
                    self.requests.append(data)
                    path = request_line.split()[1]
                    conn.sendall(self.routes.get(path, self.reply))
                except OSError:
                    continue

    def close(self) -> None:
        self._stop = True
        self.sock.close()


BAD_LOCATION = b"HTTP/1.1 302 Found\r\nLocation: /\xff bad\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
REDIRECT = b"HTTP/1.1 302 Found\r\nLocation: /moved\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
SHORT_REDIRECT = b"HTTP/1.1 302 Found\r\nLocation: /moved\r\nContent-Length: 20\r\nConnection: close\r\n\r\nabcdef"
SHORT_OK = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 20\r\nConnection: close\r\n\r\n{\"a\":"


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    for name in (*PROXY_VARS, "FI_ALLOW_INSECURE_HTTP", "FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL", "FI_GATEWAY_URL",
                 "FI_GATEWAY_BASE_URL", "AGENTCC_BASE_URL", "FI_GATEWAY_API_KEY", "AGENTCC_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def _session(kind: str):
    if kind == "sdk":
        return None
    inner = requests.Session()
    return inner if kind == "requests" else FuturesSession(session=inner)


def _call(base: str, session) -> None:
    client = HttpClient(base, session, {"X-Api-Key": KEY})
    client.request(RequestConfig(method=HttpMethod.GET, url=base + "/x", retry_attempts=3, retry_delay=0, timeout=3))


@pytest.mark.parametrize("kind", ["sdk", "requests", "futures"])
@pytest.mark.parametrize("reply", [BAD_LOCATION, SHORT_REDIRECT, SHORT_OK], ids=["bad-location", "short-redirect", "short-ok"])
def test_an_answered_keyed_request_is_sent_once(kind, reply):
    sink = RawSink(reply)
    try:
        with pytest.raises(Exception):
            _call(sink.base, _session(kind))
        assert len(sink.requests) == 1, len(sink.requests)
        assert KEY.encode() in sink.requests[0]
    finally:
        sink.close()


@pytest.mark.parametrize("kind", ["sdk", "requests", "futures"])
def test_a_short_same_origin_redirect_target_is_requested_once(kind):
    sink = RawSink(REDIRECT, routes={b"/moved": SHORT_OK})
    try:
        with pytest.raises(requests.exceptions.ChunkedEncodingError):
            _call(sink.base, _session(kind))
        assert [req.splitlines()[0] for req in sink.requests] == [b"GET /x HTTP/1.1", b"GET /moved HTTP/1.1"]
        assert all(KEY.encode() in req for req in sink.requests)
    finally:
        sink.close()


def test_a_connection_failure_is_still_retried(monkeypatch):
    attempts = []
    original = requests.Session.send

    def failing(self, request, **kwargs):
        attempts.append(request.url)
        if len(attempts) < 3:
            raise requests.exceptions.ConnectionError("connection refused by the test")
        return original(self, request, **kwargs)

    sink = RawSink(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}")
    try:
        monkeypatch.setattr(requests.Session, "send", failing)
        _call(sink.base, requests.Session())
        assert len(attempts) == 3
        assert len(sink.requests) == 1
    finally:
        sink.close()


@pytest.mark.parametrize("short_at", ["redirect", "target"])
def test_a_prompt_lookup_does_not_resend_after_a_short_body(short_at):
    from fi.prompt import Prompt
    from fi.utils.routes import Routes

    secret = "test-secret-marker"
    reply = SHORT_REDIRECT if short_at == "redirect" else REDIRECT
    sink = RawSink(reply, routes={b"/moved": SHORT_OK})
    try:
        with pytest.raises(requests.exceptions.ChunkedEncodingError):
            Prompt.get_template_by_name("probe", fi_api_key=KEY, fi_secret_key=secret, fi_base_url=sink.base,
                                        allow_insecure_http=False)
        initial = f"GET /{Routes.prompt_label_get_by_name.value}?name=probe&label=production HTTP/1.1".encode()
        expected = [initial] if short_at == "redirect" else [initial, b"GET /moved HTTP/1.1"]
        assert [req.splitlines()[0] for req in sink.requests] == expected
        assert all(KEY.encode() in req and secret.encode() in req for req in sink.requests)
    finally:
        sink.close()


OK_MODELS = b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 30\r\nConnection: close\r\n\r\n{\"object\":\"list\",\"data\":[]}   "


@pytest.mark.parametrize("released", ["FI_GATEWAY_URL", "AGENTCC_BASE_URL"])
@pytest.mark.parametrize("client", ["AgentCC", "AsyncAgentCC", "Gateway", "AsyncGateway"])
def test_the_released_gateway_variable_names_the_origin(monkeypatch, released, client):
    import fi.gateway as gw

    first, other = RawSink(OK_MODELS), RawSink(OK_MODELS)
    try:
        monkeypatch.setenv(released, first.base)
        monkeypatch.setenv("FI_GATEWAY_BASE_URL", other.base)
        cls = getattr(gw, client)
        if client.startswith("Async"):
            async def go():
                c = cls(api_key=GATEWAY_KEY, max_retries=0, allow_insecure_http=True)
                try:
                    await c.models.list()
                finally:
                    await c.aclose()
            try:
                asyncio.run(go())
            except Exception:
                pass
        else:
            c = cls(api_key=GATEWAY_KEY, max_retries=0, allow_insecure_http=True)
            try:
                c.models.list()
            except Exception:
                pass
            finally:
                c.close()
        assert len(first.requests) == 1, len(first.requests)
        assert GATEWAY_KEY.encode() in first.requests[0]
        assert other.requests == []
    finally:
        first.close()
        other.close()


def test_the_gateway_resource_modules_expose_the_081_names():
    from fi.gateway.resources import audio
    from fi.gateway.resources.chat import completions

    assert audio.NOT_GIVEN is not None
    assert completions.Iterator is not None
    for name in ("RequestOptions", "Transcription", "Translation", "NOT_GIVEN", "build_extra_headers",
                 "collect_agentcc_params", "merge_session_headers"):
        assert name in audio.__all__, name
    namespace: dict = {}
    exec("from fi.gateway.resources.audio import *", namespace)
    assert "RequestOptions" in namespace
