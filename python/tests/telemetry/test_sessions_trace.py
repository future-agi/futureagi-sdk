from types import SimpleNamespace
from uuid import uuid4

import pytest
from conftest import Source
from fi.context.sessions import ContextSessionClient


def test_session_snapshot_attaches_ids_without_emitting(tracing, monkeypatch):
    tracer, exporter, _ = tracing
    source = Source("agent_context")
    page = source.resolve(name="support", selector={"label": "production"})
    resolution = str(uuid4())
    page["resolution_id"] = resolution
    session = {**page, "session_id": str(uuid4())}
    client = SimpleNamespace(request=lambda *args, **kwargs: page)
    binding = str(uuid4())
    consumer = ContextSessionClient(client, context_id=source.id, binding_id=binding)
    consumer.source = source
    monkeypatch.setattr(consumer, "check_access", lambda *args: None)
    with tracer.start_as_current_span("request"):
        snapshot = consumer.snapshot(session)
        assert not exporter.get_finished_spans()
        verified = snapshot.read_all()
        pytest.importorskip("deepagents")
        from fi.context.adapters.deepagents import ReadOnlyContextBackend
        backend = ReadOnlyContextBackend(verified, authorize=lambda *args: None)
        backend.read("/skills/refund/SKILL.md")
    context = next(s for s in exporter.get_finished_spans() if s.name == "context.load")
    assert context.attributes["fi.context.binding_id"] == binding
    assert context.attributes["fi.context.session_id"] == session["session_id"]
    assert "session.id" not in context.attributes
    assert resolution not in str(context.attributes)
    skill = next(s for s in exporter.get_finished_spans() if s.name == "skill.load")
    assert skill.attributes["fi.context.binding_id"] == binding
    assert skill.attributes["fi.context.session_id"] == session["session_id"]


def test_session_tracing_optout_survives_verified_deepagents_handoff(
    tracing, monkeypatch
):
    pytest.importorskip("deepagents")
    from fi.context.adapters.deepagents import ReadOnlyContextBackend

    tracer, exporter, _ = tracing
    source = Source("agent_context")
    page = source.resolve(name="support", selector={"label": "production"})
    page["resolution_id"] = str(uuid4())
    session = {**page, "session_id": str(uuid4())}
    client = SimpleNamespace(request=lambda *args, **kwargs: page)
    binding = str(uuid4())
    consumer = ContextSessionClient(
        client, context_id=source.id, binding_id=binding, tracing=False
    )
    consumer.source = source
    monkeypatch.setattr(consumer, "check_access", lambda *args: None)

    snapshot = consumer.snapshot(session)
    verified = snapshot.read_all()
    assert verified._tracing is False
    assert verified._telemetry_binding_id == binding
    assert verified._telemetry_session_id == session["session_id"]
    backend = ReadOnlyContextBackend(verified, authorize=lambda *args: None)
    with tracer.start_as_current_span("real-session-request"):
        backend.read("/skills/refund/SKILL.md")
    assert not [
        span for span in exporter.get_finished_spans()
        if span.name in {"context.load", "skill.load"}
    ]
