/** The root client composes the exact platform and connector contracts and shares them on copies. */
import { FutureAGIClient } from "../../futureagi-client";
import { PLATFORM_OPERATIONS } from "../../generated/platform/policy.gen";
import { CONNECTOR_OPERATIONS } from "../connector-policy";
import { json, OPS, Script } from "../__fixtures__/platform";
import { NotFoundError, PlatformNotConfiguredError } from "../errors";

const CAPABILITIES = "platform.capabilities.get";

function client(script: Script): FutureAGIClient {
  return new FutureAGIClient({
    apiKey: "k-test-1234",
    secretKey: "s-test-1234",
    baseUrl: "http://127.0.0.1:9",
    workspaceId: "ws-test",
    organizationId: "org-test",
    retries: 0,
    fetch: script.fetch,
  });
}

describe("the root client's platform contract", () => {
  it("dispatches a canonical operation with metadata and selector headers", async () => {
    const script = new Script([json(200, { products: [] }, { "x-request-id": "req-contract" })]);
    const c = client(script);
    const features = require("../../../../../openapi/connectors/features.json");
    const overlap = Object.keys(CONNECTOR_OPERATIONS).filter((name) => name in PLATFORM_OPERATIONS).sort();
    expect(overlap).toEqual(features.credential_reads ? [
      "platform.credentials.bindings", "platform.credentials.get", "platform.credentials.list",
    ] : []);
    const connectorRows = new Map(Object.entries(CONNECTOR_OPERATIONS));
    const platformRows = new Map(Object.entries(PLATFORM_OPERATIONS));
    for (const name of overlap) expect(connectorRows.get(name)).toEqual(platformRows.get(name));
    for (const [name, operation] of Object.entries(PLATFORM_OPERATIONS)) {
      expect(c._platform.shared.table![name]).toEqual(operation);
      expect(c._platform.shared.table![name]).toBe(operation);
    }
    const composed = { ...CONNECTOR_OPERATIONS, ...PLATFORM_OPERATIONS };
    expect(c._platform.shared.table).toEqual(composed);
    for (const [name, operation] of Object.entries(composed)) {
      expect(c._platform.shared.table![name]).toBe(operation);
    }
    expect(script.requests).toHaveLength(0);
    const response = await c._platform.call(CAPABILITIES).withResponse();
    expect(response.data).toEqual({ products: [] });
    expect(response.meta.operation).toBe(CAPABILITIES);
    expect(response.requestId).toBe("req-contract");
    expect(script.requests).toHaveLength(1);
    const request = script.requests[0]!;
    const operation = PLATFORM_OPERATIONS[CAPABILITIES];
    expect(request.method).toBe(operation.method);
    expect(request.url).toBe(`http://127.0.0.1:9/omega/api${operation.path}`);
    expect(request.headers.get("x-api-key")).toBe("k-test-1234");
    expect(request.headers.get("x-secret-key")).toBe("s-test-1234");
    expect(request.headers.get("x-workspace-id")).toBe("ws-test");
    expect(request.headers.get("x-organization-id")).toBe("org-test");
    expect(request.headers.has("idempotency-key")).toBe(false);
  });

  it("keeps the generated contract on copies made before the first request", async () => {
    const script = new Script([json(200, {})]);
    const c = client(script);
    const quick = c.withOptions({ timeoutMs: 500, retries: 0 });
    await quick._platform.call(CAPABILITIES);
    await c._platform.call(CAPABILITIES);
    expect(script.requests).toHaveLength(2);
    expect(quick._platform.shared).toBe(c._platform.shared);
    const composed = { ...CONNECTOR_OPERATIONS, ...PLATFORM_OPERATIONS };
    expect(quick._platform.shared.table).toEqual(composed);
    expect(quick._platform.shared.table).toBe(c._platform.shared.table);
    for (const [name, operation] of Object.entries(composed)) {
      expect(quick._platform.shared.table![name]).toBe(operation);
    }
    expect(quick._platform.settings.timeoutMs).toBe(500);
    expect(c._platform.settings.timeoutMs).toBe(30_000);
    for (const request of script.requests) {
      expect(request.method).toBe(PLATFORM_OPERATIONS[CAPABILITIES].method);
      expect(request.url).toBe(`http://127.0.0.1:9/omega/api${PLATFORM_OPERATIONS[CAPABILITIES].path}`);
      expect(request.headers.get("x-api-key")).toBe("k-test-1234");
      expect(request.headers.get("x-secret-key")).toBe("s-test-1234");
      expect(request.headers.get("x-workspace-id")).toBe("ws-test");
      expect(request.headers.get("x-organization-id")).toBe("org-test");
      expect(request.headers.has("idempotency-key")).toBe(false);
    }
  });

  it("maps a server error through the generated operation", async () => {
    const script = new Script([json(404, { code: "not_found" })]);
    await expect(client(script)._platform.call(CAPABILITIES)).rejects.toBeInstanceOf(NotFoundError);
    expect(script.requests).toHaveLength(1);
  });

  it("rejects unknown operation names before sending", async () => {
    const script = new Script([json(200, {})]);
    await expect(client(script)._platform.call("not.an.operation")).rejects.toBeInstanceOf(PlatformNotConfiguredError);
    expect(script.requests).toHaveLength(0);
  });

  it("uses the contract's capabilities name in the fixture too", () => {
    const fixture = OPS[CAPABILITIES]!;
    const generated = PLATFORM_OPERATIONS[CAPABILITIES];
    expect([fixture.name, fixture.method, fixture.path]).toEqual([generated.name, generated.method, generated.path]);
  });
});
