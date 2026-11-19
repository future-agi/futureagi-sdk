def test_current_later_but_not_started_ancestor(tracing, make_snapshot):
    tracer, _, _ = tracing
    snapshot, _ = make_snapshot()
    with tracer.start_as_current_span("root") as root:
        with tracer.start_as_current_span("current") as current:
            snapshot.read_all()
            assert current.attributes["fi.skills.version_ids"] == (snapshot.identity.version_id,)
        assert "fi.skills.version_ids" not in root.attributes
        with tracer.start_as_current_span("later") as later:
            assert later.attributes["fi.skills.version_ids"] == (snapshot.identity.version_id,)
    with tracer.start_as_current_span("another-trace") as span:
        assert "fi.skills.version_ids" not in span.attributes
