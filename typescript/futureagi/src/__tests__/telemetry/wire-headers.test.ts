import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { trace } from "@opentelemetry/api";
import { BasicTracerProvider } from "@opentelemetry/sdk-trace-base";
import { Client } from "../../platform/client";
import { ConsumptionSource } from "../../context/source";
import { configure } from "../../telemetry";
import { SDK_VERSION } from "../../telemetry/version";

const identity = { kind: "skill" as const, resourceId: "11111111-1111-4111-8111-111111111111", versionId: "22222222-2222-4222-8222-222222222222", name: "refund", version: 1, digest: `sha256:${"a".repeat(64)}` };
const lease = { resolutionId: "opaque-lease", resolutionExpiresAt: "2099-01-01T00:00:00Z" };
afterEach(() => { configure(); trace.disable(); delete process.env.FI_SKILLS_TRACING; });

it("keeps the versioned user agent aligned with the package version", () => {
  const pkg = JSON.parse(readFileSync(resolve(__dirname, "../../../package.json"), "utf8")) as { version: string };
  expect(SDK_VERSION).toBe(pkg.version);
});

it.each(["on", "load_only", "off", "no_otel", "client_off"])("reports %s only on consumption resolve", async scenario => {
  trace.disable();
  const provider = new BasicTracerProvider();
  if (scenario !== "no_otel") configure({ tracerProvider: provider, skillsTracing: scenario === "load_only" ? "load_only" : scenario === "off" ? "off" : "on" });
  const requests: RequestInit[] = [];
  const fetch = jest.fn(async (_url: string, init: RequestInit) => {
    requests.push(init);
    return new Response(JSON.stringify({ allowed: true, version_id: identity.versionId, digest: identity.digest }), { status: 200, headers: { "Content-Type": "application/json" } });
  });
  const client = new Client({ apiKey: "test-key", secretKey: "test-secret", baseUrl: "https://example.invalid", fetch, customFetchReceivesKeys: true, maxRetries: 0 });
  const source = new ConsumptionSource(client, "skill", { tracing: scenario !== "client_off" });
  try {
    await source.resolve("refund", { label: "production" });
    await source.manifest(identity, 0, { resolutionId: lease.resolutionId });
    await source.chunk(identity, "SKILL.md", 0, { resolutionId: lease.resolutionId });
    await source.checkAccess(identity, lease);
    const headers = requests.map(request => new Headers(request.headers));
    expect(headers[0].get("X-FI-Skills-Tracing")).toBe(scenario === "client_off" ? "off" : scenario);
    expect(headers.every(header => header.get("User-Agent") === `futureagi-typescript/${SDK_VERSION}`)).toBe(true);
    for (const header of headers.slice(1)) expect(header.get("X-FI-Skills-Tracing")).toBeNull();
  } finally { await provider.shutdown(); }
});
