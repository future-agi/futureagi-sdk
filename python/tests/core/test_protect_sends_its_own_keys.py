"""``Protect`` sends the keys it is given to the base URL it is given, with other keys in the environment.

Two ``Protect`` instances get keys built at runtime (``secrets.token_hex``) and their own loopback
listeners, while FI_API_KEY, FI_SECRET_KEY and FI_BASE_URL name a third tenant with a third listener.
They screen text one after another and from 8 threads at once. Each listener must receive requests
carrying only its own instance's keys, and 0 bytes of any other tenant's keys.
"""

from __future__ import annotations

import json
import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Iterator, List

import pytest

from fi.evals.protect import Protect

THREADS = 8
ROUNDS = 3


class Tenant:
    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.api_key = f"tenant-{tag}-api-{secrets.token_hex(12)}"
        self.secret_key = f"tenant-{tag}-secret-{secrets.token_hex(12)}"

    @property
    def markers(self) -> tuple:
        return (self.api_key.encode(), self.secret_key.encode())


class Sink:
    """A loopback listener that answers every POST and keeps the raw bytes of each request."""

    def __init__(self) -> None:
        sink = self
        self.requests: List[bytes] = []
        self.lock = threading.Lock()

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                with sink.lock:
                    sink.requests.append(self.requestline.encode() + b"\r\n" + bytes(self.headers) + body)
                data = json.dumps({"result": [{"evaluations": [{"output": 1.0, "runtime": 1}]}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def marker_bytes(self, tenant: Tenant) -> int:
        with self.lock:
            return sum(len(m) * raw.count(m) for raw in self.requests for m in tenant.markers)

    def requests_with_both_keys_of(self, tenant: Tenant) -> int:
        with self.lock:
            return sum(1 for raw in self.requests if all(m in raw for m in tenant.markers))


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch) -> Iterator[Dict[str, object]]:
    tenants = {tag: Tenant(tag) for tag in ("a", "b", "env")}
    sinks = {tag: Sink() for tag in tenants}
    monkeypatch.setenv("FI_API_KEY", tenants["env"].api_key)
    monkeypatch.setenv("FI_SECRET_KEY", tenants["env"].secret_key)
    monkeypatch.setenv("FI_BASE_URL", sinks["env"].base_url)
    try:
        yield {"tenants": tenants, "sinks": sinks}
    finally:
        for sink in sinks.values():
            sink.close()


def _build(world: Dict[str, object], tag: str) -> Protect:
    tenant = world["tenants"][tag]
    return Protect(fi_api_key=tenant.api_key, fi_secret_key=tenant.secret_key,
                   fi_base_url=world["sinks"][tag].base_url)


def _screen(client: Protect) -> None:
    try:
        client.protect("some text to screen", use_flash=True, timeout=5000)
    except Exception:  # the keys at each listener are what this file checks, not the parsed answer
        pass


def _assert_each_sink_holds_only_its_own_keys(world: Dict[str, object], expected: int) -> None:
    tenants, sinks = world["tenants"], world["sinks"]
    counts = {tag: (len(sinks[tag].requests), {other: sinks[tag].marker_bytes(tenants[other]) for other in tenants})
              for tag in sinks}
    for tag in ("a", "b"):
        assert len(sinks[tag].requests) == expected, counts
        assert sinks[tag].requests_with_both_keys_of(tenants[tag]) == expected, counts
        for other in tenants:
            if other != tag:
                assert sinks[tag].marker_bytes(tenants[other]) == 0, counts
    assert len(sinks["env"].requests) == 0, counts
    assert sinks["env"].marker_bytes(tenants["a"]) == 0, counts
    assert sinks["env"].marker_bytes(tenants["b"]) == 0, counts


def test_two_instances_one_after_another_send_their_own_keys_to_their_own_sinks(world) -> None:
    first, second = _build(world, "a"), _build(world, "b")
    for _ in range(ROUNDS):
        _screen(first)
        _screen(second)
    _assert_each_sink_holds_only_its_own_keys(world, ROUNDS)


def test_two_instances_from_eight_threads_send_their_own_keys_to_their_own_sinks(world) -> None:
    clients = {"a": _build(world, "a"), "b": _build(world, "b")}
    barrier = threading.Barrier(THREADS)

    def work(i: int) -> None:
        barrier.wait(timeout=10)
        _screen(clients["a" if i % 2 == 0 else "b"])

    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        list(pool.map(work, range(THREADS)))
    _assert_each_sink_holds_only_its_own_keys(world, THREADS // 2)
