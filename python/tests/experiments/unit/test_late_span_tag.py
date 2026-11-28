"""Export-time trial deadlines: exact span attribute, bounded retention, and scrubbing with or without a deadline."""

import time
from types import SimpleNamespace

import pytest
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import Event, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExportResult
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.util.instrumentation import InstrumentationScope

from fi import experiments
from fi.experiments import _engine_trial, _tracing
from fi.experiments._redact import REDACTED, Redactor
from fi.experiments._tracing import export as exporting
from fi.experiments._tracing.export_status import ExportStatus
from fi.experiments._tracing.session import RunTracing

KEY = "fi.trial.after_deadline"
DEADLINE = 2_000_000_000


def span(*, trace_id=1, span_id=2, parent_id=1, end=DEADLINE, attributes=None, name="child"):
    def context(sid):
        return trace.SpanContext(trace_id, sid, False, trace.TraceFlags(1))

    return ReadableSpan(
        name=name, context=context(span_id), parent=context(parent_id) if parent_id else None,
        resource=Resource({"synthetic": True}), attributes=attributes or {},
        events=[Event("synthetic", {"note": "synthetic-secret"}, DEADLINE - 2)],
        start_time=DEADLINE - 10, end_time=end,
        instrumentation_scope=InstrumentationScope("synthetic"),
    )


def exporter(*, outcome=False, inner=None):
    inner = inner if inner is not None else InMemorySpanExporter()
    redactor = Redactor(["synthetic-secret"])
    state = ExportStatus("synthetic-run", "https://collector.invalid/tracer/v1/traces", redactor) if outcome else None
    return exporting.ScrubbingExporter(inner, redactor, state), inner


def register(wrapper, trace_id=1, root_id=1, deadline=DEADLINE):
    # On the pre-feature source, exercise the real export path without a missing-symbol error.
    registry = getattr(wrapper, "_deadlines", None)
    if registry is not None:
        registry.register(trace_id, root_id, deadline)


@pytest.mark.parametrize("outcome", [False, True])
@pytest.mark.parametrize("case,expected", [
    ("before", False), ("exact", True), ("after", True), ("root", False),
    ("unlimited", False), ("foreign", False), ("unfinished", False), ("root-name-child", True),
])
def test_export_deadline_boundary(case, expected, outcome):
    wrapper, inner = exporter(outcome=outcome)
    if case != "unlimited":
        register(wrapper)
    options = {
        "before": {"end": DEADLINE - 1}, "exact": {}, "after": {"end": DEADLINE + 1},
        "root": {"span_id": 1, "parent_id": None, "end": DEADLINE + 1},
        "unlimited": {"end": DEADLINE + 1}, "foreign": {"trace_id": 2, "end": DEADLINE + 1},
        "unfinished": {"end": None}, "root-name-child": {"name": "experiment.trial"},
    }[case]
    original = span(**options)
    try:
        assert wrapper.export([original]) == SpanExportResult.SUCCESS
        [exported] = inner.get_finished_spans()
        if expected:
            assert exported.attributes.get(KEY) is True
        else:
            assert KEY not in exported.attributes
        assert KEY not in original.attributes  # already-ended input is not mutated
        assert KEY not in exported.resource.attributes
        assert all(KEY not in event.attributes for event in exported.events)
    finally:
        wrapper.shutdown()


def test_otlp_exact_key_and_bool_anyvalue():
    wrapper, inner = exporter()
    register(wrapper)
    wrapper.export([span(), span(span_id=3, end=DEADLINE - 1), span(span_id=1, parent_id=None)])
    exported = inner.get_finished_spans()
    try:
        assert exported[0].attributes.get(KEY) is True
        encoder = pytest.importorskip("opentelemetry.exporter.otlp.proto.common.trace_encoder")
        request = encoder.encode_spans(exported)
        # Round-trip the actual protobuf, not a dict or a stringified representation.
        request = type(request).FromString(request.SerializeToString())
        encoded = [s for resource in request.resource_spans for scope in resource.scope_spans for s in scope.spans]
        late = next(s for s in encoded if int.from_bytes(s.span_id, "big") == 2)
        [attribute] = [a for a in late.attributes if a.key == "fi.trial.after_deadline"]
        assert attribute.value.WhichOneof("value") == "bool_value"
        assert attribute.value.bool_value is True
        assert all(KEY not in {a.key for a in s.attributes} for s in encoded if s is not late)
        assert all(KEY not in {a.key for a in r.resource.attributes} for r in request.resource_spans)
        assert all(KEY not in {a.key for a in e.attributes} for s in encoded for e in s.events)
    finally:
        wrapper.shutdown()


@pytest.mark.parametrize("provided", [True, False, "true", "false", 1])
@pytest.mark.parametrize("case", ["late", "on-time", "root", "unlimited"])
def test_reserved_marker_is_only_true_on_late_children(provided, case):
    wrapper, inner = exporter()
    if case != "unlimited":
        register(wrapper)
    original = span(attributes={KEY: provided, "keep": "unchanged"},
                    span_id=1 if case == "root" else 2,
                    parent_id=None if case == "root" else 1,
                    end=DEADLINE - 1 if case == "on-time" else DEADLINE)
    try:
        wrapper.export([original])
        [got] = inner.get_finished_spans()
        assert got.attributes["keep"] == "unchanged"
        assert original.attributes[KEY] == provided
        if case == "late":
            assert got.attributes.get(KEY) is True
        else:
            assert KEY not in got.attributes
    finally:
        wrapper.shutdown()


@pytest.mark.parametrize("outcome", [False, True])
def test_every_span_is_scrubbed_with_or_without_a_deadline(outcome):
    wrapper, inner = exporter(outcome=outcome)
    register(wrapper)
    originals = [span(trace_id=tid, attributes={
        "note": "value synthetic-secret", "authorization": "synthetic-bearer",
        "gen_ai.usage.input_tokens": 12, "input.value": "input", "output.value": "output",
    }) for tid in (1, 2)]
    try:
        wrapper.export(originals)
        for original, got in zip(originals, inner.get_finished_spans()):
            assert got.attributes["note"] == "value " + REDACTED
            assert got.attributes["authorization"] == REDACTED
            assert got.attributes["gen_ai.usage.input_tokens"] == 12
            assert got.attributes["input.value"] == "input" and got.attributes["output.value"] == "output"
            assert got.events[0].attributes["note"] == REDACTED
            assert got.resource is original.resource and got.context is original.context
            assert got.start_time == original.start_time and got.end_time == original.end_time
        assert inner.get_finished_spans()[0].attributes.get(KEY) is True
        assert KEY not in inner.get_finished_spans()[1].attributes
    finally:
        wrapper.shutdown()


def test_other_trials_use_their_own_deadline_and_exporters_are_isolated():
    wrapper, inner = exporter()
    other, other_inner = exporter()
    register(wrapper, trace_id=1, deadline=DEADLINE)
    register(wrapper, trace_id=2, deadline=DEADLINE + 1)
    try:
        batch = [span(trace_id=1), span(trace_id=2)]
        wrapper.export(batch)
        other.export(batch)
        first, second = inner.get_finished_spans()
        assert first.attributes.get(KEY) is True and KEY not in second.attributes
        assert all(KEY not in s.attributes for s in other_inner.get_finished_spans())
    finally:
        wrapper.shutdown()
        other.shutdown()


@pytest.mark.parametrize("shutdown_raises", [False, True])
def test_registry_is_bounded_retained_through_flush_and_cleared_on_shutdown(monkeypatch, shutdown_raises):
    monkeypatch.setattr(exporting, "_MAX_TRIAL_DEADLINES", 2, raising=False)

    class Inner(InMemorySpanExporter):
        def shutdown(self):
            super().shutdown()
            if shutdown_raises:
                raise RuntimeError("synthetic shutdown failure")

    wrapper, inner = exporter(inner=Inner())
    registry = getattr(wrapper, "_deadlines", None)
    assert registry is not None, "exporter must own a bounded deadline registry"
    register(wrapper, trace_id=1)
    register(wrapper, trace_id=2)
    register(wrapper, trace_id=3)
    assert len(registry._entries) == 2 and 1 not in registry._entries
    assert wrapper.force_flush()
    wrapper.export([span(trace_id=2), span(trace_id=3)])
    assert all(s.attributes.get(KEY) is True for s in inner.get_finished_spans())
    if shutdown_raises:
        with pytest.raises(RuntimeError, match="synthetic shutdown failure"):
            wrapper.shutdown()
    else:
        wrapper.shutdown()
    assert not registry._entries
    register(wrapper, trace_id=4)
    assert not registry._entries, "a late producer must not repopulate a closed exporter"


def make_provider(inner):
    return exporting.exporter_factory(
        base_url="https://collector.invalid", api_key="synthetic-key", secret_key="synthetic-secret",
        project="synthetic", run_name="synthetic", run_id="synthetic-run", redactor=Redactor([]), inner=inner,
    )()


def test_child_ending_after_trial_close_is_tagged():
    inner = InMemorySpanExporter()
    provider = make_provider(inner)
    tracing = RunTracing(provider, None, {}, "synthetic", use_router=False, owns_delegate=True)
    try:
        with tracing.trial("synthetic", 1) as tt:
            callback = getattr(tracing, "_register_deadline", None)
            if callback is not None:
                callback(tt, DEADLINE)
            child = provider.get_tracer("synthetic").start_span("late-child", start_time=DEADLINE - 1)
        provider.force_flush()  # root ended and was exported before the child ends
        child.end(end_time=DEADLINE)
        provider.force_flush()
        exported = {s.name: s for s in inner.get_finished_spans()}
        assert exported["late-child"].attributes.get(KEY) is True
        assert KEY not in exported["experiment.trial"].attributes
    finally:
        tracing.shutdown()


@pytest.mark.parametrize("timeout", [None, 1.0, float("inf"), 1e300])
def test_engine_registers_wall_deadline_before_task_and_keeps_trials_separate(monkeypatch, timeout):
    inner = InMemorySpanExporter()
    provider = make_provider(inner)
    tracing = RunTracing(provider, None, {}, "synthetic", use_router=False, owns_delegate=True)
    monkeypatch.setattr(_tracing, "setup_run_tracing", lambda **kwargs: tracing)
    wall = [DEADLINE - 1_000_000_000]
    monkeypatch.setattr(_engine_trial, "time", SimpleNamespace(monotonic=time.monotonic, time_ns=lambda: wall[0]))

    async def task(row):
        child = provider.get_tracer("synthetic").start_span("child-" + row.id, start_time=DEADLINE - 1)
        child.end(end_time=DEADLINE)
        provider.force_flush()
        # Export occurred before the task returned: registration cannot wait for the root to end.
        last = inner.get_finished_spans()[-1]
        if timeout == 1.0 and row.id == "first":
            assert last.attributes.get(KEY) is True
        else:
            assert KEY not in last.attributes
        wall[0] += 1_000_000_000
        return "synthetic-output"

    result = experiments.run(
        [{"id": "first", "input": "synthetic"}, {"id": "second", "input": "synthetic"}], task,
        timeout_s=timeout, concurrency=1, trace=True, instrument=False, upload=False, progress=False,
    )
    assert [item.status for item in result.items] == ["completed", "completed"]
    exported = {s.name: s for s in inner.get_finished_spans() if s.name != "experiment.trial"}
    assert KEY not in exported["child-second"].attributes
    if timeout == 1.0:
        assert exported["child-first"].attributes.get(KEY) is True
    else:
        assert KEY not in exported["child-first"].attributes
    assert all(KEY not in s.attributes for s in inner.get_finished_spans() if s.name == "experiment.trial")
