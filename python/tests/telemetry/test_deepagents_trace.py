import pytest


def test_adapter_evidence_and_nonread_methods(tracing, make_snapshot):
    pytest.importorskip("deepagents")
    from fi.context.adapters.deepagents import ReadOnlyContextBackend
    tracer, exporter, _ = tracing
    snapshot, _ = make_snapshot("agent_context")
    verified = snapshot.read_all(trace=False)
    backend = ReadOnlyContextBackend(verified, authorize=lambda *args: None)
    with tracer.start_as_current_span("request"):
        backend.ls_info("/skills/")
        backend.glob_info("**/*.md")
        backend.grep_raw("Refund")
        assert not [s for s in exporter.get_finished_spans() if s.name == "skill.load"]
        backend.read("/skills/refund/reference/policy.md")
        backend.download_files(["/skills/refund/SKILL.md"])
    loads = [s for s in exporter.get_finished_spans() if s.name == "skill.load"]
    assert len(loads) == 1
    assert loads[0].attributes["fi.skill.load.evidence"] == "agent_read"
    assert loads[0].attributes["fi.skill.load.root_file"] is False
    assert loads[0].attributes["fi.skill.load.cached"] is True


def test_adapter_denial_never_gets_skill_identity(tracing, make_snapshot):
    pytest.importorskip("deepagents")
    from fi.context.adapters.deepagents import ReadOnlyContextBackend
    from fi.context.snapshot import ResolutionExpiredError
    tracer, exporter, _ = tracing
    snapshot, _ = make_snapshot("agent_context")
    def deny(*args):
        raise ResolutionExpiredError("expired")
    backend = ReadOnlyContextBackend(snapshot.read_all(trace=False), authorize=deny)
    with tracer.start_as_current_span("request"):
        with pytest.raises(ResolutionExpiredError):
            backend.read("/skills/refund/SKILL.md")
    load = next(s for s in exporter.get_finished_spans() if s.name == "skill.load")
    assert load.attributes["error.type"] == "lease"
    assert "fi.skill.version_id" not in load.attributes
    assert load.status.status_code.name == "ERROR"
