/**
 * The plain-HTTP decision and its proxy rule are one table, the same in both clients
 * (tests/fixtures/loopback/proxy_env.json, with its sha256 in the sidecar): for an http:// request URL an
 * HTTP_PROXY or ALL_PROXY routes it, HTTPS_PROXY alone does not, and NO_PROXY exempts hosts as CPython's
 * proxy_bypass_environment does. Every row has the same answer here as in the Python client.
 */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { envProxyRoutes, plaintextDecision } from "../http-security";

const FILE = join(__dirname, "../../../../../tests/fixtures/loopback/proxy_env.json");
const TABLE = JSON.parse(readFileSync(FILE, "utf8")) as {
  reasons: string[];
  envProxy: { id: string; env: Record<string, string>; url: string; proxied: boolean }[];
  hostShapes: { id: string; url: string; env: Record<string, string>; allowInsecureHttp: boolean | null; callerProxied: boolean; allowed: boolean; reason: string }[];
  decisions: { id: string; url: string; env: Record<string, string>; allowInsecureHttp: boolean | null; callerProxied: boolean; allowed: boolean; reason: string }[];
};

it("reads the fixture the sidecar names", () => {
  const sidecar = readFileSync(`${FILE}.sha256`, "utf8").trim().split(/\s+/u)[0];
  expect(createHash("sha256").update(readFileSync(FILE)).digest("hex")).toBe(sidecar);
});

describe("environment proxy rows", () => {
  it.each(TABLE.envProxy.map((row) => [row.id, row] as const))("%s", (_id, row) => {
    expect(envProxyRoutes(row.url, row.env)).toBe(row.proxied);
  });
});

describe("decision rows", () => {
  it("uses only the listed reasons", () => {
    expect(new Set(TABLE.decisions.map((row) => row.reason))).toEqual(new Set(TABLE.reasons.filter((r) => r !== "unparsable")));
  });
  it.each(TABLE.decisions.map((row) => [row.id, row] as const))("%s", (_id, row) => {
    const got = plaintextDecision(row.url, { allowInsecureHttp: row.allowInsecureHttp, env: row.env, callerProxied: row.callerProxied });
    expect(got).toEqual({ allowed: row.allowed, reason: row.reason });
  });
});

describe("host shape rows", () => {
  it("covers refusals and controls", () => {
    expect(TABLE.hostShapes.some((row) => row.reason === "ambiguous_host")).toBe(true);
    expect(TABLE.hostShapes.some((row) => row.reason === "loopback")).toBe(true);
  });
  it.each(TABLE.hostShapes.map((row) => [row.id, row] as const))("%s", (_id, row) => {
    const got = plaintextDecision(row.url, { allowInsecureHttp: row.allowInsecureHttp, env: row.env, callerProxied: row.callerProxied });
    expect(got).toEqual({ allowed: row.allowed, reason: row.reason });
  });
});

describe("a URL the parser reads as http: whatever its text looks like", () => {
  it.each(["ht\ttp://example.com/x", "\u0001http://example.com/x", " http://example.com/x", "HTTP://example.com/x"])("%j is judged as plain HTTP", (raw) => {
    expect(plaintextDecision(raw, { env: {} }).allowed).toBe(false);
  });
});
