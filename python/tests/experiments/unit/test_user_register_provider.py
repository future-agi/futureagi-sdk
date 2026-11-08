"""trace=<the user's own traceAI provider>.

traceAI's ``register()`` marks its exporting processor as the provider's *default*, and its ``add_span_processor()``
shuts that default down and drops it before adding the new one. The SDK adds two processors of its own to the user's
provider (baggage, the trial's local capture). Those are additions, never a replacement: the run's spans must still
reach the user's exporter. Before the fix nothing did (on the stack, the router saw no POST /tracer/v1/traces for the
whole run, and every trial's trace id was unknown to the server).

No network: ``register()`` gets an in-memory exporter (``span_exporter=``) and no eval tags, so it makes no request.
"""

import signal

import pytest

pytest.importorskip("opentelemetry.sdk")  # absent on 3.14 (TA-1)
pytest.importorskip("fi_instrumentation")

from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402

from fi import experiments  # noqa: E402

ROWS = [{"id": "U1", "q": "where is order 1?"}, {"id": "U2", "q": "where is order 2?"}]


def _register(monkeypatch, *, batch: bool):
    from fi_instrumentation import register
    from fi_instrumentation.fi_types import ProjectType

    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:9")  # never reached: the exporter is given, no eval tags
    saved = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}  # register() installs its own
    exporter = InMemorySpanExporter()
    try:
        provider = register(project_name="my-app", project_type=ProjectType.EXPERIMENT, batch=batch, verbose=False,
                            span_exporter=exporter)
    finally:
        for s, h in saved.items():
            signal.signal(s, h)
    return provider, exporter


@pytest.mark.parametrize("batch", [True, False], ids=["batch", "simple"])
def test_the_users_register_provider_still_exports_every_trial(monkeypatch, batch):
    provider, exporter = _register(monkeypatch, batch=batch)
    try:
        result = experiments.run(ROWS, lambda row: "shipped", upload=False, progress=False, trace=provider,
                                 instrument=False)
        roots = [s for s in exporter.get_finished_spans() if s.name == "experiment.trial"]
        assert len(roots) == 2, "the user's exporter received no trial span: its processor was dropped"
        assert {format(s.context.trace_id, "032x") for s in roots} == {it.trace_id for it in result.items}
        assert {s.attributes["fi.experiment.example_id"] for s in roots} == {"U1", "U2"}
        assert all(s.resource.attributes["project_name"] == "my-app" for s in roots)  # the user's project, no other
    finally:
        provider.shutdown()


def test_the_sdks_own_processors_are_added_alongside(monkeypatch):
    """The SDK's processors still run on the user's provider: a child span gets the run identity as baggage
    attributes, and the trial's local capture (what span evaluators read) holds the root and the child."""
    from opentelemetry import trace as trace_api

    provider, exporter = _register(monkeypatch, batch=False)
    seen = {}

    def task(row):
        with trace_api.get_tracer("app", tracer_provider=provider).start_as_current_span("app.step"):
            return "shipped"

    @experiments.evaluator(name="spans")
    def spans(trace):
        seen.setdefault("names", []).append(sorted(s["name"] for s in trace))
        return len(trace)

    try:
        result = experiments.run(ROWS[:1], task, [spans], upload=False, progress=False, trace=provider,
                                 instrument=False)
        child = next(s for s in exporter.get_finished_spans() if s.name == "app.step")
        assert child.attributes["fi.experiment.run_id"] == result.run_id
        assert seen["names"] == [["app.step", "experiment.trial"]]
    finally:
        provider.shutdown()


SECRET = "sk-unit-test-0123456789abcdef"  # a value of a *_API_KEY variable: redacted wherever it appears


def test_a_failed_trials_error_on_the_users_provider_is_redacted_at_the_source(monkeypatch):
    """The SDK's own exporter scrubs every span it exports; the user's exporter does not. So what the SDK writes on
    the trial root itself (the error status and the exception event, as the input and output) is redacted before
    it is set, and reaches the user's exporter already clean."""
    monkeypatch.setenv("DSX_UNIT_API_KEY", SECRET)
    provider, exporter = _register(monkeypatch, batch=False)

    def task(row):
        raise RuntimeError(f"the upstream refused key {SECRET}")

    try:
        result = experiments.run(ROWS[:1], task, upload=False, progress=False, trace=provider, instrument=False)
        [root] = [s for s in exporter.get_finished_spans() if s.name == "experiment.trial"]
        written = [root.status.description or ""] + [str(v) for e in root.events for v in (e.attributes or {}).values()]
        assert result.items[0].status == "failed"
        assert root.events and all(SECRET not in text for text in written), written
        assert "[redacted]" in root.status.description and any("[redacted]" in text for text in written[1:])
    finally:
        provider.shutdown()


def test_the_users_next_processor_is_added_beside_registers_exporter(monkeypatch):
    """After a run has added the SDK's processors, register()'s exporter is no longer the provider's replaceable
    default: a processor the user adds later runs beside it, it does not replace it."""
    from opentelemetry import trace as trace_api
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    provider, exporter = _register(monkeypatch, batch=False)
    second = InMemorySpanExporter()
    try:
        experiments.run(ROWS[:1], lambda row: "shipped", upload=False, progress=False, trace=provider, instrument=False)
        provider.add_span_processor(SimpleSpanProcessor(second))
        with trace_api.get_tracer("app", tracer_provider=provider).start_as_current_span("app.after"):
            pass
        assert [s.name for s in second.get_finished_spans()] == ["app.after"]
        assert "app.after" in [s.name for s in exporter.get_finished_spans()]
    finally:
        provider.shutdown()
