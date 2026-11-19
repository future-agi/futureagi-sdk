import { createHash } from "node:crypto";
import { context, trace, ROOT_CONTEXT, SpanStatusCode } from "@opentelemetry/api";
import { AsyncLocalStorageContextManager } from "@opentelemetry/context-async-hooks";
import { BasicTracerProvider, InMemorySpanExporter, SimpleSpanProcessor } from "@opentelemetry/sdk-trace-base";
import { ContextSnapshot, manifestDigest, SnapshotIntegrityError } from "../../context/snapshot";
import { SkillsClient } from "../../skills/client";
import type { SnapshotManifest, SnapshotSource } from "../../context/types";
import { configure, declareSkill, FutureAGISkillsSpanProcessor, status, withAgentScope } from "../../telemetry";
import { api, currentSpan, CARRIER_KEY, PROCESSOR_KEY, REGISTRY_KEY } from "../../telemetry/otel";
import { doctorText } from "../../telemetry/status";

const ID = "11111111-1111-4111-8111-111111111111";
const VERSION = "22222222-2222-4222-8222-222222222222";
const CTX = "33333333-3333-4333-8333-333333333333";
function hash(text: string) { return createHash("sha256").update(text).digest("hex"); }
function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value !== null && typeof value === "object") return `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical((value as Record<string, unknown>)[key])}`).join(",")}}`;
  return JSON.stringify(value);
}
function fixture(kind: "skill" | "agent_context" = "skill", tracing = true) {
  const files: Record<string, string> = { "SKILL.md": "policy", "reference/policy.md": "details" };
  const child = Object.entries(files).map(([path, text]) => ({ path, sha256: hash(text), sizeBytes: Buffer.byteLength(text) }));
  if (kind === "agent_context") {
    delete files["SKILL.md"]; delete files["reference/policy.md"];
    files["AGENTS.md"] = "support instructions";
    files["skills/refund/SKILL.md"] = "policy";
    files["skills/refund/reference/policy.md"] = "details";
    files[".futureagi/context.json"] = canonical({ schema: 1, kind, name: "support", entrypoint: "AGENTS.md", owned_paths: ["AGENTS.md"], links: [{ mount: "skills/refund/", skill_id: ID, version_id: VERSION, version: 3, digest: manifestDigest(child), requested: { version: 3 } }] });
  }
  const metadata = Object.entries(files).map(([path, text]) => ({ path, sha256: hash(text), sizeBytes: Buffer.byteLength(text) }));
  const manifest: SnapshotManifest = {
    identity: { kind, resourceId: ID, versionId: kind === "skill" ? VERSION : CTX, version: 3, name: kind === "skill" ? "refund" : "support", digest: manifestDigest(metadata) },
    requested: { label: "production" },
    lease: { resolutionId: "never-export-this-lease", resolutionExpiresAt: "2099-01-01T00:00:00Z" }, files: metadata,
  };
  const chunk = jest.fn(async (_id: unknown, path: string) => ({ path, sha256: hash(files[path]), size_bytes: Buffer.byteLength(files[path]), text: files[path], total_chars: Array.from(files[path]).length, offset: 0, next_offset: null, eof: true, resource_id: ID, version_id: manifest.identity.versionId, digest: manifest.identity.digest }));
  const source: SnapshotSource = { resolve: jest.fn(), manifest: jest.fn(), chunk };
  return { snapshot: new ContextSnapshot(manifest, source, { tracing }), source, chunk, manifest };
}
let exporter: InMemorySpanExporter;
let provider: BasicTracerProvider;
let manager: AsyncLocalStorageContextManager;
let info: jest.SpyInstance;
beforeEach(() => {
  trace.disable(); context.disable();
  const globals = globalThis as unknown as Record<symbol, unknown>;
  delete globals[REGISTRY_KEY]; delete globals[PROCESSOR_KEY];
  delete process.env.FI_SKILLS_TRACING;
  configure({ skillsTracing: "on" });
  exporter = new InMemorySpanExporter();
  provider = new BasicTracerProvider({ spanProcessors: [new FutureAGISkillsSpanProcessor(), new SimpleSpanProcessor(exporter)] });
  manager = new AsyncLocalStorageContextManager().enable();
  context.setGlobalContextManager(manager);
  trace.setGlobalTracerProvider(provider);
  info = jest.spyOn(console, "info").mockImplementation(() => undefined);
});
afterEach(async () => {
  configure(); trace.disable(); context.disable(); manager.disable();
  await provider.shutdown(); info.mockRestore(); delete process.env.FI_SKILLS_TRACING;
});
function loads() { return exporter.getFinishedSpans().filter(span => span.name === "skill.load"); }
async function request(callback: () => Promise<void>) {
  return provider.getTracer("test").startActiveSpan("request", async span => {
    try { await callback(); } finally { span.end(); }
  });
}

it("V2 reads the real OTel 1.x provider and context manager from their registered global", async () => {
  expect(api()?.trace).toBeDefined();
  expect(api()?.context).toBeDefined();
  await request(async () => {
    expect(currentSpan()).toBe(trace.getActiveSpan());
    expect(status().provider).toBe("global");
    await fixture().snapshot.readFile("SKILL.md");
  });
  expect(loads()).toHaveLength(1);
});

it("records the first supporting-file read, deduplicates roots, and stamps only later spans", async () => {
  const { snapshot } = fixture();
  await request(async () => {
    const before = provider.getTracer("test").startSpan("before");
    await snapshot.readFile("reference/policy.md");
    await snapshot.readFile("SKILL.md");
    expect((trace.getActiveSpan() as unknown as { attributes: Record<string, unknown> }).attributes["fi.skills.version_ids"]).toEqual([VERSION]);
    before.end();
    provider.getTracer("test").startSpan("after").end();
  });
  expect(loads()).toHaveLength(1);
  expect(loads()[0].attributes).toMatchObject({ "fi.skill.id": ID, "fi.skill.version_id": VERSION, "fi.skill.requested_label": "production", "fi.skill.load.via": "sdk.read_file", "fi.skill.load.evidence": "delivered", "fi.skill.load.cached": false, "fi.skill.load.root_file": false });
  const spans = exporter.getFinishedSpans();
  expect(spans.find(span => span.name === "before")!.attributes["fi.skills.count"]).toBeUndefined();
  expect(spans.find(span => span.name === "after")!.attributes["fi.skills.version_ids"]).toEqual([VERSION]);
  expect(spans.find(span => span.name === "after")!.attributes["fi.skill.version_id"]).toBeUndefined();
  expect(JSON.stringify(spans.map(span => span.attributes))).not.toContain("never-export-this-lease");
});

it("resolve is untraced and client options reach the resolved snapshot", async () => {
  const { manifest, source } = fixture();
  source.resolve = async () => ({
    kind: "skill", name: "refund", resource_id: ID, version_id: VERSION, version: 3,
    digest: manifest.identity.digest, requested: manifest.requested, entrypoint: "SKILL.md", descriptor_path: null,
    resolution_id: manifest.lease.resolutionId, resolution_expires_at: manifest.lease.resolutionExpiresAt,
    file_count: manifest.files.length, file_offset: 0, next_file_offset: null,
    files: manifest.files.map(file => ({ path: file.path, sha256: file.sha256, size_bytes: file.sizeBytes })),
  });
  await request(async () => {
    const snapshot = await new SkillsClient(source).resolve("refund");
    expect(loads()).toHaveLength(0);
    await snapshot.readAll({ trace: false });
    const disabled = await new SkillsClient(source, { tracing: false }).resolve("refund");
    await disabled.readAll();
  });
  expect(loads()).toHaveLength(0);
});

it("readAll emits one load; declared evidence is not hidden by delivered evidence", async () => {
  const { snapshot } = fixture();
  await request(async () => {
    const verified = await snapshot.readAll();
    declareSkill(verified); declareSkill(verified);
  });
  expect(loads()).toHaveLength(2);
  expect(loads()[0].attributes["fi.skill.load.via"]).toBe("sdk.read_all");
  expect(loads()[0].attributes["fi.skill.load.root_file"]).toBe(true);
  expect(loads()[1].attributes["fi.skill.load.evidence"]).toBe("declared");
  expect(loads()[1].attributes["fi.skill.load.cached"]).toBe(true);
});

it("does not record untraced reads and allows OTel to be registered later", async () => {
  const { snapshot } = fixture();
  trace.disable(); context.disable();
  await snapshot.readAll();
  expect(loads()).toHaveLength(0);
  context.setGlobalContextManager(manager); trace.setGlobalTracerProvider(provider);
  await request(async () => { await snapshot.readFile("SKILL.md"); });
  expect(loads()).toHaveLength(1);
});

it("context readAll records available links but no skill loads; later child reads use verified identity", async () => {
  const { snapshot, chunk } = fixture("agent_context");
  await request(async () => {
    await snapshot.readAll();
    expect(loads()).toHaveLength(0);
    await snapshot.readFile("skills/refund/reference/policy.md");
  });
  expect(chunk).toHaveBeenCalledTimes(5);
  const contextLoad = exporter.getFinishedSpans().find(span => span.name === "context.load")!;
  expect(contextLoad.attributes["fi.context.linked_skill_version_ids"]).toEqual([VERSION]);
  expect(loads()[0].attributes).toMatchObject({ "fi.skill.version_id": VERSION, "fi.skill.via_context.version_id": CTX, "fi.skill.load.via": "context.read", "fi.skill.load.root_file": false, "gen_ai.agent.name": "support", "fi.context.version_id": CTX });
});

it("does not invent a linked identity or fetch extra files for a lazy direct read", async () => {
  const { snapshot, chunk } = fixture("agent_context");
  await request(async () => { await snapshot.readFile("skills/refund/SKILL.md"); });
  expect(chunk).toHaveBeenCalledTimes(1);
  expect(loads()).toHaveLength(0); // Explicitly incomplete until consumption supplies closure metadata.
});

it("does not misattribute an unverified child failure to a skill with the context's name", async () => {
  const { snapshot, chunk } = fixture("agent_context");
  const error = new SnapshotIntegrityError("child verification failed");
  chunk.mockRejectedValue(error);
  await request(async () => { await expect(snapshot.readFile("skills/refund/SKILL.md")).rejects.toBe(error); });
  expect(loads()).toHaveLength(0); // Blocked on verified closure metadata, not reported as complete.
});

it("failed reads retain only name, selector and scope; errors are unchanged and deduplicated", async () => {
  const { snapshot, chunk } = fixture();
  const error = new SnapshotIntegrityError("secret-content-not-exported");
  chunk.mockRejectedValue(error);
  await withAgentScope({ agent: "refund-agent" }, () => request(async () => {
    await expect(snapshot.readAll()).rejects.toBe(error);
    await expect(snapshot.readAll()).rejects.toBe(error);
  }));
  expect(loads()).toHaveLength(1);
  expect(loads()[0].status.code).toBe(SpanStatusCode.ERROR);
  expect(loads()[0].attributes).toMatchObject({ "fi.skill.name": "refund", "fi.skill.requested_label": "production", "gen_ai.agent.name": "refund-agent", "error.type": "integrity" });
  for (const key of ["fi.skill.id", "fi.skill.version_id", "fi.skill.digest"]) expect(loads()[0].attributes[key]).toBeUndefined();
  expect(JSON.stringify(loads()[0].attributes)).not.toContain(error.message);
  expect(loads()[0].events).toHaveLength(0);
});

it("isolates nested contexts and concurrent agents, restores on rejection, and publishes immutable carriers", async () => {
  const { snapshot } = fixture();
  await request(async () => {
    const work = (agent: string) => withAgentScope({ agent }, async () => {
      const before = context.active().getValue(CARRIER_KEY) as { attrs: Record<string, unknown> };
      await snapshot.readAll();
      expect(before.attrs["fi.skills.count"]).toBeUndefined();
      const after = context.active().getValue(CARRIER_KEY) as { attrs: Record<string, unknown> };
      expect(Object.isFrozen(after)).toBe(true);
      expect(after.attrs["fi.skills.count"]).toBe(1);
      provider.getTracer("test").startSpan(agent).end();
    });
    await Promise.all([work("a"), work("b")]);
    expect(context.active().getValue(CARRIER_KEY)).toBeUndefined();
    const error = new Error("application rejection");
    await expect(withAgentScope({ agent: "cancelled" }, async () => { throw error; })).rejects.toBe(error);
    expect(context.active().getValue(CARRIER_KEY)).toBeUndefined();
    await withAgentScope({ agent: "parent" }, async () => {
      await snapshot.readAll();
      await withAgentScope({ context: fixture("agent_context").snapshot }, async () => {
        provider.getTracer("test").startSpan("nested-context").end();
      });
      provider.getTracer("test").startSpan("parent-restored").end();
    });
  });
  const spans = exporter.getFinishedSpans();
  expect(spans.find(span => span.name === "a")!.attributes["gen_ai.agent.name"]).toBe("a");
  expect(spans.find(span => span.name === "b")!.attributes["gen_ai.agent.name"]).toBe("b");
  expect(spans.find(span => span.name === "nested-context")!.attributes["fi.skills.count"]).toBeUndefined();
  expect(spans.find(span => span.name === "parent-restored")!.attributes["fi.skills.count"]).toBe(1);
});

it.each(["client", "call", "environment", "programmatic"])("respects %s opt-out", async control => {
  const { snapshot } = fixture("skill", control !== "client");
  if (control === "environment") { configure(); process.env.FI_SKILLS_TRACING = "off"; }
  if (control === "programmatic") configure({ skillsTracing: "off" });
  await request(async () => { await snapshot.readAll({ trace: control !== "call" }); });
  expect(loads()).toHaveLength(0);
  if (control === "environment" || control === "programmatic") expect(info).not.toHaveBeenCalled();
});

it("load_only emits direct scope identity without enriching current/later spans or shared registry", async () => {
  configure({ skillsTracing: "load_only" });
  const { snapshot } = fixture();
  await withAgentScope({ agent: "refund-agent" }, () => request(async () => {
    await Promise.all([snapshot.readAll(), snapshot.readAll()]);
    provider.getTracer("test").startSpan("after").end();
  }));
  expect(loads()).toHaveLength(1);
  expect(loads()[0].attributes["gen_ai.agent.name"]).toBe("refund-agent");
  expect((globalThis as unknown as Record<symbol, unknown>)[REGISTRY_KEY]).toBeUndefined();
  for (const span of exporter.getFinishedSpans().filter(span => span.name !== "skill.load")) expect(span.attributes).toEqual({});
});

it("configure wins over the environment and a configured non-global provider records", async () => {
  trace.disable(); process.env.FI_SKILLS_TRACING = "off";
  configure({ tracerProvider: provider, skillsTracing: "on" });
  await request(async () => { await fixture().snapshot.readAll(); expect(status().provider).toBe("configured"); });
  expect(loads()).toHaveLength(1);
});

it("bridge failures never replace delivered bytes or application errors", async () => {
  const { snapshot } = fixture();
  configure({ tracerProvider: { getTracer() { throw new Error("bridge-secret"); } } });
  await request(async () => { expect(await snapshot.readFile("SKILL.md")).toBe("policy"); });
  expect(loads()).toHaveLength(0);
});

it("status and doctor report mode, rule and actionable diagnostics without identities", async () => {
  await withAgentScope({ agent: "private-agent-name" }, () => request(async () => {
    await fixture().snapshot.readAll();
    const facts = status();
    expect(facts.otel_found).toBe(true);
    expect(facts.processor_installed).toBe(true);
    expect(facts.last_load).toMatchObject({ name: "refund", version: 3, evidence: "delivered" });
    expect(doctorText()).not.toContain("private-agent-name");
    expect(doctorText()).toContain("first read of any file");
  }));
});

it("automatic sibling reads deduplicate in load_only without publishing a scope registry", async () => {
  configure({ skillsTracing: "load_only" });
  const { snapshot } = fixture();
  await request(async () => { await Promise.all([snapshot.readFile("SKILL.md"), snapshot.readAll()]); });
  expect(loads()).toHaveLength(1);
  expect((globalThis as unknown as Record<symbol, unknown>)[REGISTRY_KEY]).toBeUndefined();
});

it("a vanilla provider without the processor emits loads but leaves later spans unstamped", async () => {
  const localExporter = new InMemorySpanExporter();
  const local = new BasicTracerProvider({ spanProcessors: [new SimpleSpanProcessor(localExporter)] });
  configure({ tracerProvider: local });
  try {
    await local.getTracer("test").startActiveSpan("vanilla", async span => {
      await fixture().snapshot.readAll();
      local.getTracer("test").startSpan("later").end();
      expect(status().processor_installed).toBe(false);
      span.end();
    });
    expect(localExporter.getFinishedSpans().filter(span => span.name === "skill.load")).toHaveLength(1);
    expect(localExporter.getFinishedSpans().find(span => span.name === "later")!.attributes).toEqual({});
  } finally { await local.shutdown(); }
});

it("an undiscoverable non-global provider enriches current without fabricating load evidence", async () => {
  trace.disable();
  await request(async () => {
    await fixture().snapshot.readAll();
    expect((trace.getActiveSpan() as unknown as { attributes: Record<string, unknown> }).attributes["fi.skills.count"]).toBe(1);
  });
  expect(loads()).toHaveLength(0);
});

it.each([[401, "authorization"], [403, "authorization"], [404, "not_found"], [500, "other"]])("maps HTTP %s failures without exporting their bodies", async (httpStatus, expected) => {
  const { snapshot, chunk } = fixture();
  const error = Object.assign(new Error("private-response-body"), { status: httpStatus });
  chunk.mockRejectedValue(error);
  await request(async () => { await expect(snapshot.readFile("SKILL.md")).rejects.toBe(error); });
  expect(loads()[0].attributes["error.type"]).toBe(expected);
  expect(loads()[0].attributes["fi.skill.version_id"]).toBeUndefined();
});

it("reports an expired lease as failure and does not make a network read", async () => {
  const { manifest, source, chunk } = fixture();
  const snapshot = new ContextSnapshot({ ...manifest, lease: { ...manifest.lease, resolutionExpiresAt: "2000-01-01T00:00:00Z" } }, source);
  await request(async () => { await expect(snapshot.readAll()).rejects.toThrow(); });
  expect(chunk).not.toHaveBeenCalled();
  expect(loads()[0].attributes["error.type"]).toBe("lease");
});

it("keeps explicit span agent names and accepts no-op sampling without loads", async () => {
  await withAgentScope({ agent: "parent" }, () => provider.getTracer("test").startActiveSpan("framework", { attributes: { "gen_ai.agent.name": "child" } }, async span => {
    await fixture().snapshot.readAll(); span.end();
  }));
  expect(loads()[0].attributes["gen_ai.agent.name"]).toBe("child");
  expect(exporter.getFinishedSpans().find(span => span.name === "framework")!.attributes["gen_ai.agent.name"]).toBe("child");
  const count = loads().length;
  await context.with(trace.setSpanContext(ROOT_CONTEXT, { traceId: "a".repeat(32), spanId: "b".repeat(16), traceFlags: 0 }), async () => { await fixture().snapshot.readAll(); });
  expect(loads()).toHaveLength(count);
});
