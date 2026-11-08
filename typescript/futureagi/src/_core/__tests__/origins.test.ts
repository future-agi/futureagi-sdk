/**
 * Platform origins: derivation; same-source acceptance; refusal on mixed sources
 * without the flag; mixed credentials refused; Bearer mode; selectors.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { CredentialsMissingError, HostNotAllowedError, MixedCredentialsError, PlatformNotConfiguredError } from "../errors";
import { resetWarnings, resolvePlatformOrigin } from "../origins";

// One verdict table for the host guard, read by both languages
// (python/tests/core/test_origins.py reads the same file), so the two URL parsers cannot drift.
const GUARD_TABLE = join(__dirname, "../../../../../tests/fixtures/platform-origins/guard-urls.json");
const GUARD_CASES = (JSON.parse(readFileSync(GUARD_TABLE, "utf8")) as { cases: { url: string; verdict: string }[] }).cases;

const KEYS = { apiKey: "k-test-1234", secretKey: "s-test-1234" };

describe("platform origin", () => {
  it("derives from the base URL, and derived is always exempt", () => {
    expect(resolvePlatformOrigin({ ...KEYS, baseUrl: "https://fa.example.org/" }, {}).base).toBe("https://fa.example.org/omega/api");
    const o = resolvePlatformOrigin(KEYS, { FI_BASE_URL: "http://fa.internal:8000" });
    expect([o.base, o.source]).toEqual(["http://fa.internal:8000/omega/api", "derived"]);
    expect(resolvePlatformOrigin(KEYS, {}).base).toBe("https://api.futureagi.com/omega/api");
  });

  it("accepts an origin from the same explicit source as the keys", () => {
    expect(resolvePlatformOrigin({ ...KEYS, platformBaseUrl: "https://ee.example.org/omega/api" }, {}).source).toBe("argument");
    const env = { FI_API_KEY: "k-env-1234", FI_SECRET_KEY: "s-env-1234", FI_PLATFORM_BASE_URL: "http://ee.lan:8080/omega/api" };
    const o = resolvePlatformOrigin({}, env);
    expect([o.source, o.headers["X-Api-Key"]]).toEqual(["env", "k-env-1234"]);
  });

  it("accepts the Future AGI zone and loopback from any source", () => {
    expect(resolvePlatformOrigin(KEYS, { FI_PLATFORM_BASE_URL: "https://staging.futureagi.com/omega/api" }).custom).toBe(false);
    expect(resolvePlatformOrigin(KEYS, { FI_PLATFORM_BASE_URL: "http://127.0.0.1:18700/omega/api" }).custom).toBe(false);
    expect(resolvePlatformOrigin(KEYS, { FI_PLATFORM_BASE_URL: "http://[::1]:18700/omega/api" }).custom).toBe(false);
  });

  it.each([
    "https://evil.example/omega/api",
    "https://futureagi.com.evil.example/omega/api",
    "https://xn--futureag-xxx.com/omega/api",
    "https://fútureagi.com/omega/api",
    "http://staging.futureagi.com/omega/api",
  ])("refuses %s from another source than the keys", (url) => {
    expect(() => resolvePlatformOrigin(KEYS, { FI_PLATFORM_BASE_URL: url })).toThrow(HostNotAllowedError);
    try {
      resolvePlatformOrigin(KEYS, { FI_PLATFORM_BASE_URL: url });
    } catch (error) {
      expect(String((error as Error).message)).not.toContain("k-test-1234");
    }
  });

  it("the flag allows it with one warning; an explicit false beats the environment", () => {
    resetWarnings();
    const warn = jest.spyOn(console, "warn").mockImplementation(() => undefined);
    const env = { FI_PLATFORM_BASE_URL: "https://ee.corp.example/omega/api" };
    expect(resolvePlatformOrigin({ ...KEYS, allowCustomPlatformUrl: true }, env).custom).toBe(true);
    resolvePlatformOrigin({ ...KEYS, allowCustomPlatformUrl: true }, env);
    expect(resolvePlatformOrigin(KEYS, { ...env, FI_ALLOW_CUSTOM_PLATFORM_URL: "1" }).custom).toBe(true);
    expect(warn).toHaveBeenCalledTimes(1);
    expect(String(warn.mock.calls[0]![0])).not.toContain("k-test-1234");
    warn.mockRestore();
    expect(() => resolvePlatformOrigin({ ...KEYS, allowCustomPlatformUrl: false }, { ...env, FI_ALLOW_CUSTOM_PLATFORM_URL: "1" })).toThrow(
      HostNotAllowedError,
    );
  });

  it("refuses mixed credentials", () => {
    expect(() => resolvePlatformOrigin({ ...KEYS, platformToken: "ee-token-123456" }, {})).toThrow(MixedCredentialsError);
    expect(() => resolvePlatformOrigin({}, { FI_API_KEY: "k", FI_SECRET_KEY: "s", FI_PLATFORM_TOKEN: "ee-token-123456" })).toThrow(
      MixedCredentialsError,
    );
  });

  it("Bearer mode sends the token and its selectors only", () => {
    const o = resolvePlatformOrigin(
      { allowInsecureHttp: true },
      {
        FI_PLATFORM_TOKEN: "ee-token-123456",
        FI_PLATFORM_BASE_URL: "http://ee.lan:8080",
        FI_WORKSPACE_ID: "ws-1",
        FI_ORGANIZATION_ID: "org-1",
      },
    );
    expect(o.mode).toBe("bearer");
    expect(o.headers).toEqual({ Authorization: "Bearer ee-token-123456", "X-Omega-Workspace": "ws-1", "X-Omega-Org": "org-1" });
  });

  it("sends selectors only when set", () => {
    expect(Object.keys(resolvePlatformOrigin(KEYS, {}).headers).sort()).toEqual(["X-Api-Key", "X-Secret-Key"]);
    const o = resolvePlatformOrigin({ ...KEYS, workspaceId: "ws-9", organizationId: "org-9" }, {});
    expect([o.headers["X-Workspace-Id"], o.headers["X-Organization-Id"]]).toEqual(["ws-9", "org-9"]);
  });

  it.each(["ftp://ee.example/x", "https://user:pw@ee.example/x", "https://ee.example/x?a=1", "https://ee.example/x#f", "not a url"])(
    "an unusable origin %s is PlatformNotConfiguredError",
    (url) => {
      expect(() => resolvePlatformOrigin({ ...KEYS, platformBaseUrl: url }, {})).toThrow(PlatformNotConfiguredError);
    },
  );

  // The key pair comes from one place, as in Python (test_origins.py has the same rows). A half pair from the
  // arguments never borrows the other half from the environment, so the guard's "same source" can
  // never exempt an origin that matches only one of the two keys.
  it.each([
    [
      "reverse: secretKey argument, FI_API_KEY and a non-zone FI_PLATFORM_BASE_URL in the environment",
      { secretKey: "s-arg-reverse", baseUrl: "https://api.futureagi.com" },
      { FI_API_KEY: "k-env-reverse", FI_PLATFORM_BASE_URL: "https://evil.example/omega/api" },
      "FI_API_KEY",
    ],
    [
      "forward: apiKey and a non-zone platformBaseUrl as arguments, FI_SECRET_KEY in the environment",
      { apiKey: "k-arg-forward", baseUrl: "https://api.futureagi.com", platformBaseUrl: "https://evil.example/omega/api" },
      { FI_SECRET_KEY: "s-env-forward" },
      "FI_SECRET_KEY",
    ],
    ["a half pair with a derived origin", { apiKey: "k-arg-derived" }, { FI_SECRET_KEY: "s-env-derived" }, "FI_SECRET_KEY"],
    [
      "a half pair even with the allow flag",
      { apiKey: "k-arg-flag", platformBaseUrl: "https://ee.corp.example/omega/api", allowCustomPlatformUrl: true },
      { FI_SECRET_KEY: "s-env-flag", FI_ALLOW_CUSTOM_PLATFORM_URL: "1" },
      "FI_SECRET_KEY",
    ],
  ] as const)("%s is CredentialsMissingError, never a split pair", (_name, inputs, env, missing) => {
    let caught: unknown;
    try {
      resolvePlatformOrigin(inputs, env);
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(CredentialsMissingError);
    const message = String((caught as Error).message);
    expect(message).toContain(`No ${missing}`);
    expect(message).toContain("The key pair comes from one place");
    for (const value of [...Object.values(inputs), ...Object.values(env)]) {
      if (typeof value === "string" && /^[ks]-/u.test(value)) expect(message).not.toContain(value);
    }
  });

  it("an argument pair ignores the environment's keys, and an environment half pair names what is missing", () => {
    const o = resolvePlatformOrigin(KEYS, { FI_API_KEY: "k-env-other", FI_SECRET_KEY: "s-env-other" });
    expect([o.headers["X-Api-Key"], o.headers["X-Secret-Key"]]).toEqual(["k-test-1234", "s-test-1234"]);
    expect(() => resolvePlatformOrigin({}, { FI_API_KEY: "k-env-only" })).toThrow(/No FI_SECRET_KEY for/u);
    expect(() => resolvePlatformOrigin({}, { FI_API_KEY: "k-env-only" })).not.toThrow(/one place/u);
  });

  it.each(GUARD_CASES.map((c) => [JSON.stringify(c.url), c.verdict, c.url] as const))(
    "the shared guard table: %s is %s",
    (_shown, verdict, url) => {
      let got: string;
      try {
        resolvePlatformOrigin(KEYS, { FI_PLATFORM_BASE_URL: url });
        got = "allow";
      } catch (error) {
        if (error instanceof HostNotAllowedError) got = "refuse:host";
        else if (error instanceof PlatformNotConfiguredError) {
          expect(error.code).toBe("invalid_platform_url");
          got = "refuse:invalid";
        } else throw error;
      }
      expect(got).toBe(verdict);
    },
  );

  it("no keys and no token is CredentialsMissingError naming FI_PLATFORM_TOKEN", () => {
    expect(() => resolvePlatformOrigin({}, {})).toThrow(CredentialsMissingError);
    expect(() => resolvePlatformOrigin({}, {})).toThrow(/FI_PLATFORM_TOKEN/u);
  });
});
