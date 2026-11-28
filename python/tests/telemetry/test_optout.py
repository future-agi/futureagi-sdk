import pytest
from fi.telemetry import agent_scope, configure
from fi.telemetry._registry import registry


@pytest.mark.parametrize("control", ["environment", "programmatic", "client", "call"])
def test_off_controls(tracing, make_snapshot, monkeypatch, control):
    tracer, exporter, provider = tracing
    snapshot, _ = make_snapshot(tracing=control != "client")
    if control == "environment":
        configure(tracer_provider=provider)
        monkeypatch.setenv("FI_SKILLS_TRACING", "off")
    if control == "programmatic":
        configure(skills_tracing="off", tracer_provider=provider)
    with tracer.start_as_current_span("request") as span:
        snapshot.read_all(trace=control != "call")
        assert "fi.skills.count" not in span.attributes
    assert not [s for s in exporter.get_finished_spans() if s.name in ("skill.load", "context.load")]
    assert not registry._entries


def test_programmatic_wins(tracing, make_snapshot, monkeypatch):
    tracer, exporter, provider = tracing
    monkeypatch.setenv("FI_SKILLS_TRACING", "off")
    configure(skills_tracing="on", tracer_provider=provider)
    snapshot, _ = make_snapshot()
    with tracer.start_as_current_span("request"):
        snapshot.read_all()
    assert len([s for s in exporter.get_finished_spans() if s.name == "skill.load"]) == 1


def test_load_only_keeps_identity_without_propagation(tracing, make_snapshot):
    tracer, exporter, provider = tracing
    configure(skills_tracing="load_only", tracer_provider=provider)
    skill, _ = make_snapshot()
    context, _ = make_snapshot("agent_context")
    with agent_scope(agent="refund-agent", context=context):
        with tracer.start_as_current_span("request") as parent:
            skill.read_all()
            skill.read_file("SKILL.md")
            with tracer.start_as_current_span("later") as later:
                assert "fi.skills.count" not in later.attributes
                assert "fi.context.id" not in later.attributes
            assert "fi.skills.count" not in parent.attributes
    load = [s for s in exporter.get_finished_spans() if s.name == "skill.load"]
    assert len(load) == 1
    assert load[0].attributes["gen_ai.agent.name"] == "refund-agent"
    assert load[0].attributes["fi.context.version_id"] == context.identity.version_id
    assert not registry._entries


@pytest.mark.parametrize("control", ["environment", "programmatic"])
@pytest.mark.parametrize("corrupt", [False, True], ids=["success", "failure"])
def test_pending_public_read_respects_off_at_completion(make_snapshot, monkeypatch, control, corrupt):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from fi.context.snapshot import SnapshotIntegrityError
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    backend = pytest.importorskip("fi_instrumentation.otel")
    exporter = InMemorySpanExporter()
    provider = backend.register(project_name="pending-read", set_global_tracer_provider=False,
                                span_exporter=exporter, batch=False, verbose=False)
    tracer = provider.get_tracer(__name__)
    entered, deliver = Event(), Event()
    snapshot, source = make_snapshot()
    chunk = source.chunk
    source.corrupt = corrupt

    def gated_chunk(*args, **kwargs):
        entered.set()
        assert deliver.wait(10)
        return chunk(*args, **kwargs)

    source.chunk = gated_chunk

    def consume():
        with tracer.start_as_current_span("ordinary") as span:
            if corrupt:
                with pytest.raises(SnapshotIntegrityError):
                    snapshot.read_file("SKILL.md")
            else:
                assert snapshot.read_file("SKILL.md") == source.files["SKILL.md"]
            assert "fi.skills.count" not in span.attributes

    try:
        monkeypatch.setenv("FI_SKILLS_TRACING", "on" if control == "environment" else "off")
        configure(skills_tracing=None if control == "environment" else "on")
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(consume)
            try:
                assert entered.wait(10)
                if control == "environment":
                    monkeypatch.setenv("FI_SKILLS_TRACING", "off")
                else:
                    configure(skills_tracing="off")
            finally:
                deliver.set()
            future.result(timeout=10)
        assert [s.name for s in exporter.get_finished_spans()] == ["ordinary"]
    finally:
        provider.shutdown()
        configure()
