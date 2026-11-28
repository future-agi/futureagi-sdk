"""``fi.evals.otel.setup_tracing`` configures one process-wide tracing setup: each configuration's spans reach its own
collector with its own headers, and no request carries another configuration's keys.

Each configuration ("tenant") gets its own loopback sink and its own header values, derived at run time from the shared
test markers. Every request a sink receives is checked for the bytes of each tenant's values: a sink gets 0 bytes of
another tenant's values, one configuration after another and from 8 threads at once. A second configuration while one
is active is refused, so the module and the OTel global provider name the same configuration.
"""

from __future__ import annotations

import secrets
import threading
from typing import Any, Iterator

import pytest

pytest.importorskip("opentelemetry.sdk.trace")
pytest.importorskip("opentelemetry.exporter.otlp.proto.http.trace_exporter")

from fi.evals.otel import tracer as tracer_module  # noqa: E402
from fi.evals.otel.config import ExporterConfig, ExporterType, TraceConfig  # noqa: E402
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, Sink  # noqa: E402

THREADS = 8


class Tenant:
    """One configuration: its sink and the header values its exporter sends, unique to this run."""

    def __init__(self, label: str) -> None:
        run = secrets.token_hex(6)
        self.label = label
        self.key = f"{MARKER_KEY}-{label}-{run}"
        self.secret = f"{MARKER_SECRET}-{label}-{run}"
        self.sink = Sink()

    @property
    def markers(self) -> tuple[bytes, bytes]:
        return self.key.encode(), self.secret.encode()

    def config(self) -> TraceConfig:
        return TraceConfig(
            service_name=f"svc-{self.label}",
            exporters=[ExporterConfig(
                type=ExporterType.OTLP_HTTP,
                endpoint=f"http://127.0.0.1:{self.sink.port}/v1/traces",
                headers={"x-api-key": self.key, "x-secret-key": self.secret},
                timeout_ms=5000,
            )],
        )


def _count(request: bytes, tenant: Tenant) -> int:
    return sum(request.count(marker) for marker in tenant.markers)


def _counts(tenants: list[Tenant]) -> dict[str, dict[str, Any]]:
    """Per sink: how many requests it got, and per tenant the bytes of that tenant's values in each request."""
    table: dict[str, dict[str, Any]] = {}
    for sink_owner in tenants:
        table[sink_owner.label] = {
            "requests": len(sink_owner.sink.chunks),
            **{t.label: [_count(chunk, t) for chunk in sink_owner.sink.chunks] for t in tenants},
        }
    return table


def _assert_only_own_keys(tenants: list[Tenant]) -> None:
    table = _counts(tenants)
    for owner in tenants:
        for other in tenants:
            if other is owner:
                continue
            assert sum(table[owner.label][other.label]) == 0, (
                f"sink {owner.label} got {other.label}'s values: {table}"
            )


def _spans_named(tenant: Tenant, name: str) -> int:
    return sum(chunk.count(name.encode()) for chunk in tenant.sink.chunks)


@pytest.fixture(autouse=True)
def _fresh_global_provider() -> Iterator[None]:
    """Each test starts with no OTel global provider and no configuration, and leaves none behind."""
    from opentelemetry import trace
    from opentelemetry.util._once import Once

    def reset() -> None:
        tracer_module.shutdown_tracing()
        trace._TRACER_PROVIDER_SET_ONCE = Once()
        trace._TRACER_PROVIDER = None

    reset()
    yield
    reset()


@pytest.fixture
def tenants() -> Iterator[list[Tenant]]:
    made = [Tenant(chr(ord("a") + i)) for i in range(THREADS)]
    yield made
    for tenant in made:
        tenant.sink.close()


def _emit(name: str, count: int, cached: Any = None) -> None:
    tracer = tracer_module.get_tracer("fi.tests.each-client")
    for _ in range(count):
        tracer.start_span(name).end()
        with tracer.start_as_current_span(name):
            pass
        if cached is not None:
            cached.start_span(name).end()


def _emit_from_threads(name: str, cached: Any = None) -> None:
    barrier = threading.Barrier(THREADS)
    errors: list[BaseException] = []

    def work() -> None:
        try:
            barrier.wait(timeout=10)
            _emit(name, 3, cached)
        except BaseException as error:  # noqa: BLE001 - reported below
            errors.append(error)

    threads = [threading.Thread(target=work) for _ in range(THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert not errors, errors


def test_one_configuration_after_another_sends_each_ones_keys_to_its_own_sink(tenants):
    a, b = tenants[0], tenants[1]
    tracer_module.setup_tracing(a.config())
    cached = tracer_module.get_tracer("fi.tests.cached")  # held across the switch, as instrumentors hold theirs
    _emit("span-of-a", 3, cached)
    tracer_module.shutdown_tracing()

    tracer_module.setup_tracing(b.config())
    _emit("span-of-b", 3, cached)
    tracer_module.shutdown_tracing()

    table = _counts([a, b])
    _assert_only_own_keys([a, b])
    assert table["a"]["requests"] > 0 and all(table["a"]["a"]), table
    assert table["b"]["requests"] > 0 and all(table["b"]["b"]), table
    assert _spans_named(a, "span-of-b") == 0 and _spans_named(b, "span-of-a") == 0
    assert _spans_named(b, "span-of-b") == 9, table


def test_spans_from_eight_threads_reach_only_the_active_configuration(tenants):
    a, b = tenants[0], tenants[1]
    tracer_module.setup_tracing(a.config())
    cached = tracer_module.get_tracer("fi.tests.cached")
    _emit_from_threads("span-of-a", cached)
    tracer_module.shutdown_tracing()

    tracer_module.setup_tracing(b.config())
    _emit_from_threads("span-of-b", cached)
    tracer_module.shutdown_tracing()

    table = _counts([a, b])
    _assert_only_own_keys([a, b])
    assert table["a"]["requests"] > 0 and all(table["a"]["a"]), table
    assert table["b"]["requests"] > 0 and all(table["b"]["b"]), table
    assert _spans_named(a, "span-of-b") == 0 and _spans_named(b, "span-of-a") == 0
    assert _spans_named(b, "span-of-b") == THREADS * 9, table


def _flush() -> None:
    """Flush whatever provider the OTel global is, so a span that went to another configuration's exporter shows up."""
    from opentelemetry import trace

    flush = getattr(trace.get_tracer_provider(), "force_flush", None)
    if flush is not None:
        flush()


def _carrying(tenants: list[Tenant], name: str) -> dict[str, list[dict[str, int]]]:
    """Per sink, for each request that carries spans named ``name``: the bytes of each tenant's values in it."""
    return {
        owner.label: [{t.label: _count(chunk, t) for t in tenants} for chunk in owner.sink.chunks if name.encode() in chunk]
        for owner in tenants
    }


def test_a_second_configuration_while_one_is_active_is_refused(tenants):
    a, b = tenants[0], tenants[1]
    tracer_module.setup_tracing(a.config())
    refused: BaseException | None = None
    try:
        tracer_module.setup_tracing(b.config())
        active, other = b, a
    except Exception as error:  # noqa: BLE001 - checked below
        refused, active, other = error, a, b
    _emit("span-after-second", 3)
    _flush()
    tracer_module.shutdown_tracing()

    carrying = _carrying([a, b], "span-after-second")
    _assert_only_own_keys([a, b])
    # The spans after the second call go out with the keys of the configuration the module reports as active.
    assert carrying[active.label] and all(r[active.label] and not r[other.label] for r in carrying[active.label]), carrying
    assert carrying[other.label] == [], f"active {active.label}: {carrying}"
    assert type(refused).__name__ == "TracingAlreadyConfigured", f"second configuration accepted; {carrying}"


def test_eight_configurations_at_once_leave_one_active_and_its_sink_alone_gets_spans(tenants):
    barrier = threading.Barrier(THREADS)
    accepted: list[tuple[Tenant, Any]] = []
    refused: list[tuple[Tenant, BaseException]] = []
    lock = threading.Lock()

    def configure(tenant: Tenant) -> None:
        barrier.wait(timeout=10)
        try:
            provider = tracer_module.setup_tracing(tenant.config())
        except Exception as error:  # noqa: BLE001 - checked below
            with lock:
                refused.append((tenant, error))
        else:
            with lock:
                accepted.append((tenant, provider))

    threads = [threading.Thread(target=configure, args=(tenant,)) for tenant in tenants]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    active = [tenant for tenant, provider in accepted if provider is tracer_module._tracer_provider]
    _emit_from_threads("span-at-once")
    _flush()
    tracer_module.shutdown_tracing()

    carrying = _carrying(tenants, "span-at-once")
    _assert_only_own_keys(tenants)
    assert len(active) == 1, carrying
    winner = active[0]
    # Every request with these spans carries the active configuration's values and 0 bytes of any other's.
    sent = [(sink, r) for sink, requests in carrying.items() for r in requests]
    wrong = [(sink, r) for sink, r in sent if sink != winner.label or any(n for t, n in r.items() if t != winner.label)]
    assert sent and not wrong, f"active {winner.label}; requests with others' sink or values: {wrong}"
    assert _spans_named(winner, "span-at-once") == THREADS * 6, carrying
    assert len(accepted) == 1, f"accepted {[t.label for t, _ in accepted]}; active {winner.label}"
    assert {type(error).__name__ for _, error in refused} == {"TracingAlreadyConfigured"}
