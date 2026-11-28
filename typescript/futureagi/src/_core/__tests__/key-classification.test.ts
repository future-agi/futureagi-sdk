/**
 * What makes a request keyed beyond its header names: a key in the query or the params, and a key a JSON or URL encoder
 * has re-spelled inside a header value (the gateway's `x-agentcc-metadata` is JSON). Counted at loopback listeners
 * behind a name-resolution shim.
 */
import net from "node:net";

import { HttpClient } from "../../api/auth";
import { HttpMethod } from "../../api/types";
import { ConfigurationError } from "../errors";
import { resetHttpWarnings } from "../http-security";
import { headersCarryKey, queryCarriesKey } from "../key-headers";
import { Sink, realConnect, shimConnect } from "../__fixtures__/plaintext-sinks";

/** A planted key with a quote, a backslash and a non-ASCII letter: each encoder spells it differently. */
const ODD_KEY = 'FIMARKQ"ER\\KEY-é7f3a91';
const PLAIN_KEY = ["FIMARK", "ERKEY-", "7f3a91", "c2"].join("");
const target = new Sink();
const proxy = new Sink("502 Bad Gateway");
const NAMES = ["FI_API_KEY", "FI_SECRET_KEY", "FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy"];
const saved: Record<string, string | undefined> = {};
beforeAll(async () => { await Promise.all([target.listen(), proxy.listen()]); net.Socket.prototype.connect = shimConnect as never; });
afterAll(() => { net.Socket.prototype.connect = realConnect; target.close(); proxy.close(); });
beforeEach(() => {
  for (const name of NAMES) { saved[name] = process.env[name]; delete process.env[name]; }
  target.reset(); proxy.reset(); resetHttpWarnings();
  jest.spyOn(console, "warn").mockImplementation(() => undefined);
});
afterEach(() => { jest.restoreAllMocks(); for (const name of NAMES) { if (saved[name] === undefined) delete process.env[name]; else process.env[name] = saved[name]; } });

describe("a key re-spelled inside a header value", () => {
  const spellings: Array<[string, (key: string) => string]> = [
    ["a JSON string", (key) => JSON.stringify({ note: key })],
    ["a JSON string with every non-ASCII letter as \\u escapes", (key) => JSON.stringify({ note: key }).replace(/[\u0080-￿]/gu, (c) => `\\u${c.charCodeAt(0).toString(16).padStart(4, "0")}`)],
    ["a percent-encoded value", (key) => `note=${encodeURIComponent(key)}`],
  ];
  it.each(spellings)("is found as %s", (_name, spell) => {
    expect(headersCarryKey([{ "x-agentcc-metadata": spell(ODD_KEY) }], { configured: [ODD_KEY], env: {} })).toBe(true);
  });
  it("leaves a value without the key alone", () => {
    expect(headersCarryKey([{ "x-agentcc-metadata": JSON.stringify({ note: "nothing here" }) }], { configured: [ODD_KEY], env: {} })).toBe(false);
  });
});

describe("a key in the query or the params", () => {
  it.each([
    ["a key-named param", "/probe", { api_key: "abc" }],
    ["a header-named param", "/probe", { "X-Api-Key": "abc" }],
    ["a key-named query item", "/probe?secret-key=abc", undefined],
    ["a param holding the configured key", "/probe", { note: PLAIN_KEY }],
    ["a query item holding the configured key, percent-encoded", `/probe?note=${encodeURIComponent(ODD_KEY)}`, undefined],
    ["a list of param pairs", "/probe", [["apikey", "abc"]]],
  ])("counts %s as a key", (_name, url, params) => {
    expect(queryCarriesKey(url as string, params, { configured: [PLAIN_KEY, ODD_KEY], env: {} })).toBe(true);
  });
  it("leaves ordinary params alone", () => {
    expect(queryCarriesKey("/probe?limit=1", { page: 2, name: "x" }, { configured: [PLAIN_KEY], env: {} })).toBe(false);
  });
});

describe("an HttpClient send", () => {
  const client = (base: string, allow?: boolean) => new HttpClient({ baseUrl: base, retryAttempts: 1, timeout: 3000, ...(allow === undefined ? {} : { allowInsecureHttp: allow }) });
  const run = (c: HttpClient, url: string, params?: unknown) => c.request({ method: HttpMethod.GET, url, ...(params === undefined ? {} : { params: params as never }) }).then(() => undefined, (error: unknown) => error);

  it("refuses a key-named param to a Future AGI host over http: no connection, no key byte", async () => {
    const error = await run(client(`http://api.futureagi.com:${target.port}`), "/probe", { api_key: PLAIN_KEY });
    expect(error).toBeInstanceOf(ConfigurationError);
    expect(target.connections).toBe(0);
    expect(target.markerBytes).toBe(0);
  });
  it("refuses a key in the URL's query to a non-loopback http host without the opt-in", async () => {
    process.env.FI_API_KEY = PLAIN_KEY;
    const error = await run(client(`http://plain.example.test:${target.port}`), `/probe?note=${PLAIN_KEY}`);
    expect(error).toBeInstanceOf(ConfigurationError);
    expect(target.connections).toBe(0);
    expect(target.markerBytes).toBe(0);
  });
  it("sends a key-named param with the opt-in straight to the target, not through an environment proxy", async () => {
    const url = `http://127.0.0.1:${proxy.port}`;
    Object.assign(process.env, { HTTP_PROXY: url, http_proxy: url });
    await run(client(`http://plain.example.test:${target.port}`, true), "/probe", { api_key: PLAIN_KEY });
    expect(target.markerBytes).toBeGreaterThan(0);
    expect(proxy.connections).toBe(0);
  });
});
