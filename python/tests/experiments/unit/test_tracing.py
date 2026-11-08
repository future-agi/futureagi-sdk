"""Tracing: routed delegates per run, baggage on child spans, refusal of a foreign global provider."""

import asyncio
import sys

import pytest
from opentelemetry import baggage, context, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from fi import experiments
from fi.experiments._tracing.baggage import BaggageAttributesProcessor
from fi.experiments._tracing.routing import RoutingTracerProvider, bind_delegate, install_router, unbind_delegate
from fi.experiments.errors import TracingConflictError, TracingUnsupportedError


def _delegate():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(BaggageAttributesProcessor())
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


def test_two_interleaved_runs_stay_separate():
    router = install_router()
    tracer = trace.get_tracer("instrumented.lib")  # bound once, like an instrumentor
    (p1, e1), (p2, e2) = _delegate(), _delegate()

    async def trial(provider, label):
        token = bind_delegate(provider)
        try:
            for i in range(3):
                with tracer.start_as_current_span(f"{label}-{i}"):
                    await asyncio.sleep(0.001)
        finally:
            unbind_delegate(token)

    async def main():
        await asyncio.gather(trial(p1, "a"), trial(p2, "b"))

    asyncio.run(main())
    assert sorted(s.name for s in e1.get_finished_spans()) == ["a-0", "a-1", "a-2"]
    assert sorted(s.name for s in e2.get_finished_spans()) == ["b-0", "b-1", "b-2"]
    with tracer.start_as_current_span("outside"):  # outside any trial: nowhere
        pass
    assert len(e1.get_finished_spans()) == 3 and isinstance(router, RoutingTracerProvider)


def test_baggage_processor_copies_only_fi_keys():
    provider, exporter = _delegate()
    ctx = baggage.set_baggage("fi.experiment.run_id", "R1")
    ctx = baggage.set_baggage("fi.dataset.id", "D1", ctx)
    ctx = baggage.set_baggage("user.secret", "nope", ctx)
    token = context.attach(ctx)
    try:
        with provider.get_tracer("t").start_as_current_span("child"):
            pass
    finally:
        context.detach(token)
    attrs = exporter.get_finished_spans()[0].attributes
    assert attrs["fi.experiment.run_id"] == "R1" and attrs["fi.dataset.id"] == "D1"
    assert "user.secret" not in attrs


def test_refuses_a_foreign_or_observe_global_provider():
    observe = TracerProvider(resource=Resource.create({"project_type": "observe"}))
    trace.set_tracer_provider(observe)
    with pytest.raises(TracingConflictError) as info:
        experiments.run([{"q": 1}], lambda r: 1, upload=False, progress=False)
    assert "OBSERVE" in str(info.value) and "trace=" in str(info.value)
    # passing it explicitly is allowed, and trace=False always works
    ok = experiments.run([{"q": 1}], lambda r: 1, upload=False, progress=False, trace=observe)
    assert ok.items[0].trace_id
    off = experiments.run([{"q": 1}], lambda r: 1, upload=False, progress=False, trace=False)
    assert off.items[0].trace_id is None


def test_trial_root_span_identity_and_capture():
    def task(row):
        with trace.get_tracer("app").start_as_current_span("tool-call", attributes={"fi.span.kind": "TOOL",
                                                                                     "tool.name": "lookup"}):
            return "x"

    seen = {}

    @experiments.evaluator(name="spans")
    def spans(trace):
        seen["spans"] = trace
        return len(trace)

    result = experiments.run([{"id": "T1", "q": 1}], task, [spans], upload=False, progress=False, params={"model": "m"})
    names = sorted(s["name"] for s in seen["spans"])
    assert names == ["experiment.trial", "tool-call"]
    tool = next(s for s in seen["spans"] if s["name"] == "tool-call")
    assert tool["attributes"]["fi.experiment.run_id"] == result.run_id
    assert tool["attributes"]["fi.experiment.example_id"] == "T1"
    assert tool["attributes"]["fi.experiment.param.model"] == "m"
    root = next(s for s in seen["spans"] if s["name"] == "experiment.trial")
    assert root["trace_id"] == result.items[0].trace_id and root["span_id"] == result.items[0].root_span_id
    assert root["attributes"]["output.value"] == "x"


def test_python_314_refusal(monkeypatch):
    from fi.experiments._tracing import instrument

    monkeypatch.setattr(instrument, "python_supported", lambda: False)
    with pytest.raises(TracingUnsupportedError) as info:
        experiments.run([{"q": 1}], lambda r: 1, upload=False, progress=False)
    assert "TA-1" in str(info.value)
    assert experiments.run([{"q": 1}], lambda r: 1, upload=False, progress=False, trace=False).items


def test_instrument_plan_names_missing_packages(monkeypatch):
    from fi.experiments._tracing import instrument

    monkeypatch.setattr(instrument, "_installed", lambda m: m in ("openai",))
    plan = instrument.plan("langgraph", "auto")
    assert plan.enable == [] and ("langchain", "traceAI-langchain") in plan.missing
    assert 'pip install "futureagi[langchain]"' in plan.header()
    assert instrument.plan("langgraph", False).enable == []


def test_tracer_bound_once_survives_many_sequential_runs():
    """M1: an instrumentor binds its tracer once; each run's delegate is freed at the end and CPython
    reuses the address. Every run must still capture its own child spans (none lost to a dead run)."""
    import gc

    holder = {}

    def task(row):
        tracer = holder.setdefault("tracer", trace.get_tracer("fake.instrumentor"))  # bound once
        with tracer.start_as_current_span("child.llm") as span:
            span.set_attribute("gen_ai.span.kind", "TOOL")
        return row.input

    @experiments.evaluator(name="children")
    def children(trace):
        return float(sum(1 for s in trace or [] if s.get("name") == "child.llm"))

    rows = [{"input": "a"}, {"input": "b"}]
    lost = []
    for i in range(30):
        result = experiments.run(rows, task, [children], upload=False, progress=False, instrument=False)
        got = [t.scores["children"].value for t in result.items]
        if got != [1.0, 1.0]:
            lost.append((i, got))
        del result
        gc.collect()
    assert lost == []
    # the routing tracer keeps no dead run's provider alive
    assert len(holder["tracer"]._cache) <= 1


def test_missing_instrumentor_names_its_futureagi_extra():
    from fi.experiments._tracing.instrument import InstrumentPlan, install_line

    assert install_line("langchain") == 'pip install "futureagi[langchain]"'
    assert install_line("openai-agents") == 'pip install "futureagi[openai-agents]"'
    assert install_line("openai") == 'pip install "futureagi[openai]"'
    # no futureagi extra for these: the line names the package that really installs (anthropic: F3, see EXTRAS)
    assert install_line("anthropic") == "pip install traceAI-anthropic"
    assert install_line("groq") == "pip install traceAI-groq"
    header = InstrumentPlan(enable=[], missing=[("langchain", "traceAI-langchain")]).header()
    assert header == 'traceAI-langchain missing (pip install "futureagi[langchain]")'
