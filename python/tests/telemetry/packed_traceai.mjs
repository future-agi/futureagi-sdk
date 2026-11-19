// Run from an isolated npm fixture with the three locally built tarballs installed.
// No remote exporters or application credentials: all spans stay in memory.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { trace } from "@opentelemetry/api";
import { InMemorySpanExporter, SimpleSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { register } from "@traceai/fi-core";
import { ContextSnapshot } from "@future-agi/sdk/context";
import { configure, withAgentScope } from "@future-agi/sdk/telemetry";

const mode = process.argv[2];
assert.ok(["on", "load_only", "off"].includes(mode));
configure({ skillsTracing: mode });
const exporter = new InMemorySpanExporter();
const provider = register({
  projectName: "synthetic-package-qualification",
  spanProcessors: [new SimpleSpanProcessor(exporter)],
});
const text = "verified policy";
const sha256 = createHash("sha256").update(text).digest("hex");
const versionId = "22222222-2222-4222-8222-222222222222";
const identity = {
  kind: "skill", resourceId: "11111111-1111-4111-8111-111111111111",
  versionId, version: 1, name: "refund",
  digest: "sha256:" + createHash("sha256").update(JSON.stringify([["SKILL.md", sha256]])).digest("hex"),
};
let reads = 0;
const snapshot = new ContextSnapshot({
  identity, requested: { label: "production" },
  lease: { resolutionId: "opaque", resolutionExpiresAt: "2099-01-01T00:00:00Z" },
  files: [{ path: "SKILL.md", sha256, sizeBytes: Buffer.byteLength(text) }],
}, {
  chunk: async () => {
    reads++;
    return {
      path: "SKILL.md", sha256, size_bytes: Buffer.byteLength(text), text,
      total_chars: text.length, offset: 0, next_offset: null, eof: true,
      resource_id: identity.resourceId, version_id: versionId, digest: identity.digest,
    };
  },
});
try {
  await withAgentScope({ agent: "refund-agent" }, async () => {
    await trace.getTracer("packed-sdk").startActiveSpan("request", async span => {
      try {
        assert.equal((await snapshot.readAll()).files["SKILL.md"], text);
        trace.getTracer("packed-sdk").startSpan("after-load").end();
      } finally { span.end(); }
    });
  });
  await provider.forceFlush();
  const spans = exporter.getFinishedSpans();
  const loads = spans.filter(span => span.name === "skill.load");
  assert.equal(loads.length, mode === "off" ? 0 : 1);
  assert.equal(reads, 1);
  const after = spans.find(span => span.name === "after-load");
  assert.ok(after);
  if (mode === "on") {
    assert.deepEqual(after.attributes["fi.skills.version_ids"], [versionId]);
    assert.equal(after.attributes["gen_ai.agent.name"], "refund-agent");
  } else {
    assert.equal(after.attributes["fi.skills.version_ids"], undefined);
    assert.equal(after.attributes["gen_ai.agent.name"], undefined);
  }
  assert.equal(after.attributes["fi.skill.version_id"], undefined);
  if (loads.length) {
    assert.equal(loads[0].attributes["fi.skill.version_id"], versionId);
    assert.equal(loads[0].attributes["fi.skill.load.evidence"], "delivered");
  }
  console.log(`PASS packed SDK + traceAI (${mode}): ${spans.length} spans, ${reads} content read`);
} finally { await provider.shutdown(); }
