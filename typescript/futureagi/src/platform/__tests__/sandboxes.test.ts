/**
 * `client.sandboxes` (src/platform/resources/sandboxes.ts) against a mock API driven by the scoped contract
 * (src/sandbox/__fixtures__/openapi-mock.ts): every wrapped operation under its `x-omega-sdk` name, the retry
 * rules, the sandbox error classes, both credential modes and their scope headers, no default host, the HTTPS
 * rule, the self-hosted origin opt-in (`allowCustomBaseUrl`), redirect privacy and the exec stream's SSE framing.
 * Synthetic credentials only; no socket.
 */
import { FutureAGIClient, type FutureAGIClientOptions } from "../../futureagi-client";
import * as E from "../../_core/errors";
import { PLATFORM_OPERATIONS } from "../../generated/platform/policy.gen";
import {
  ConflictError,
  QuotaExceededError,
  Sandbox,
  SandboxConnectionError,
  SandboxError,
  SandboxHibernatedError,
  SandboxStateError,
  UnavailableError,
} from "../../sandbox";
import { EXEC, SID, SID2, SNAP, SandboxApi, json, sseText, streamed } from "../../sandbox/__fixtures__/openapi-mock";
import { type ExecFrame, Sandboxes } from "../resources/sandboxes";

const API_KEY = "sbx-test-api-key-not-valid";
const SECRET_KEY = "sbx-test-secret-key-not-valid";
const TOKEN = "sbx-test-bearer-token-not-valid";
const ENV = [
  "FI_BASE_URL", "FI_PLATFORM_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_TOKEN", "FI_WORKSPACE_ID",
  "FI_ORGANIZATION_ID", "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS",
  "OMEGA_BASE_URL", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
];

let saved: [string, string | undefined][] = [];
let api: SandboxApi;
let warn: jest.SpyInstance;
beforeEach(() => {
  saved = ENV.map((key) => [key, process.env[key]]);
  for (const key of ENV) delete process.env[key];
  warn = jest.spyOn(console, "warn").mockImplementation(() => undefined);
  api = new SandboxApi();
});
afterEach(() => {
  warn.mockRestore();
  for (const [key, value] of saved) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  expect(api.problems).toEqual([]);
});

/** A client on the mock. A Bearer client on the (non-loopback) mock host opts in with `allowCustomBaseUrl`. */
function client(mode: "keys" | "bearer" = "keys", options: FutureAGIClientOptions = {}, target: SandboxApi = api): FutureAGIClient {
  const c = new FutureAGIClient({
    ...(mode === "keys" ? { apiKey: API_KEY, secretKey: SECRET_KEY } : { platformToken: TOKEN, allowCustomBaseUrl: true }),
    platformBaseUrl: target.base,
    fetch: target.fetch,
    ...options,
  });
  Object.assign(c._platform.shared, { sleep: async () => undefined });
  return c;
}

async function drain(stream: AsyncIterable<ExecFrame>): Promise<ExecFrame[]> {
  const frames: ExecFrame[] = [];
  for await (const frame of stream) frames.push(frame);
  return frames;
}

const failure = (call: () => PromiseLike<unknown>): Promise<unknown> => Promise.resolve().then(call).then(() => undefined, (e: unknown) => e);

/** One call per contract operation, keyed by operationId, through the generated-layer name. */
const CALLS: Readonly<Record<string, (s: Sandboxes) => PromiseLike<unknown>>> = {
  listWorkspaceSandboxes: (s) => s.list(),
  createWorkspaceSandbox: (s) => s.create({ body: { name: "demo", size: "small" } }),
  getWorkspaceSandboxSettings: (s) => s.settings.get(),
  getWorkspaceSandbox: (s) => s.getInfo(SID),
  updateWorkspaceSandbox: (s) => s.update(SID, { body: { name: "renamed", idleTtlSeconds: 600 } }),
  destroyWorkspaceSandbox: (s) => s.kill(SID),
  getWorkspaceSandboxNetworkPolicy: (s) => s.networkPolicy.get(SID),
  putWorkspaceSandboxNetworkPolicy: (s) => s.networkPolicy.update(SID, { body: { version: 1, mode: "off" }, ifMatch: '"0"' }),
  listWorkspaceSandboxFiles: (s) => s.files.list(SID, { path: "src" }),
  readWorkspaceSandboxFile: (s) => s.files.read(SID, "dir/a b.txt", { maxBytes: 10 }),
  writeWorkspaceSandboxFile: (s) => s.files.write(SID, "dir/a b.txt", { body: { content: "hi", encoding: "utf8" } }),
  deleteWorkspaceSandboxPath: (s) => s.files.remove(SID, "dir", { recursive: true }),
  downloadWorkspaceSandboxFile: (s) => s.files.download(SID, "dir/a b.txt"),
  uploadWorkspaceSandboxFile: (s) => s.files.upload(SID, "dir/a b.txt", { body: new Uint8Array([1, 2, 3]) }),
  moveWorkspaceSandboxPath: (s) => s.files.rename(SID, { body: { from: "a.txt", to: "b.txt" } }),
  createWorkspaceSandboxFolder: (s) => s.files.makeDir(SID, "dir/sub"),
  listWorkspaceSandboxSnapshots: (s) => s.snapshots.list(SID),
  snapshotWorkspaceSandbox: (s) => s.snapshots.create(SID),
  restoreWorkspaceSandboxSnapshot: (s) => s.snapshots.restore(SID, SNAP),
  listWorkspaceSandboxActivity: (s) => s.activity.list(SID),
  hibernateWorkspaceSandbox: (s) => s.hibernate(SID),
  resumeWorkspaceSandbox: (s) => s.resume(SID),
  execInWorkspaceSandbox: async (s) => drain(await s.commands.run(SID, { body: { command: "echo hello" } })),
  cancelWorkspaceSandboxExec: (s) => s.commands.cancel(SID, EXEC),
};

/** The value at a dotted path under `client.sandboxes` (`files.makeDir`). */
function at(root: unknown, dotted: string): unknown {
  let node: unknown = root;
  for (const part of dotted.split(".")) node = node === null || node === undefined ? undefined : (node as Record<string, unknown>)[part];
  return node;
}

describe("the contract, the generated table and the generated-layer names", () => {
  it("wraps every sandbox operation but the human-only settings update", () => {
    const wrapped = api.operations.filter((o) => !o.humanOnly);
    expect(wrapped.map((o) => o.operationId).sort()).toEqual(Object.keys(CALLS).sort());
    expect(wrapped).toHaveLength(24);
    for (const o of wrapped) {
      const entry = (PLATFORM_OPERATIONS as Record<string, { operationId?: string }>)[o.sdkName];
      expect([o.sdkName, entry?.operationId]).toEqual([o.sdkName, o.operationId]);
    }
    expect((PLATFORM_OPERATIONS as Record<string, unknown>)["sandboxes.settings.update"]).toBeUndefined();
  });

  it("names each method by its x-omega-sdk method", () => {
    const s = client().sandboxes;
    for (const o of api.operations.filter((op) => !op.humanOnly)) {
      const method = o.sdkName.slice("sandboxes.".length);
      expect([method, typeof at(s, method)]).toEqual([method, "function"]);
    }
    expect(
      ["list", "create", "settings.get", "getInfo", "update", "kill", "networkPolicy.get", "networkPolicy.update", "files.list",
        "files.read", "files.write", "files.remove", "files.download", "files.upload", "files.rename", "files.makeDir",
        "snapshots.list", "snapshots.create", "snapshots.restore", "activity.list", "hibernate", "resume", "commands.run",
        "commands.cancel"].filter((name) => typeof at(s, name) !== "function"),
    ).toEqual([]);
    // the contract's handle alias of getInfo
    expect(typeof s.connect).toBe("function");
    // descriptive v1 names are not methods of this layer
    for (const old of ["get", "destroy", "exec", "execCancel", "download", "upload", "move", "folders", "files.delete", "networkPolicy.put"]) {
      expect([old, at(s, old)]).toEqual([old, undefined]);
    }
  });

  it("offers no settings write: sandbox settings are changed in the Console", () => {
    const settings = client().sandboxes.settings as unknown as Record<string, unknown>;
    for (const name of ["update", "put", "set"]) expect([name, settings[name]]).toEqual([name, undefined]);
  });

  it("exposes client.sandboxes on the client and on withOptions views", () => {
    const c = client();
    for (const view of [c, c.withOptions({ retries: 0 }), c.withOptions({ timeoutMs: 5 })]) {
      expect("sandboxes" in view).toBe(true);
      expect(view.sandboxes).toBeInstanceOf(Sandboxes);
    }
  });
});

describe("every operation", () => {
  it.each(Object.keys(CALLS))("%s goes to its contract path with a contract-valid request", async (operationId) => {
    await CALLS[operationId]!(client().sandboxes);
    const calls = api.callsTo(operationId);
    expect(calls).toHaveLength(1);
    expect(api.calls).toHaveLength(1);
  });

  it("encodes a multi-segment path segment by segment", async () => {
    await client().sandboxes.files.read(SID, "dir/a b.txt");
    expect(api.calls[0]!.request.url).toBe(`${api.base}/workspace/sandboxes/${SID}/files/dir/a%20b.txt`);
    expect(api.calls[0]!.params.path).toBe("dir/a b.txt");
  });

  it("sends the query keys and bodies the contract declares", async () => {
    const s = client().sandboxes;
    await s.files.remove(SID, "dir", { recursive: true });
    await s.files.list(SID);
    await s.files.read(SID, "a.txt", { maxBytes: 64 });
    expect(api.calls.map((c) => c.query.toString())).toEqual(["recursive=true", "", "maxBytes=64"]);
    await s.files.write(SID, "a.txt", { body: { content: "aGk=", encoding: "base64" } });
    await s.files.upload(SID, "b.bin", { body: new Uint8Array([7, 8]).buffer });
    const [write, upload] = api.calls.slice(3);
    expect(write!.json).toEqual({ content: "aGk=", encoding: "base64" });
    expect(write!.request.headers.get("content-type")).toBe("application/json");
    expect(upload!.request.headers.get("content-type")).toBe("application/octet-stream");
    expect(Array.from(new TextEncoder().encode(upload!.text))).toEqual([7, 8]);
  });

  it("returns a Sandbox from create, connect and restore; getInfo returns the record; restore's is a new sandbox", async () => {
    const s = client().sandboxes;
    const created = await s.create();
    expect(created).toBeInstanceOf(Sandbox);
    expect(api.calls[0]!.json).toEqual({});
    const info = await s.getInfo(SID);
    expect(info).not.toBeInstanceOf(Sandbox);
    expect(info.sandbox.id).toBe(SID);
    const connected = await s.connect(SID);
    expect(connected).toBeInstanceOf(Sandbox);
    expect(connected.id).toBe(SID);
    const restored = await s.snapshots.restore(SID, SNAP);
    expect(restored).toBeInstanceOf(Sandbox);
    expect(restored.id).toBe(SID2);
    expect(api.callsTo("restoreWorkspaceSandboxSnapshot")[0]!.json).toEqual({});
    expect(api.callsTo("getWorkspaceSandbox")).toHaveLength(2);
  });

  it("returns the download's bytes", async () => {
    expect(Array.from(await client().sandboxes.files.download(SID, "a.bin"))).toEqual([0, 1, 2, 255]);
  });

  it("sends If-Match on the network policy update, and returns the GET's ETag in meta", async () => {
    api.on("getWorkspaceSandboxNetworkPolicy", () => api.ok("getWorkspaceSandboxNetworkPolicy", {}, { etag: '"3"' }));
    const s = client().sandboxes;
    const read = await s.networkPolicy.get(SID).withResponse();
    expect(read.meta.headers.etag).toBe('"3"');
    await s.networkPolicy.update(SID, { body: { version: 1, mode: "allow-all-public" }, ifMatch: '"3"' });
    expect(api.callsTo("putWorkspaceSandboxNetworkPolicy")[0]!.request.headers.get("if-match")).toBe('"3"');
  });
});

describe("retries", () => {
  const unavailable = () => json(503, { error: "omega_service_unavailable", requestId: "gw-1" });
  it.each([
    ["listWorkspaceSandboxes", 4],
    ["downloadWorkspaceSandboxFile", 4],
    ["uploadWorkspaceSandboxFile", 1],
    ["writeWorkspaceSandboxFile", 1],
    ["createWorkspaceSandboxFolder", 1],
    ["deleteWorkspaceSandboxPath", 1],
    ["putWorkspaceSandboxNetworkPolicy", 1],
    ["createWorkspaceSandbox", 1],
    ["moveWorkspaceSandboxPath", 1],
    ["hibernateWorkspaceSandbox", 1],
    ["resumeWorkspaceSandbox", 1],
    ["snapshotWorkspaceSandbox", 1],
    ["restoreWorkspaceSandboxSnapshot", 1],
    ["execInWorkspaceSandbox", 1],
  ] as const)("a 503 on %s is sent %i time(s)", async (operationId, attempts) => {
    api.on(operationId, unavailable);
    const error = await failure(() => CALLS[operationId]!(client().sandboxes));
    expect(error).toBeInstanceOf(UnavailableError);
    expect(error).toBeInstanceOf(E.CoreServerError);
    expect(api.callsTo(operationId)).toHaveLength(attempts);
  });

  // no method retries a non-idempotent call, so not even a 429 is sent again
  it.each([
    "uploadWorkspaceSandboxFile", "writeWorkspaceSandboxFile", "createWorkspaceSandboxFolder", "deleteWorkspaceSandboxPath",
    "putWorkspaceSandboxNetworkPolicy", "createWorkspaceSandbox", "hibernateWorkspaceSandbox", "resumeWorkspaceSandbox",
    "snapshotWorkspaceSandbox", "restoreWorkspaceSandboxSnapshot", "moveWorkspaceSandboxPath",
  ])("a 429 on %s is not retried either", async (operationId) => {
    api.on(operationId, () => json(429, { error: "rate_limited", requestId: "gw-2" }, { "retry-after": "0" }));
    await expect(CALLS[operationId]!(client().sandboxes)).rejects.toBeInstanceOf(E.CoreRateLimitError);
    expect(api.callsTo(operationId)).toHaveLength(1);
  });

  it.each(["createWorkspaceSandbox", "hibernateWorkspaceSandbox", "snapshotWorkspaceSandbox", "moveWorkspaceSandboxPath"])(
    "a connection refused on %s (a failure before sending) is not retried either",
    async (operationId) => {
      const refused = Object.assign(new TypeError("fetch failed"), { cause: Object.assign(new Error("connect refused"), { code: "ECONNREFUSED" }) });
      api.on(operationId, () => { throw refused; });
      const error = await failure(() => CALLS[operationId]!(client().sandboxes));
      expect(error).toBeInstanceOf(SandboxConnectionError);
      expect(error).toBeInstanceOf(E.APIConnectionError);
      expect(api.callsTo(operationId)).toHaveLength(1);
    },
  );

  it.each(["updateWorkspaceSandbox", "cancelWorkspaceSandboxExec"])(
    "%s keeps the executor's POST/PATCH rule: a 429 is retried, a 503 is not",
    async (operationId) => {
      api.on(operationId, () => json(429, { error: "rate_limited", requestId: "gw-3" }, { "retry-after": "0" }), () => api.ok(operationId));
      await CALLS[operationId]!(client().sandboxes);
      expect(api.callsTo(operationId)).toHaveLength(2);
      const other = new SandboxApi();
      other.on(operationId, unavailable);
      await expect(CALLS[operationId]!(client("keys", {}, other).sandboxes)).rejects.toBeInstanceOf(UnavailableError);
      expect(other.callsTo(operationId)).toHaveLength(1);
      expect(other.problems).toEqual([]);
    },
  );

  it("a 412 on the network policy update is a ConflictError, sent once", async () => {
    api.on("putWorkspaceSandboxNetworkPolicy", () => json(412, { code: "network_policy_revision_mismatch", message: "stale revision" }));
    const error = await failure(() => CALLS.putWorkspaceSandboxNetworkPolicy!(client().sandboxes));
    expect(error).toBeInstanceOf(ConflictError);
    expect(error).toBeInstanceOf(E.ConflictError);
    expect(error).toBeInstanceOf(SandboxError);
    expect(error).toMatchObject({ statusCode: 412, code: "network_policy_revision_mismatch" });
    expect(api.callsTo("putWorkspaceSandboxNetworkPolicy")).toHaveLength(1);
  });

  it("a 404 on a retried kill means it was applied", async () => {
    api.on("destroyWorkspaceSandbox", unavailable, () => json(404, { code: "not_found", message: "no such sandbox" }));
    const raw = await client().sandboxes.kill(SID).withResponse();
    expect(raw.data).toBeUndefined();
    expect(raw.meta.alreadyApplied).toBe(true);
  });

  it("a withOptions view with retries 0 sends a read once", async () => {
    api.on("listWorkspaceSandboxes", unavailable);
    await expect(client().withOptions({ retries: 0 }).sandboxes.list()).rejects.toBeInstanceOf(E.CoreServerError);
    expect(api.calls).toHaveLength(1);
  });
});

describe("errors: client.sandboxes throws the same sandbox classes as the handle", () => {
  it("create, connect and snapshots.restore throw the sandbox classes, which are the shared ones too", async () => {
    const s = client().sandboxes;
    api.on("createWorkspaceSandbox", () => json(409, { code: "quota_exceeded", message: "full", detail: { scope: "org" } }));
    const quota = await failure(() => s.create());
    expect(quota).toBeInstanceOf(QuotaExceededError);
    expect(quota).toBeInstanceOf(ConflictError);
    expect(quota).toBeInstanceOf(E.ConflictError);
    expect(quota).toBeInstanceOf(SandboxError);
    expect(quota).toMatchObject({ statusCode: 409, code: "quota_exceeded", detail: { scope: "org" } });
    api.on("getWorkspaceSandbox", () => json(409, { code: "conflict", message: "asleep", detail: { state: "hibernated" } }));
    const asleep = await failure(() => s.connect(SID));
    expect(asleep).toBeInstanceOf(SandboxHibernatedError);
    expect(asleep).toBeInstanceOf(SandboxStateError);
    expect(asleep).toBeInstanceOf(ConflictError);
    expect(asleep).toBeInstanceOf(E.SandboxStateError);
    api.on("restoreWorkspaceSandboxSnapshot", () => json(409, { code: "conflict", message: "busy" }));
    const busy = await failure(() => s.snapshots.restore(SID, SNAP));
    expect(busy).toBeInstanceOf(SandboxStateError);
    expect(busy).toBeInstanceOf(ConflictError);
    expect(busy).toBeInstanceOf(E.SandboxStateError);
    expect(busy).not.toBeInstanceOf(SandboxHibernatedError);
  });

  it("a connection failure is a SandboxConnectionError", async () => {
    const refused = Object.assign(new TypeError("fetch failed"), { cause: Object.assign(new Error("connect refused"), { code: "ECONNREFUSED" }) });
    api.on("listWorkspaceSandboxes", () => { throw refused; });
    const error = await failure(() => client().withOptions({ retries: 0 }).sandboxes.list());
    expect(error).toBeInstanceOf(SandboxConnectionError);
    expect(error).toBeInstanceOf(SandboxError);
  });
});

describe("credentials, scope headers and origin", () => {
  it.each(["keys", "bearer"] as const)("%s mode: no base URL anywhere is refused before any request (no default host)", async (mode) => {
    const c = new FutureAGIClient({
      ...(mode === "keys" ? { apiKey: API_KEY, secretKey: SECRET_KEY } : { platformToken: TOKEN }),
      fetch: api.fetch,
    });
    for (const view of [c, c.withOptions({ retries: 0 })]) {
      const calls: Array<() => PromiseLike<unknown>> = [
        () => view.sandboxes.list(),
        () => view.sandboxes.create(),
        () => view.sandboxes.commands.run(SID, { body: { command: "id" } }),
        () => view.sandboxes.files.download(SID, "a"),
      ];
      for (const call of calls) {
        const error = await failure(call);
        expect(error).toBeInstanceOf(E.PlatformNotConfiguredError);
        expect(error).toBeInstanceOf(E.ConfigurationError);
        expect(error).toMatchObject({ code: "missing_base_url" });
        expect(String(error)).toMatch(/baseUrl/u);
        expect(String(error)).toMatch(/OMEGA_BASE_URL/u);
        for (const secret of [API_KEY, SECRET_KEY, TOKEN]) expect(String(error)).not.toContain(secret);
      }
    }
    expect(api.calls).toEqual([]);
  });

  it.each<[string, FutureAGIClientOptions, Record<string, string>]>([
    ["baseUrl", { baseUrl: "http://127.0.0.1:9" }, {}],
    ["FI_BASE_URL", {}, { FI_BASE_URL: "http://127.0.0.1:9" }],
    ["FI_PLATFORM_BASE_URL", {}, { FI_PLATFORM_BASE_URL: "http://127.0.0.1:9/omega/api" }],
  ])("a host given by %s is used", async (_label, options, env) => {
    Object.assign(process.env, env);
    const local = new SandboxApi("http://127.0.0.1:9/omega/api");
    const c = new FutureAGIClient({ apiKey: API_KEY, secretKey: SECRET_KEY, fetch: local.fetch, ...options });
    await c.sandboxes.list();
    await c.withOptions({ retries: 0 }).sandboxes.list();
    expect(local.calls).toHaveLength(2);
    expect(local.problems).toEqual([]);
  });

  it.each(["keys", "bearer"] as const)("%s mode sends only its own credential", async (mode) => {
    const s = client(mode).sandboxes;
    await s.list();
    await drain(await s.commands.run(SID, { body: { command: "true" } }));
    for (const { request } of api.calls) {
      if (mode === "keys") {
        expect([request.headers.get("x-api-key"), request.headers.get("x-secret-key")]).toEqual([API_KEY, SECRET_KEY]);
        expect(request.headers.has("authorization")).toBe(false);
      } else {
        expect(request.headers.get("authorization")).toBe(`Bearer ${TOKEN}`);
        expect(request.headers.has("x-api-key") || request.headers.has("x-secret-key")).toBe(false);
      }
    }
  });

  it.each([
    ["keys", { "x-workspace-id": "ws_1", "x-organization-id": "org_1" }, ["x-omega-workspace", "x-omega-org"]],
    ["bearer", { "x-omega-workspace": "ws_1", "x-omega-org": "org_1" }, ["x-workspace-id", "x-organization-id"]],
  ] as const)("%s mode sends the workspace and organization as its own scope headers", async (mode, expected, absent) => {
    const s = client(mode, { workspaceId: "ws_1", organizationId: "org_1" }).sandboxes;
    await s.list();
    await s.files.makeDir(SID, "d");
    for (const { request } of api.calls) {
      for (const [name, value] of Object.entries(expected)) expect([name, request.headers.get(name)]).toEqual([name, value]);
      for (const name of absent) expect([name, request.headers.has(name)]).toEqual([name, false]);
    }
  });

  it.each<[string, FutureAGIClientOptions, string | undefined]>([
    ["no opt-in", {}, undefined],
    ["allowCustomPlatformUrl", { allowCustomPlatformUrl: true }, undefined],
    ["FI_ALLOW_CUSTOM_PLATFORM_URL", {}, "1"],
  ])("a self-hosted token to a host that is not loopback needs allowCustomBaseUrl: %s", async (_label, flags, env) => {
    if (env !== undefined) process.env.FI_ALLOW_CUSTOM_PLATFORM_URL = env;
    const c = new FutureAGIClient({ platformToken: TOKEN, platformBaseUrl: api.base, fetch: api.fetch, ...flags });
    const calls: Array<() => PromiseLike<unknown>> = [
      () => c.sandboxes.list(),
      () => c.sandboxes.create(),
      () => c.sandboxes.commands.run(SID, { body: { command: "id" } }),
      () => c.withOptions({ retries: 0 }).sandboxes.files.download(SID, "a"),
    ];
    for (const call of calls) {
      const error = await failure(call);
      expect(error).toBeInstanceOf(E.HostNotAllowedError);
      expect(error).toBeInstanceOf(E.ConfigurationError);
      expect(String(error)).toContain("allowCustomBaseUrl");
      expect(String(error)).not.toContain(TOKEN);
    }
    expect(api.calls).toEqual([]);
  });

  it("allowCustomBaseUrl carries to withOptions views, and keys mode does not need it", async () => {
    const c = client("bearer");
    await c.withOptions({ retries: 0 }).sandboxes.list();
    await client("keys").sandboxes.list();
    expect(api.calls).toHaveLength(2);
  });

  it.each(["http://127.0.0.1:9/omega/api", "http://localhost:9/omega/api"])(
    "a self-hosted token to loopback needs no opt-in: %s",
    async (base) => {
      const target = new SandboxApi(base);
      const c = new FutureAGIClient({ platformToken: TOKEN, platformBaseUrl: base, fetch: target.fetch });
      await c.sandboxes.list();
      expect(target.calls).toHaveLength(1);
      expect(target.problems).toEqual([]);
    },
  );

  // A Bearer token is the self-hosted credential (OpenAPI servers[1], securitySchemes.OmegaBearer): no host name
  // admits it without the opt-in, a Future AGI one included.
  it.each(["https://sandbox-fixture.futureagi.com/omega/api", "https://api.futureagi.com/omega/api"])(
    "a self-hosted token to a Future AGI host needs allowCustomBaseUrl too: %s",
    async (base) => {
      const target = new SandboxApi(base);
      const refused = new FutureAGIClient({ platformToken: TOKEN, platformBaseUrl: base, fetch: target.fetch });
      const error = await failure(() => refused.sandboxes.list());
      expect(error).toBeInstanceOf(E.HostNotAllowedError);
      expect(error).toMatchObject({ code: "host_not_allowed" });
      expect(String(error)).toContain("allowCustomBaseUrl");
      expect(String(error)).not.toContain(TOKEN);
      expect(target.calls).toEqual([]);
      const allowed = new FutureAGIClient({ platformToken: TOKEN, platformBaseUrl: base, fetch: target.fetch, allowCustomBaseUrl: true });
      await allowed.sandboxes.list();
      expect(target.calls).toHaveLength(1);
      expect(target.problems).toEqual([]);
    },
  );

  it("both credential modes on one client is a configuration error before any request", async () => {
    const c = new FutureAGIClient({ apiKey: API_KEY, secretKey: SECRET_KEY, platformToken: TOKEN, platformBaseUrl: api.base, fetch: api.fetch, allowCustomBaseUrl: true });
    const error = await failure(() => c.sandboxes.list());
    expect(error).toBeInstanceOf(E.MixedCredentialsError);
    for (const secret of [API_KEY, SECRET_KEY, TOKEN]) expect(String(error)).not.toContain(secret);
    expect(api.calls).toEqual([]);
  });

  it.each((["keys", "bearer"] as const).flatMap((mode) => ["argument", "environment"].map((flag) => [mode, flag] as const)))(
    "plain HTTP to a remote host is refused before any request: %s, opt-out by %s",
    async (mode, flag) => {
      const insecure = new SandboxApi("http://sandbox-insecure.test/omega/api");
      if (flag === "environment") process.env.FI_ALLOW_INSECURE_HTTP = "1";
      const c = client(mode, flag === "argument" ? { allowInsecureHttp: true } : {}, insecure);
      const calls: Array<() => PromiseLike<unknown>> = [
        () => c.sandboxes.list(),
        () => c.sandboxes.commands.run(SID, { body: { command: "id" } }),
        () => c.sandboxes.files.download(SID, "a"),
      ];
      for (const call of calls) {
        const error = await failure(call);
        expect(error).toBeInstanceOf(E.ConfigurationError);
        expect(error).toMatchObject({ code: "insecure_sandbox_origin" });
        expect(String(error)).not.toContain(API_KEY);
        expect(String(error)).not.toContain(TOKEN);
      }
      expect(insecure.calls).toEqual([]);
    },
  );

  it("plain HTTP to loopback is allowed", async () => {
    const local = new SandboxApi("http://127.0.0.1:9/omega/api");
    await client("keys", {}, local).sandboxes.list();
    expect(local.calls).toHaveLength(1);
    expect(local.problems).toEqual([]);
  });

  it("a redirect never names its target", async () => {
    const location = "https://elsewhere.test/collect/private-path";
    api.on("listWorkspaceSandboxes", () => new Response(null, { status: 302, headers: { location } }));
    api.on("execInWorkspaceSandbox", () => new Response(null, { status: 307, headers: { location } }));
    const s = client().sandboxes;
    const calls: Array<() => PromiseLike<unknown>> = [() => s.list(), () => s.commands.run(SID, { body: { command: "id" } })];
    for (const call of calls) {
      const error = (await failure(call)) as E.UnexpectedRedirectError;
      expect(error).toBeInstanceOf(E.UnexpectedRedirectError);
      expect(error.targetHost).toBeUndefined();
      expect(error.cause).toBeUndefined();
      expect(String(error)).not.toMatch(/elsewhere|private-path/u);
    }
    expect(api.calls).toHaveLength(2);
  });

  it("keeps a sandbox state in an error's detail out of the redactor's reach", async () => {
    api.on("hibernateWorkspaceSandbox", () => json(409, { code: "conflict", message: "the sandbox is hibernated", detail: { state: "hibernated" } }));
    const error = (await failure(() => client().sandboxes.hibernate(SID))) as E.FutureAGIAPIError;
    expect(error).toBeInstanceOf(SandboxHibernatedError);
    expect(error).toBeInstanceOf(E.ConflictError);
    expect(error).toMatchObject({ detail: { state: "hibernated" } });
    expect((error.payload as { detail: Record<string, unknown> }).detail).toMatchObject({ sandboxState: "hibernated" });
  });
});

describe("exec stream framing", () => {
  const FRAMES: [string, unknown, string][] = [
    ["started", { execId: EXEC, sandboxId: SID }, "1"],
    ["stdout", { data: "héllo ✓\n" }, "2"],
    ["stderr", { data: "warn\n" }, "3"],
    ["exit", { exitCode: 2, timedOut: false, cancelled: false, truncated: false, durationMs: 9, stdoutBytes: 10, stderrBytes: 5 }, "4"],
  ];
  const expected = FRAMES.map(([event, data, id]) => ({ event, id, data }));

  it("parses frames split at every byte, across CRLF and inside UTF-8, with keepalives", async () => {
    const text = (": keepalive\n\n" + sseText(FRAMES)).replace(/\n/gu, "\r\n");
    const bytes = new TextEncoder().encode(text);
    api.on("execInWorkspaceSandbox", () => streamed(Array.from(bytes, (b) => new Uint8Array([b]))));
    const stream = await client().sandboxes.commands.run(SID, { body: { command: "run" } });
    expect(await drain(stream)).toEqual(expected);
    expect(stream.execId).toBe(EXEC);
    const call = api.calls[0]!;
    expect(call.request.headers.get("accept")).toBe("text/event-stream");
    expect(call.json).toEqual({ command: "run" });
  });

  it("yields an unknown event as such and keeps going", async () => {
    api.on("execInWorkspaceSandbox", () => streamed([sseText([FRAMES[0]!, ["progress", { pct: 50 }, "2"], FRAMES[3]!])]));
    const frames = await drain(await client().sandboxes.commands.run(SID, { body: { command: "run" } }));
    expect(frames.map((f) => f.event)).toEqual(["started", "unknown", "exit"]);
    expect(frames[1]).toEqual({ event: "unknown", eventType: "progress", id: "2", raw: { pct: 50 } });
  });

  it("just ends when the connection ends without an exit frame (the handle judges it)", async () => {
    api.on("execInWorkspaceSandbox", () => streamed([sseText(FRAMES.slice(0, 2))]));
    const frames = await drain(await client().sandboxes.commands.run(SID, { body: { command: "run" } }));
    expect(frames.map((f) => f.event)).toEqual(["started", "stdout"]);
  });

  it("closes the connection when the loop stops early", async () => {
    let cancelled = false;
    api.on("execInWorkspaceSandbox", () => streamed([sseText(FRAMES.slice(0, 2))], { hold: true, onCancel: () => { cancelled = true; } }));
    const stream = await client().sandboxes.commands.run(SID, { body: { command: "sleep 100" } });
    for await (const frame of stream) {
      expect(frame.event).toBe("started");
      break;
    }
    expect(cancelled).toBe(true);
    expect(await stream.next()).toEqual({ done: true, value: undefined });
  });

  it("a dropped connection is a connection error that may have applied", async () => {
    const reset = Object.assign(new TypeError("terminated"), { cause: Object.assign(new Error("socket hang up"), { code: "ECONNRESET" }) });
    api.on("execInWorkspaceSandbox", () => streamed([sseText(FRAMES.slice(0, 1))], { fail: reset }));
    const stream = await client().sandboxes.commands.run(SID, { body: { command: "run" } });
    const error = await drain(stream).then(() => undefined, (e: unknown) => e);
    expect(error).toBeInstanceOf(SandboxConnectionError);
    expect(error).toBeInstanceOf(E.APIConnectionError);
    expect(error).toMatchObject({ possiblyApplied: true, operation: "sandboxes.commands.run" });
    expect(api.calls).toHaveLength(1);
  });
});
