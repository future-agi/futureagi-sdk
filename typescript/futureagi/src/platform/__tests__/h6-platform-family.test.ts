/** Released-client H6 contract pins. Mock-only; synthetic credentials, no discovery. */
import { Socket } from "node:net";
import * as httpSecurity from "../../_core/http-security";
import * as platform from "../index";
import { APIError, APIConnectionError, AuthenticationError, InternalServerError, PermissionDeniedError } from "../errors";
import type { FetchLike } from "../transport";

const US = "https://api.futureagi.com";
const EU = "https://api-eu.futureagi.com";
const SERVER_HOST = "untrusted-platform-h6.invalid";
const DESTINATION = `https://${SERVER_HOST}/server-only-destination`;
const KEY = "synthetic-platform-h6-key";
const SECRET = "synthetic-platform-h6-secret";
const TOKEN = "synthetic-platform-h6-token";

let restore: () => void;
let warn: jest.SpyInstance;
beforeEach(() => {
  httpSecurity.resetHttpWarnings();
  warn = jest.spyOn(console, "warn").mockImplementation(() => undefined);
  const env = { ...process.env };
  const attempts: string[] = [];
  const socket = jest.spyOn(Socket.prototype, "connect").mockImplementation(function (): never {
    attempts.push("socket");
    throw new Error("H6 tests must not open sockets");
  });
  const nativeFetch = jest.spyOn(globalThis, "fetch").mockImplementation(async () => {
    attempts.push("native fetch");
    throw new Error("H6 mock fetch was bypassed");
  });
  restore = () => {
    socket.mockRestore();
    nativeFetch.mockRestore();
    process.env = env;
    warn.mockRestore();
    httpSecurity.resetHttpWarnings();
    expect(attempts).toEqual([]);
  };
});
afterEach(() => restore());

function json(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...headers } });
}

async function exchange(respond: (request: Request) => Response, options: {
  base?: string; method?: string; retries?: number; fromEnvironment?: boolean;
} = {}): Promise<{ outcome: unknown; seen: Request[] }> {
  const seen: Request[] = [];
  const fetch: FetchLike = async (url, init) => {
    const request = new Request(url, init);
    seen.push(request);
    return respond(request);
  };
  const client = new platform.Client({
    apiKey: KEY, secretKey: SECRET, fetch, maxRetries: options.retries ?? 2,
    ...(options.fromEnvironment ? {} : { baseUrl: options.base ?? US }),
  });
  let outcome: unknown;
  try { outcome = await client.request(options.method ?? "GET", "/h6-probe"); }
  catch (error) { outcome = error; }
  return { outcome, seen };
}

function selectedOnce(seen: Request[], base: string): void {
  expect(seen).toHaveLength(1);
  expect(seen[0]!.url).toBe(`${base}/h6-probe`);
  expect(seen[0]!.headers.get("x-api-key")).toBe(KEY);
  expect(seen[0]!.headers.get("x-secret-key")).toBe(SECRET);
  expect(seen[0]!.redirect).toBe("manual");
}

const regionalCases = [US, EU].flatMap(base => ["GET", "POST"].map(method => ({
  base, method, id: `${base === US ? "us" : "eu"}-${method}`,
})));

test.each(regionalCases)("exact wrong_region is an exported permission subclass: $id", async ({ base, method }) => {
  const { outcome, seen } = await exchange(() => json(403, { error: "wrong_region" }), { base, method });
  // Guard the new export, so the base fails by expect rather than import/type/reference error.
  const kind = (platform as unknown as Record<string, unknown>).WrongRegionError;
  expect(typeof kind).toBe("function");
  expect(outcome).toBeInstanceOf(kind);
  expect(outcome).toBeInstanceOf(PermissionDeniedError);
  try { throw outcome; }
  catch (error) { expect(error instanceof PermissionDeniedError).toBe(true); }
  expect(outcome).toMatchObject({ status: 403, code: "wrong_region" });
  selectedOnce(seen, base);
});

const nearMisses = [
  { id: "code-only", status: 403, text: '{"code":"wrong_region"}', kind: PermissionDeniedError },
  { id: "nested", status: 403, text: '{"error":{"code":"wrong_region"}}', kind: PermissionDeniedError },
  { id: "wrapped", status: 403, text: '{"status":false,"result":{"error":"wrong_region"}}', kind: PermissionDeniedError },
  { id: "array", status: 403, text: '{"error":["wrong_region"]}', kind: PermissionDeniedError },
  { id: "string", status: 403, text: '"wrong_region"', kind: PermissionDeniedError },
  { id: "invalid-json", status: 403, text: '{"error":"wrong_region"', kind: PermissionDeniedError },
  { id: "substring", status: 403, text: '{"error":"prefix_wrong_region"}', kind: PermissionDeniedError },
  { id: "whitespace", status: 403, text: '{"error":"wrong_region "}', kind: PermissionDeniedError },
  { id: "case", status: 403, text: '{"error":"WRONG_REGION"}', kind: PermissionDeniedError },
  { id: "prose-only", status: 403, text: '{"message":"wrong_region"}', kind: PermissionDeniedError },
  { id: "null", status: 403, text: '{"error":null}', kind: PermissionDeniedError },
  { id: "401", status: 401, text: '{"error":"wrong_region"}', kind: AuthenticationError },
  { id: "503", status: 503, text: '{"error":"wrong_region"}', kind: InternalServerError },
];
test.each(nearMisses)("near miss keeps the released status class: $id", async ({ status, text, kind }) => {
  const { outcome, seen } = await exchange(() => new Response(text, { status }), { retries: 0 });
  expect(outcome).toBeInstanceOf(APIError);
  expect((outcome as Error).constructor).toBe(kind);
  selectedOnce(seen, US);
});

test.each(regionalCases)("wrong_region never retries or follows Location: $id", async ({ base, method }) => {
  const { outcome, seen } = await exchange(() => json(403, {
    error: "wrong_region", reason: `move to ${DESTINATION}`,
  }, { location: DESTINATION, "retry-after": "0" }), { base, method });
  expect(outcome).toBeInstanceOf(PermissionDeniedError);
  selectedOnce(seen, base);
});

test("wrong_region guidance and diagnostics are SDK-authored", async () => {
  const messages: string[] = [];
  for (const body of [{ error: "wrong_region" }, {
    error: "wrong_region", code: "role_forbidden", message: `move to ${DESTINATION}`,
    reason: `your workspace resides at ${DESTINATION}`, fix: DESTINATION,
    detail: { destination: DESTINATION }, requestId: DESTINATION,
  }]) {
    const { outcome, seen } = await exchange(() => json(403, body, {
      location: DESTINATION, "x-request-id": DESTINATION,
    }));
    expect(outcome).toBeInstanceOf(PermissionDeniedError);
    const error = outcome as APIError;
    expect(error.message).not.toContain(SERVER_HOST);
    expect(error.message).not.toContain(DESTINATION);
    expect(error.message).toContain(US);
    expect(error.message).toContain(EU);
    expect(error.message).toContain("Manually select");
    expect(error.message).toContain("baseUrl / FI_BASE_URL");
    expect(error.message).toContain("never probes, redirects or retries against another region");
    expect(error.body).toEqual({ error: "wrong_region" });
    expect(error.detail).toBeUndefined();
    expect(error.requestId).toBeNull();
    expect(error.code).toBe("wrong_region");
    messages.push(error.message);
    selectedOnce(seen, US);
  }
  expect(messages[0]).toBe(messages[1]);
});

const redirectCases = [301, 302, 303, 307, 308].flatMap(status => [
  { status, target: DESTINATION, id: `${status}-foreign-host` },
  { status, target: `${US.replace("https:", "http:")}/server-only-destination`, id: `${status}-downgrade` },
]);
test.each(redirectCases)("redirect refusal does not echo destination: $id", async ({ status, target }) => {
  const { outcome, seen } = await exchange(() => new Response(null, { status, headers: { location: target } }));
  expect(outcome).toBeInstanceOf(APIConnectionError);
  const text = String(outcome);
  expect(text).not.toContain(SERVER_HOST);
  expect(text).not.toContain(target);
  expect(text).not.toContain("server-only-destination");
  expect(text).toContain("not followed");
  selectedOnce(seen, US);
});

test.each(redirectCases)("cross-origin redirect never sends to target: $id", async ({ status, target }) => {
  const { outcome, seen } = await exchange(() => new Response(null, { status, headers: { location: target } }));
  expect(outcome).toBeInstanceOf(APIConnectionError);
  selectedOnce(seen, US);
});

const cleartextCases = [
  { base: "http://remote-platform-h6.invalid", id: "remote" },
  { base: "http://localhost.attacker.invalid", id: "localhost-suffix" },
  { base: "http://128.0.0.1", id: "outside-127" },
  { base: "http://[::ffff:127.0.0.1]", id: "mapped-ipv6" },
  { base: "http://[::2]", id: "other-ipv6" },
].flatMap(row => [false, true].map(fromEnvironment => ({
  ...row, fromEnvironment, id: `${row.id}-${fromEnvironment ? "environment" : "argument"}`,
})));
test.each(cleartextCases)("keys HTTP sends once per call and warns once per origin: $id", async ({ base, fromEnvironment }) => {
  delete process.env.FI_ALLOW_INSECURE_HTTP;
  delete process.env.FI_ALLOW_CUSTOM_PLATFORM_URL;
  for (const path of ["/private-path/a", "/private-path/b"]) {
    const target = base + path;
    process.env.FI_BASE_URL = target;
    const { outcome, seen } = await exchange(() => json(200, { ok: true }), { base: target, fromEnvironment });
    expect(outcome).toEqual({ ok: true });
    selectedOnce(seen, new URL(target).toString());
    expect(seen[0]!.headers.has("authorization")).toBe(false);
    expect(warn).toHaveBeenCalledTimes(1);
    const notice = String(warn.mock.calls[0]![0]);
    expect(notice).toContain("cleartext");
    expect(notice).toContain("deprecated");
    expect(notice).toContain("keys");
    for (const marker of [KEY, SECRET, TOKEN, "private-path", "h6-probe"]) expect(notice).not.toContain(marker);
  }
});

const budgetCases = (["lane", "released"] as const).flatMap(first => (["keys", "bearer"] as const).map(mode => ({
  first, mode, id: `${first}-${mode}`,
})));
test.each(budgetCases)("HTTP notice budget is shared with lane and canonical origins: $id", async ({ first, mode }) => {
  const base = "http://shared-platform-h6.invalid";
  const lane = async () => { httpSecurity.checkHttpSecurity(new URL(`${base}/private-path/lane`), mode, true); };
  const released = async () => {
    const { outcome, seen } = await exchange(() => json(200, { ok: true }), {
      base: "http://SHARED-PLATFORM-H6.invalid.:80/private-path/released",
    });
    expect(outcome).toEqual({ ok: true });
    expect(seen).toHaveLength(1);
  };
  for (const caller of first === "lane" ? [lane, released] : [released, lane]) {
    await caller();
    expect(warn).toHaveBeenCalledTimes(1);
    for (const marker of [KEY, SECRET, TOKEN, "private-path"]) expect(String(warn.mock.calls[0]![0])).not.toContain(marker);
  }
  const { outcome, seen } = await exchange(() => json(200, { ok: true }), { base: `${base}:8080` });
  expect(outcome).toEqual({ ok: true });
  expect(seen).toHaveLength(1);
  expect(warn).toHaveBeenCalledTimes(2);
});

test.each([{ base: US, id: "https" }, { base: "http://token-ignored-platform-h6.invalid", id: "http" }])(
  "released keys client does not discover or send bearer tokens: $id", async ({ base }) => {
    // ClientConfig has no bearer credential mode; an environment token must not be discovered.
    process.env.FI_PLATFORM_TOKEN = TOKEN;
    process.env.FI_ALLOW_INSECURE_HTTP = "1";
    const { outcome, seen } = await exchange(() => json(200, { ok: true }), { base });
    expect(outcome).toEqual({ ok: true });
    selectedOnce(seen, base);
    expect(seen[0]!.headers.has("authorization")).toBe(false);
    expect(JSON.stringify(Array.from(seen[0]!.headers.entries()))).not.toContain(TOKEN);
  },
);

const allowedCases = [
  { base: "https://secure-platform-h6.invalid", id: "https" },
  { base: "http://localhost:19876", id: "localhost" },
  { base: "http://LOCALHOST.:19876", id: "localhost-dot" },
  { base: "http://127.0.0.1:19876", id: "127-1" },
  { base: "http://127.0.0.2:19876", id: "127-2" },
  { base: "http://127.255.255.254:19876", id: "127-last" },
  { base: "http://[::1]:19876", id: "ipv6" },
];
test.each(allowedCases)("HTTPS and loopback HTTP still send credentials: $id", async ({ base }) => {
  const { outcome, seen } = await exchange(() => json(200, { ok: true }), { base });
  expect(outcome).toEqual({ ok: true });
  selectedOnce(seen, new URL(base).origin);
  expect(seen[0]!.headers.has("authorization")).toBe(false);
  expect(warn).not.toHaveBeenCalled();
});

test("same-origin HTTP redirect rechecks shared policy", async () => {
  const base = "http://redirect-platform-h6.invalid";
  const check = jest.spyOn(httpSecurity, "checkHttpSecurity"); // delegates to the real shared helper
  try {
    const { outcome, seen } = await exchange(request => new URL(request.url).pathname === "/h6-probe"
      ? new Response(null, { status: 302, headers: { location: "/private-path/done" } })
      : json(200, { ok: true }), { base });
    expect(outcome).toEqual({ ok: true });
    const destinations = [`${base}/h6-probe`, `${base}/private-path/done`];
    expect(seen.map(r => r.url)).toEqual(destinations);
    expect(check.mock.calls.map(([url, mode]) => [url.toString(), mode])).toEqual(destinations.map(url => [url, "keys"]));
    for (const request of seen) {
      expect(request.headers.get("x-api-key")).toBe(KEY);
      expect(request.headers.get("x-secret-key")).toBe(SECRET);
      expect(request.redirect).toBe("manual");
    }
    expect(warn).toHaveBeenCalledTimes(1);
    for (const marker of [KEY, SECRET, TOKEN, "private-path", "h6-probe"]) expect(String(warn.mock.calls[0]![0])).not.toContain(marker);
  } finally { check.mockRestore(); }
});

const sameOriginCases = [US, "http://127.0.0.2:19876"].flatMap(base => [301, 302, 303, 307, 308].map(status => ({
  base, status, method: status <= 303 ? "GET" : "POST", id: `${base === US ? "https" : "loopback"}-${status}`,
})));
test.each(sameOriginCases)("same-origin redirects keep method rules: $id", async ({ base, status, method }) => {
  const { outcome, seen } = await exchange(request => new URL(request.url).pathname === "/h6-probe"
    ? new Response(null, { status, headers: { location: "/done" } })
    : json(200, { ok: true }), { base, method: "POST" });
  expect(outcome).toEqual({ ok: true });
  expect(seen.map(r => r.url)).toEqual([`${base}/h6-probe`, `${base}/done`]);
  expect(seen.map(r => r.method)).toEqual(["POST", method]);
  for (const request of seen) {
    expect(request.headers.get("x-api-key")).toBe(KEY);
    expect(request.headers.get("x-secret-key")).toBe(SECRET);
    expect(request.redirect).toBe("manual");
  }
});

test("same-origin redirect budget is unchanged", async () => {
  const { outcome, seen } = await exchange(() => new Response(null, { status: 302, headers: { location: "/h6-probe" } }));
  expect(outcome).toBeInstanceOf(APIConnectionError);
  expect(String(outcome)).toContain("more than 5 redirects");
  expect(seen).toHaveLength(6);
  expect(seen.every(r => r.url === `${US}/h6-probe` && r.redirect === "manual")).toBe(true);
});
