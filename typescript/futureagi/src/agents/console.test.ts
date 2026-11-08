import { FutureAGIClient } from "../futureagi-client";
import { ConfigurationError, FutureAGIAPIError } from "../_core/errors";

const cases: [string, unknown[], string, string, unknown, boolean][] = [
  ["agents.list", [], "GET", "/workspace/workforce", undefined, false],
  ["agents.get", ["a b"], "GET", "/workspace/workforce/agents/a%20b", undefined, false],
  ["agents.create", [], "POST", "/workspace/workforce/agents", { name: "Agent", role: "Analyst", purpose: "Review", responsibilities: [], workMode: "on_demand", connectorBindingIds: [] }, false],
  ["agents.update", ["a"], "PATCH", "/workspace/workforce/agents/a", { purpose: "New", expectedVersion: 2, environmentId: null, environmentRevision: null }, false],
  ["agents.retire", ["a"], "DELETE", "/workspace/workforce/agents/a", undefined, false],
  ["agents.draft", [], "POST", "/workspace/workforce/agent-drafts", { message: "Draft" }, true],
  ["agents.revisions", ["a"], "GET", "/workspace/workforce/agents/a/revisions", undefined, false],
  ["agents.rollbackRevision", ["a", 2], "POST", "/workspace/workforce/agents/a/revisions/2/rollback", { expectedVersion: 3 }, true],
  ["agents.releases", ["a"], "GET", "/workspace/workforce/agents/a/deployments", undefined, false],
  ["agents.rollbackRelease", ["a", 2], "POST", "/workspace/workforce/agents/a/deployments/2/rollback", { expectedDeploymentVersion: 3, expectedProcessId: "p" }, true],
  ["agents.schedules.list", [], "GET", "/workspace/schedules", undefined, false],
  ["agents.schedules.get", ["s"], "GET", "/workspace/schedules/s", undefined, false],
  ["agents.schedules.create", [], "POST", "/workspace/schedules", { prompt: "Review", cadence: "daily", enabled: false }, true],
  ["agents.schedules.update", ["s"], "PATCH", "/workspace/schedules/s", { enabled: false }, false],
  ["agents.schedules.delete", ["s"], "DELETE", "/workspace/schedules/s", undefined, false],
  ["agents.schedules.runNow", ["s"], "POST", "/workspace/schedules/s/run", {}, true],
  ["environments.list", [], "GET", "/workspace/environments", undefined, false],
  ["environments.get", ["e"], "GET", "/workspace/environments/e", undefined, false],
  ["environments.create", [], "POST", "/workspace/environments", { name: "Local", sandboxKind: "local", resourcePreset: "small", browserOrigins: [], credentialBindingIds: [] }, true],
  ["environments.revisions", ["e"], "GET", "/workspace/environments/e/revisions", undefined, false],
  ["environments.getRevision", ["e", 2], "GET", "/workspace/environments/e/revisions/2", undefined, false],
  ["environments.revise", ["e"], "POST", "/workspace/environments/e/revisions", { name: "Local", sandboxKind: "local", resourcePreset: "small", browserOrigins: [], credentialBindingIds: [], baseRevision: 1 }, true],
  ["environments.control", ["e"], "POST", "/workspace/environments/e/control", { action: "pause", expectedRevision: 2 }, true],
];

function make(fetch_: typeof fetch, retries = 0): FutureAGIClient {
  return new FutureAGIClient({ apiKey: "person-key", secretKey: "person-secret", baseUrl: "http://127.0.0.1:1",
    organizationId: "org-a", workspaceId: "ws-a", fetch: fetch_, retries });
}
function invoke(client: FutureAGIClient, name: string, args: unknown[], options: unknown = {}): Promise<unknown> {
  const parts = name.split(".");
  let target: any = client;
  for (const part of parts.slice(0, -1)) target = target[part];
  return target[parts[parts.length - 1]!]!(...args, options);
}

test.each(cases)("%s sends the declared request and retains unknown response fields", async (name, args, method, path, body, keyed) => {
  const calls: Request[] = [];
  const response = { schemaVersion: "future-version", unknown: { kept: true }, items: [] };
  const fetch_ = jest.fn(async (input: RequestInfo | URL) => {
    const request = input as Request;
    calls.push(request);
    expect(request.method).toBe(method);
    expect(new URL(request.url).pathname).toBe("/omega/api" + path);
    expect(request.headers.get("X-Api-Key")).toBe("person-key");
    expect(request.headers.get("X-Secret-Key")).toBe("person-secret");
    expect(request.headers.get("X-Organization-Id")).toBe("org-a");
    expect(request.headers.get("X-Workspace-Id")).toBe("ws-a");
    expect(request.headers.has("Idempotency-Key")).toBe(keyed);
    expect(request.redirect).toBe("manual");
    const text = await request.text();
    expect(text ? JSON.parse(text) : undefined).toEqual(body);
    return new Response(JSON.stringify(response));
  }) as unknown as typeof fetch;
  const result = await invoke(make(fetch_), name, args, { ...(body !== undefined ? { body } : {}),
    ...(keyed ? { idempotencyKey: "retry-the-same-write" } : {}), timeoutMs: 4000 });
  expect(result).toEqual(response);
  expect(calls).toHaveLength(1);
});

for (const status of [400, 401, 403, 404, 409, 422, 429, 503]) {
  test.each(cases)(`%s preserves HTTP ${status} as a typed error`, async (name, args, _method, _path, body) => {
    const fetch_ = jest.fn(async () => new Response(JSON.stringify({ error: { code: "refused", message: "refused" } }), { status }));
    try {
      await invoke(make(fetch_ as typeof fetch), name, args, body !== undefined ? { body } : {});
      throw new Error("request should fail");
    } catch (error) {
      expect(error).toBeInstanceOf(FutureAGIAPIError);
      expect((error as FutureAGIAPIError).statusCode).toBe(status);
    }
    expect(fetch_).toHaveBeenCalledTimes(1);
  });
}

test("schedule body identity becomes its header without mutating caller input", async () => {
  const fetch_ = jest.fn(async (input: RequestInfo | URL) => {
    expect((input as Request).headers.get("Idempotency-Key")).toBe("body-key");
    return new Response("{}");
  });
  const client = make(fetch_ as typeof fetch);
  const options = { body: { idempotencyKey: "body-key" } };
  await client.agents.schedules.runNow("s", options);
  expect(options).toEqual({ body: { idempotencyKey: "body-key" } });
  expect(() => client.agents.schedules.runNow("s", { ...options, idempotencyKey: "different" })).toThrow(ConfigurationError);
  expect(fetch_).toHaveBeenCalledTimes(1);
});

test.each([0, -1, 1.5, Number.MAX_SAFE_INTEGER + 1, NaN])("revision %s is refused before HTTP", (version) => {
  const fetch_ = jest.fn();
  expect(() => make(fetch_ as typeof fetch).agents.rollbackRevision("a", version)).toThrow(ConfigurationError);
  expect(fetch_).not.toHaveBeenCalled();
});

test("withOptions uses the same fetch and request metadata remains available", async () => {
  const fetch_ = jest.fn(async () => new Response("{\"agents\":[]}", { headers: { "x-request-id": "req-test" } }));
  const client = make(fetch_ as typeof fetch);
  const quick = client.withOptions({ timeoutMs: 2000 });
  const result = await quick.agents.list().withResponse();
  expect(result.data).toEqual({ agents: [] });
  expect(result.meta.requestId).toBe("req-test");
  await quick.environments.list();
  await quick.agents.schedules.list();
  expect(fetch_).toHaveBeenCalledTimes(3);
});

test("portable-definition preview is not offered in TypeScript", () => {
  const fetch_ = jest.fn();
  expect("code" in make(fetch_ as typeof fetch).agents).toBe(false);
  expect(fetch_).not.toHaveBeenCalled();
});

test("unsafe create does not retry a server failure", async () => {
  const fetch_ = jest.fn(async () => new Response("{}", { status: 503 }));
  await expect(invoke(make(fetch_ as typeof fetch, 1), "agents.create", [], { body: cases[2]![4] })).rejects.toBeInstanceOf(FutureAGIAPIError);
  expect(fetch_).toHaveBeenCalledTimes(1);
});
