import pytest


def loads(exporter):
    return [span for span in exporter.get_finished_spans() if span.name == "skill.load"]


@pytest.mark.parametrize("path,root", [("SKILL.md", True), ("reference/policy.md", False)])
def test_first_file_and_dedup(tracing, make_snapshot, path, root):
    tracer, exporter, _ = tracing
    snapshot, source = make_snapshot()
    assert not exporter.get_finished_spans()
    with tracer.start_as_current_span("request") as parent:
        snapshot.read_file(path)
        snapshot.read_file("SKILL.md")
        snapshot.read_all()
    spans = loads(exporter)
    assert len(spans) == 1
    span = spans[0]
    assert span.parent.span_id == parent.get_span_context().span_id
    assert span.instrumentation_scope.name == "futureagi.skills"
    assert span.attributes["fi.skill.version_id"] == snapshot.identity.version_id
    assert span.attributes["fi.skill.digest"] == snapshot.identity.digest
    assert span.attributes["fi.skill.load.root_file"] is root
    assert span.attributes["fi.skill.load.cached"] is False
    assert span.attributes["fi.skill.load.evidence"] == "delivered"
    assert span.attributes["fi.skill.load.via"] == "sdk.read_file"
    assert span.attributes["fi.skill.requested_label"] == "production"
    assert "synthetic-lease" not in str(span.attributes)
    assert "Refund instructions" not in str(span.attributes)


def test_read_all_is_one_boundary(tracing, make_snapshot):
    tracer, exporter, _ = tracing
    snapshot, source = make_snapshot()
    with tracer.start_as_current_span("request"):
        snapshot.read_all()
    assert len(loads(exporter)) == 1
    assert loads(exporter)[0].attributes["fi.skill.load.via"] == "sdk.read_all"
    assert source.calls == ["resolve"] + [item.path for item in snapshot.manifest.files]


def test_failure_has_no_verified_identity(tracing, make_snapshot):
    from fi.context.snapshot import SnapshotIntegrityError
    from fi.telemetry import agent_scope
    tracer, exporter, _ = tracing
    snapshot, source = make_snapshot()
    context, _ = make_snapshot("agent_context")
    source.corrupt = True
    with agent_scope(agent="refund-agent", context=context):
        with tracer.start_as_current_span("request"):
            for _ in range(2):
                with pytest.raises(SnapshotIntegrityError):
                    snapshot.read_file("SKILL.md")
    spans = loads(exporter)
    assert len(spans) == 1
    span = spans[0]
    assert span.status.status_code.name == "ERROR"
    assert span.attributes["error.type"] == "integrity"
    assert span.attributes["gen_ai.agent.name"] == "refund-agent"
    assert span.attributes["fi.context.version_id"] == context.identity.version_id
    assert span.attributes["fi.skill.requested_label"] == "production"
    for key in ("fi.skill.id", "fi.skill.version_id", "fi.skill.digest", "fi.skill.version"):
        assert key not in span.attributes


def test_no_trace_no_load_and_later_setup(tracing, make_snapshot):
    tracer, exporter, _ = tracing
    snapshot, _ = make_snapshot()
    snapshot.read_all()
    assert not loads(exporter)
    with tracer.start_as_current_span("request"):
        snapshot.read_all()
    assert len(loads(exporter)) == 1


async def test_async_reads(tracing):
    from conftest import Source
    from fi.context.client import AsyncSnapshotClient
    class AsyncSource(Source):
        async def resolve(self, **kwargs):
            return super().resolve(**kwargs)
        async def chunk(self, *args, **kwargs):
            return super().chunk(*args, **kwargs)
    tracer, exporter, _ = tracing
    snapshot = await AsyncSnapshotClient(AsyncSource(), kind="skill").resolve("refund")
    with tracer.start_as_current_span("request"):
        await snapshot.read_all()
        await snapshot.read_file("SKILL.md")
    assert len(loads(exporter)) == 1


def test_broken_telemetry_does_not_change_consumption(tracing, make_snapshot, monkeypatch):
    from fi.telemetry import _hooks
    tracer, exporter, _ = tracing
    snapshot, _ = make_snapshot()
    def broken(*args, **kwargs):
        raise RuntimeError("secret that must not be logged")
    monkeypatch.setattr(_hooks, "_emit", broken)
    with tracer.start_as_current_span("request"):
        assert snapshot.read_file("SKILL.md") == "Refund instructions"
