"""Header injection on the wire: the exact request bytes a raw 127.0.0.1 socket server receives.

For each injection attempt, through FI_EXTRA_HEADERS and through extra_headers= (mapping and text),
and through each HTTP stack the SDK sends platform requests with (the requests session of
``fi.api.auth``, the knowledge-base direct upload, the httpx typed clients sync and async, the
webhooks client, the CLI): either the SDK refuses with EXTRA_HEADERS_INVALID and the server gets
no connection at all, or exactly the intended header lines arrive. A second, injected header line
never does. The server is a bare socket (no HTTP library), so what it records is what was sent.
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import threading
from typing import Callable

import pytest

from fi._extra_headers import ENV_VAR, ExtraHeadersError

KB = "00000000-0000-0000-0000-0000000000d5"
FORBIDDEN = (b"x-evil", b"other", b"smuggled", b"evil-token")


class RawServer:
    """Accepts on 127.0.0.1, records each request's raw head (request line and header lines, as
    bytes) and answers 200 with a small JSON body, closing the connection."""

    def __init__(self) -> None:
        self.connections = 0
        self.heads: list[bytes] = []
        self.answers = {b"/model-hub/knowledge-base/": json.dumps(
            {"result": {"kb_id": KB, "kb_name": "kb", "file_ids": []}}).encode()}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(32)
        self.url = f"http://127.0.0.1:{self.sock.getsockname()[1]}"
        self._lock = threading.Lock()
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            with self._lock:
                self.connections += 1
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn: socket.socket) -> None:
        with conn:
            conn.settimeout(10)
            data = b""
            try:
                while b"\r\n\r\n" not in data:
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    data += chunk
                head, _, rest = data.partition(b"\r\n\r\n")
                with self._lock:
                    self.heads.append(head)
                length = 0
                for line in head.split(b"\r\n")[1:]:
                    name, _, value = line.partition(b":")
                    if name.strip().lower() == b"content-length":
                        length = int(value.strip() or 0)
                while len(rest) < length:
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    rest += chunk
                parts = head.split(b" ")
                path = parts[1].split(b"?")[0] if len(parts) > 1 else b"/"
                body = self.answers.get(path, b"{}")
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
                             + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
            except OSError:
                pass

    def close(self) -> None:
        self.sock.close()


def header_lines(head: bytes) -> list[bytes]:
    return head.split(b"\r\n")[1:]


def assert_exact(server: RawServer, expected: dict[str, str]) -> None:
    """One request arrived; each expected header is exactly one line with exactly its value; every
    line is a well-formed header line; nothing injected; the SDK's key arrives once, unchanged."""
    assert server.connections == 1 and len(server.heads) == 1, (server.connections, server.heads)
    lines = header_lines(server.heads[0])
    names = [line.partition(b":")[0].lower() for line in lines]
    for line in lines:
        assert b":" in line and line[:1] not in (b" ", b"\t"), line  # no stray or folded line
        assert all(32 <= byte < 127 or byte == 9 for byte in line), line
        assert not any(word in line.lower() for word in FORBIDDEN), line
    for name, value in expected.items():
        assert names.count(name.lower().encode()) == 1, (name, lines)
        line = lines[names.index(name.lower().encode())]
        assert line.partition(b":")[2].strip() == value.encode(), line
    assert names.count(b"x-api-key") <= 1 and names.count(b"x-secret-key") <= 1
    for line in lines:
        if line.lower().startswith(b"x-api-key:"):
            assert line.partition(b":")[2].strip() == b"ak-test", line


# ---- the clients: each sends one platform request; ``arg`` is its extra_headers= ---------------


def via_http_client(base: str, arg) -> None:
    from fi.api.auth import APIKeyAuth
    from fi.api.types import HttpMethod, RequestConfig

    client = APIKeyAuth(extra_headers=arg)
    try:
        client.request(RequestConfig(method=HttpMethod.GET, url=f"{base}/model-hub/x", retry_attempts=1))
    finally:
        client.close()


def via_kb_upload(base: str, arg) -> None:
    from fi.kb.client import KnowledgeBase

    KnowledgeBase(extra_headers=arg).create_kb("kb")


def via_typed_sync(base: str, arg) -> None:
    from fi.futureagi_client import FutureAGIClient

    with FutureAGIClient(extra_headers=arg) as client:
        client.generated_client.get_httpx_client().get("/model-hub/x")


def via_typed_async(base: str, arg) -> None:
    from fi.futureagi_async_client import AsyncFutureAGIClient

    async def go() -> None:
        client = AsyncFutureAGIClient(extra_headers=arg)
        try:
            await client.request("GET", "/model-hub/x")
        finally:
            await client.generated_client.get_async_httpx_client().aclose()

    asyncio.run(go())


def via_webhooks(base: str, arg) -> None:
    from fi.webhooks import Webhooks

    with Webhooks(extra_headers=arg) as wh:
        wh.event_types()


CLIENTS: dict[str, Callable[[str, object], None]] = {
    "http_client": via_http_client,
    "kb_upload": via_kb_upload,
    "typed_sync": via_typed_sync,
    "typed_async": via_typed_async,
    "webhooks": via_webhooks,
}

# FI_EXTRA_HEADERS text: every one refused, nothing sent
SETTING_ATTEMPTS = {
    "crlf-colon-api-key": "X-A=1\r\nX-Api-Key: other",
    "crlf-equals-api-key": "X-A=1\r\nX-Api-Key=other",
    "lf-colon-authorization": "X-A=1\nAuthorization: Bearer evil-token-1",
    "cr-colon-header": "X-A=1\rX-Evil: 1",
    "crlf-smuggled-request": "X-A=1\r\n\r\nGET /smuggled HTTP/1.1",
    "nul-header": "X-A=1\x00X-Evil: 1",
    "tab-header": "X-A=1\tX-Evil: 1",
    "vt-header": "X-A=1\x0bX-Evil: 1",
    "del-header": "X-A=1\x7fX-Evil: 1",
    "colon-name": "X-A: 1=2",
    "space-name": "X A=1",
    "tab-name": "X-A\t=1",
}

# extra_headers= as a mapping: every one refused when the client is built, nothing sent
MAPPING_ATTEMPTS = {
    "value-crlf-api-key": {"X-A": "1\r\nX-Api-Key: other"},
    "value-lf-header": {"X-A": "1\nX-Evil: 1"},
    "value-cr-header": {"X-A": "1\rX-Evil: 1"},
    "value-crlf-trailing": {"X-A": "1\r\n"},
    "value-crlf-smuggle": {"X-A": "1\r\n\r\nGET /smuggled HTTP/1.1"},
    "value-nul-header": {"X-A": "1\x00X-Evil: 1"},
    "value-tab-header": {"X-A": "1\tX-Evil: 1"},
    "value-esc": {"X-A": "1\x1b[2J"},
    "value-del": {"X-A": "1\x7f"},
    "name-crlf-header": {"X-A\r\nX-Evil": "1"},
    "name-lf-trailing": {"X-A\n": "1"},
    "name-colon": {"X-A:": "1"},
    "name-header-line": {"X-A: 1\r\nX-Evil": "1"},
    "name-space-inside": {"X A": "1"},
    "name-space-trailing": {"X-A ": "1"},
    "name-tab": {"X\tA": "1"},
}

# extra_headers= as text: the same rules as the setting
TEXT_ATTEMPTS = {
    "text-crlf-colon-api-key": "X-A=1\r\nX-Api-Key: other",
    "text-crlf-equals-api-key": "X-A=1\r\nX-Api-Key=other",
    "text-nul-header": "X-A=1\x00X-Evil: 1",
    "text-colon-name": "X-A:=1",
}

# by design: ';', CR and LF separate entries, each checked; exactly these lines arrive
SETTING_BY_DESIGN = {
    "crlf-two-headers": ("X-A=1\r\nX-B=2", {"X-A": "1", "X-B": "2"}),
    "lf-two-headers": ("X-A=1\nX-B=2", {"X-A": "1", "X-B": "2"}),
    "crlf-trailing-one-header": ("X-A=1\r\n", {"X-A": "1"}),
}


@pytest.fixture
def server(monkeypatch, tmp_path):
    srv = RawServer()
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setenv("FI_BASE_URL", srv.url)
    monkeypatch.setenv("FI_API_KEY", "ak-test")
    monkeypatch.setenv("FI_SECRET_KEY", "sk-test")
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "no-login.json"))
    yield srv
    srv.close()


def set_setting(monkeypatch, payload: str) -> None:
    """FI_EXTRA_HEADERS = payload. A real environment cannot hold NUL: the OS refuses it (checked
    here), so for a NUL payload a stand-in os.environ mapping still drives the SDK's own check."""
    if "\x00" not in payload:
        monkeypatch.setenv(ENV_VAR, payload)
        return
    with pytest.raises(ValueError):
        os.environ[ENV_VAR] = payload
    assert ENV_VAR not in os.environ
    monkeypatch.setattr(os, "environ", {**os.environ, ENV_VAR: payload})


def refused_and_nothing_sent(server: RawServer, call: Callable[[], None]) -> ExtraHeadersError:
    with pytest.raises(ExtraHeadersError) as info:
        call()
    assert info.value.get_error_code() == "EXTRA_HEADERS_INVALID"
    message = str(info.value)
    assert not any(word.decode() in message.lower() for word in FORBIDDEN) and "\r" not in message, message
    assert server.connections == 0 and server.heads == [], server.heads  # no connection, not one byte
    return info.value


@pytest.mark.parametrize("client", list(CLIENTS))
@pytest.mark.parametrize("payload", list(SETTING_ATTEMPTS.values()), ids=list(SETTING_ATTEMPTS))
def test_wire_setting_injection_sends_nothing(server, monkeypatch, client, payload):
    set_setting(monkeypatch, payload)
    error = refused_and_nothing_sent(server, lambda: CLIENTS[client](server.url, None))
    assert str(error).startswith(ENV_VAR)


@pytest.mark.parametrize("client", list(CLIENTS))
@pytest.mark.parametrize("arg", list(MAPPING_ATTEMPTS.values()), ids=list(MAPPING_ATTEMPTS))
def test_wire_argument_mapping_injection_sends_nothing(server, client, arg):
    error = refused_and_nothing_sent(server, lambda: CLIENTS[client](server.url, arg))
    assert str(error).startswith("extra_headers=")


@pytest.mark.parametrize("client", list(CLIENTS))
@pytest.mark.parametrize("arg", list(TEXT_ATTEMPTS.values()), ids=list(TEXT_ATTEMPTS))
def test_wire_argument_text_injection_sends_nothing(server, client, arg):
    error = refused_and_nothing_sent(server, lambda: CLIENTS[client](server.url, arg))
    assert str(error).startswith("extra_headers=")


@pytest.mark.parametrize("client", list(CLIENTS))
@pytest.mark.parametrize("case", list(SETTING_BY_DESIGN))
def test_wire_setting_separators_send_exactly_the_checked_lines(server, monkeypatch, client, case):
    text, expected = SETTING_BY_DESIGN[case]
    monkeypatch.setenv(ENV_VAR, text)
    CLIENTS[client](server.url, None)
    assert_exact(server, expected)


@pytest.mark.parametrize("client", list(CLIENTS))
def test_wire_valid_argument_arrives_as_exactly_one_line(server, monkeypatch, client):
    monkeypatch.setenv(ENV_VAR, "X-A=from-setting;X-B=2")
    CLIENTS[client](server.url, {"X-A": "from-argument", "X-C": "Bearer abc.def-ghi"})
    assert_exact(server, {"X-A": "from-argument", "X-B": "2", "X-C": "Bearer abc.def-ghi"})


@pytest.mark.parametrize("payload", list(SETTING_ATTEMPTS.values()), ids=list(SETTING_ATTEMPTS))
def test_wire_cli_setting_injection_exits_3_and_sends_nothing(server, monkeypatch, capsys, payload):
    from fi._cli.main import main

    set_setting(monkeypatch, payload)
    assert main(["webhooks", "ls", "--json"]) == 3
    doc = json.loads(capsys.readouterr().out)
    assert doc["error"]["code"] == "EXTRA_HEADERS_INVALID" and doc["error"]["message"].startswith(ENV_VAR)
    assert main(["doctor", "--json"]) == 3
    raw = capsys.readouterr().out
    assert json.loads(raw)["extra_headers"]["error"].startswith(ENV_VAR)
    assert not any(word.decode() in raw.lower() for word in FORBIDDEN)
    assert server.connections == 0 and server.heads == []


def test_wire_raw_server_sees_what_the_sdk_sends(server, monkeypatch):
    """Control: the raw server does record header lines (so the empty results above are real)."""
    monkeypatch.setenv(ENV_VAR, "X-A=1")
    via_typed_sync(server.url, None)
    assert_exact(server, {"X-A": "1"})
    assert b"x-api-key: ak-test" in server.heads[0].lower()

