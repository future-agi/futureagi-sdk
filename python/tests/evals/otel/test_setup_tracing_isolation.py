"""``setup_tracing`` keeps one active configuration: the OpenTelemetry global provider is the module's switching
provider, which sends spans to the active configuration's provider and to none between configurations.

The providers here have no exporters of their own; each test attaches an in-memory exporter to the provider
``setup_tracing`` returns and checks which one gets each span. ``tests/core/test_each_client_sends_its_own_keys_3.py``
checks the same over loopback collectors with per-configuration headers.
"""

from __future__ import annotations

import threading
from typing import Any, Iterator

import pytest

pytest.importorskip("opentelemetry.sdk.trace")

from opentelemetry import trace  # noqa: E402
from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402
from opentelemetry.util._once import Once  # noqa: E402

from fi.errors import ConfigurationError  # noqa: E402
from fi.evals.otel import tracer as tracer_module  # noqa: E402
from fi.evals.otel.config import TraceConfig  # noqa: E402
from fi.evals.otel.tracer import TracingAlreadyConfigured  # noqa: E402

THREADS = 8


def _reset_global() -> None:
    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None


@pytest.fixture(autouse=True)
def _fresh() -> Iterator[None]:
    tracer_module.shutdown_tracing()
    _reset_global()
    yield
    tracer_module.shutdown_tracing()
    _reset_global()


def _configure(name: str) -> tuple[Any, InMemorySpanExporter]:
    provider = tracer_module.setup_tracing(TraceConfig(service_name=name, exporters=[]))
    assert isinstance(provider, TracerProvider)
    memory = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(memory))
    return provider, memory


def _names(memory: InMemorySpanExporter) -> list[str]:
    return [span.name for span in memory.get_finished_spans()]


def test_a_second_configuration_without_shutdown_is_refused():
    provider_a, memory_a = _configure("a")
    with pytest.raises(TracingAlreadyConfigured, match="shutdown_tracing") as info:
        tracer_module.setup_tracing(TraceConfig(service_name="b", exporters=[]))
    assert isinstance(info.value, ConfigurationError)
    assert tracer_module._tracer_provider is provider_a and tracer_module.is_tracing_enabled()
    tracer_module.get_tracer().start_span("after-refusal").end()
    assert _names(memory_a) == ["after-refusal"]


def test_a_foreign_global_provider_is_refused_and_keeps_its_place():
    foreign = TracerProvider()
    foreign_memory = InMemorySpanExporter()
    foreign.add_span_processor(SimpleSpanProcessor(foreign_memory))
    trace.set_tracer_provider(foreign)

    with pytest.raises(TracingAlreadyConfigured, match="global tracer provider is already set"):
        tracer_module.setup_tracing(TraceConfig(service_name="a", exporters=[]))
    assert trace.get_tracer_provider() is foreign
    assert not tracer_module.is_tracing_enabled() and tracer_module._tracer_provider is None


def test_the_global_provider_is_installed_once_and_follows_the_active_configuration():
    _, memory_a = _configure("a")
    switch = trace.get_tracer_provider()
    assert isinstance(switch, trace.TracerProvider) and not isinstance(switch, TracerProvider)
    cached = trace.get_tracer("cached")  # obtained during a, as instrumentors keep theirs
    cached.start_span("in-a").end()
    tracer_module.shutdown_tracing()

    between = cached.start_span("between")
    assert not between.is_recording()
    between.end()
    with tracer_module.get_tracer().start_as_current_span("between-current") as span:
        assert not span.is_recording()

    _, memory_b = _configure("b")
    assert trace.get_tracer_provider() is switch
    cached.start_span("in-b").end()
    with tracer_module.trace_llm_call("call-in-b", model="m", system="s"):
        pass

    assert _names(memory_a) == ["in-a"]
    assert _names(memory_b) == ["in-b", "call-in-b"]


def test_spans_from_eight_threads_after_a_switch_reach_only_the_active_configuration():
    _, memory_a = _configure("a")
    cached = tracer_module.get_tracer("cached")
    tracer_module.shutdown_tracing()
    _, memory_b = _configure("b")

    barrier = threading.Barrier(THREADS)

    def work(index: int) -> None:
        barrier.wait(timeout=10)
        for round_ in range(5):
            cached.start_span(f"b-{index}-{round_}").end()
            with tracer_module.get_tracer().start_as_current_span(f"b-current-{index}-{round_}"):
                pass

    threads = [threading.Thread(target=work, args=(i,)) for i in range(THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert _names(memory_a) == []
    assert len(_names(memory_b)) == THREADS * 10


def test_eight_configurations_at_once_leave_exactly_one_active():
    barrier = threading.Barrier(THREADS)
    results: list[Any] = []
    lock = threading.Lock()

    def configure(index: int) -> None:
        barrier.wait(timeout=10)
        try:
            outcome: Any = tracer_module.setup_tracing(TraceConfig(service_name=f"s{index}", exporters=[]))
        except TracingAlreadyConfigured as error:
            outcome = error
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=configure, args=(i,)) for i in range(THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    providers = [r for r in results if isinstance(r, TracerProvider)]
    assert len(providers) == 1 and len(results) == THREADS
    assert tracer_module._tracer_provider is providers[0]


def test_disabled_tracing_installs_nothing():
    assert tracer_module.setup_tracing(TraceConfig(enabled=False)) is None
    assert isinstance(trace.get_tracer_provider(), trace.ProxyTracerProvider)
    assert not tracer_module.is_tracing_enabled()
