"""Bounded black-box regressions for the two installed distributions."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Event
from types import SimpleNamespace
from uuid import uuid4

import pytest
from conftest import Source
from fi.context.client import SnapshotClient
from fi.context.sessions import ContextSessionClient
from fi.context.snapshot import SnapshotIntegrityError
from fi.telemetry import agent_scope, configure, declare_skill


@pytest.fixture
def pair():
    from fi_instrumentation.otel import register
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    exporter = InMemorySpanExporter()
    provider = register(project_name="paired-history", set_global_tracer_provider=False,
                        span_exporter=exporter, batch=False, verbose=False)
    try:
        yield provider.get_tracer("paired-history"), exporter
    finally:
        provider.shutdown()
        configure()


def set_mode(control, value, monkeypatch):
    if control == "env":
        configure()
        monkeypatch.setenv("FI_SKILLS_TRACING", value)
    else:
        monkeypatch.setenv("FI_SKILLS_TRACING", "off" if value == "on" else "on")
        configure(skills_tracing=value)


@pytest.mark.parametrize("control", ["env", "configured"])
@pytest.mark.parametrize("scoped", [False, True])
@pytest.mark.parametrize("corrupt", [False, True])
@pytest.mark.parametrize("start,end", [("on", "load_only"), ("load_only", "on"), ("on", "off"), ("off", "on")])
@pytest.mark.parametrize("kind", ["skill", "agent_context"])
def test_completion_routes_public_read(pair, make_snapshot, monkeypatch, control, scoped, corrupt, start, end, kind):
    tracer, exporter = pair
    path, key = ("SKILL.md", "fi.skills.version_ids") if kind == "skill" else ("AGENTS.md", "fi.context.version_id")
    snapshot, source = make_snapshot(kind)
    chunk = source.chunk
    entered, release = Event(), Event()
    source.corrupt = corrupt

    def barrier(*args, **kwargs):
        entered.set()
        assert release.wait(10)
        return chunk(*args, **kwargs)

    source.chunk = barrier
    set_mode(control, start, monkeypatch)

    def consume():
        with tracer.start_as_current_span("parent") as parent:
            with agent_scope(agent="explicit") if scoped else nullcontext():
                if corrupt:
                    with pytest.raises(SnapshotIntegrityError):
                        snapshot.read_file(path)
                else:
                    assert snapshot.read_file(path) == source.files[path]
                # Re-enable before creating the child: load_only is not just hiding writes.
                set_mode(control, "on", monkeypatch)
                version = snapshot.identity.version_id
                expected = ((version,) if kind == "skill" else version) if start != "off" and end == "on" and not corrupt else None
                with tracer.start_as_current_span("following") as child:
                    assert child.attributes.get(key) == expected
                assert parent.attributes.get(key) == (None if scoped else expected)

    with ThreadPoolExecutor(max_workers=1) as pool:
        result = pool.submit(consume)
        try:
            assert entered.wait(10)
            set_mode(control, end, monkeypatch)
        finally:
            release.set()
        result.result(timeout=10)
    loads = [s for s in exporter.get_finished_spans() if s.name.endswith(".load")]
    assert len(loads) == int(start != "off" and end != "off")
    if loads:
        if corrupt:
            assert loads[0].attributes["error.type"] == "integrity"
            assert "fi.skill.version_id" not in loads[0].attributes
        else:
            assert loads[0].attributes[f"fi.{'skill' if kind == 'skill' else 'context'}.version_id"] == snapshot.identity.version_id


@pytest.mark.parametrize("control", ["env", "configured"])
@pytest.mark.parametrize("scoped", [False, True])
@pytest.mark.parametrize("first,second", [("load_only", "on"), ("on", "load_only")])
def test_history_across_modes(pair, make_snapshot, monkeypatch, control, scoped, first, second):
    tracer, exporter = pair
    snapshot, source = make_snapshot()
    with tracer.start_as_current_span("parent"), agent_scope(agent="explicit") if scoped else nullcontext():
        for m in [first, second]:
            set_mode(control, m, monkeypatch)
            snapshot.read_file("SKILL.md", trace=False)
            make_snapshot(tracing=False)[0].read_all()
            source.corrupt = True
            with pytest.raises(SnapshotIntegrityError):
                snapshot.read_file("SKILL.md")
        source.corrupt = False
        for m, path in [(first, "reference/policy.md"), (second, "SKILL.md")]:
            set_mode(control, m, monkeypatch)
            snapshot.read_file(path)
        set_mode(control, "on", monkeypatch)
        with tracer.start_as_current_span("following") as child:
            assert child.attributes["fi.skills.version_ids"] == (snapshot.identity.version_id,)
        for m in [first, second]:
            set_mode(control, m, monkeypatch)
            declare_skill(snapshot)
    set_mode(control, "on", monkeypatch)
    with tracer.start_as_current_span("independent") as parent, agent_scope(agent="explicit") if scoped else nullcontext():
        assert "fi.skills.count" not in parent.attributes
        snapshot.read_file("SKILL.md")
    loads = [s for s in exporter.get_finished_spans() if s.name == "skill.load"]
    assert [s.attributes.get("fi.skill.load.evidence") for s in loads] == [None, "delivered", "declared", "delivered"]
    assert loads[0].attributes["error.type"] == "integrity"
    assert loads[1].attributes["fi.skill.load.root_file"] is False
    assert loads[1].context.trace_id != loads[3].context.trace_id


@pytest.mark.parametrize("control", ["env", "configured"])
@pytest.mark.parametrize("scoped", [False, True])
@pytest.mark.parametrize("middle", ["on", "load_only"])
def test_context_is_current_even_if_event_already_sent(pair, monkeypatch, control, scoped, middle):
    tracer, exporter = pair
    def context(name):
        source = Source("agent_context")
        source.id, source.version_id, source.name = str(uuid4()), str(uuid4()), name
        return SnapshotClient(source, kind="agent_context").resolve(name)
    a, b = context("alpha"), context("beta")
    with tracer.start_as_current_span("parent") as parent, agent_scope(agent="explicit") if scoped else nullcontext():
        for snapshot, selected, propagated in [(a, "on", a), (b, middle, b if middle == "on" else a), (a, "on", a)]:
            set_mode(control, selected, monkeypatch)
            snapshot.read_file("AGENTS.md")
            set_mode(control, "on", monkeypatch)
            with tracer.start_as_current_span("following") as child:
                assert child.attributes["fi.context.version_id"] == propagated.identity.version_id
                assert child.attributes["gen_ai.agent.name"] == ("explicit" if scoped else propagated.identity.name)
            assert parent.attributes.get("fi.context.version_id") == (None if scoped else propagated.identity.version_id)
    loads = [s for s in exporter.get_finished_spans() if s.name == "context.load"]
    assert [s.attributes["fi.context.version_id"] for s in loads] == [a.identity.version_id, b.identity.version_id]


def test_authorized_session_snapshot_through_real_consumer_and_provider(pair):
    from fi.platform import _operations as ops
    tracer, exporter = pair
    source = Source("agent_context")
    page = source.resolve(name=source.name, selector={"label": "production"})
    page["resolution_id"] = str(uuid4())
    receipt, binding = str(uuid4()), str(uuid4())
    session = {**page, "history_mode": "fresh", "session_id": receipt}
    permission = {"allowed": True, "version_id": source.version_id, "digest": page["digest"]}
    calls = []

    def request(method, path, **kwargs):
        if method == "GET" and path.endswith("/manifest/"):
            calls.append("manifest")
            return page
        if method == "POST" and path.endswith("/sessions/"):
            calls.append("open")
            return session
        assert path.endswith(f"/sessions/{receipt}/access-check/")
        calls.append("session-access")
        return permission

    def call(op, **kwargs):
        assert kwargs["options"].resolution_id == page["resolution_id"]
        if op == ops.OP_CONTEXTS_CHECK_ACCESS:
            calls.append("snapshot-access")
            return permission
        assert op == ops.OP_CONTEXTS_READ_FILE
        calls.append("chunk")
        return source.chunk(SimpleNamespace(resource_id=source.id, version_id=source.version_id, digest=page["digest"]),
                            path=kwargs["query"]["path"], offset=0, options=kwargs["options"])

    consumer = ContextSessionClient(SimpleNamespace(request=request, _transport=SimpleNamespace(call=call)), context_id=source.id, binding_id=binding)
    with tracer.start_as_current_span("parent"):
        opened = consumer.open({}, idempotency_key=str(uuid4()))
        snapshot = consumer.snapshot(opened)
        assert snapshot.read_file("AGENTS.md") == source.files["AGENTS.md"]
        with tracer.start_as_current_span("following") as child:
            assert child.attributes["fi.context.session_id"] == receipt
        permission["allowed"] = False
        with pytest.raises(SnapshotIntegrityError):
            consumer.snapshot(opened)
    assert calls == ["open", "manifest", "session-access", "snapshot-access", "chunk", "manifest", "session-access"]
    events = [s for s in exporter.get_finished_spans() if s.name == "context.load"]
    assert len(events) == 1
    assert events[0].attributes["fi.context.binding_id"] == binding
    assert events[0].attributes["fi.context.session_id"] == receipt
    assert page["resolution_id"] not in str(events[0].attributes)
