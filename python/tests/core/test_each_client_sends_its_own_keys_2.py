"""Two guardrails gateways with their own OpenAI moderation keys send only those keys.

A loopback HTTP sink stands in for the moderation API (``OPENAI_BASE_URL`` points at it). Each
request carries a tenant marker in its body, so the sink can count, per request, which tenant's key
bytes arrived. The keys are derived at runtime; nothing here is a real credential.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Iterator, List, Tuple

import pytest

pytest.importorskip("openai")

from fi.evals.guardrails.gateway import GuardrailsGateway  # noqa: E402

TENANTS = ("tenant-a", "tenant-b")
THREADS = 8
ROUNDS = 6


def _derive_key(tenant: str) -> str:
    return f"{tenant}-{secrets.token_hex(16)}"


class _Sink:
    """Counts, per sending tenant, the bytes of each tenant's key seen in the raw request."""

    def __init__(self, keys: Dict[str, str]) -> None:
        self.keys = keys
        self.lock = threading.Lock()
        self.requests: List[Tuple[str, Dict[str, int]]] = []
        sink = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length)
                raw = str(self.headers).encode() + body
                text = json.loads(body.decode() or "{}").get("input", "")
                sender = next((t for t in TENANTS if text.startswith(t + ":")), "unknown")
                counts = {
                    t: raw.count(k.encode()) * len(k.encode()) for t, k in sink.keys.items()
                }
                with sink.lock:
                    sink.requests.append((sender, counts))
                reply = json.dumps({
                    "id": "modr-sink",
                    "model": "omni-moderation-latest",
                    "results": [{"flagged": False, "categories": {}, "category_scores": {}}],
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(reply)))
                self.end_headers()
                self.wfile.write(reply)

            def log_message(self, *args: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}/v1"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def other_tenant_bytes(self) -> Dict[str, int]:
        """Bytes of the other tenant's key that arrived in requests sent by each tenant."""
        totals = {t: 0 for t in TENANTS}
        for sender, counts in self.requests:
            assert sender in TENANTS, f"request with no tenant marker: {sender}"
            totals[sender] += sum(n for t, n in counts.items() if t != sender)
        return totals

    def own_tenant_requests(self) -> Dict[str, int]:
        totals = {t: 0 for t in TENANTS}
        for sender, counts in self.requests:
            if counts.get(sender):
                totals[sender] += 1
        return totals


@pytest.fixture
def busy_switching() -> Iterator[None]:
    """Switch threads often so concurrent builds interleave inside the gateway constructor."""
    interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    try:
        yield
    finally:
        sys.setswitchinterval(interval)


@pytest.fixture
def keys() -> Dict[str, str]:
    return {t: _derive_key(t) for t in TENANTS}


@pytest.fixture
def sink(monkeypatch: pytest.MonkeyPatch, keys: Dict[str, str]) -> Iterator[_Sink]:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    s = _Sink(keys)
    monkeypatch.setenv("OPENAI_BASE_URL", s.base_url)
    try:
        yield s
    finally:
        s.close()


def _build(tenant: str, keys: Dict[str, str]) -> GuardrailsGateway:
    return GuardrailsGateway.with_openai(api_key=keys[tenant])


def _screen(gateway: GuardrailsGateway, tenant: str) -> None:
    response = gateway.screen(f"{tenant}: sample text")
    assert response.passed, response


def test_one_after_another_with_a_process_key_for_the_second(
    monkeypatch: pytest.MonkeyPatch, sink: _Sink, keys: Dict[str, str]
) -> None:
    # Tenant B relies on the process key; tenant A passes its own key explicitly.
    monkeypatch.setenv("OPENAI_API_KEY", keys["tenant-b"])
    env_before = dict(os.environ)
    gateway_a = _build("tenant-a", keys)
    gateway_b = GuardrailsGateway.with_openai()
    for _ in range(3):
        _screen(gateway_a, "tenant-a")
        _screen(gateway_b, "tenant-b")
    assert sink.other_tenant_bytes() == {"tenant-a": 0, "tenant-b": 0}
    assert sink.own_tenant_requests() == {"tenant-a": 3, "tenant-b": 3}
    assert dict(os.environ) == env_before


def test_one_after_another_with_explicit_keys(sink: _Sink, keys: Dict[str, str]) -> None:
    env_before = dict(os.environ)
    gateway_a = _build("tenant-a", keys)
    gateway_b = _build("tenant-b", keys)
    for _ in range(3):
        _screen(gateway_b, "tenant-b")
        _screen(gateway_a, "tenant-a")
    assert sink.other_tenant_bytes() == {"tenant-a": 0, "tenant-b": 0}
    assert sink.own_tenant_requests() == {"tenant-a": 3, "tenant-b": 3}
    assert dict(os.environ) == env_before


def test_concurrently_from_eight_threads(
    sink: _Sink, keys: Dict[str, str], busy_switching: None
) -> None:
    env_before = dict(os.environ)
    calls = 0
    for _ in range(ROUNDS):
        barrier = threading.Barrier(THREADS)

        def work(i: int) -> None:
            tenant = TENANTS[i % 2]
            barrier.wait()
            gateway = _build(tenant, keys)
            _screen(gateway, tenant)

        with ThreadPoolExecutor(max_workers=THREADS) as pool:
            list(pool.map(work, range(THREADS)))
        calls += THREADS // 2
    assert sink.other_tenant_bytes() == {"tenant-a": 0, "tenant-b": 0}
    assert sink.own_tenant_requests() == {"tenant-a": calls, "tenant-b": calls}
    assert dict(os.environ) == env_before


def test_concurrently_from_async_tasks(
    sink: _Sink, keys: Dict[str, str], busy_switching: None
) -> None:
    env_before = dict(os.environ)

    async def one(i: int) -> None:
        tenant = TENANTS[i % 2]
        gateway = await asyncio.to_thread(_build, tenant, keys)
        response = await gateway.screen_async(f"{tenant}: sample text")
        assert response.passed, response

    async def main() -> None:
        await asyncio.gather(*(one(i) for i in range(THREADS * ROUNDS)))

    asyncio.run(main())
    calls = THREADS * ROUNDS // 2
    assert sink.other_tenant_bytes() == {"tenant-a": 0, "tenant-b": 0}
    assert sink.own_tenant_requests() == {"tenant-a": calls, "tenant-b": calls}
    assert dict(os.environ) == env_before
