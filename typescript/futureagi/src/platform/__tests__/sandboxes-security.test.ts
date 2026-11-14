/**
 * Where sandbox credentials may go and what server text may carry, against the contract-driven mock API: hosted
 * keys from the environment go only to a Future AGI host over HTTPS (or loopback) unless
 * FI_ALLOW_CUSTOM_PLATFORM_URL or allowCustomBaseUrl opens another host, with the client's one-time notice; a
 * self-hosted Bearer token goes only to loopback without allowCustomBaseUrl; the environment path sends
 * FI_EXTRA_HEADERS; scope header names are refused in extra headers; exec error text is scrubbed and capped;
 * downloads are capped; a client's resolved origin never shows under inspection. The statics build their own
 * client, so their requests are caught at the global `fetch`. Synthetic credentials only; no socket.
 */
import { mkdir, mkdtemp, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { inspect } from "node:util";

import { ExtraHeadersError, parseExtraHeaders, validateExtraHeaders } from "../../extra-headers";
import { FutureAGIClient } from "../../futureagi-client";
import * as E from "../../_core/errors";
import { resetWarnings } from "../../_core/origins";
import { PlatformCore } from "../../_core/platform-base";
import { BODY_LIMITS } from "../../_core/request";
import { PLATFORM_OPERATIONS } from "../../generated/platform/policy.gen";
import { CommandFailedError, Sandbox, SandboxError, Sandboxes } from "../../sandbox";
import { resolveSandboxOrigin } from "../../sandbox/config";
import type { DownloadOptions, ExecFrame } from "../../sandbox/wire";
import { EXEC, SID, SandboxApi, sseText, streamed } from "../../sandbox/__fixtures__/openapi-mock";

const API_KEY = "sbx-sec-api-key-not-valid";
const SECRET_KEY = "sbx-sec-secret-key-not-valid";
const TOKEN = "sbx-sec-bearer-token-not-valid";
const ENV_VALUE = "sbx-sec-env-value-not-valid";
const PROXY_VALUE = "sbx-sec-proxy-value-not-valid";
const HOSTED_ORIGIN = "https://sandbox-fixture.futureagi.com";
const HOSTED = `${HOSTED_ORIGIN}/omega/api`;
const ATTACKER = "https://attacker.example/omega/api";
const ENV = [
  "FI_BASE_URL", "FI_PLATFORM_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_TOKEN", "FI_WORKSPACE_ID",
  "FI_ORGANIZATION_ID", "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS",
  "OMEGA_BASE_URL", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
];
const START = ["started", { execId: EXEC, sandboxId: SID }, "1"] as const;
const EXIT = { exitCode: 0, timedOut: false, cancelled: false, truncated: false, durationMs: 3, stdoutBytes: 0, stderrBytes: 0 };
const EXEC_OP = "execInWorkspaceSandbox";
const DOWNLOAD_OP = "downloadWorkspaceSandboxFile";

let saved: [string, string | undefined][] = [];
let warn: jest.SpyInstance;
let globalFetch: jest.SpyInstance;
/** The API the global `fetch` (the statics' client) reaches. */
let routed: SandboxApi;
beforeEach(() => {
  saved = ENV.map((key) => [key, process.env[key]]);
  for (const key of ENV) delete process.env[key];
  resetWarnings();
  warn = jest.spyOn(console, "warn").mockImplementation(() => undefined);
  routed = new SandboxApi(HOSTED);
  globalFetch = jest.spyOn(globalThis, "fetch").mockImplementation((input, init) => routed.fetch(input as RequestInfo, init));
});
afterEach(() => {
  globalFetch.mockRestore();
  warn.mockRestore();
  for (const [key, value] of saved) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  expect(routed.problems).toEqual([]);
});

const keysEnv = (base: string, extra: Record<string, string> = {}): void => {
  Object.assign(process.env, { OMEGA_BASE_URL: base, FI_API_KEY: API_KEY, FI_SECRET_KEY: SECRET_KEY, ...extra });
};
const failure = (call: () => PromiseLike<unknown>): Promise<unknown> => Promise.resolve().then(call).then(() => undefined, (e: unknown) => e);
/** The client's one-time notice that keys leave the Future AGI zone. */
const notices = (): string[] => warn.mock.calls.map((args: unknown[]) => String(args[0])).filter((line) => line.includes("outside the Future AGI zone"));
const keysClient = (api: SandboxApi): FutureAGIClient =>
  new FutureAGIClient({ apiKey: API_KEY, secretKey: SECRET_KEY, platformBaseUrl: api.base, fetch: api.fetch });

async function drain(stream: AsyncIterable<ExecFrame>): Promise<ExecFrame[]> {
  const frames: ExecFrame[] = [];
  for await (const frame of stream) frames.push(frame);
  return frames;
}

describe("hosted keys from the environment go only to Future AGI hosts", () => {
  it.each([
    ATTACKER,
    "https://attacker.example:8443/omega/api",
    "https://futureagi.com.attacker.example/omega/api",
    "https://attackerfutureagi.com/omega/api",
    "http://attacker.example/omega/api",
    "http://127.0.0.2:9/omega/api",
  ])("a keys request to %s is refused before anything is sent, naming the host only", async (base) => {
    keysEnv(base);
    for (const call of [() => Sandbox.list(), () => Sandbox.create({ name: "demo" }), () => Sandbox.connect(SID), () => Sandbox.settings()]) {
      const error = await failure(call);
      expect(error).toBeInstanceOf(E.HostNotAllowedError);
      expect(error).toBeInstanceOf(E.ConfigurationError);
      expect(error).toMatchObject({ code: "host_not_allowed" });
      const text = String(error);
      expect(text).toContain(`to ${new URL(base).host}:`);
      expect(text).not.toContain("/omega/api");
      expect(text).toContain("FI_ALLOW_CUSTOM_PLATFORM_URL");
      expect(text).toContain("FUTUREAGI_OMEGA_API_KEY");
      for (const secret of [API_KEY, SECRET_KEY]) expect(text).not.toContain(secret);
    }
    expect(globalFetch).not.toHaveBeenCalled();
    expect(routed.calls).toEqual([]);
    expect(notices()).toEqual([]);
  });

  it.each([HOSTED, "https://api-eu.futureagi.com/omega/api", "https://futureagi.com/omega/api"])(
    "a Future AGI host over HTTPS gets the keys, with no notice: %s",
    async (base) => {
      routed = new SandboxApi(base);
      keysEnv(base);
      await Sandbox.list();
      expect(routed.calls).toHaveLength(1);
      expect(routed.calls[0]!.request.headers.get("x-api-key")).toBe(API_KEY);
      expect(warn).not.toHaveBeenCalled();
    },
  );

  it.each(["http://127.0.0.1:9/omega/api", "http://localhost:9/omega/api"])("loopback gets the keys, as the client's rule says: %s", async (base) => {
    routed = new SandboxApi(base);
    keysEnv(base);
    await Sandbox.list();
    expect(routed.calls).toHaveLength(1);
    expect(warn).not.toHaveBeenCalled();
  });

  it.each(["1", "true", " YES "])("FI_ALLOW_CUSTOM_PLATFORM_URL=%j opens another host, with the client's notice once", async (flag) => {
    routed = new SandboxApi(ATTACKER);
    keysEnv(ATTACKER, { FI_ALLOW_CUSTOM_PLATFORM_URL: flag });
    await Sandbox.list();
    await Sandbox.list();
    expect(routed.calls).toHaveLength(2);
    expect(routed.calls[0]!.request.headers.get("x-api-key")).toBe(API_KEY);
    expect(notices()).toHaveLength(1);
    expect(notices()[0]).toContain("attacker.example");
    expect(notices()[0]).not.toContain(API_KEY);
  });

  it.each(["0", "false", "on", ""])("FI_ALLOW_CUSTOM_PLATFORM_URL=%j does not", async (flag) => {
    keysEnv(ATTACKER, { FI_ALLOW_CUSTOM_PLATFORM_URL: flag });
    expect(await failure(() => Sandbox.list())).toBeInstanceOf(E.HostNotAllowedError);
    expect(globalFetch).not.toHaveBeenCalled();
  });

  it("allowCustomBaseUrl in code opens another host for the keys, with the same notice once", async () => {
    const env = { OMEGA_BASE_URL: ATTACKER, FI_API_KEY: API_KEY, FI_SECRET_KEY: SECRET_KEY };
    expect(() => resolveSandboxOrigin(env)).toThrow(E.HostNotAllowedError);
    expect(() => resolveSandboxOrigin(env, { allowCustomBaseUrl: false })).toThrow(E.HostNotAllowedError);
    const origin = resolveSandboxOrigin(env, { allowCustomBaseUrl: true });
    expect(origin).toMatchObject({ mode: "keys", source: "env", custom: true });
    resolveSandboxOrigin(env, { allowCustomBaseUrl: true });
    expect(notices()).toHaveLength(1);
    const api = new SandboxApi(ATTACKER);
    const core = new PlatformCore({ resolveOrigin: () => origin, table: PLATFORM_OPERATIONS, fetch: api.fetch });
    await new Sandboxes({ _platform: core }).list();
    expect(api.calls).toHaveLength(1);
    expect(api.calls[0]!.request.headers.get("x-api-key")).toBe(API_KEY);
    expect(api.problems).toEqual([]);
  });

  it("a Future AGI origin is not custom", () => {
    expect(resolveSandboxOrigin({ OMEGA_BASE_URL: HOSTED, FI_API_KEY: API_KEY, FI_SECRET_KEY: SECRET_KEY })).toMatchObject({ custom: false });
  });

  it("client.sandboxes keeps the client's own host rule for keys", async () => {
    const api = new SandboxApi(ATTACKER);
    // keys and origin from one place (arguments): the client's rule lets them through
    await keysClient(api).sandboxes.list();
    expect(api.calls).toHaveLength(1);
    // keys from the environment, the origin from an argument: refused unless allowCustomPlatformUrl
    Object.assign(process.env, { FI_API_KEY: API_KEY, FI_SECRET_KEY: SECRET_KEY });
    const error = await failure(() => new FutureAGIClient({ platformBaseUrl: ATTACKER, fetch: api.fetch }).sandboxes.list());
    expect(error).toBeInstanceOf(E.HostNotAllowedError);
    expect(api.calls).toHaveLength(1);
    expect(api.problems).toEqual([]);
  });
});

describe("a self-hosted Bearer token goes only to loopback without allowCustomBaseUrl", () => {
  it("from the environment, a Future AGI host is refused too", async () => {
    Object.assign(process.env, { OMEGA_BASE_URL: HOSTED, FUTUREAGI_OMEGA_API_KEY: TOKEN, FI_ALLOW_CUSTOM_PLATFORM_URL: "1" });
    const error = await failure(() => Sandbox.list());
    expect(error).toBeInstanceOf(E.HostNotAllowedError);
    expect(String(error)).toContain("allowCustomBaseUrl");
    expect(String(error)).not.toContain(TOKEN);
    expect(globalFetch).not.toHaveBeenCalled();
  });

  it("from the environment, loopback is used", async () => {
    routed = new SandboxApi("http://127.0.0.1:9/omega/api");
    Object.assign(process.env, { OMEGA_BASE_URL: routed.base, FUTUREAGI_OMEGA_API_KEY: TOKEN });
    await Sandbox.list();
    expect(routed.calls[0]!.request.headers.get("authorization")).toBe(`Bearer ${TOKEN}`);
  });
});

describe("FI_EXTRA_HEADERS on the environment path", () => {
  it("the statics send it under OMEGA_BASE_URL, never over the SDK's own headers", async () => {
    keysEnv(HOSTED, { FI_EXTRA_HEADERS: `X-Team=team-env-value;X-Proxy-Identity=${PROXY_VALUE};X-Request-Tag=tag-1` });
    await Sandbox.list();
    const { request } = routed.calls[0]!;
    expect(request.headers.get("x-team")).toBe("team-env-value");
    expect(request.headers.get("x-proxy-identity")).toBe(PROXY_VALUE);
    expect(request.headers.get("x-request-tag")).toBe("tag-1");
    expect(request.headers.get("x-api-key")).toBe(API_KEY);
  });

  it("is read on each request", async () => {
    keysEnv(HOSTED, { FI_EXTRA_HEADERS: "X-Team=first" });
    await Sandbox.list();
    process.env.FI_EXTRA_HEADERS = "X-Team=second";
    await Sandbox.list();
    expect(routed.calls.map((call) => call.request.headers.get("x-team"))).toEqual(["first", "second"]);
  });

  it.each(["x-omega-workspace", "X-Workspace-Id", "X-Organization-Id", "x-omega-org", "X-Api-Key"])(
    "naming %s refuses the call before anything is sent",
    async (name) => {
      keysEnv(HOSTED, { FI_EXTRA_HEADERS: `${name}=extra-header-value` });
      const error = await failure(() => Sandbox.list());
      expect(error).toBeInstanceOf(ExtraHeadersError);
      expect(String(error)).not.toContain("extra-header-value");
      expect(globalFetch).not.toHaveBeenCalled();
    },
  );
});

describe("scope header names are refused in extra headers, in both credential modes", () => {
  it.each(["X-Workspace-Id", "x-organization-id", "X-Omega-Workspace", "X-OMEGA-ORG"])("%s", (name) => {
    const refusals: Array<() => unknown> = [
      () => parseExtraHeaders(`${name}=scope-extra-value`),
      () => validateExtraHeaders({ [name]: "scope-extra-value" }),
      () => validateExtraHeaders(`${name}=scope-extra-value`),
      () => new FutureAGIClient({ apiKey: API_KEY, secretKey: SECRET_KEY, extraHeaders: { [name]: "scope-extra-value" } }),
      () => new FutureAGIClient({ platformToken: TOKEN, extraHeaders: { [name]: "scope-extra-value" } }),
    ];
    for (const refusal of refusals) {
      let error: unknown;
      try {
        refusal();
      } catch (e) {
        error = e;
      }
      expect(error).toBeInstanceOf(ExtraHeadersError);
      expect((error as Error).message).toMatch(/cannot be set here/u);
      expect((error as Error).message).toMatch(/FI_WORKSPACE_ID/u);
      expect((error as Error).message).not.toContain("scope-extra-value");
    }
  });

  it("other names still pass", () => {
    expect(parseExtraHeaders("X-Workspace=a;X-Org-Tag=b")).toEqual({ "X-Workspace": "a", "X-Org-Tag": "b" });
  });
});

describe("exec error text is scrubbed and capped as an HTTP error body's message is", () => {
  const echoed = `lost ${API_KEY} ${SECRET_KEY} ${ENV_VALUE} ${PROXY_VALUE}`;
  const scrubbed = "lost [redacted] [redacted] [redacted] [redacted]";

  /** A client whose platform origin is under its base URL, so its extra headers go on sandbox calls. */
  const client = (api: SandboxApi): FutureAGIClient =>
    new FutureAGIClient({ apiKey: API_KEY, secretKey: SECRET_KEY, baseUrl: HOSTED_ORIGIN, fetch: api.fetch, extraHeaders: { "X-Proxy-Identity": PROXY_VALUE } });

  it("an error frame's message has every secret the request carried replaced, before CommandFailedError", async () => {
    const api = new SandboxApi(HOSTED);
    api.on(EXEC_OP, () => streamed([sseText([START, ["error", { message: echoed }, "2"]])]));
    const sbx = await client(api).sandboxes.connect(SID);
    const error = (await failure(() => sbx.commands.run("x", { env: { SERVICE_PASSWORD: ENV_VALUE } }))) as CommandFailedError;
    expect(error).toBeInstanceOf(CommandFailedError);
    expect(error.message).toBe(`the command failed on the server: ${scrubbed}`);
    const dump = String(error) + JSON.stringify(error) + inspect(error, { depth: 20, showHidden: true, customInspect: false });
    for (const secret of [API_KEY, SECRET_KEY, ENV_VALUE, PROXY_VALUE]) expect(dump).not.toContain(secret);
    // the request carried every one of them
    const sent = api.callsTo(EXEC_OP)[0]!;
    expect(sent.json).toEqual({ command: "x", env: { SERVICE_PASSWORD: ENV_VALUE } });
    expect(sent.request.headers.get("x-proxy-identity")).toBe(PROXY_VALUE);
    expect(sent.request.headers.get("x-api-key")).toBe(API_KEY);
    expect(api.problems).toEqual([]);
  });

  it("client.sandboxes.commands.run yields the scrubbed frame", async () => {
    const api = new SandboxApi(HOSTED);
    api.on(EXEC_OP, () => streamed([sseText([START, ["error", { message: echoed }, "2"]])]));
    const frames = await drain(await client(api).sandboxes.commands.run(SID, { body: { command: "x", env: { SERVICE_PASSWORD: ENV_VALUE } } }));
    expect(frames[1]).toEqual({ event: "error", id: "2", data: { message: scrubbed } });
    expect(api.problems).toEqual([]);
  });

  it("an exit frame's error is scrubbed the same way; the command's own output is passed as sent", async () => {
    const api = new SandboxApi(HOSTED);
    api.on(EXEC_OP, () =>
      streamed([sseText([START, ["stdout", { data: `value=${ENV_VALUE}\n` }, "2"],
        ["exit", { ...EXIT, exitCode: null, error: `spawn failed for ${ENV_VALUE} with ${API_KEY}` }, "3"]])]));
    const sbx = await client(api).sandboxes.connect(SID);
    const result = await sbx.commands.run("x", { env: { SERVICE_PASSWORD: ENV_VALUE } });
    expect(result.error).toBe("spawn failed for [redacted] with [redacted]");
    expect(result.exit.error).toBe("spawn failed for [redacted] with [redacted]");
    expect(result.stdout).toBe(`value=${ENV_VALUE}\n`);
    expect(api.problems).toEqual([]);
  });

  it("long server text is put on one line and capped", async () => {
    const api = new SandboxApi(HOSTED);
    api.on(EXEC_OP, () => streamed([sseText([START, ["error", { message: `first line\n\n  ${"x".repeat(2000)}` }, "2"]])]));
    const sbx = await client(api).sandboxes.connect(SID);
    const error = (await failure(() => sbx.commands.run("x"))) as CommandFailedError;
    const said = error.message.slice("the command failed on the server: ".length);
    expect(said.startsWith("first line x")).toBe(true);
    expect(said.endsWith("...")).toBe(true);
    expect(said).toHaveLength(503);
    expect(api.problems).toEqual([]);
  });

  it("the environment path scrubs FI_EXTRA_HEADERS values too", async () => {
    keysEnv(HOSTED, { FI_EXTRA_HEADERS: `X-Proxy-Identity=${PROXY_VALUE}` });
    routed.on(EXEC_OP, () => streamed([sseText([START, ["error", { message: echoed }, "2"]])]));
    const sbx = await Sandbox.connect(SID);
    const error = (await failure(() => sbx.commands.run("x", { env: { SERVICE_PASSWORD: ENV_VALUE } }))) as CommandFailedError;
    expect(error).toBeInstanceOf(CommandFailedError);
    expect(error.message).toBe(`the command failed on the server: ${scrubbed}`);
  });
});

describe("downloads are capped", () => {
  const sandbox = async (api: SandboxApi): Promise<Sandbox> => keysClient(api).sandboxes.connect(SID);

  it("a file over maxBytes is refused, naming the limit and the keyword; it is not retried", async () => {
    const api = new SandboxApi(HOSTED);
    const sbx = await sandbox(api);
    const error = (await failure(() => sbx.files.download("a.bin", { maxBytes: 3 }))) as E.PayloadTooLargeError;
    expect(error).toBeInstanceOf(E.PayloadTooLargeError);
    expect(error).toBeInstanceOf(SandboxError);
    expect(error).toMatchObject({ local: true, limitBytes: 3, code: "download_too_large", operation: "sandboxes.files.download" });
    expect(error.message).toContain("3 bytes");
    expect(error.message).toContain("maxBytes");
    expect(api.callsTo(DOWNLOAD_OP)).toHaveLength(1);
    expect(Array.from(await sbx.files.download("a.bin", { maxBytes: 4 }))).toEqual([0, 1, 2, 255]);
    expect(api.problems).toEqual([]);
  });

  it("a body without a length is counted as it arrives", async () => {
    const api = new SandboxApi(HOSTED);
    api.on(DOWNLOAD_OP, () => streamed([new Uint8Array([1, 2]), new Uint8Array([3, 4])], { contentType: "application/octet-stream" }));
    const options: DownloadOptions = { maxBytes: 3 };
    const error = await failure(() => keysClient(api).sandboxes.files.download(SID, "a.bin", options));
    expect(error).toMatchObject({ limitBytes: 3, code: "download_too_large" });
    expect(api.problems).toEqual([]);
  });

  it("the default limit is the upload limit, 64 MiB; a larger announced length is refused, and maxBytes raises it", async () => {
    expect(BODY_LIMITS.bundle).toBe(64 * 1024 * 1024);
    const api = new SandboxApi(HOSTED);
    const announced = String(BODY_LIMITS.bundle + 1);
    api.on(DOWNLOAD_OP, () =>
      new Response(new Uint8Array([7, 8]), { status: 200, headers: { "content-type": "application/octet-stream", "content-length": announced } }));
    const error = await failure(() => keysClient(api).sandboxes.files.download(SID, "big.bin"));
    expect(error).toBeInstanceOf(E.PayloadTooLargeError);
    expect(error).toMatchObject({ limitBytes: BODY_LIMITS.bundle, code: "download_too_large" });
    const sbx = await sandbox(api);
    expect(Array.from(await sbx.files.download("big.bin", { maxBytes: BODY_LIMITS.bundle + 1 }))).toEqual([7, 8]);
    expect(api.problems).toEqual([]);
  });

  it.each([-1, 1.5, Number.NaN])("maxBytes %p is refused before anything is sent", async (maxBytes) => {
    const api = new SandboxApi(HOSTED);
    const sbx = await sandbox(api);
    const error = await failure(() => sbx.files.download("a.bin", { maxBytes }));
    expect(error).toBeInstanceOf(E.ConfigurationError);
    expect(error).toMatchObject({ code: "invalid_max_bytes" });
    expect(api.callsTo(DOWNLOAD_OP)).toEqual([]);
  });

  it("downloadTo leaves no file behind: not over the limit, and not when the rename fails", async () => {
    const api = new SandboxApi(HOSTED);
    const sbx = await sandbox(api);
    const dir = await mkdtemp(join(tmpdir(), "sbx-download-cap-"));
    try {
      expect(await failure(() => sbx.files.downloadTo("a.bin", join(dir, "a.bin"), { maxBytes: 3 }))).toBeInstanceOf(E.PayloadTooLargeError);
      expect(await readdir(dir)).toEqual([]);
      // the target is a folder: the temporary file is written, the rename fails, and the temporary file is removed
      await mkdir(join(dir, "folder"));
      const renameFailure = await failure(() => sbx.files.downloadTo("a.bin", join(dir, "folder")));
      expect(typeof (renameFailure as { code?: unknown }).code).toBe("string");
      expect(await readdir(dir)).toEqual(["folder"]);
      expect(await readdir(join(dir, "folder"))).toEqual([]);
    } finally {
      await rm(dir, { recursive: true, force: true });
    }
    expect(api.problems).toEqual([]);
  });
});

describe("a client's resolved origin never shows", () => {
  it.each(["keys", "bearer"] as const)("%s: util.inspect and JSON.stringify of a client after a sandbox call show no credential", async (mode) => {
    const api = new SandboxApi(mode === "keys" ? HOSTED : "http://127.0.0.1:9/omega/api");
    const c = new FutureAGIClient({
      ...(mode === "keys" ? { apiKey: API_KEY, secretKey: SECRET_KEY } : { platformToken: TOKEN }),
      platformBaseUrl: api.base,
      fetch: api.fetch,
    });
    await c.sandboxes.list();
    const copy = c.withOptions({ retries: 0 });
    await copy.sandboxes.list();
    for (const target of [c, copy, c._platform, copy._platform, c._platform.shared]) {
      const dump = inspect(target, { depth: null }) + JSON.stringify(target);
      for (const secret of [API_KEY, SECRET_KEY, TOKEN]) expect(dump).not.toContain(secret);
    }
    // the origin is still resolved once and used
    expect(c._platform.origin().mode).toBe(mode);
    expect(api.calls).toHaveLength(2);
    for (const { request } of api.calls) {
      if (mode === "keys") expect(request.headers.get("x-api-key")).toBe(API_KEY);
      else expect(request.headers.get("authorization")).toBe(`Bearer ${TOKEN}`);
    }
    expect(api.problems).toEqual([]);
  });
});
