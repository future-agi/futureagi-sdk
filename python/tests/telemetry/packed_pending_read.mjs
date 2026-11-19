// Run in an isolated consumer with both tarballs installed. Only transport is
// synthetic: the public reader verifies actual bytes and completes its own hook.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { trace } from '@opentelemetry/api';
import { InMemorySpanExporter, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { test, after } from 'node:test';
const require = createRequire(import.meta.url);
const [coreForm, sdkForm] = process.argv.slice(2);
const load = (form, name) => form === 'cjs' ? require(name) : import(name);
const core = await load(coreForm, '@traceai/fi-core');
const { configure, withAgentScope } = await load(sdkForm === 'cjs' ? 'esm' : 'cjs', '@future-agi/sdk/telemetry');
const { ContextSnapshot } = await load(sdkForm, '@future-agi/sdk/context');
const exporter = new InMemorySpanExporter();
const provider = core.register({projectName: 'pending-read', spanProcessors: [new SimpleSpanProcessor(exporter)]});
const tracer = trace.getTracer('pending');
const key = 'fi.skills.version_ids';
const versionId = '22222222-2222-4222-8222-222222222222';
const hash = value => createHash('sha256').update(value).digest('hex');
function pendingRead() {
  const entered = Promise.withResolvers(), resume = Promise.withResolvers();
  const text = 'verified', sha256 = hash(text);
  const identity = {kind: 'skill', resourceId: '11111111-1111-4111-8111-111111111111', versionId,
    version: 1, name: 'sample', digest: 'sha256:' + hash(JSON.stringify([['SKILL.md', sha256]]))};
  const snapshot = new ContextSnapshot({identity, requested: {version: 1},
    lease: {resolutionId: 'fixture', resolutionExpiresAt: '2099-01-01T00:00:00Z'},
    files: [{path: 'SKILL.md', sha256, sizeBytes: text.length}]}, {
    async chunk() {
      entered.resolve(); await resume.promise;
      return {resource_id: identity.resourceId, version_id: versionId, digest: identity.digest,
        path: 'SKILL.md', sha256, size_bytes: text.length, text, total_chars: text.length, offset: 0, next_offset: null, eof: true};
    },
  });
  return {snapshot, entered: entered.promise, release: resume.resolve, text};
}
function apply(source, value) {
  if (source === 'explicit') {
    process.env.FI_SKILLS_TRACING = value === 'off' ? 'on' : 'off';
    configure({skillsTracing: value});
  } else {
    process.env.FI_SKILLS_TRACING = value;
    configure();
  }
}
for (const [source, next] of [['explicit', 'explicit'], ['environment', 'environment'],
  ['explicit', 'environment'], ['environment', 'explicit']]) {
  for (const [start, end] of [['on', 'load_only'], ['load_only', 'on'], ['on', 'off'], ['load_only', 'off'], ['off', 'on']]) {
    for (const scoped of [false, true]) test(`${source}->${next} ${start}->${end} scoped=${scoped}`, async () => {
      exporter.reset(); apply(source, start);
      const {snapshot, entered, release, text} = pendingRead();
      const consume = () => tracer.startActiveSpan('parent', async parent => {
        try {
          const read = snapshot.readFile('SKILL.md');
          await entered;
          if (source === 'environment' && next === source) process.env.FI_SKILLS_TRACING = end;
          else apply(next, end);
          release();
          assert.equal(await read, text);
          apply(source, 'on');
          tracer.startSpan('later').end();
        } finally { parent.end(); }
      });
      if (scoped) await withAgentScope({agent: 'test-agent'}, consume); else await consume();
      const spans = exporter.getFinishedSpans();
      const loads = spans.filter(s => s.name === 'skill.load');
      const parent = spans.find(s => s.name === 'parent');
      const later = spans.find(s => s.name === 'later');
      assert.ok(parent && later);
      assert.ok(spans.every(s => s.spanContext().traceId === parent.spanContext().traceId));
      const enabled = start !== 'off' && end !== 'off';
      assert.equal(loads.length, enabled ? 1 : 0);
      if (enabled) {
        assert.equal(loads[0].attributes['fi.skill.version_id'], versionId);
        assert.equal(loads[0].attributes['fi.skill.load.evidence'], 'delivered');
        if (scoped) assert.equal(loads[0].attributes['gen_ai.agent.name'], 'test-agent');
      }
      assert.deepEqual(later.attributes[key], enabled && end === 'on' ? [versionId] : undefined);
      assert.deepEqual(parent.attributes[key], enabled && end === 'on' && !scoped ? [versionId] : undefined);
    });
  }
}
after(async () => { delete process.env.FI_SKILLS_TRACING; configure(); await provider.shutdown(); });
