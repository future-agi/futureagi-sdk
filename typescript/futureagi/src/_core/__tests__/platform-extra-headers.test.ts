/**
 * `FI_EXTRA_HEADERS` and `extraHeaders` on the platform executor: the same scoped, per-request headers
 * the core namespaces send (extra-headers.ts). A platform call and a `withOptions` copy carry them when
 * the platform origin is under `baseUrl`; the setting is read on each call; the SDK's own headers and a
 * declared per-call header win; an origin off `baseUrl` gets none; a malformed setting throws before
 * anything is sent; a reflected value never reaches an error. No sockets: a scripted fetch records every
 * request, and every header value here is made up.
 */
import { EXTRA_HEADERS_ENV, ExtraHeadersError } from "../../extra-headers";
import { FutureAGIClient, type FutureAGIClientOptions } from "../../futureagi-client";
import { json, OPS, Script } from "../__fixtures__/platform";
import { FutureAGIAPIError } from "../errors";
import type { OperationTable } from "../policy";

// low entropy on purpose (never a real token)
const TOKEN = "fake-identity-token-" + "x".repeat(12);
const PROXY = `Bearer ${TOKEN}`;
const BASE = "http://127.0.0.1:9";
const CAPABILITIES = "platform.capabilities.get";
const CAPABILITIES_PATH = "/omega/api/workspace/capabilities";
const TABLE: OperationTable = {
  ...OPS,
  "team.get": { name: "team.get", family: "platform", method: "GET", path: "/workspace/team", headers: ["x-team"] },
};
const SAVED = ["FI_EXTRA_HEADERS", "FI_PLATFORM_BASE_URL", "FI_PLATFORM_TOKEN", "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID"];

function client(script: Script, options: FutureAGIClientOptions = {}): FutureAGIClient {
  const c = new FutureAGIClient({
    apiKey: "k-test-1234",
    secretKey: "s-test-1234",
    baseUrl: BASE,
    retries: 0,
    fetch: script.fetch,
    ...options,
  });
  c._platform.shared.table = TABLE;
  return c;
}

const pathOf = (request: Request): string => new URL(request.url).pathname;
const carries = (request: Request, team = "argument-team"): boolean =>
  request.headers.get("proxy-authorization") === PROXY && request.headers.get("x-team") === team;

describe("extra headers on platform calls", () => {
  let saved: Record<string, string | undefined>;

  beforeEach(() => {
    saved = Object.fromEntries(SAVED.map((name) => [name, process.env[name]]));
    for (const name of SAVED) delete process.env[name];
    process.env[EXTRA_HEADERS_ENV] = `Proxy-Authorization=${PROXY};X-Team=env-team`;
  });

  afterEach(() => {
    for (const [name, value] of Object.entries(saved)) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  });

  it("a platform call and a withOptions copy carry the headers a core call carries", async () => {
    const script = new Script([json(200, {})]);
    const c = client(script, { extraHeaders: { "X-Team": "argument-team" } });
    await c.users.current();
    await c._platform.call(CAPABILITIES);
    const copy = c.withOptions({ timeoutMs: 500 });
    await copy._platform.call(CAPABILITIES);
    await copy.users.current();
    expect(script.requests.map(pathOf).slice(1, 3)).toEqual([CAPABILITIES_PATH, CAPABILITIES_PATH]);
    expect(script.requests).toHaveLength(4);
    expect(script.requests.map((r) => carries(r))).toEqual([true, true, true, true]);
    expect(script.requests[1]!.headers.get("x-api-key")).toBe("k-test-1234");
  });

  it("reads the setting on each platform call", async () => {
    const script = new Script([json(200, {})]);
    const c = client(script, { extraHeaders: { "X-Arg": "argument-value" } });
    await c._platform.call(CAPABILITIES);
    process.env[EXTRA_HEADERS_ENV] = "Proxy-Authorization=Bearer refreshed-token-yyyyyyyy";
    await c._platform.call(CAPABILITIES);
    delete process.env[EXTRA_HEADERS_ENV];
    await c._platform.call(CAPABILITIES);
    const [first, refreshed, unset] = script.requests.map((r) => r.headers);
    expect(first!.get("proxy-authorization")).toBe(PROXY);
    expect(first!.get("x-team")).toBe("env-team");
    expect(refreshed!.get("proxy-authorization")).toBe("Bearer refreshed-token-yyyyyyyy");
    expect(refreshed!.has("x-team")).toBe(false);
    expect(unset!.has("proxy-authorization")).toBe(false);
    expect([first, refreshed, unset].map((h) => h!.get("x-arg"))).toEqual(["argument-value", "argument-value", "argument-value"]);
  });

  it("the SDK's own headers and a declared per-call header win over extra headers", async () => {
    const script = new Script([json(200, {})]);
    const c = client(script, {
      workspaceId: "ws-own",
      extraHeaders: { "x-workspace-id": "ws-extra", Accept: "text/plain", "X-Team": "argument-team" },
    });
    await c._platform.call("team.get", {}, { headers: { "X-Team": "caller-team" } });
    await c._platform.call("team.get");
    const [declared, plain] = script.requests.map((r) => r.headers);
    expect(declared!.get("proxy-authorization")).toBe(PROXY);
    expect(declared!.get("x-workspace-id")).toBe("ws-own"); // one value: Headers.get joins duplicates
    expect(declared!.get("accept")).toBe("application/json");
    expect(declared!.get("x-team")).toBe("caller-team");
    expect(plain!.get("x-team")).toBe("argument-team");
  });

  it.each<[string, string | undefined, boolean]>([
    [BASE, "http://platform.other.test/omega/api", false],
    [`${BASE}/tenant`, `${BASE}/other/omega/api`, false],
    [`${BASE}/tenant`, undefined, true],
  ])("only a platform origin under the base URL gets them (%s, %s)", async (baseUrl, platformBaseUrl, sent) => {
    const script = new Script([json(200, {})]);
    const c = client(script, {
      baseUrl,
      ...(platformBaseUrl !== undefined ? { platformBaseUrl } : {}),
      extraHeaders: { "X-Team": "argument-team" },
    });
    await c.users.current();
    await c._platform.call(CAPABILITIES);
    const [core, platform] = script.requests;
    expect(carries(core!)).toBe(true);
    expect(pathOf(platform!).endsWith(CAPABILITIES_PATH)).toBe(true);
    if (sent) expect(carries(platform!)).toBe(true);
    else expect([platform!.headers.has("proxy-authorization"), platform!.headers.has("x-team")]).toEqual([false, false]);
  });

  it("a malformed setting throws before any platform request and is never retried", async () => {
    process.env[EXTRA_HEADERS_ENV] = `Proxy-Authorization ${PROXY}`;
    const script = new Script([json(200, {})]);
    const c = client(script, { retries: 3 });
    let error: unknown;
    try {
      await c._platform.call(CAPABILITIES);
    } catch (e) {
      error = e;
    }
    expect(error).toBeInstanceOf(ExtraHeadersError);
    expect(String((error as Error).message)).not.toContain(TOKEN);
    expect(script.requests).toHaveLength(0);
  });

  it("a reflected extra header value never reaches a platform error", async () => {
    const script = new Script([json(403, { code: "forbidden", message: `proxy refused ${PROXY}` })]);
    const c = client(script);
    let error: unknown;
    try {
      await c._platform.call(CAPABILITIES);
    } catch (e) {
      error = e;
    }
    expect(error).toBeInstanceOf(FutureAGIAPIError);
    expect(script.requests[0]!.headers.get("proxy-authorization")).toBe(PROXY);
    expect(String((error as Error).message)).toContain("proxy refused");
    expect(String((error as Error).message)).not.toContain(TOKEN);
    expect(JSON.stringify((error as FutureAGIAPIError).payload ?? null)).not.toContain(TOKEN);
  });

  const QUOTE = 'fake-quote-"-header-value';
  const BACKSLASH = "fake-backslash-\\-header-value";
  const SLASH = "fake-slash/header-value";
  const reflecting = (value: string): string => JSON.stringify({ code: "forbidden", message: `proxy refused ${value}`, [value]: 1 });
  // raw JSON text that writes SLASH's "/" as the optional escape a JSON encoder may use, as a message and a key
  const SLASH_TEXT = '{"code":"forbidden","message":"proxy refused fake-slash\\/header-value","fake-slash\\/header-value":1}';
  const strings = (value: unknown): string[] =>
    typeof value === "string"
      ? [value]
      : Array.isArray(value)
        ? value.flatMap(strings)
        : value !== null && typeof value === "object"
          ? Object.entries(value).flatMap(([key, item]) => [key, ...strings(item)])
          : [];
  const failure = async (c: FutureAGIClient): Promise<FutureAGIAPIError> => {
    try {
      await c._platform.call(CAPABILITIES);
    } catch (e) {
      expect(e).toBeInstanceOf(FutureAGIAPIError);
      return e as FutureAGIAPIError;
    }
    throw new Error("expected the call to fail");
  };

  it.each<[string, string, string]>([
    ["quote", QUOTE, reflecting(QUOTE)],
    ["backslash", BACKSLASH, reflecting(BACKSLASH)],
    ["slash escape", SLASH, SLASH_TEXT],
  ])("a reflected value the server escaped in its JSON (%s) is scrubbed once decoded", async (_case, value, text) => {
    const script = new Script([new Response(text, { status: 403, headers: { "content-type": "application/json" } })]);
    const error = await failure(client(script, { extraHeaders: { "X-Probe": value } }));
    expect(script.requests[0]!.headers.get("x-probe")).toBe(value);
    expect(error.code).toBe("forbidden");
    expect(error.message).toContain("proxy refused [redacted]"); // scrubbed, not dropped
    expect(error.message).not.toContain(value);
    expect(strings(error.payload).filter((s) => s.includes(value))).toEqual([]);
  });

  it("a reflected value in a body that is not JSON is never echoed", async () => {
    const script = new Script([new Response(`<html>proxy refused ${QUOTE}</html>`, { status: 403 })]);
    const error = await failure(client(script, { extraHeaders: { "X-Probe": QUOTE } }));
    expect(script.requests[0]!.headers.get("x-probe")).toBe(QUOTE);
    expect(error.payload).toBeUndefined();
    expect(error.message).not.toContain("proxy refused");
    expect(error.message).not.toContain(QUOTE);
  });
});
