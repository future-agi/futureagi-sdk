// Isolated packed consumer; only transport is synthetic. No direct hook calls.
import assert from 'node:assert/strict';
import { createHash, randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
import { after, test } from 'node:test';
import { trace, context as otelContext } from '@opentelemetry/api';
import { InMemorySpanExporter, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
const require = createRequire(import.meta.url);
const load = (form, name) => form === 'cjs' ? require(name) : import(name);
const [coreForm, sdkForm] = process.argv.slice(2);
const {register, FITracer} = await load(coreForm, '@traceai/fi-core');
const {ContextSnapshot, SnapshotIntegrityError} = await load(sdkForm, '@future-agi/sdk/context');
const {configure, withAgentScope, declareSkill, FutureAGISkillsSpanProcessor} = await load(sdkForm === 'esm' ? 'cjs' : 'esm', '@future-agi/sdk/telemetry');
const memory = new InMemorySpanExporter();
const sdkProcessor = process.argv[4] === 'sdk-processor';
const provider = register({projectName: 'history', runtimeAttributes: !sdkProcessor,
  spanProcessors: [...(sdkProcessor ? [new FutureAGISkillsSpanProcessor()] : []), new SimpleSpanProcessor(memory)]});
const tracer = trace.getTracer('history');
const hash = v => createHash('sha256').update(v).digest('hex');
function fixture(kind, name, tracing = true, linked = false) {
  const files = kind === 'skill' ? {'SKILL.md': 'root', 'reference/help.md': 'help'} : {'AGENTS.md': name};
  if (linked) {
    const child = {digest:'sha256:' + hash(JSON.stringify([['SKILL.md',hash('policy')]])), mount:'skills/refund/', requested:{version:1}, skill_id:randomUUID(), version:1, version_id:randomUUID()};
    files['skills/refund/SKILL.md'] = 'policy';
    // Descriptor and manifest are canonical and independently verified by readAll().
    files['.futureagi/context.json'] = JSON.stringify({entrypoint:'AGENTS.md', kind, links:[child], name, owned_paths:['AGENTS.md'], schema:1});
  }
  const metadata = Object.entries(files).sort(([a],[b]) => a < b ? -1 : a > b ? 1 : 0).map(([path, text]) => ({path, sha256: hash(text), sizeBytes: text.length}));
  const identity = {kind, resourceId: randomUUID(), versionId: randomUUID(), version: 1, name,
    digest: 'sha256:' + hash(JSON.stringify(metadata.map(f => [f.path, f.sha256])))};
  const source = { corrupt: false, pause: undefined, async chunk(id, path) {
    const text = files[path];
    if (this.pause) { const {entered, resume} = this.pause; this.pause = undefined; entered.resolve(); await resume.promise; }
    return {resource_id: id.resourceId, version_id: id.versionId, digest: id.digest, path, sha256: hash(text), size_bytes: text.length,
      total_chars: text.length, text: this.corrupt ? 'X'.repeat(text.length) : text, offset: 0, next_offset: null, eof: true};
  }};
  const snapshot = new ContextSnapshot({identity, requested: {version: 1}, files: metadata,
    lease: {resolutionId: 'fixture', resolutionExpiresAt: '2099-01-01T00:00:00Z'}}, source, {tracing});
  return {snapshot, source, version: identity.versionId};
}
function mode(environment, value) {
  process.env.FI_SKILLS_TRACING = environment ? value : value === 'on' ? 'off' : 'on';
  configure(environment ? {} : {skillsTracing: value});
}
function request(name, scoped, body, context) {
  return tracer.startActiveSpan(name, async parent => {
    try { return await (scoped ? withAgentScope({agent: 'explicit', context}, () => body(parent)) : body(parent)); }
    finally { parent.end(); }
  });
}
const observer = (key) => { const span = tracer.startSpan('following'); try { return span.attributes[key]; } finally { span.end(); } };
const events = name => memory.getFinishedSpans().filter(s => s.name === name);
for (const scoped of [false, true]) for (const env of [false, true]) {
  for (const first of ['on', 'load_only']) test(`history ${first} scope=${scoped} env=${env}`, async () => {
    memory.reset(); const set = value => mode(env, value);
    const {snapshot, source, version} = fixture('skill', 'a'); const other = first === 'on' ? 'load_only' : 'on';
    set(first);
    await request('one', scoped, async () => {
      await snapshot.readFile('SKILL.md', {trace:false});
      await fixture('skill', 'disabled', false).snapshot.readFile('SKILL.md');
      assert.equal(events('skill.load').length, 0);
      source.corrupt = true;
      for (const end of [first, other]) {
        const {entered, resume} = source.pause = {entered:Promise.withResolvers(), resume:Promise.withResolvers()};
        const rejected = assert.rejects(snapshot.readFile('SKILL.md'), SnapshotIntegrityError);
        await entered.promise; set(end); resume.resolve(); await rejected;
      }
      assert.deepEqual(events('skill.load').map(s => s.attributes['error.type']), ['integrity']);
      source.corrupt = false; set(first);
      assert.equal(await snapshot.readFile('reference/help.md'), 'help');
      // Hold the second real, verified read until the mode has changed.
      const {entered, resume} = source.pause = {entered:Promise.withResolvers(), resume:Promise.withResolvers()};
      const read = snapshot.readFile('SKILL.md'); await entered.promise; set(other); resume.resolve(); assert.equal(await read, 'root');
      set('on'); assert.deepEqual(observer('fi.skills.version_ids'), [version]); set(other);
      declareSkill(snapshot); set(first); declareSkill(snapshot); set('on');
      assert.deepEqual(observer('fi.skills.version_ids'), [version]);
      assert.deepEqual(events('skill.load').map(s => s.attributes['fi.skill.load.evidence']), [undefined, 'delivered', 'declared']);
      assert.equal(events('skill.load')[1].attributes['fi.skill.load.root_file'], false);
    });
    await request('independent', scoped, async () => { assert.equal(observer('fi.skills.count'), undefined); await snapshot.readFile('SKILL.md'); });
    assert.equal(events('skill.load').length, 4);
    assert.notEqual(events('skill.load')[1].spanContext().traceId, events('skill.load')[3].spanContext().traceId);
  });
  for (const middle of ['on','load_only']) test(`context A/B/A ${middle} scope=${scoped} env=${env}`, async () => {
    memory.reset(); mode(env, 'on'); const a = fixture('agent_context', 'alpha'), b = fixture('agent_context', 'beta');
    await request('context', scoped, async parent => {
      for (const [context, selected, propagated] of [[a,'on',a], [b,middle,middle==='on'?b:a], [a,'on',a]]) {
        mode(env, selected); await context.snapshot.readFile('AGENTS.md');
        if (context === b) {
          const skill = fixture('skill','inside');
          await skill.snapshot.readFile('reference/help.md');
          assert.equal(events('skill.load').at(-1).attributes['fi.context.version_id'], b.version);
          mode(env, 'on');
          assert.deepEqual(observer('fi.skills.version_ids'), middle === 'on' ? [skill.version] : undefined);
          await skill.snapshot.readFile('SKILL.md');
          assert.equal(events('skill.load').length, 1);
          assert.deepEqual(observer('fi.skills.version_ids'), [skill.version]);
        }
        mode(env, 'on');
        assert.equal(observer('fi.context.version_id'), propagated.version);
        assert.equal(observer('gen_ai.agent.name'), scoped ? 'explicit' : propagated.snapshot.identity.name);
        assert.equal(parent.attributes['fi.context.version_id'], scoped ? undefined : propagated.version);
      }
      if (middle === 'on' && !scoped) { assert.equal(parent.attributes['fi.skills.count'], 0); assert.deepEqual(parent.attributes['fi.skills.version_ids'], []); }
      assert.deepEqual(events('context.load').map(s => s.attributes['fi.context.version_id']), [a.version,b.version]);
    }, a.snapshot);
  });
}
const NAME = 'gen_ai.agent.name', VERSION = 'fi.context.version_id';
for (const nested of [false, true]) for (const override of ['none', 'start_same', 'setter_same', 'bulk_same', 'setter_different']) {
  test(`context name nested=${nested} origin=${override}`, async () => {
    memory.reset(); mode(false, 'on');
    const a = fixture('agent_context', 'alpha'), b = fixture('agent_context', 'beta');
    const options = override === 'start_same' ? {attributes:{[NAME]:'alpha'}} : {};
    await tracer.startActiveSpan('root', nested ? {} : options, async root => {
      try {
        assert.equal(await a.snapshot.readFile('AGENTS.md'), 'alpha');
        const select = async active => {
          if (override.startsWith('setter')) active.setAttribute(NAME, override.endsWith('different') ? 'gamma' : 'alpha');
          if (override === 'bulk_same') active.setAttributes({[NAME]: 'alpha'});
          assert.equal(await b.snapshot.readFile('AGENTS.md'), 'beta');
        };
        if (nested) await tracer.startActiveSpan('nested', options, async s => { try {await select(s);} finally {s.end();} });
        else await select(root);
      } finally { root.end(); }
    });
    const expected = override === 'none' ? 'beta' : override.endsWith('different') ? 'gamma' : 'alpha';
    for (const span of [events('context.load').at(-1), events(nested ? 'nested' : 'root')[0]]) {
      assert.equal(span.attributes[VERSION], b.version);
      assert.equal(span.attributes[NAME], expected);
    }
  });
}
for (const entry of ['load_only', 'on']) for (const completion of ['load_only','on','off']) for (const env of [false,true]) {
  test(`entry context ${entry} completion=${completion} env=${env}`, async () => {
    memory.reset(); mode(env, entry);
    const b = fixture('agent_context','beta'), c = fixture('agent_context','gamma');
    await tracer.startActiveSpan('root', async root => {
      try {
        await withAgentScope({context: b.snapshot}, async () => {
          mode(env, 'on'); tracer.startSpan('mode-alone').end();
          const {entered,resume} = c.source.pause = {entered:Promise.withResolvers(), resume:Promise.withResolvers()};
          const read = c.snapshot.readFile('AGENTS.md'); await entered.promise;
          mode(env, completion); resume.resolve(); assert.equal(await read, 'gamma');
          mode(env, 'on'); tracer.startSpan('after-delivery').end();
          assert.equal(await c.snapshot.readFile('AGENTS.md'), 'gamma'); tracer.startSpan('selected').end();
        });
        tracer.startSpan('outside').end();
      } finally { root.end(); }
    });
    const seeded = entry === 'on' ? b : undefined;
    for (const [label, context] of [['mode-alone',seeded], ['after-delivery',completion === 'on' ? c : seeded], ['selected',c], ['outside',undefined]]) {
      const event = events(label)[0].attributes;
      assert.equal(event[VERSION], context?.version, label); assert.equal(event[NAME], context?.snapshot.identity.name, label);
    }
    assert.deepEqual(events('context.load').map(s => s.attributes[VERSION]), [b.version,c.version]);
  });
}
for (const wrapped of [false, true]) for (const scoped of ['automatic','agent','context','plain']) {
  for (const linked of [false,true]) for (const writer of ['automatic','start','single','bulk']) {
    test(`public provenance wrapped=${wrapped} scope=${scoped} linked=${linked} writer=${writer}`, async () => {
      memory.reset(); mode(false,'on');
      const a = fixture('agent_context','alpha'), b = fixture('agent_context','beta',true,linked);
      if (linked) await b.snapshot.readAll();
      const api = wrapped ? new FITracer({tracer}) : tracer;
      const oldName = scoped === 'agent' ? 'scope' : 'alpha';
      const childName = writer === 'single' ? 'different' : oldName;
      const id = 'gen_ai.agent.id';
      const run = () => api.startActiveSpan('child', {attributes:{[id]:'child-id', ...(writer === 'start' ? {[NAME]:childName} : {})}}, async child => {
        try {
          assert.equal(trace.getSpan(otelContext.active()), child);
          if (writer === 'single') child.setAttribute(NAME,childName);
          if (writer === 'bulk') child.setAttributes({[NAME]:childName});
          child.setAttribute('test.unrelated',true);
          assert.equal(await b.snapshot.readFile(linked ? 'skills/refund/SKILL.md' : 'AGENTS.md'),linked ? 'policy' : 'beta');
          tracer.startSpan('later').end();
        } finally { child.end(); }
      });
      await tracer.startActiveSpan('parent', async parent => { try {
        await a.snapshot.readFile('AGENTS.md');
        if (scoped === 'automatic') await run();
        else await withAgentScope(scoped === 'context' ? {context:a.snapshot} : scoped === 'agent' ? {agent:'scope'} : {},run);
        tracer.startSpan('outside').end();
      } finally { parent.end(); } });
      const standing = scoped === 'agent' ? 'scope' : 'beta';
      const expected = writer === 'automatic' ? standing : childName;
      const selected = events('context.load').at(-1).attributes;
      for (const data of [selected,...(linked ? [events('skill.load').at(-1).attributes] : [])]) {
        assert.deepEqual([data[VERSION],data['fi.context.id'],data[NAME],data[id],data['fi.context.session_id'],data['fi.context.binding_id']],
          [b.version,b.snapshot.identity.resourceId,expected,'child-id',undefined,undefined]);
      }
      if (linked) assert.equal(events('skill.load')[0].attributes['fi.skill.via_context.version_id'],b.version);
      const later = events('later')[0].attributes, outside = events('outside')[0].attributes;
      assert.deepEqual([later[VERSION],later[NAME],later[id]],[b.version,standing,undefined]);
      assert.deepEqual([outside[VERSION],outside[NAME]],scoped === 'automatic' ? [b.version,'beta'] : [a.version,'alpha']);
      const child = events('child')[0].attributes;
      assert.equal(child[id],'child-id');
      assert.equal(child[NAME],scoped === 'automatic' ? expected : writer === 'automatic' ? oldName : childName);
    });
  }
}
for (const scoped of [true,false]) for (const write of [true,false]) {
  test(`standalone root, nested scope=${scoped}, explicit same string=${write}`,async () => {
    memory.reset(); mode(false,'on');
    const a = fixture('agent_context','alpha'), b = fixture('agent_context','beta');
    const run = () => new FITracer({tracer}).startActiveSpan('fi-root',async active => { try {
      await a.snapshot.readFile('AGENTS.md');
      if (write) active.setAttributes({[NAME]:'alpha'});
      active.setAttribute('test.other',true);
      const select = async () => { await b.snapshot.readFile('AGENTS.md'); tracer.startSpan('observed').end(); };
      if (scoped) await withAgentScope({agent:'inner'},select); else await select();
    } finally { active.end(); } });
    if (scoped) await withAgentScope({agent:'alpha'},run); else await run();
    const expected = scoped ? 'inner' : 'beta', event = events('context.load').at(-1).attributes;
    assert.deepEqual([event[VERSION],event[NAME]],[b.version,write ? 'alpha' : expected]);
    assert.equal(events('observed')[0].attributes[NAME],expected);
  });
}
after(async () => { delete process.env.FI_SKILLS_TRACING; configure(); await provider.shutdown(); });
