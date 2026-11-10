"""The tracing span processors work with every OpenTelemetry SDK the package allows.

Newer 1.x SDKs call an extra ``_on_ending`` hook on each registered span processor while a span
ends. These tests end real spans through a real ``TracerProvider`` and also call the hook directly,
so they check the processors on both older and newer SDKs.
"""

from __future__ import annotations

import importlib
import importlib.util

import pytest


def _dependency(name):
    try:
        spec = importlib.util.find_spec(name)
    except ModuleNotFoundError:
        spec = None
    if spec is None:
        pytest.skip("futureagi[evals] is not installed: " + name)
    # An installed but broken dependency must fail, rather than become a skip.
    return importlib.import_module(name)


_dependency("opentelemetry.sdk.trace")

from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402

from fi.evals.otel import CostConfig, EvaluationConfig, TraceConfig  # noqa: E402
from fi.evals.otel.processors import (  # noqa: E402
    AttributeEnrichmentProcessor,
    BaseSpanProcessor,
    CompositeSpanProcessor,
    ConditionalProcessor,
    CostSpanProcessor,
    FilteringSpanProcessor,
    LLMSpanProcessor,
)
from fi.evals.otel.tracer import _create_custom_processors  # noqa: E402


class _Recording(BaseSpanProcessor):
    def __init__(self, calls, name, enabled=True):
        super().__init__(enabled=enabled)
        self._calls = calls
        self._name = name

    def _on_ending(self, span):
        self._calls.append((self._name, "ending", span.name))

    def on_end(self, span):
        self._calls.append((self._name, "end", span.name))


class _NoEndingHook:
    """A duck-typed child processor that predates the ending hook."""

    enabled = True

    def __init__(self, calls):
        self._calls = calls

    def on_start(self, span, parent_context=None):
        self._calls.append(("plain", "start", span.name))

    def on_end(self, span):
        self._calls.append(("plain", "end", span.name))

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis=30000):
        return True


class _FailingEndingHook(_Recording):
    def _on_ending(self, span):
        raise RuntimeError("ending hook failed")


def _provider_with(processor):
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    provider.add_span_processor(processor)
    return provider, exporter


def test_default_tracing_processors_let_a_span_end_and_export():
    composite = _create_custom_processors(TraceConfig(
        evaluation=EvaluationConfig(enabled=False), cost=CostConfig(enabled=False)))
    assert isinstance(composite, CompositeSpanProcessor)
    provider, exporter = _provider_with(composite)
    try:
        with provider.get_tracer("test").start_as_current_span("chat") as span:
            span.set_attribute("gen_ai.system", "openai")
        assert [s.name for s in exporter.get_finished_spans()] == ["chat"]
    finally:
        provider.shutdown()


def test_composite_with_every_built_in_child_lets_a_span_end_and_export():
    composite = CompositeSpanProcessor([
        LLMSpanProcessor(),
        CostSpanProcessor(),
        AttributeEnrichmentProcessor({"service.team": "sdk"}),
        FilteringSpanProcessor(filter_fn=lambda span: True, delegate=LLMSpanProcessor()),
        ConditionalProcessor(conditions=[(lambda span: False, LLMSpanProcessor())],
                             default=CostSpanProcessor()),
    ])
    provider, exporter = _provider_with(composite)
    try:
        with provider.get_tracer("test").start_as_current_span("chat"):
            pass
        finished = exporter.get_finished_spans()
        assert [s.name for s in finished] == ["chat"]
        assert finished[0].attributes["service.team"] == "sdk"
    finally:
        provider.shutdown()


@pytest.mark.parametrize("make", [
    LLMSpanProcessor,
    CostSpanProcessor,
    lambda: AttributeEnrichmentProcessor({"service.team": "sdk"}),
    lambda: FilteringSpanProcessor(filter_fn=lambda span: True),
    lambda: ConditionalProcessor(conditions=[]),
], ids=["llm", "cost", "attributes", "filtering", "conditional"])
def test_each_built_in_processor_registered_directly_lets_a_span_end(make):
    provider, exporter = _provider_with(make())
    try:
        with provider.get_tracer("test").start_as_current_span("chat"):
            pass
        assert [s.name for s in exporter.get_finished_spans()] == ["chat"]
    finally:
        provider.shutdown()


def test_composite_passes_the_ending_hook_to_children_that_have_it():
    calls = []
    composite = CompositeSpanProcessor([
        _Recording(calls, "first"), _NoEndingHook(calls), _Recording(calls, "second")])
    provider, _ = _provider_with(composite)
    try:
        span = provider.get_tracer("test").start_span("chat")
        assert calls == [("plain", "start", "chat")]
        composite._on_ending(span)
        assert calls[1:] == [("first", "ending", "chat"), ("second", "ending", "chat")]
        span.end()
    finally:
        provider.shutdown()


def test_composite_ending_hook_keeps_going_after_a_child_raises():
    calls = []
    composite = CompositeSpanProcessor([
        _FailingEndingHook(calls, "failing"), _Recording(calls, "after")])
    provider, _ = _provider_with(composite)
    try:
        span = provider.get_tracer("test").start_span("chat")
        composite._on_ending(span)
        assert calls == [("after", "ending", "chat")]
        span.end()
    finally:
        provider.shutdown()


def test_disabled_composite_does_not_call_the_ending_hook():
    calls = []
    composite = CompositeSpanProcessor([_Recording(calls, "child")], enabled=False)
    provider, _ = _provider_with(composite)
    try:
        span = provider.get_tracer("test").start_span("chat")
        composite._on_ending(span)
        assert calls == []
        span.end()
    finally:
        provider.shutdown()


def test_base_processor_ending_hook_is_a_no_op():
    provider, _ = _provider_with(LLMSpanProcessor())
    try:
        span = provider.get_tracer("test").start_span("chat")
        assert LLMSpanProcessor()._on_ending(span) is None
        span.end()
    finally:
        provider.shutdown()
