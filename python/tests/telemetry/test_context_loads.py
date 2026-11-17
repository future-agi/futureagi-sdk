from fi.telemetry import agent_scope, declare_skill


def test_context_read_all_links_not_loads(tracing, make_snapshot):
    tracer, exporter, _ = tracing
    snapshot, _ = make_snapshot("agent_context")
    with tracer.start_as_current_span("request"):
        snapshot.read_all()
        snapshot.read_file("skills/refund/reference/policy.md")
        snapshot.read_file("skills/refund/SKILL.md")
    contexts = [s for s in exporter.get_finished_spans() if s.name == "context.load"]
    loads = [s for s in exporter.get_finished_spans() if s.name == "skill.load"]
    assert len(contexts) == len(loads) == 1
    assert len(contexts[0].attributes["fi.context.linked_skill_version_ids"]) == 1
    attrs = loads[0].attributes
    assert attrs["fi.skill.load.via"] == "context.read"
    assert attrs["fi.skill.load.root_file"] is False
    assert attrs["fi.skill.requested_version"] == 3
    assert attrs["fi.skill.via_context.version_id"] == snapshot.identity.version_id
    assert attrs["gen_ai.agent.name"] == "support"


def test_declaration_has_distinct_evidence(tracing, make_snapshot):
    tracer, exporter, _ = tracing
    snapshot, _ = make_snapshot()
    with agent_scope(agent="refund-agent"):
        with tracer.start_as_current_span("request"):
            declare_skill(snapshot)
            snapshot.read_all()
            declare_skill(snapshot)
    loads = [s for s in exporter.get_finished_spans() if s.name == "skill.load"]
    assert [s.attributes["fi.skill.load.evidence"] for s in loads] == ["declared", "delivered"]


def test_verified_lock_declaration(tracing, make_snapshot):
    from fi.context.materialize import LockedLink
    from fi.telemetry._identity import verified_links
    tracer, exporter, _ = tracing
    context, _ = make_snapshot("agent_context")
    verified = context.read_all(trace=False)
    entry = LockedLink.model_validate(verified_links(verified)[0])
    with tracer.start_as_current_span("request"):
        declare_skill(entry)
    load = next(s for s in exporter.get_finished_spans() if s.name == "skill.load")
    assert load.attributes["fi.skill.load.via"] == "lock"
    assert load.attributes["fi.skill.requested_version"] == 3


def test_unavailable_child_identity_is_not_invented(tracing, make_snapshot):
    # Current manifests contain no LockedLink. Until the closure has been
    # verified, telemetry must not fabricate identity or add network reads.
    tracer, exporter, _ = tracing
    context, source = make_snapshot("agent_context")
    with tracer.start_as_current_span("request"):
        context.read_file("skills/refund/SKILL.md")
    assert source.calls == ["resolve", "skills/refund/SKILL.md"]
    assert not [s for s in exporter.get_finished_spans() if s.name == "skill.load"]
