"""Consumer/export regressions: real session checks, closure reads and scoped async delivery."""
import asyncio
import copy
import json
from dataclasses import replace
from types import SimpleNamespace
from uuid import uuid4

import pytest
from conftest import Source
from fi.context.client import AsyncContextSnapshot, ContextSnapshot, SnapshotClient
from fi.context.sessions import ContextSessionClient
from fi.context.snapshot import VerifiedSnapshot
from fi.platform import _operations as ops
from fi.telemetry import agent_scope, configure
from test_delivery_state import pair  # noqa: F401 - installed-pair exporter fixture


NAME = 'gen_ai.agent.name'
VERSION = 'fi.context.version_id'
BINDING = 'fi.context.binding_id'
SESSION = 'fi.context.session_id'
ROOT = 'AGENTS.md'
LINK = 'skills/refund/SKILL.md'


def source(name):
    src = Source('agent_context')
    src.name, src.id, src.version_id = name, str(uuid4()), str(uuid4())
    desc = json.loads(src.files['.futureagi/context.json'])
    desc['name'] = name
    src.files['.futureagi/context.json'] = json.dumps(desc, sort_keys=True, separators=(',', ':'))
    return src


def ordinary(src):
    return SnapshotClient(src, kind=src.kind).resolve(src.name)


def session(src):
    page = src.resolve(name=src.name, selector={'label': 'stable'})
    page['resolution_id'] = str(uuid4())
    receipt, binding = str(uuid4()), str(uuid4())
    mapping = {**page, 'history_mode': 'fresh', 'session_id': receipt}
    permission = {'allowed': True, 'version_id': src.version_id, 'digest': page['digest']}
    def request(method, path, **kwargs):
        if path.endswith('/sessions/') and method == 'POST':
            return mapping
        if path.endswith('/manifest/') and method == 'GET':
            assert kwargs['options'].resolution_id == page['resolution_id']
            return page
        assert method == 'POST' and path == f'/model-hub/skills/contexts/bindings/{binding}/sessions/{receipt}/access-check/'
        return permission
    def call(op, **kwargs):
        assert kwargs['options'].resolution_id == page['resolution_id']
        if op == ops.OP_CONTEXTS_CHECK_ACCESS:
            return permission
        assert op == ops.OP_CONTEXTS_READ_FILE
        return src.chunk(SimpleNamespace(resource_id=src.id, version_id=src.version_id, digest=page['digest']),
                         path=kwargs['query']['path'], offset=kwargs['query']['offset'], options=kwargs['options'])
    client = ContextSessionClient(SimpleNamespace(request=request, _transport=SimpleNamespace(call=call)),
                                  context_id=src.id, binding_id=binding)
    opened = client.open({}, idempotency_key=str(uuid4()))
    return client.snapshot(opened), {BINDING: binding, SESSION: receipt}, client, opened


def attrs(exporter, span):
    return [s.attributes for s in exporter.get_finished_spans() if s.name == span]


def receipt(attributes):
    return {k: attributes[k] for k in (BINDING, SESSION) if k in attributes}


@pytest.mark.parametrize('session_second', [False, True])
@pytest.mark.parametrize('override', [False, True])
def test_link_uses_own_source(pair, session_second, override):
    tracer, exporter = pair
    session_src, other_src = source('session-agent'), source('ordinary-agent')
    authorized, expected, _, _ = session(session_src)
    plain = ordinary(other_src)
    first, second = (plain, authorized) if session_second else (authorized, plain)
    # The telemetry closure is learned only by a delivered read. Prime it on
    # an independent recording trace, not by fabricating snapshot metadata.
    with tracer.start_as_current_span("verified-closure"):
        assert second.read_all().files[LINK] == "Refund instructions"
    with tracer.start_as_current_span('parent', attributes={NAME: first.identity.name} if override else {}):
        assert first.read_file(ROOT) == 'Support agent'
        assert second.read_file(LINK) == 'Refund instructions'
    event, = attrs(exporter, 'skill.load')
    assert receipt(event) == (expected if session_second else {})
    assert (event[VERSION], event['fi.skill.via_context.version_id']) == (second.identity.version_id,) * 2
    assert event[NAME] == (first.identity.name if override else second.identity.name)
    assert event['fi.context.requested_label'] == ('stable' if session_second else 'production')


@pytest.mark.parametrize('variant', ['authentic', 'constructor', 'copy', 'replace', 'changed_session', 'changed_binding', 'changed_identity', 'changed_selector', 'client_binding_disagrees'])
def test_receipt_bound_to_verified_instance_and_values(pair, variant):
    tracer, exporter = pair
    original, expected, client, opened = session(source('alpha'))
    snap = original
    if variant == 'client_binding_disagrees':
        # The actual authorized session route remains under the original binding.
        client.binding_id = str(uuid4())
        snap = client.snapshot(opened)
    elif variant == 'constructor':
        snap = ContextSnapshot(original.manifest, original._source, _telemetry_binding_id=expected[BINDING], _telemetry_session_id=expected[SESSION])
    elif variant == 'copy':
        snap = copy.copy(original)
    elif variant == 'replace':
        snap = replace(original)
    elif variant in ('changed_session', 'changed_binding'):
        object.__setattr__(snap, '_telemetry_' + variant.removeprefix('changed_') + '_id', str(uuid4()))
    elif variant == 'changed_identity':
        object.__setattr__(snap.identity, 'name', 'beta')
    elif variant == 'changed_selector':
        object.__setattr__(snap.manifest, 'requested', {'label':'another'})
    with tracer.start_as_current_span('parent'):
        assert snap.read_file(ROOT) == 'Support agent'
        tracer.start_span('observer').end()
    for event in (attrs(exporter, 'context.load')[0], attrs(exporter, 'observer')[0]):
        assert event[VERSION] == snap.identity.version_id
        assert receipt(event) == (expected if variant == 'authentic' else {})


@pytest.mark.parametrize('variant', ['authentic', 'copy', 'reconstructed', 'changed_session'])
def test_exact_verified_handoff_at_adapter(pair, variant):
    from fi.context.adapters.deepagents import ReadOnlyContextBackend
    tracer, exporter = pair
    snap, expected, client, opened = session(source('alpha'))
    verified = snap.read_all(trace=False)
    if variant == 'copy':
        verified = copy.copy(verified)
    elif variant == 'reconstructed':
        verified = VerifiedSnapshot(verified.manifest, verified.files)
        for k in (BINDING, SESSION):
            object.__setattr__(verified, '_telemetry_' + k.rsplit('.',1)[1], expected[k])
    elif variant == 'changed_session':
        object.__setattr__(verified, '_telemetry_session_id', str(uuid4()))
    backend = ReadOnlyContextBackend(verified, authorize=lambda *_: client.check_access(opened, snap))
    with tracer.start_as_current_span('adapter'):
        result, = backend.download_files(['/' + LINK])
        assert result.content == b'Refund instructions'
    event, = attrs(exporter, 'skill.load')
    assert event[VERSION] == verified.identity.version_id
    assert event['fi.skill.load.evidence'] == 'agent_read'
    assert receipt(event) == (expected if variant == 'authentic' else {})


@pytest.mark.parametrize('nested', [False, True], ids=['direct', 'processor'])
@pytest.mark.parametrize('override', ['none', 'start_same', 'setter_same', 'bulk_same', 'setter_different'])
def test_name_write_origin(pair, nested, override):
    from contextlib import nullcontext
    tracer, exporter = pair
    a, b = ordinary(source('alpha')), ordinary(source('beta'))
    options = {NAME: 'alpha'} if override == 'start_same' else {}
    with tracer.start_as_current_span('parent', attributes={} if nested else options) as root:
        assert a.read_file(ROOT) == 'Support agent'
        with tracer.start_as_current_span('child', attributes=options) if nested else nullcontext(root) as active:
            if override.startswith('setter'):
                active.set_attribute(NAME, 'gamma' if override.endswith('different') else 'alpha')
            elif override.startswith('bulk'):
                active.set_attributes({NAME: 'alpha'})
            assert b.read_file(ROOT) == 'Support agent'
    expect = 'beta' if override == 'none' else 'gamma' if override.endswith('different') else 'alpha'
    for event in (attrs(exporter, 'context.load')[-1], attrs(exporter, 'child' if nested else 'parent')[0]):
        assert event[VERSION] == b.identity.version_id
        assert event[NAME] == expect


@pytest.mark.asyncio
@pytest.mark.parametrize('entry', ['load_only', 'on'])
@pytest.mark.parametrize('completion', ['load_only', 'on', 'off'])
@pytest.mark.parametrize('control', ['configured', 'env'])
async def test_scope_entry_and_actual_suspended_coroutine(pair, entry, completion, control, monkeypatch):
    from test_delivery_state import set_mode
    tracer, exporter = pair
    src = source('beta'); b = ordinary(src); c = ordinary(source('gamma'))
    entered, resume = asyncio.Event(), asyncio.Event()
    class PausedTransport:
        async def chunk(self, *args, **kwargs):
            entered.set()
            await asyncio.wait_for(resume.wait(), 5)
            return c._source.chunk(*args, **kwargs)
    pending = AsyncContextSnapshot(c.manifest, PausedTransport())
    set_mode(control, entry, monkeypatch)
    with tracer.start_as_current_span('parent'):
        async with agent_scope(context=b):
            set_mode(control, 'on', monkeypatch)
            tracer.start_span('mode-alone').end()
            read = asyncio.create_task(pending.read_file(ROOT))
            await asyncio.wait_for(entered.wait(), 5)
            set_mode(control, completion, monkeypatch); resume.set()
            assert await read == 'Support agent'
            set_mode(control, 'on', monkeypatch); tracer.start_span('after-delivery').end()
            assert await pending.read_file(ROOT) == 'Support agent'
            tracer.start_span('selected').end()
        tracer.start_span('outside').end()
    seeded = b if entry == 'on' else None
    for label, snapshot in [('mode-alone', seeded), ('after-delivery', c if completion == 'on' else seeded), ('selected', c), ('outside', None)]:
        event, = attrs(exporter, label)
        assert event.get(VERSION) == (snapshot.identity.version_id if snapshot else None), label
        assert event.get(NAME) == (snapshot.identity.name if snapshot else None), label
    assert [e[VERSION] for e in attrs(exporter, 'context.load')] == [b.identity.version_id, c.identity.version_id]


@pytest.mark.asyncio
@pytest.mark.parametrize('entry,end', [('load_only', 'on'), ('on', 'load_only'), ('off', 'on'), ('on', 'off')])
@pytest.mark.parametrize('scoped', [False, True])
@pytest.mark.parametrize('corrupt', [False, True])
@pytest.mark.parametrize('whole', [False, True], ids=['read_file', 'read_all'])
async def test_verified_async_delivery_mode_at_completion(pair, entry, end, scoped, corrupt, whole):
    from contextlib import nullcontext
    from fi.context.snapshot import SnapshotIntegrityError
    tracer, exporter = pair
    src = source('coroutine'); lazy = ordinary(src)
    entered, release = asyncio.Event(), asyncio.Event()
    class Transport:
        async def chunk(self, *args, **kwargs):
            entered.set()
            await asyncio.wait_for(release.wait(), 5)
            return src.chunk(*args, **kwargs)
    pending = AsyncContextSnapshot(lazy.manifest, Transport())
    configure(skills_tracing=entry)
    with tracer.start_as_current_span('parent'), agent_scope(agent='agent') if scoped else nullcontext():
        read = asyncio.create_task(pending.read_all() if whole else pending.read_file(ROOT))
        await asyncio.wait_for(entered.wait(), 5)
        src.corrupt = corrupt
        configure(skills_tracing=end); release.set()
        if corrupt:
            with pytest.raises(SnapshotIntegrityError):
                await read
        else:
            data = await read
            assert (data.files[ROOT] if whole else data) == 'Support agent'
        configure(skills_tracing='on'); tracer.start_span('observer').end()
    delivered = entry != 'off' and end != 'off'
    event = attrs(exporter, 'skill.load' if corrupt else 'context.load')
    assert len(event) == int(delivered)
    if delivered and corrupt:
        assert event[0]['error.type'] == 'integrity'
        assert VERSION not in event[0]
    elif delivered:
        assert event[0][VERSION] == lazy.identity.version_id
    assert attrs(exporter, 'observer')[0].get(VERSION) == (lazy.identity.version_id if delivered and end == 'on' and not corrupt else None)


@pytest.mark.parametrize('wrapped', [False, True], ids=['native', 'opaque-host'])
def test_reselection_never_exports_new_identity_with_old_session(pair, wrapped):
    from contextlib import nullcontext
    from opentelemetry import trace
    from wrapt import ObjectProxy

    tracer, exporter = pair
    a, expected_a, _, _ = session(source('alpha'))
    b = ordinary(source('beta'))
    with tracer.start_as_current_span('parent'):
        assert a.read_file(ROOT) == 'Support agent'
        with tracer.start_as_current_span('nested') as active:
            # A delegate may expose only the public API; don't use private SDK
            # storage on it or rewrite half of its existing complete identity.
            with trace.use_span(ObjectProxy(active)) if wrapped else nullcontext():
                assert b.read_file(ROOT) == 'Support agent'
        tracer.start_span('following').end()
    for data in (attrs(exporter, 'context.load')[-1], attrs(exporter, 'following')[0]):
        assert (data[VERSION], data[NAME], receipt(data)) == (b.identity.version_id, 'beta', {})
    nested, = attrs(exporter, 'nested')
    assert (nested[VERSION], nested[NAME], receipt(nested)) == (
        (a.identity.version_id, 'alpha', expected_a) if wrapped else (b.identity.version_id, 'beta', {}))


@pytest.mark.asyncio
@pytest.mark.parametrize('wrapped', [False, True], ids=['native', 'FITracer'])
@pytest.mark.parametrize('scope_kind', ['automatic', 'agent', 'context', 'plain'])
@pytest.mark.parametrize('operation', ['root', 'linked', 'async-root', 'async-linked'])
@pytest.mark.parametrize('writer', ['automatic', 'start', 'single', 'bulk'])
async def test_public_name_provenance(pair, wrapped, scope_kind, operation, writer):
    from contextlib import nullcontext
    from fi_instrumentation import FITracer
    from opentelemetry import trace

    native, exporter = pair
    tracer = FITracer(native) if wrapped else native
    a = ordinary(source('alpha'))
    b, expected_receipt, _, _ = session(source('beta'))
    root = operation.endswith('root')
    if operation.startswith('async'):
        # Async clients do not issue binding receipts. Verify their own closure
        # via public read_all; never copy the synchronous producer's receipt.
        base = ordinary(source('beta'))
        class AsyncTransport:
            async def chunk(self, *args, **kwargs):
                await asyncio.sleep(0)
                return base._source.chunk(*args, **kwargs)
        b, expected_receipt = AsyncContextSnapshot(base.manifest, AsyncTransport()), {}
    if not root:
        with native.start_as_current_span('prime'):
            result = b.read_all()
            if operation.startswith('async'):
                result = await result
            assert result.files[LINK] == 'Refund instructions'
    expected_standing = 'scope' if scope_kind == 'agent' else 'alpha'
    child_name = 'different' if writer == 'single' else expected_standing
    framework = {NAME: child_name} if writer == 'start' else {}
    agent_id = 'gen_ai.agent.id'
    with native.start_as_current_span('parent'):
        scopes = {'automatic': nullcontext(), 'agent': agent_scope(agent='scope'),
                  'context': agent_scope(context=a), 'plain': agent_scope()}
        with scopes[scope_kind]:
            assert a.read_file(ROOT) == 'Support agent'
            with tracer.start_as_current_span('child', attributes={**framework, agent_id: 'child-id'}) as child:
                assert trace.get_current_span() is child
                if writer == 'single':
                    child.set_attribute(NAME, child_name)
                if writer == 'bulk':
                    child.set_attributes({NAME: child_name})
                child.set_attribute('test.unrelated', True)
                data = b.read_file(ROOT if root else LINK)
                if operation.startswith('async'):
                    data = await data
                assert data == ('Support agent' if root else 'Refund instructions')
                native.start_span('following').end()
    load = (attrs(exporter, 'context.load') if root else attrs(exporter, 'skill.load'))[-1]
    expected = child_name if writer != 'automatic' else 'scope' if scope_kind == 'agent' else 'beta'
    assert (load[VERSION], load['fi.context.id'], receipt(load), load[NAME], load.get(agent_id)) == (
        b.identity.version_id, b.identity.resource_id, expected_receipt, expected, 'child-id')
    if not root:
        assert load['fi.skill.via_context.version_id'] == b.identity.version_id
    standing = b if root else a
    later, = attrs(exporter, 'following')
    assert (later[VERSION], later[NAME], receipt(later), later.get(agent_id)) == (
        standing.identity.version_id, 'scope' if scope_kind == 'agent' else standing.identity.name,
        expected_receipt if root else {}, None)
    finished, = attrs(exporter, 'child')
    assert finished[agent_id] == 'child-id'
    if root and scope_kind == 'automatic':
        assert (finished[VERSION], finished[NAME], receipt(finished)) == (b.identity.version_id, expected, expected_receipt)


@pytest.mark.parametrize('scope', [True, False], ids=['nested-scope', 'direct-root'])
@pytest.mark.parametrize('writer', [True, False], ids=['same-string', 'derived'])
def test_fitracer_current_writer_not_inherited_stamp(pair, scope, writer):
    from contextlib import nullcontext
    from fi_instrumentation import FITracer

    native, exporter = pair
    tracer = FITracer(native)
    a, b = ordinary(source('alpha')), ordinary(source('beta'))
    with (agent_scope(agent='alpha') if scope else nullcontext()):
        with tracer.start_as_current_span('fi-root') as active:
            assert a.read_file(ROOT) == 'Support agent'
            if writer:
                active.set_attributes({NAME: 'alpha'})
            with (agent_scope(agent='inner') if scope else nullcontext()):
                assert b.read_file(ROOT) == 'Support agent'
                native.start_span('observed').end()
    expected = 'inner' if scope else 'beta'
    event = attrs(exporter, 'context.load')[-1]
    assert (event[VERSION], event[NAME]) == (b.identity.version_id, 'alpha' if writer else expected)
    assert attrs(exporter, 'observed')[0][NAME] == expected
