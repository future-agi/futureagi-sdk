/** Supplemental H6/K2W controls authored after the recorded RED, NOT_RUN.
 * These are not additional observed RED cases. Regional URLs are mock configuration only. */
import { WrongRegionError as PublicWrongRegionError } from "../../index";
import { resilientFetch } from "../../transport";
import { apiError, errorClassFor } from "../error-map";
import { AuthenticationError, ConfigurationError, CredentialsMissingError, HostNotAllowedError,
  MixedCredentialsError, PermissionDeniedError, WrongRegionError, isAuthError } from "../errors";
import { CoreServerError } from "../__fixtures__/platform";
import { resetWarnings, resolvePlatformOrigin } from "../origins";
import { ACTIONS, API_KEY, SECRET_KEY, TOKEN, SUBMITTED, EU, US, Wire, assertPrivate,
  assertSelectedOnly, failure, foldEach, invoke, isolate, type Action, type Mode } from "../__fixtures__/h6-k2w-transport";

let restore: () => void;
let warn: jest.SpyInstance;
beforeEach(() => {
  restore = isolate();
  resetWarnings();
  warn = jest.spyOn(console, "warn").mockImplementation(() => undefined);
});
afterEach(() => { warn.mockRestore(); resetWarnings(); restore(); });

test("supplemental: WrongRegionError is a public permission-denied specialization with fixed guidance", () => {
  const error = apiError(403, { error: "wrong_region" });
  expect(PublicWrongRegionError).toBe(WrongRegionError);
  expect(error.constructor).toBe(WrongRegionError);
  expect(error).toBeInstanceOf(PermissionDeniedError);
  expect(isAuthError(error)).toBe(true);
  expect(error.getErrorCode()).toBe("WRONG_REGION");
  expect(error.code).toBe("wrong_region");
  expect(error.message).toContain(US);
  expect(error.message).toContain(EU);
  expect(error.message).toMatch(/manual|explicit/i);
  expect(error.requestId).toBeUndefined();
  expect(error.retryAfter).toBeUndefined();
  // The shared code table cannot prove the exact wire envelope.
  expect(errorClassFor(403, "wrong_region")).toBe(PermissionDeniedError);
});

const nearMisses: { label: string; body: unknown }[] = [
  { label: "nested error code", body: { error: { code: "wrong_region" } } },
  { label: "code only", body: { code: "wrong_region" } },
  { label: "error_code only", body: { error_code: "wrong_region" } },
  { label: "result wrapper", body: { status: "error", result: { error: "wrong_region" } } },
  { label: "prose only", body: { message: "wrong_region" } },
  { label: "different case", body: { error: "WRONG_REGION" } },
  { label: "padded string", body: { error: "wrong_region " } },
  { label: "array", body: [{ error: "wrong_region" }] },
  { label: "string", body: "wrong_region" },
  { label: "absent", body: null },
];
test.each(nearMisses)("supplemental: $label is not the regional wire envelope", ({ body }) => {
  const error = apiError(403, body);
  expect(error.constructor).toBe(PermissionDeniedError);
  expect(error.message).not.toContain(US);
  expect(error.message).not.toContain(EU);
});

test("supplemental: inherited fields and a privacy-normalized shape cannot promote a response", () => {
  expect(apiError(403, Object.create({ error: "wrong_region" })).constructor).toBe(PermissionDeniedError);
  expect(apiError(403, { error: "wrong_region" }, undefined, { wrongRegion: false }).constructor).toBe(PermissionDeniedError);
});

test.each([{ status: 401, kind: AuthenticationError }, { status: 503, kind: CoreServerError }])(
  "supplemental: wrong_region at $status remains an ordinary status error", ({ status, kind }) => {
    const error = apiError(status, { error: "wrong_region" });
    expect(error.constructor).toBe(kind);
    expect(error.message).not.toContain(US);
    expect(error.message).not.toContain(EU);
  },
);

const scopes: { action: Action; mode: Mode }[] = [
  { action: "core", mode: "keys" },
  ...[...ACTIONS, "console" as const].flatMap(action => (["keys", "bearer"] as const).map(mode => ({ action, mode }))),
];
foldEach(scopes, row => row.action !== "core" && row.action !== "console")("supplemental: $action $mode discards hostile regional payload and diagnostic metadata", async ({ action, mode }) => {
  const bait = "https://untrusted-h6.invalid/" + SUBMITTED;
  const wire = new Wire(), c = wire.client(mode, 0, { baseUrl: EU });
  wire.respond = () => Response.json({
    error: "wrong_region", code: "role_forbidden", error_code: "role_forbidden",
    message: "send credentials to " + bait, reason: "your organization is in stolen-region",
    fix: bait, detail: { private: SUBMITTED, token: TOKEN }, requestId: SUBMITTED,
    request_id: SUBMITTED, retryAfterSeconds: 99,
  }, { status: 403, headers: {
    "x-request-id": SUBMITTED, "x-upstream-request-id": SUBMITTED, "x-omega-receipt-id": SUBMITTED,
    "retry-after": "99",
  } });
  const got = await failure(() => invoke(c, action));
  expect(got).toBeInstanceOf(WrongRegionError);
  const error = got as WrongRegionError;
  expect(error.message).toBe(apiError(403, { error: "wrong_region" }).message);
  expect(error.payload).toEqual({ error: "wrong_region" });
  expect(error.requestId).toBeUndefined();
  expect(error.upstreamRequestId).toBeUndefined();
  expect(error.receiptId).toBeUndefined();
  expect(error.retryAfter).toBeUndefined();
  expect(Object.prototype.hasOwnProperty.call(error, "detail")).toBe(false);
  assertPrivate(error, warn.mock.calls, [bait, "stolen-region"]);
  assertSelectedOnly(wire, EU, mode, 1);
  expect(wire.sleeps).toEqual([]);
});

foldEach(["json", "sse", "upload", "console"] as const, action => action !== "console")(
  "supplemental: normalized nested code is not regional evidence on %s", async action => {
    const wire = new Wire(), c = wire.client("keys", 0, { baseUrl: US });
    wire.respond = () => Response.json({ error: { code: "wrong_region" } }, { status: 403 });
    const got = await failure(() => invoke(c, action));
    expect((got as Error).constructor).toBe(PermissionDeniedError);
    expect(String(got)).not.toContain(EU);
    expect(String(got)).not.toContain(US);
    assertSelectedOnly(wire, US, "keys", 1);
  },
);

test.each([false, true])("supplemental: explicit false overrides environment HTTP optout, clone=%s", async clone => {
  process.env.FI_ALLOW_INSECURE_HTTP = "1";
  const wire = new Wire(), original = wire.client("bearer", undefined, {
    baseUrl: "http://false-k2w.invalid", allowInsecureHttp: false, allowCustomPlatformUrl: true,
  });
  const c = clone ? original.withOptions({ retries: 0 }) : original;
  const got = await failure(() => c.environments.list());
  expect(got).toBeInstanceOf(ConfigurationError);
  expect(got).toMatchObject({ code: "insecure_http_origin" });
  expect(wire.requests).toEqual([]);
  expect(warn).not.toHaveBeenCalled();
  assertPrivate(got);
});

test("supplemental: explicit true overrides a false environment flag", async () => {
  process.env.FI_ALLOW_INSECURE_HTTP = "0";
  const wire = new Wire(), c = wire.client("bearer", 0, {
    baseUrl: "http://true-k2w.invalid", allowInsecureHttp: true,
  });
  await c.withOptions({ retries: 0 }).environments.list();
  assertSelectedOnly(wire, "http://true-k2w.invalid", "bearer", 1);
  expect(warn).toHaveBeenCalledTimes(1);
});

test("supplemental: HTTP optout never bypasses keys credential provenance", () => {
  const env = { FI_PLATFORM_BASE_URL: "http://other-source-k2w.invalid/private-path", FI_ALLOW_INSECURE_HTTP: "1" };
  expect(() => resolvePlatformOrigin({ apiKey: API_KEY, secretKey: SECRET_KEY, allowInsecureHttp: true }, env))
    .toThrow(HostNotAllowedError);
  expect(warn).not.toHaveBeenCalled();
});

test("supplemental: credential errors precede valid-origin HTTP policy without borrowing a half pair", () => {
  const baseUrl = "http://precedence-k2w.invalid";
  expect(() => resolvePlatformOrigin({ baseUrl, apiKey: API_KEY }, { FI_SECRET_KEY: SECRET_KEY }))
    .toThrow(CredentialsMissingError);
  expect(() => resolvePlatformOrigin({ baseUrl, apiKey: API_KEY, platformToken: TOKEN }, { FI_ALLOW_INSECURE_HTTP: "1" }))
    .toThrow(MixedCredentialsError);
  expect(warn).not.toHaveBeenCalled();
});

test("supplemental: core, platform and clones share a canonical-origin keys warning", async () => {
  const wire = new Wire();
  const c = wire.client("keys", 0, {
    baseUrl: "http://CANONICAL-k2w.invalid/private-path/a",
    platformBaseUrl: "http://canonical-k2w.invalid:80/private-path/b",
  });
  await c.prompts.list();
  await c.environments.list();
  await c.withOptions({ retries: 0 }).prompts.list();
  await c.withOptions({ retries: 0 }).environments.list();
  expect(warn).toHaveBeenCalledTimes(1);
  expect(String(warn.mock.calls[0])).toMatch(/keys.*deprecat.*future/i);
  expect(String(warn.mock.calls[0])).not.toContain("private-path");
  assertSelectedOnly(wire, "http://canonical-k2w.invalid", "keys", 4);
});

test("supplemental: HTTP with the custom-host flag emits one cleartext warning, not two", async () => {
  process.env.FI_PLATFORM_BASE_URL = "http://custom-warning-k2w.invalid/private-path/a";
  const wire = new Wire(), c = wire.client("keys", 0, { allowCustomPlatformUrl: true });
  await c.environments.list();
  process.env.FI_PLATFORM_BASE_URL = "http://CUSTOM-warning-k2w.invalid:80/private-path/b";
  await wire.client("keys", 0, { allowCustomPlatformUrl: true }).environments.list();
  expect(warn).toHaveBeenCalledTimes(1);
  expect(String(warn.mock.calls[0])).toMatch(/cleartext.*deprecat.*future/i);
  assertPrivate({}, warn.mock.calls, ["private-path"]);
  assertSelectedOnly(wire, "http://custom-warning-k2w.invalid", "keys", 2);
});

test.each([301, 302, 303, 307, 308])("supplemental: shared transport cannot opt into redirect following (%s)", async status => {
  const requests: Request[] = [];
  const send = resilientFetch({
    resolveCredentials: () => ({ apiKey: API_KEY, secretKey: SECRET_KEY }),
    fetch: async (input, init) => {
      const request = new Request(input, init);
      requests.push(request);
      expect(request.redirect).toBe("manual");
      return new Response(null, { status, headers: { location: EU + "/untrusted" } });
    },
    sleep: async () => { throw new Error("a redirect must not retry"); },
  });
  const response = await send(new Request(US + "/test", { redirect: "follow" }), { redirect: "follow" });
  expect(response.status).toBe(status);
  expect(requests).toHaveLength(1);
  expect(requests[0]!.url).toBe(US + "/test");
  expect(requests[0]!.headers.get("x-api-key")).toBe(API_KEY);
  expect(requests[0]!.headers.get("x-secret-key")).toBe(SECRET_KEY);
});

test.each(["127.0.0.2", "127.255.255.254"])("supplemental: any 127/8 loopback Bearer HTTP is not refused (%s)", async host => {
  const base = `http://${host}:19876`;
  const wire = new Wire(), c = wire.client("bearer", 0, { baseUrl: base });
  await c.environments.list();
  assertSelectedOnly(wire, base, "bearer", 1);
  expect(warn).not.toHaveBeenCalled();
});

test("supplemental: a trailing DNS dot shares the origin warning, as in Python", async () => {
  const wire = new Wire(), host = "dot-k2w-" + Date.now() + ".invalid";
  for (const baseUrl of [`http://${host}`, `http://${host}.`]) await wire.client("keys", 0, { baseUrl }).prompts.list();
  expect(warn).toHaveBeenCalledTimes(1);
});

test("supplemental: a loopback custom host keeps its custom-host warning, as in Python", async () => {
  process.env.FI_PLATFORM_BASE_URL = "http://127.0.0.2:20002/omega/api";
  const wire = new Wire(), c = wire.client("keys", 0, { baseUrl: "https://loopback-custom-core.invalid", allowCustomPlatformUrl: true });
  await c.environments.list();
  expect(warn).toHaveBeenCalledTimes(1);
  expect(String(warn.mock.calls[0])).toMatch(/outside the Future AGI zone/);
});
