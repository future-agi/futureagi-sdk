"""Clients built at once on threads, each with its own API key and the secret key from ``FI_SECRET_KEY``.

Eight threads, released together by a barrier, each build one client per round with their own ``fi_api_key``;
the secret key of every client comes from the environment. Each client then sends one request to a listener on
the loopback interface, under a path that names its tenant. Each request carries the API key of its own tenant
and the bytes of no other tenant's key.
"""

from __future__ import annotations

import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from fi.api.auth import APIKeyAuth
from fi.api.types import HttpMethod, RequestConfig
from tests.test_plain_http_key_guards import _marker_forms, net  # noqa: F401

THREADS = 8
ROUNDS = 150


class Desk:
    """A listener on 127.0.0.1 that records the path and the raw header bytes of each request."""

    def __init__(self) -> None:
        self.received: list[tuple[str, bytes]] = []
        lock = threading.Lock()
        desk = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def do_GET(self):
                with lock:
                    desk.received.append((self.path, bytes(self.headers)))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", "2")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(b"{}")
                self.close_connection = True

        class Server(ThreadingHTTPServer):
            daemon_threads = True

        self._server = Server(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


def _count(raw: bytes, value: str) -> int:
    return sum(raw.count(form) for form in _marker_forms(value))


@pytest.mark.parametrize("cls_name", ["api-key-auth", "dataset"])
def test_clients_built_at_once_with_the_secret_from_the_environment_send_their_own_api_key(cls_name, monkeypatch, net):  # noqa: F811
    from fi.datasets.dataset import Dataset

    cls = {"api-key-auth": APIKeyAuth, "dataset": Dataset}[cls_name]
    shared_secret = "fisec-env-" + secrets.token_hex(10)
    monkeypatch.delenv("FI_API_KEY", raising=False)
    monkeypatch.setenv("FI_SECRET_KEY", shared_secret)
    desk = Desk()
    keys = ["fikey-%s-%s" % ("abcdefgh"[i], secrets.token_hex(10)) for i in range(THREADS)]
    built: list[tuple[int, object]] = []
    errors: list[BaseException] = []
    interval = sys.getswitchinterval()
    try:
        sys.setswitchinterval(1e-6)
        for _ in range(ROUNDS):
            barrier = threading.Barrier(THREADS)
            made: list = [None] * THREADS

            def build(index: int) -> None:
                try:
                    barrier.wait()
                    made[index] = cls(fi_api_key=keys[index], fi_base_url=desk.base)
                except BaseException as exc:  # reported below
                    errors.append(exc)

            threads = [threading.Thread(target=build, args=(index,)) for index in range(THREADS)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            built.extend((index, client) for index, client in enumerate(made) if client is not None)
    finally:
        sys.setswitchinterval(interval)
    try:
        assert errors == [], errors
        for number, (index, client) in enumerate(built):
            client.request(
                RequestConfig(method=HttpMethod.GET, url=f"{desk.base}/tenant-{index}/{number}", retry_attempts=1, retry_delay=0, timeout=5)
            )
            client.close()
        assert len(desk.received) == len(built) == THREADS * ROUNDS
        crossed = []
        own_missing = 0
        for path, raw in desk.received:
            index = int(path.split("/")[1].split("-")[1])
            other = sum(_count(raw, key) for position, key in enumerate(keys) if position != index)
            if other:
                crossed.append((path, other))
            if _count(raw, keys[index]) == 0:
                own_missing += 1
        table = ", ".join(
            "tenant %s: own %d, others %d"
            % (
                "abcdefgh"[index],
                sum(_count(raw, keys[index]) for path, raw in desk.received if path.startswith(f"/tenant-{index}/")),
                sum(
                    _count(raw, key)
                    for path, raw in desk.received
                    if path.startswith(f"/tenant-{index}/")
                    for position, key in enumerate(keys)
                    if position != index
                ),
            )
            for index in range(THREADS)
        )
        assert (len(crossed), own_missing) == (0, 0), f"{len(crossed)} requests with another tenant's key; marker bytes per tenant: {table}"
        assert (net.target.connections, net.proxy.connections) == (0, 0)
    finally:
        desk.close()
