/**
 * A key in the query is found under a nested or bracketed param name (`auth[api_key]`, `api_key[]`, `auth.api_key`),
 * after a `;` separator and inside nested params, and a configured key is found in a header value in the spellings a
 * form encoder, a lower-case percent encoder, `encodeURI` and a slash-escaping JSON encoder give it. Counted at a
 * loopback target behind a dial shim.
 */
import net from "node:net";

import { HttpClient } from "../../api/auth";
import { HttpMethod } from "../../api/types";
import { ConfigurationError } from "../errors";
import { resetHttpWarnings } from "../http-security";
import { headersCarryKey, queryCarriesKey } from "../key-headers";
import { Sink, realConnect, shimConnect } from "../__fixtures__/plaintext-sinks";

const MARKER = "marker-query-0000000000";
/** A planted key with characters each encoder treats differently: `!`, `(`, `)`, `/`, a space and a non-ASCII letter. */
const ODD = "marker odd!(odd)/é-0000000000";
const NAMES = ["FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_API_KEY", "FI_SECRET_KEY"];
const saved: Record<string, string | undefined> = {};
const target = new Sink();
const wire = (): string => Buffer.concat(target.chunks).toString("latin1");
const markers = (): number => wire().split(MARKER).length - 1;

beforeAll(async () => { await target.listen(); net.Socket.prototype.connect = shimConnect as never; });
afterAll(() => { net.Socket.prototype.connect = realConnect; target.close(); });
beforeEach(() => {
  for (const name of NAMES) { saved[name] = process.env[name]; delete process.env[name]; }
  target.reset();
  resetHttpWarnings();
  jest.spyOn(console, "warn").mockImplementation(() => undefined);
});
afterEach(() => {
  jest.restoreAllMocks();
  for (const name of NAMES) { if (saved[name] === undefined) delete process.env[name]; else process.env[name] = saved[name]; }
});

async function outcome(run: () => PromiseLike<unknown>): Promise<unknown> {
  try { await run(); } catch (error) { return error; }
  return undefined;
}
const FUTURE = (): string => `http://api.futureagi.com:${target.port}`;
const client = (): HttpClient => new HttpClient({ baseUrl: FUTURE(), retryAttempts: 1, timeout: 3000 });

describe("a key-named param", () => {
  it.each([
    ["a bracketed name in the URL", `/probe?auth[api_key]=${MARKER}`, undefined],
    ["a name with empty brackets in the URL", `/probe?api_key[]=${MARKER}`, undefined],
    ["a percent-encoded bracketed name in the URL", `/probe?auth%5Bx-api-key%5D=${MARKER}`, undefined],
    ["a dotted name in the URL", `/probe?auth.secret_key=${MARKER}`, undefined],
    ["an item after a ; separator", `/probe?page=1;api_key=${MARKER}`, undefined],
    ["a nested params object", "/probe", { auth: { api_key: MARKER } }],
    ["a params list under a name", "/probe", { auth: [{ apikey: MARKER }] }],
  ])("is found as %s", (_name, url, params) => {
    expect(queryCarriesKey(url, params, { env: {} })).toBe(true);
  });

  it.each([
    ["a bracketed name in the URL", `/probe?auth[api_key]=${MARKER}`, undefined],
    ["an item after a ; separator", `/probe?page=1;api_key=${MARKER}`, undefined],
    ["a nested params object", "/probe", { auth: { api_key: MARKER } }],
  ])("as %s is refused by HttpClient for a Future AGI host over http: no connection, no key byte", async (_name, url, params) => {
    const error = await outcome(() => client().request({ method: HttpMethod.GET, url, ...(params === undefined ? {} : { params: params as never }) }));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect([target.connections, markers()]).toEqual([0, 0]);
  });
});

describe("a configured key re-spelled inside a header value", () => {
  const spelled: Array<[string, (key: string) => string]> = [
    ["form-encoded", (key) => new URLSearchParams({ note: key }).toString()],
    ["percent-encoded with lower-case hex", (key) => encodeURIComponent(key).replace(/%[0-9A-F]{2}/gu, (h) => h.toLowerCase())],
    ["written by encodeURI", (key) => encodeURI(key)],
    ["in JSON with every slash escaped", (key) => JSON.stringify({ note: key }).replace(/\//gu, "\\/")],
  ];
  it.each(spelled)("is found %s", (_name, spell) => {
    expect(headersCarryKey([{ "x-note": spell(ODD) }], { configured: [ODD], env: {} })).toBe(true);
  });

  it("form-encoded, is refused by HttpClient for a Future AGI host over http when the key is FI_API_KEY: no connection", async () => {
    process.env.FI_API_KEY = ODD;
    const spelledKey = new URLSearchParams({ note: ODD }).toString();
    const error = await outcome(() => client().request({ method: HttpMethod.GET, url: "/probe", headers: { "x-note": spelledKey } as never }));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect([target.connections, wire().split(spelledKey).length - 1]).toEqual([0, 0]);
  });
});
