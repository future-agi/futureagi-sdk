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
