from __future__ import annotations

import asyncio
import secrets
import select
from contextlib import contextmanager
from socketserver import StreamRequestHandler, TCPServer
from threading import Thread

import pytest
from fi.errors import ConfigurationError
from fi.gateway import check_valid_key, health_check
from fi.platform import AsyncClient, Client


class _Recorder(TCPServer):
    def __init__(self):
        self.connections = 0
        self.requests: list[bytes] = []
        super().__init__(("127.0.0.1", 0), _ReadRequest)

    def get_request(self):
        connection, address = super().get_request()
        self.connections += 1
        connection.settimeout(2)
        return connection, address

    def assert_wire(self, expected_requests, markers, expected_copies):
        encoded = [marker.encode("ascii") for marker in markers]
        observed = (
            self.connections,
            len(self.requests),
            *(len(marker) * sum(request.count(marker) for request in self.requests) for marker in encoded),
        )
        expected = (
            expected_requests,
            expected_requests,
            *(len(marker) * count for marker, count in zip(encoded, expected_copies)),
        )
        assert observed == expected, "Counts are connections, requests, API marker bytes and secret marker bytes."


class _ReadRequest(StreamRequestHandler):
    def handle(self):
        lines = []
        for line in self.rfile:
            if line == b"\r\n":
                self.server.requests.append(b"".join(lines))
                self.wfile.write(
                    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                    b"Content-Length: 11\r\nConnection: close\r\n\r\n{\"ok\":true}"
                )
                break
            lines.append(line)


@contextmanager
def _record_requests():
    with _Recorder() as listener:
        worker = Thread(target=listener.serve_forever, kwargs={"poll_interval": 0.01})
        worker.start()
        try:
            yield listener
        finally:
            listener.shutdown()
            worker.join()
            # Count queued connections even if the worker exited without accepting them.
            while select.select([listener], [], [], 0)[0]:
                listener.handle_request()


def new_markers(tmp_path, monkeypatch):
    """Two generated key markers, with the saved login pointed at an empty scratch file."""
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "login.json"))
    return tuple("MARKER-" + secrets.token_hex(8) for _ in range(2))


def _send(sender, base_url, markers):
    api_key, secret_key = markers
    if sender == "health_check":
        return health_check(api_key=api_key, base_url=base_url, timeout=2)
    if sender == "check_valid_key":
        return check_valid_key(api_key, base_url)
    kwargs = dict(api_key=api_key, secret_key=secret_key, base_url=base_url, max_retries=0, timeout=2)
    if sender == "async_client":
        async def request():
            async with AsyncClient(**kwargs) as client:
                return await client.request("GET", "/probe")

        return asyncio.run(request())
    with Client(**kwargs) as client:
        return client.request("GET", "/probe")


SENDERS = ("client", "async_client", "health_check", "check_valid_key")


@pytest.mark.parametrize("sender", SENDERS)
@pytest.mark.parametrize(
    ("url", "opt_in"),
    [
        pytest.param("http://127.0.0.1:{port}/alpha\\beta", False, id="path-backslash"),
        pytest.param("http://127。0。0。1:{port}", True, id="ideographic-dot"),
        pytest.param("http://127．0．0．1:{port}", True, id="fullwidth-dot"),
        pytest.param("http://127｡0｡0｡1:{port}", True, id="halfwidth-dot"),
    ],
)
def test_ambiguous_plain_http_base_is_refused(sender, url, opt_in, tmp_path, monkeypatch):
    markers = new_markers(tmp_path, monkeypatch)
    if opt_in:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    else:
        monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    error = None
    outcome = None
    with _record_requests() as listener:
        try:
            outcome = _send(sender, url.format(port=listener.server_address[1]), markers)
        except ConfigurationError as exc:
            error = exc
    listener.assert_wire(0, markers, (0, 0))
    if sender == "health_check":
        assert outcome["status"] == "error" and "latency_ms" not in outcome
    elif sender == "check_valid_key":
        assert outcome is False
    else:
        assert isinstance(error, ConfigurationError)
        assert error.code == error.get_error_code() == "insecure_http_origin"


@pytest.mark.parametrize("sender", SENDERS)
@pytest.mark.parametrize("path", ["", "/alpha/beta"], ids=["origin", "base-path"])
def test_plain_http_loopback_base_sends_once(sender, path, tmp_path, monkeypatch):
    markers = new_markers(tmp_path, monkeypatch)
    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    with _record_requests() as listener:
        outcome = _send(sender, f"http://127.0.0.1:{listener.server_address[1]}{path}", markers)
    if sender == "health_check":
        assert outcome["status"] == "ok"
    elif sender == "check_valid_key":
        assert outcome is True
    else:
        assert outcome == {"ok": True}
    listener.assert_wire(1, markers, (1, int(sender in {"client", "async_client"})))
