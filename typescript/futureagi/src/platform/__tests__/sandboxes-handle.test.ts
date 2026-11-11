/**
 * The `Sandbox` handle (src/sandbox) against the contract-driven mock API: the environment-only statics and the
 * explicit client, every handle method, every error class, the whole exit record, the network policy ETag, and
 * credential privacy. The statics build their own client, so their requests are caught at the global `fetch`.
 * Synthetic credentials only; no socket.
 */
import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { inspect } from "node:util";

import * as Root from "../../index";
import { FutureAGIClient } from "../../futureagi-client";
import * as E from "../../_core/errors";
import { PlatformCore } from "../../_core/platform-base";
import { PLATFORM_OPERATIONS } from "../../generated/platform/policy.gen";
import {
  AuthenticationError,
  CommandFailedError,
  CommandIncompleteError,
  CommandResult,
  ConflictError,
  InsufficientStorageError,
  NotFoundError,
  PermissionDeniedError,
  ProviderError,
  QuotaExceededError,
  RateLimitError,
  Sandbox,
  SandboxConnectionError,
  SandboxError,
  SandboxHibernatedError,
  Sandboxes,
  SandboxStateError,
  UnavailableError,
  UnprocessableEntityError,
  ValidationError,
} from "../../sandbox";
import { resolveSandboxOrigin } from "../../sandbox/config";
import { BASE, EXEC, SID, SID2, SNAP, SandboxApi, json, sseText, streamed } from "../../sandbox/__fixtures__/openapi-mock";

const API_KEY = "sbx-test-api-key-not-valid";
const SECRET_KEY = "sbx-test-secret-key-not-valid";
const TOKEN = "sbx-test-bearer-token-not-valid";
const OS_KEY = "sbx-test-operator-key-never-sent";
const LOCAL = "http://127.0.0.1:9/omega/api";
const ENV = [
  "FI_BASE_URL", "FI_PLATFORM_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_TOKEN", "FI_WORKSPACE_ID",
  "FI_ORGANIZATION_ID", "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS",
  "OMEGA_BASE_URL", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
];
const START = ["started", { execId: EXEC, sandboxId: SID }, "1"] as const;
const EXIT = { exitCode: 0, timedOut: false, cancelled: false, truncated: false, durationMs: 3, stdoutBytes: 0, stderrBytes: 0 };
const exitFrame = (fields: Record<string, unknown> = {}, id = "9") => ["exit", { ...EXIT, ...fields }, id] as const;

let saved: [string, string | undefined][] = [];
let api: SandboxApi;
let globalFetch: jest.SpyInstance;
/** The API the global `fetch` (the statics' client) reaches. */
let routed: SandboxApi;
beforeEach(() => {
  saved = ENV.map((key) => [key, process.env[key]]);
  for (const key of ENV) delete process.env[key];
  api = new SandboxApi();
  routed = api;
  globalFetch = jest.spyOn(globalThis, "fetch").mockImplementation((input, init) => routed.fetch(input as RequestInfo, init));
});
afterEach(() => {
  globalFetch.mockRestore();
  for (const [key, value] of saved) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  expect(api.problems).toEqual([]);
  expect(routed.problems).toEqual([]);
});

function client(mode: "keys" | "bearer" = "keys"): FutureAGIClient {
  const c = new FutureAGIClient({
    ...(mode === "keys" ? { apiKey: API_KEY, secretKey: SECRET_KEY } : { platformToken: TOKEN, allowCustomBaseUrl: true }),
    platformBaseUrl: api.base,
    fetch: api.fetch,
  });
  Object.assign(c._platform.shared, { sleep: async () => undefined });
  return c;
}

/** Hosted keys and the mock's base in the environment, for the statics. */
const hostedEnv = (extra: Record<string, string> = {}): void => {
  Object.assign(process.env, { OMEGA_BASE_URL: BASE, FI_API_KEY: API_KEY, FI_SECRET_KEY: SECRET_KEY, ...extra });
};

const connect = (): Promise<Sandbox> => client().sandboxes.connect(SID);
const failure = (call: () => PromiseLike<unknown>): Promise<unknown> => Promise.resolve().then(call).then(() => undefined, (e: unknown) => e);
const headerValues = (target: SandboxApi = api): string =>
  target.calls
    .map(({ request }) => {
      const lines: string[] = [];
      request.headers.forEach((value, key) => lines.push(`${key}: ${value}`));
      return lines.join("\n");
    })
    .join("\n");

describe("imports", () => {
  it("the package root offers FutureAGIClient, Sandbox and SandboxError, and the same classes as the sandbox module", () => {
    expect(Root.FutureAGIClient).toBe(FutureAGIClient);
    expect(Root.Sandbox).toBe(Sandbox);
    expect(Root.SandboxError).toBe(SandboxError);
    expect(Root.CommandResult).toBe(CommandResult);
    expect(Root.CommandIncompleteError).toBe(CommandIncompleteError);
    expect(Root.Sandboxes).toBe(Sandboxes);
    // the root's own status classes are unchanged; the sandbox ones extend them
    expect(Root.NotFoundError).toBe(E.NotFoundError);
    expect(NotFoundError.prototype).toBeInstanceOf(E.NotFoundError);
  });
});

describe("Sandbox statics read the environment only", () => {
  it("hosted keys from the environment, sent as X-Api-Key / X-Secret-Key", async () => {
    hostedEnv({ OMEGA_OS_API_KEY: OS_KEY });
    const sbx = await Sandbox.create({ name: "demo", size: "small" });
    expect(sbx).toBeInstanceOf(Sandbox);
    const { request, json: body } = api.calls[0]!;
    expect([request.headers.get("x-api-key"), request.headers.get("x-secret-key")]).toEqual([API_KEY, SECRET_KEY]);
    expect(request.headers.has("authorization")).toBe(false);
    expect(body).toEqual({ name: "demo", size: "small" });
    expect(headerValues()).not.toContain(OS_KEY);
  });

  it("a self-hosted Bearer token from FUTUREAGI_OMEGA_API_KEY to a loopback EE, and nothing else", async () => {
    routed = new SandboxApi(LOCAL);
    Object.assign(process.env, { OMEGA_BASE_URL: LOCAL, FUTUREAGI_OMEGA_API_KEY: TOKEN, OMEGA_OS_API_KEY: OS_KEY });
    await Sandbox.list();
    const { request } = routed.calls[0]!;
    expect(request.headers.get("authorization")).toBe(`Bearer ${TOKEN}`);
    expect(request.headers.has("x-api-key") || request.headers.has("x-secret-key")).toBe(false);
    expect(headerValues(routed)).not.toContain(OS_KEY);
  });

  it("a self-hosted token to an EE that is not loopback needs a client built with allowCustomBaseUrl", async () => {
    Object.assign(process.env, { OMEGA_BASE_URL: BASE, FUTUREAGI_OMEGA_API_KEY: TOKEN, FI_ALLOW_CUSTOM_PLATFORM_URL: "1" });
    const error = await failure(() => Sandbox.connect(SID));
    expect(error).toBeInstanceOf(E.HostNotAllowedError);
    expect(String(error)).toContain("allowCustomBaseUrl");
    expect(String(error)).not.toContain(TOKEN);
    expect(api.calls).toEqual([]);
  });

  it.each([
    ["keys", { "x-workspace-id": "ws_1", "x-organization-id": "org_1" }, ["x-omega-workspace", "x-omega-org"]],
    ["bearer", { "x-omega-workspace": "ws_1", "x-omega-org": "org_1" }, ["x-workspace-id", "x-organization-id"]],
  ] as const)("%s mode sends FI_WORKSPACE_ID and FI_ORGANIZATION_ID as its own scope headers", async (mode, expected, absent) => {
    const scope = { FI_WORKSPACE_ID: "ws_1", FI_ORGANIZATION_ID: "org_1" };
    if (mode === "keys") {
      hostedEnv(scope);
    } else {
      routed = new SandboxApi(LOCAL);
      Object.assign(process.env, { OMEGA_BASE_URL: LOCAL, FUTUREAGI_OMEGA_API_KEY: TOKEN, ...scope });
    }
    await Sandbox.connect(SID);
    const { request } = routed.calls[0]!;
    for (const [name, value] of Object.entries(expected)) expect([name, request.headers.get(name)]).toEqual([name, value]);
    for (const name of absent) expect([name, request.headers.has(name)]).toEqual([name, false]);
  });

  it("keys passed to a static are not credentials: only the create body's fields are sent", async () => {
    hostedEnv();
    await Sandbox.create({ name: "demo", apiKey: "sbx-test-argument-key", baseUrl: "https://elsewhere.test" } as never);
    expect(api.calls[0]!.json).toEqual({ name: "demo" });
    expect(api.calls[0]!.request.headers.get("x-api-key")).toBe(API_KEY);
    expect(headerValues()).not.toContain("sbx-test-argument-key");
  });

  it("has no default host: a missing OMEGA_BASE_URL is named and nothing is sent", async () => {
    Object.assign(process.env, { FI_API_KEY: API_KEY, FI_SECRET_KEY: SECRET_KEY, FI_BASE_URL: BASE, FI_PLATFORM_BASE_URL: BASE });
    const error = await failure(() => Sandbox.connect(SID));
    expect(error).toBeInstanceOf(E.ConfigurationError);
    expect(String(error)).toContain("OMEGA_BASE_URL");
    expect(api.calls).toEqual([]);
  });

  it("a malformed OMEGA_BASE_URL names OMEGA_BASE_URL", async () => {
    hostedEnv({ OMEGA_BASE_URL: "not a url" });
    const error = await failure(() => Sandbox.connect(SID));
    expect(error).toBeInstanceOf(E.PlatformNotConfiguredError);
    expect(String(error)).toContain("OMEGA_BASE_URL");
    expect(String(error)).not.toContain("FI_PLATFORM_BASE_URL");
  });

  it("both credential modes in the environment is a configuration error, and nothing is sent", async () => {
    hostedEnv({ FUTUREAGI_OMEGA_API_KEY: TOKEN });
    for (const call of [() => Sandbox.list(), () => Sandbox.create(), () => Sandbox.settings()]) {
      const error = await failure(call);
      expect(error).toBeInstanceOf(E.MixedCredentialsError);
      expect(error).toMatchObject({ code: "mixed_credentials" });
      for (const secret of [API_KEY, SECRET_KEY, TOKEN]) expect(String(error)).not.toContain(secret);
    }
    expect(api.calls).toEqual([]);
  });

  it("never uses OMEGA_OS_API_KEY as a credential", async () => {
    Object.assign(process.env, { OMEGA_BASE_URL: BASE, OMEGA_OS_API_KEY: OS_KEY });
    const error = await failure(() => Sandbox.list());
    expect(error).toBeInstanceOf(E.CredentialsMissingError);
    expect(String(error)).not.toContain(OS_KEY);
    expect(api.calls).toEqual([]);
  });

  it.each([{ FI_API_KEY: API_KEY, FI_SECRET_KEY: SECRET_KEY }, { FUTUREAGI_OMEGA_API_KEY: TOKEN }])(
    "refuses plain HTTP to a remote host before any request",
    async (credentials) => {
      Object.assign(process.env, { OMEGA_BASE_URL: "http://remote-ee.test:8080", FI_ALLOW_INSECURE_HTTP: "1", ...credentials });
      const error = await failure(() => Sandbox.list());
      expect(error).toMatchObject({ code: "insecure_sandbox_origin" });
      expect(api.calls).toEqual([]);
    },
  );

  it("client.sandboxes and Sandbox.create give the same handle type", async () => {
    // One credential mode at a time: the bearer client runs with the environment still clear (an explicit token
    // beside FI_API_KEY / FI_SECRET_KEY is a MixedCredentialsError), then the static reads the hosted keys.
    const viaClient = await client("bearer").sandboxes.create({ body: { name: "a" } });
    hostedEnv();
    const viaStatic = await Sandbox.create({ name: "a" });
    expect(viaClient).toBeInstanceOf(Sandbox);
    expect(viaStatic).toBeInstanceOf(Sandbox);
    expect(api.calls.map((call) => call.json)).toEqual([{ name: "a" }, { name: "a" }]);
    expect(api.calls[0]!.request.headers.get("authorization")).toBe(`Bearer ${TOKEN}`);
    expect(api.calls[1]!.request.headers.get("x-api-key")).toBe(API_KEY);
  });
});

describe("credentials never leak", () => {
  it("not through the handle's string, JSON or inspection", async () => {
    for (const sbx of [await connect(), await client("bearer").sandboxes.connect(SID)]) {
      const dump = String(sbx) + JSON.stringify(sbx) + inspect(sbx, { depth: 20, showHidden: true, customInspect: false }) + inspect(sbx);
      for (const secret of [API_KEY, SECRET_KEY, TOKEN, "Bearer "]) expect(dump).not.toContain(secret);
      expect(String(sbx)).toBe(`Sandbox(${SID}, active)`);
    }
  });

  it("not through an error whose body echoes the key", async () => {
    api.on("listWorkspaceSandboxFiles", () => json(401, { code: "unauthorized", message: `bad key ${API_KEY}` }));
    const error = await failure(async () => (await connect()).files.list());
    expect(error).toBeInstanceOf(AuthenticationError);
    const dump = String(error) + JSON.stringify(error) + inspect(error, { depth: 20, showHidden: true, customInspect: false });
    for (const secret of [API_KEY, SECRET_KEY]) expect(dump).not.toContain(secret);
  });
});

describe("errors", () => {
  const CASES: [number, unknown, Record<string, string>, new (...args: never[]) => Error, new (...args: never[]) => Error][] = [
    [400, { code: "invalid_request", message: "bad path" }, {}, ValidationError, E.BadRequestError],
    [401, { error: "omega_session_unavailable", requestId: "gw-401" }, {}, AuthenticationError, E.AuthenticationError],
    [403, { code: "forbidden", message: "members only" }, {}, PermissionDeniedError, E.PermissionDeniedError],
    [404, { code: "not_found", message: "no such sandbox" }, {}, NotFoundError, E.NotFoundError],
    [409, { code: "conflict", message: "busy" }, {}, ConflictError, E.SandboxStateError],
    [409, { code: "conflict", message: "busy" }, {}, SandboxStateError, E.ConflictError],
    [409, { code: "sandbox_busy", message: "busy" }, {}, ConflictError, E.ConflictError],
    [409, { code: "conflict", message: "asleep", detail: { state: "hibernated" } }, {}, SandboxHibernatedError, E.SandboxStateError],
    [409, { code: "quota_exceeded", message: "full", detail: { scope: "org" } }, {}, QuotaExceededError, E.ConflictError],
    [422, { code: "invalid_body", message: "bad body" }, {}, ValidationError, E.UnprocessableEntityError],
    [422, { code: "invalid_body", message: "bad body" }, {}, UnprocessableEntityError, E.UnprocessableEntityError],
    [429, { error: "rate_limited", requestId: "gw-429" }, { "retry-after": "5" }, RateLimitError, E.CoreRateLimitError],
    [502, { code: "provider_error", message: "runtime failed", request_id: "ee-502" }, {}, ProviderError, E.CoreServerError],
    [503, { code: "unavailable", message: "later", detail: { retryAfterSeconds: 9 } }, {}, UnavailableError, E.CoreServerError],
    [507, { code: "insufficient_storage", message: "disk", detail: { limitMb: 10 } }, {}, InsufficientStorageError, E.CoreServerError],
  ];

  it.each(CASES)("%i %j is its sandbox class and still the shared class", async (status, body, headers, cls, shared) => {
    api.on("createWorkspaceSandboxFolder", () => json(status, body, { "x-request-id": "hdr-1", ...headers }));
    const error = (await failure(async () => (await connect()).files.makeDir("d"))) as SandboxError;
    expect(error).toBeInstanceOf(cls);
    expect(error).toBeInstanceOf(shared);
    expect(error).toBeInstanceOf(SandboxError);
    expect(error).toBeInstanceOf(E.FutureAGIAPIError);
    expect(error.status).toBe(status);
    expect(typeof error.code).toBe("string");
    expect(error.requestId).toBe((body as { requestId?: string }).requestId ?? "hdr-1");
    expect(api.callsTo("createWorkspaceSandboxFolder")).toHaveLength(1);
  });

  it("reads detail, the hibernated state, Retry-After and detail.retryAfterSeconds", async () => {
    const sbx = await connect();
    api.on("createWorkspaceSandboxFolder",
      () => json(409, { code: "conflict", message: "asleep", detail: { state: "hibernated" } }),
      () => json(429, { error: "rate_limited", requestId: "gw" }, { "retry-after": "5" }),
      () => json(503, { code: "unavailable", message: "later", detail: { retryAfterSeconds: 9 } }));
    const hibernated = (await failure(() => sbx.files.makeDir("a"))) as SandboxHibernatedError;
    expect(hibernated.detail).toEqual({ state: "hibernated" });
    expect(hibernated.code).toBe("conflict");
    expect(((await failure(() => sbx.files.makeDir("b"))) as RateLimitError).retryAfterSeconds).toBe(5);
    expect(((await failure(() => sbx.files.makeDir("c"))) as UnavailableError).retryAfterSeconds).toBe(9);
  });

  it("an EE request_id is the request id when no other is sent", async () => {
    api.on("createWorkspaceSandboxFolder", () => json(502, { code: "provider_error", message: "x", request_id: "ee-1" }));
    expect(((await failure(async () => (await connect()).files.makeDir("d"))) as ProviderError).requestId).toBe("ee-1");
  });

  it("a stale network policy revision (412) is a ConflictError network_policy_revision_mismatch, never retried or re-read", async () => {
    const sbx = await connect();
    api.on("putWorkspaceSandboxNetworkPolicy", () => json(412, { code: "network_policy_revision_mismatch", message: "the policy changed" }));
    const error = (await failure(() => sbx.networkPolicy.set({ version: 1, mode: "off" }, { ifMatch: '"1"' }))) as ConflictError;
    expect(error).toBeInstanceOf(ConflictError);
    expect(error).toBeInstanceOf(E.ConflictError);
    expect(error).toBeInstanceOf(SandboxError);
    expect(error).toMatchObject({ status: 412, code: "network_policy_revision_mismatch" });
    expect(error).not.toBeInstanceOf(SandboxHibernatedError);
    expect(api.callsTo("putWorkspaceSandboxNetworkPolicy")).toHaveLength(1);
    expect(api.callsTo("getWorkspaceSandboxNetworkPolicy")).toHaveLength(0);
  });

  it("a 412 or 428 body without a code gets the contract's code", async () => {
    const sbx = await connect();
    // a gateway body whose `error` is prose, not a code
    api.on("putWorkspaceSandboxNetworkPolicy",
      () => json(412, { error: "Precondition failed.", requestId: "gw-412" }),
      () => json(428, { error: "Precondition required.", requestId: "gw-428" }));
    const stale = await failure(() => sbx.networkPolicy.set({ version: 1 }, { ifMatch: '"1"' }));
    expect(stale).toBeInstanceOf(ConflictError);
    expect(stale).toMatchObject({ status: 412, code: "network_policy_revision_mismatch" });
    const missing = await failure(() => sbx.networkPolicy.set({ version: 1 }, { ifMatch: '"1"' }));
    expect(missing).toBeInstanceOf(ValidationError);
    expect(missing).toBeInstanceOf(SandboxError);
    expect(missing).not.toBeInstanceOf(E.BadRequestError);
    expect(stale).not.toBeInstanceOf(E.SandboxStateError);
    expect(missing).toMatchObject({ status: 428, code: "network_policy_precondition_required" });
    expect(api.callsTo("putWorkspaceSandboxNetworkPolicy")).toHaveLength(2);
  });

  it.each([
    [413, E.PayloadTooLargeError],
    [500, E.CoreServerError],
  ] as const)("an unnamed status %i keeps its shared class and is still a SandboxError", async (status, shared) => {
    api.on("uploadWorkspaceSandboxFile", () => json(status, { code: `status_${status}`, message: "refused" }));
    const sbx = await connect();
    const error = await failure(() => sbx.files.upload("a.bin", new Uint8Array(2)));
    expect(error).toBeInstanceOf(shared);
    expect(error).toBeInstanceOf(SandboxError);
    expect(error).toMatchObject({ status });
  });

  it("a transport failure on a create says completion is unknown, and is not retried", async () => {
    hostedEnv();
    api.on("createWorkspaceSandbox", () => {
      throw Object.assign(new TypeError("fetch failed"), { cause: Object.assign(new Error("socket hang up"), { code: "ECONNRESET" }) });
    });
    const error = (await failure(() => Sandbox.create())) as SandboxConnectionError;
    expect(error).toBeInstanceOf(SandboxConnectionError);
    expect(error).toBeInstanceOf(E.APIConnectionError);
    expect(error).toBeInstanceOf(SandboxError);
    expect(error.possiblyApplied).toBe(true);
    expect(error.message).toMatch(/unknown/u);
    expect(api.calls).toHaveLength(1);
  });

  it("configuration errors and redirects pass through unchanged", async () => {
    api.on("listWorkspaceSandboxActivity", () => new Response(null, { status: 302, headers: { location: "https://elsewhere.test/x" } }));
    expect(await failure(async () => (await connect()).activity())).toBeInstanceOf(E.UnexpectedRedirectError);
  });
});

describe("commands", () => {
  it("run collects output in order, calls back, and returns a non-zero exit code with the whole exit record", async () => {
    api.on("execInWorkspaceSandbox", () =>
      streamed([sseText([START, ["stdout", { data: "a" }, "2"], ["stderr", { data: "x" }, "3"], ["stdout", { data: "b" }, "4"],
        exitFrame({ exitCode: 3, durationMs: 12, stdoutBytes: 2, stderrBytes: 1 })])]));
    const seen: string[] = [];
    const sbx = await connect();
    const result = await sbx.commands.run("make", {
      cwd: "/work", env: { MODE: "test" }, timeoutSeconds: 30,
      onStdout: (t) => seen.push(`out:${t}`), onStderr: (t) => seen.push(`err:${t}`),
    });
    expect(result).toBeInstanceOf(CommandResult);
    expect(result).toMatchObject({
      exitCode: 3, timedOut: false, cancelled: false, truncated: false, durationMs: 12, stdoutBytes: 2, stderrBytes: 1,
      stdout: "ab", stderr: "x", execId: EXEC,
    });
    expect(result.signal).toBeUndefined();
    expect(result.error).toBeUndefined();
    expect(seen).toEqual(["out:a", "err:x", "out:b"]);
    expect(api.callsTo("execInWorkspaceSandbox")[0]!.json).toEqual({ command: "make", cwd: "/work", env: { MODE: "test" }, timeoutSeconds: 30 });
  });

  it.each([
    ["a timeout", { exitCode: null, signal: "SIGKILL", timedOut: true }],
    ["a signal", { exitCode: null, signal: "SIGTERM" }],
    ["a cancel", { exitCode: null, signal: "SIGKILL", cancelled: true }],
    ["truncated output", { exitCode: 0, truncated: true, stdoutBytes: 1048577 }],
    ["a spawn failure", { exitCode: null, error: "spawn /bin/nope ENOENT" }],
  ] as const)("run resolves (never throws) for %s, with the exit record", async (_label, fields) => {
    api.on("execInWorkspaceSandbox", () => streamed([sseText([START, exitFrame(fields)])]));
    const result = await (await connect()).commands.run("x");
    expect(result).toBeInstanceOf(CommandResult);
    expect(result).toMatchObject({ ...EXIT, ...fields, stdout: "", stderr: "", execId: EXEC });
    expect(result.exit).toEqual({ ...EXIT, ...fields });
  });

  it("run without an exit frame throws CommandIncompleteError with the output so far", async () => {
    api.on("execInWorkspaceSandbox", () => streamed([sseText([START, ["stdout", { data: "partial" }, "2"]])]));
    const error = (await failure(async () => (await connect()).commands.run("long"))) as CommandIncompleteError;
    expect(error).toBeInstanceOf(CommandIncompleteError);
    expect(error).toBeInstanceOf(SandboxError);
    expect(error).toMatchObject({ execId: EXEC, stdout: "partial", stderr: "", code: "command_incomplete" });
    expect(error.message).toMatch(/unknown/u);
    expect(api.callsTo("execInWorkspaceSandbox")).toHaveLength(1);
  });

  it("run on an error frame throws CommandFailedError", async () => {
    api.on("execInWorkspaceSandbox", () => streamed([sseText([START, ["error", { message: "runtime lost" }, "2"]])]));
    const error = (await failure(async () => (await connect()).commands.run("x"))) as CommandFailedError;
    expect(error).toBeInstanceOf(CommandFailedError);
    expect(error.message).toContain("runtime lost");
    expect(error.execId).toBe(EXEC);
  });

  it("run is never retried, whatever the status", async () => {
    api.on("execInWorkspaceSandbox", () => json(503, { error: "omega_service_unavailable", requestId: "gw" }));
    expect(await failure(async () => (await connect()).commands.run("x"))).toBeInstanceOf(UnavailableError);
    expect(api.callsTo("execInWorkspaceSandbox")).toHaveLength(1);
  });

  it("a stream dropped after it opened is CommandIncompleteError; its cause is the SandboxConnectionError", async () => {
    const reset = Object.assign(new TypeError("terminated"), { cause: Object.assign(new Error("socket hang up"), { code: "ECONNRESET" }) });
    api.on("execInWorkspaceSandbox", () => streamed([sseText([START, ["stdout", { data: "so far" }, "2"]])], { fail: reset }));
    const error = (await failure(async () => (await connect()).commands.run("x"))) as CommandIncompleteError;
    expect(error).toBeInstanceOf(CommandIncompleteError);
    expect(error).toMatchObject({ execId: EXEC, stdout: "so far", code: "command_incomplete" });
    expect(error.cause).toBeInstanceOf(SandboxConnectionError);
    expect(error.cause).toMatchObject({ kind: "connection", possiblyApplied: true });
    expect(error.message).toMatch(/unknown/u);
    expect(api.callsTo("execInWorkspaceSandbox")).toHaveLength(1);
  });

  it("an idle stream is CommandIncompleteError caused by a timeout", async () => {
    const origin = resolveSandboxOrigin({ OMEGA_BASE_URL: BASE, FI_API_KEY: API_KEY, FI_SECRET_KEY: SECRET_KEY });
    const core = new PlatformCore(
      { resolveOrigin: () => origin, table: PLATFORM_OPERATIONS, fetch: api.fetch },
      { timeoutMs: 5_000, streamIdleTimeoutMs: 30 },
    );
    api.on("execInWorkspaceSandbox", () => streamed([sseText([START])], { hold: true }));
    const sbx = await new Sandboxes({ _platform: core }).connect(SID);
    const error = (await failure(() => sbx.commands.run("sleep 60"))) as CommandIncompleteError;
    expect(error).toBeInstanceOf(CommandIncompleteError);
    expect(error.cause).toBeInstanceOf(SandboxConnectionError);
    expect(error.cause).toMatchObject({ kind: "timeout" });
  });

  it("stream yields typed frames; leaving the loop closes the connection", async () => {
    let cancelled = false;
    api.on("execInWorkspaceSandbox", () =>
      streamed([sseText([START, ["stdout", { data: "tick" }, "2"]])], { hold: true, onCancel: () => { cancelled = true; } }));
    const stream = await (await connect()).commands.stream("watch");
    const events: string[] = [];
    for await (const frame of stream) {
      events.push(frame.event);
      if (frame.event === "stdout") break;
    }
    expect(events).toEqual(["started", "stdout"]);
    expect(stream.execId).toBe(EXEC);
    expect(cancelled).toBe(true);
  });

  it("stream throws CommandIncompleteError after the frames when no exit frame came", async () => {
    api.on("execInWorkspaceSandbox", () => streamed([sseText([START])]));
    const stream = await (await connect()).commands.stream("x");
    const events: string[] = [];
    const error = await failure(async () => {
      for await (const frame of stream) events.push(frame.event);
    });
    expect(events).toEqual(["started"]);
    expect(error).toBeInstanceOf(CommandIncompleteError);
  });

  it("cancel sends the exec id", async () => {
    const response = await (await connect()).commands.cancel(EXEC);
    expect(response.cancelled).toBe(true);
    expect(api.callsTo("cancelWorkspaceSandboxExec")[0]!.params).toEqual({ id: SID, execId: EXEC });
  });
});

describe("files", () => {
  it("read returns text for utf8 and bytes for base64", async () => {
    api.on("readWorkspaceSandboxFile",
      () => api.ok("readWorkspaceSandboxFile", { file: { path: "a.txt", encoding: "utf8", content: "hello" } }),
      () => api.ok("readWorkspaceSandboxFile", { file: { path: "a.bin", encoding: "base64", content: "AAEC/w==", bytes: 4 } }));
    const sbx = await connect();
    expect(await sbx.files.read("a.txt", { maxBytes: 100 })).toBe("hello");
    expect(Array.from((await sbx.files.read("a.bin")) as Uint8Array)).toEqual([0, 1, 2, 255]);
    expect(api.callsTo("readWorkspaceSandboxFile")[0]!.query.get("maxBytes")).toBe("100");
  });

  it("write sends text as utf8 and bytes as base64; upload sends raw bytes", async () => {
    const sbx = await connect();
    await sbx.files.write("a.txt", "hi");
    await sbx.files.write("a.bin", new Uint8Array([0, 1, 2, 255]));
    await sbx.files.upload("dir/big.bin", new Uint8Array([9, 8, 7]));
    const [text, binary] = api.callsTo("writeWorkspaceSandboxFile");
    expect(text!.json).toEqual({ content: "hi", encoding: "utf8" });
    expect(binary!.json).toEqual({ content: "AAEC/w==", encoding: "base64" });
    const upload = api.callsTo("uploadWorkspaceSandboxFile")[0]!;
    expect(upload.params.path).toBe("dir/big.bin");
    expect(Array.from(new Uint8Array(await upload.request.clone().arrayBuffer()))).toEqual([9, 8, 7]);
  });

  it("list, remove, move and makeDir call their operations", async () => {
    const sbx = await connect();
    expect(await sbx.files.list()).toEqual([]);
    await sbx.files.remove("old", { recursive: true });
    await sbx.files.move("a.txt", "b.txt");
    await sbx.files.makeDir("dir/sub");
    expect(api.callsTo("listWorkspaceSandboxFiles")[0]!.query.get("path")).toBe(".");
    expect(api.callsTo("deleteWorkspaceSandboxPath")[0]!.query.get("recursive")).toBe("true");
    expect(api.callsTo("moveWorkspaceSandboxPath")[0]!.json).toEqual({ from: "a.txt", to: "b.txt" });
    expect(api.callsTo("createWorkspaceSandboxFolder")[0]!.params.path).toBe("dir/sub");
  });

  it("download returns bytes; downloadTo renames a finished temporary file", async () => {
    const sbx = await connect();
    expect(Array.from(await sbx.files.download("a.bin"))).toEqual([0, 1, 2, 255]);
    const dir = await mkdtemp(join(tmpdir(), "sbx-download-"));
    try {
      const target = join(dir, "a.bin");
      expect(await sbx.files.downloadTo("a.bin", target)).toBe(target);
      expect(Array.from(await readFile(target))).toEqual([0, 1, 2, 255]);
      expect(await readdir(dir)).toEqual(["a.bin"]);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
  });
});

describe("lifecycle, settings, snapshots and network policy", () => {
  it("list and settings are static reads from the environment; settings are read-only", async () => {
    hostedEnv();
    const list = await Sandbox.list();
    expect(list.sandboxes).toEqual([]);
    expect(list.caps).toBeDefined();
    expect((await Sandbox.settings()).caps).toBeDefined();
    expect(api.calls.map((c) => c.operation.operationId)).toEqual(["listWorkspaceSandboxes", "getWorkspaceSandboxSettings"]);
    const statics = Sandbox as unknown as Record<string, unknown>;
    for (const name of ["updateSettings", "setSettings", "putSettings"]) expect([name, statics[name]]).toEqual([name, undefined]);
  });

  it("refresh, update, hibernate and resume keep info current", async () => {
    const sbx = await connect();
    expect(sbx.info.state).toBe("active");
    expect((await sbx.hibernate()).state).toBe("hibernated");
    expect(sbx.state).toBe("hibernated");
    api.on("resumeWorkspaceSandbox", () => api.ok("resumeWorkspaceSandbox", { sandbox: { id: SID, state: "active" } }));
    expect((await sbx.resume()).state).toBe("active");
    api.on("updateWorkspaceSandbox", () => api.ok("updateWorkspaceSandbox", { sandbox: { id: SID, name: "renamed" } }));
    expect((await sbx.update({ name: "renamed" })).name).toBe("renamed");
    expect(api.callsTo("updateWorkspaceSandbox")[0]!.json).toEqual({ name: "renamed" });
    api.on("getWorkspaceSandbox", () => api.ok("getWorkspaceSandbox", { sandbox: { id: SID, name: "fresh" } }));
    expect((await sbx.refresh()).info.name).toBe("fresh");
    expect(await sbx.activity()).toEqual([]);
  });

  it("delete returns the final record, and a sandbox already gone is not an error", async () => {
    const sbx = await connect();
    expect((await sbx.delete()).state).toBe("destroyed");
    api.on("destroyWorkspaceSandbox", () => json(404, { code: "not_found", message: "gone" }));
    const again = await connect();
    expect((await again.delete()).state).toBe("destroyed");
    expect(again.state).toBe("destroyed");
  });

  it("restore returns a new sandbox and leaves the source unchanged", async () => {
    const sbx = await connect();
    const before = JSON.stringify(sbx.info);
    const snapshot = await sbx.snapshots.create();
    expect(snapshot.id).toBe(SNAP);
    expect(await sbx.snapshots.list()).toEqual([]);
    const restored = await sbx.snapshots.restore(SNAP, { name: "copy" });
    expect(restored).toBeInstanceOf(Sandbox);
    expect(restored.id).toBe(SID2);
    expect(restored).not.toBe(sbx);
    expect(JSON.stringify(sbx.info)).toBe(before);
    expect(api.callsTo("restoreWorkspaceSandboxSnapshot")[0]!.params).toEqual({ id: SID, snapshotId: SNAP });
  });

  it("networkPolicy.get returns the policy with its etag", async () => {
    api.on("getWorkspaceSandboxNetworkPolicy",
      () => api.ok("getWorkspaceSandboxNetworkPolicy", { policy: { desiredRevision: 4 } }, { etag: '"4"' }),
      () => api.ok("getWorkspaceSandboxNetworkPolicy", { policy: { desiredRevision: 6 } }));
    const sbx = await connect();
    const policy = await sbx.networkPolicy.get();
    expect(policy).toMatchObject({ desiredRevision: 4, etag: '"4"' });
    expect(policy.desired).toBeDefined();
    // without the header, the etag is the quoted desired revision
    expect((await sbx.networkPolicy.get()).etag).toBe('"6"');
  });

  it("networkPolicy.set reads first and sends that ETag unless ifMatch is given", async () => {
    api.on("getWorkspaceSandboxNetworkPolicy", () => api.ok("getWorkspaceSandboxNetworkPolicy", {}, { etag: '"4"' }));
    const sbx = await connect();
    await sbx.networkPolicy.set({ version: 1, mode: "allow-all-public" });
    expect(api.calls.map((c) => c.operation.operationId).slice(1)).toEqual(["getWorkspaceSandboxNetworkPolicy", "putWorkspaceSandboxNetworkPolicy"]);
    await sbx.networkPolicy.set({ version: 1, mode: "off" }, { ifMatch: '"7"' });
    const puts = api.callsTo("putWorkspaceSandboxNetworkPolicy");
    expect(puts.map((c) => c.request.headers.get("if-match"))).toEqual(['"4"', '"7"']);
    expect(api.callsTo("getWorkspaceSandboxNetworkPolicy")).toHaveLength(1);
  });

  const disposable = typeof (Symbol as { asyncDispose?: symbol }).asyncDispose === "symbol" ? it : it.skip;

  disposable("await using deletes the sandbox when the block ends", async () => {
    {
      await using sbx = await connect();
      expect(sbx.id).toBe(SID);
    }
    expect(api.callsTo("destroyWorkspaceSandbox")).toHaveLength(1);
  });

  disposable("await using never hides the block's error behind a failed delete", async () => {
    api.on("destroyWorkspaceSandbox", () => json(503, { error: "omega_service_unavailable", requestId: "gw" }));
    const bodyError = new Error("the block failed");
    const caught = await failure(async () => {
      await using sbx = await connect();
      expect(sbx.id).toBe(SID);
      throw bodyError;
    });
    expect((caught as { suppressed?: unknown }).suppressed).toBe(bodyError);
    expect((caught as { error?: unknown }).error).toBeInstanceOf(UnavailableError);
  });
});
