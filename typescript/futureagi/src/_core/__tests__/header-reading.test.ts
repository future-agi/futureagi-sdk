/**
 * Header containers the SDK cannot read are refused with the typed `unreadable_headers` error (an iterable whose
 * iterator throws, a pair whose name is not a string), and an axios `common` or method layer held as a list of pairs is
 * read like a record layer. Counted at a loopback target behind a dial shim.
 */
import net from "node:net";

import { HttpClient } from "../../api/auth";
import { HttpMethod } from "../../api/types";
import { ConfigurationError } from "../errors";
import { resetHttpWarnings } from "../http-security";
import { headersCarryKey, normalizeHeaders } from "../key-headers";
import { Sink, realConnect, shimConnect } from "../__fixtures__/plaintext-sinks";

const MARKER = "marker-reading-0000000000";
const NAMES = ["FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_API_KEY", "FI_SECRET_KEY"];
const saved: Record<string, string | undefined> = {};
const target = new Sink();
const targetMarkers = (): number => Buffer.concat(target.chunks).toString("latin1").split(MARKER).length - 1;

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

function thrown(run: () => unknown): unknown {
  try { run(); } catch (error) { return error; }
  return undefined;
}
async function outcome(run: () => PromiseLike<unknown>): Promise<unknown> {
  try { await run(); } catch (error) { return error; }
  return undefined;
}
const THROWING = (): unknown => ({ [Symbol.iterator]: () => ({ next: () => { throw new Error("read failed"); } }) });
const SYMBOL_NAME = (): unknown => [[Symbol("x-api-key"), MARKER]];
const FUTURE = (): string => `http://api.futureagi.com:${target.port}`;

describe("a header container that cannot be read", () => {
  it.each([
    ["an iterable whose iterator throws", THROWING],
    ["a pair whose name is a symbol", SYMBOL_NAME],
    ["a spread pair whose name is a symbol", () => ({ ...[[Symbol("x-api-key"), MARKER]] })],
  ])("is %s: refused with unreadable_headers, and counted as keyed", (_name, build) => {
    const error = thrown(() => normalizeHeaders(build() as never));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect((error as ConfigurationError).code).toBe("unreadable_headers");
    expect(headersCarryKey([build() as never], { env: {} })).toBe(true);
  });

  it.each([
    ["an iterable whose iterator throws", THROWING],
    ["a pair whose name is a symbol", SYMBOL_NAME],
  ])("is %s as HttpClient's defaultHeaders: refused with unreadable_headers, no connection", async (_name, build) => {
    const error = await outcome(async () => new HttpClient({ baseUrl: `http://127.0.0.1:${target.port}`, defaultHeaders: build() as never, retryAttempts: 1, timeout: 3000 })
      .request({ method: HttpMethod.GET, url: "/probe" }));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect((error as ConfigurationError).code).toBe("unreadable_headers");
    expect([target.connections, targetMarkers()]).toEqual([0, 0]);
  });
});

describe("an axios layer held as a list of pairs", () => {
  it.each([
    ["the common layer", { common: [["X-Api-Key", MARKER]] }],
    ["the layer of the method sent", { get: [["X-Api-Key", MARKER]] }],
  ])("is read for %s: the key in it makes the request keyed", (_name, layered) => {
    expect(headersCarryKey([layered as never], { env: {}, axiosMethod: "get" })).toBe(true);
  });

  it("is read only for the layer of the method sent: a key in the post layer is part of a POST, not of a GET", () => {
    expect(headersCarryKey([{ post: [["X-Api-Key", MARKER]] } as never], { env: {}, axiosMethod: "post" })).toBe(true);
    expect(headersCarryKey([{ post: [["X-Api-Key", MARKER]] } as never], { env: {}, axiosMethod: "get" })).toBe(false);
  });

  it("with a key, in HttpClient's defaultHeaders, is refused for a Future AGI host over http: no connection, no key byte", async () => {
    const error = await outcome(() => new HttpClient({ baseUrl: FUTURE(), defaultHeaders: { common: [["X-Api-Key", MARKER]] } as never, retryAttempts: 1, timeout: 3000, allowInsecureHttp: true })
      .request({ method: HttpMethod.GET, url: "/probe" }));
    expect(error).toBeInstanceOf(ConfigurationError);
    expect([target.connections, targetMarkers()]).toEqual([0, 0]);
  });
});
