from types import SimpleNamespace
from uuid import uuid4

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
        snapshot.read_all()
    context = next(s for s in exporter.get_finished_spans() if s.name == "context.load")
    assert context.attributes["fi.context.binding_id"] == binding
    assert context.attributes["fi.context.session_id"] == session["session_id"]
    assert "session.id" not in context.attributes
    assert resolution not in str(context.attributes)
