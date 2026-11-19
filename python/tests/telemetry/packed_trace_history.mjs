// Isolated packed consumer; only transport is synthetic. No direct hook calls.
import assert from 'node:assert/strict';
import { createHash, randomUUID } from 'node:crypto';
import { createRequire } from 'node:module';
import { after, test } from 'node:test';
import { trace } from '@opentelemetry/api';
import { InMemorySpanExporter, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
const require = createRequire(import.meta.url);
const load = (form, name) => form === 'cjs' ? require(name) : import(name);
const [coreForm, sdkForm] = process.argv.slice(2);
const {register} = await load(coreForm, '@traceai/fi-core');
const {ContextSnapshot, SnapshotIntegrityError} = await load(sdkForm, '@future-agi/sdk/context');
const {configure, withAgentScope, declareSkill} = await load(sdkForm === 'esm' ? 'cjs' : 'esm', '@future-agi/sdk/telemetry');
const memory = new InMemorySpanExporter();
const provider = register({projectName: 'history', spanProcessors: [new SimpleSpanProcessor(memory)]});
const tracer = trace.getTracer('history');
const hash = v => createHash('sha256').update(v).digest('hex');
function fixture(kind, name, tracing = true) {
  const files = kind === 'skill' ? {'SKILL.md': 'root', 'reference/help.md': 'help'} : {'AGENTS.md': name};
  const metadata = Object.entries(files).map(([path, text]) => ({path, sha256: hash(text), sizeBytes: text.length}));
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
function request(name, scoped, body) {
  return tracer.startActiveSpan(name, async parent => {
    try { return await (scoped ? withAgentScope({agent: 'explicit'}, () => body(parent)) : body(parent)); }
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
        mode(env, selected); await context.snapshot.readFile('AGENTS.md'); mode(env, 'on');
        assert.equal(observer('fi.context.version_id'), propagated.version);
        assert.equal(observer('gen_ai.agent.name'), scoped ? 'explicit' : propagated.snapshot.identity.name);
        assert.equal(parent.attributes['fi.context.version_id'], scoped ? undefined : propagated.version);
      }
      assert.deepEqual(events('context.load').map(s => s.attributes['fi.context.version_id']), [a.version,b.version]);
    });
  });
}
after(async () => { delete process.env.FI_SKILLS_TRACING; configure(); await provider.shutdown(); });
