// Run from an isolated npm fixture with the locally built SDK and traceAI tarballs.
// node packed_traceai_opt_in.mjs off|on — one provider per process (it is global).
// "off": register() without opt-in. Even with configure({skillsTracing: "on"}),
// no span gains a runtime attribute or a context agent name, as before traceAI
// had a runtime processor. "on": runtimeAttributes: true stamps and names.
import assert from "node:assert/strict";
import { InMemorySpanExporter, SimpleSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { FITracer, register } from "@traceai/fi-core";
import { configure, declareSkill, withAgentScope } from "@future-agi/sdk/telemetry";

const mode = process.argv[2];
assert.ok(mode === "off" || mode === "on");
for (const key of Object.keys(process.env)) if (/^(FI_|OTEL_)/.test(key)) delete process.env[key];
const RUNTIME = /^(fi\.skills\.|fi\.context\.|gen_ai\.agent\.)/;
const skill = { kind: "skill", resourceId: "11111111-1111-4111-8111-111111111111", versionId: "22222222-2222-4222-8222-222222222222",
  name: "sample", version: 1, digest: "sha256:" + "a".repeat(64), requested: { version: 1 } };
const exporter = new InMemorySpanExporter();
const provider = register({ projectName: "opt-in-check", ...(mode === "on" ? { runtimeAttributes: true } : {}),
  spanProcessors: [new SimpleSpanProcessor(exporter)] });
configure({ skillsTracing: "on" }); // The SDK reader alone can never opt a provider in.
try {
  const native = provider.getTracer("native"), fi = new FITracer({ tracer: provider.getTracer("fi") });
  await withAgentScope({ agent: "refund-agent" }, async () => {
    await native.startActiveSpan("root", async root => {
      try {
        declareSkill(skill);
        native.startSpan("native-child").end();
        fi.startSpan("fi-child").end();
      } finally { root.end(); }
    });
  });
  await provider.forceFlush();
  const spans = Object.fromEntries(exporter.getFinishedSpans().map(span => [span.name, { ...span.attributes }]));
  for (const name of ["root", "native-child", "fi-child"]) assert.ok(spans[name], name);
  if (mode === "off") {
    for (const name of ["root", "native-child", "fi-child"]) {
      assert.deepEqual(Object.keys(spans[name]).filter(key => RUNTIME.test(key)), [], `${name} gains no runtime attribute without opt-in`);
    }
  } else {
    for (const name of ["native-child", "fi-child"]) assert.equal(spans[name]["gen_ai.agent.name"], "refund-agent", name);
    assert.deepEqual(spans["native-child"]["fi.skills.version_ids"], [skill.versionId]);
  }
  console.log(`PASS: provider opt-in ${mode}; configure() alone does not opt in`);
} finally { await provider.shutdown(); }
