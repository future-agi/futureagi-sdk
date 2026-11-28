/**
 * Headers written as a spread list of pairs (`{ ...[["X-Api-Key", key]] }`, which is `{ "0": ["X-Api-Key", key] }`) or
 * as an array-like record are read by the header names they hold: a key in them makes the request keyed, so the
 * plain-http rule and the proxy rule apply, and the header is not sent under the name "0". Counted at a loopback target
 * behind a dial shim and at a loopback proxy that answers CONNECT and forwards nothing.
 */
import http from "node:http";
import net from "node:net";

import { HttpClient } from "../../api/auth";
import { HttpMethod } from "../../api/types";
import { ConfigurationError } from "../errors";
import { resetHttpWarnings } from "../http-security";
import { headersCarryKey, normalizeHeaders } from "../key-headers";
import { Sink, realConnect, shimConnect } from "../__fixtures__/plaintext-sinks";

const MARKER = "marker-spread-0000000000";
const NAMES = ["FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_API_KEY", "FI_SECRET_KEY"];
const saved: Record<string, string | undefined> = {};

/** A proxy on 127.0.0.1 that counts every connection and every marker it receives, for a plain request or a CONNECT tunnel. */
class ProxySink {
  readonly server: http.Server;
  port = 0;
  connections = 0;
  received = "";
  constructor() {
    this.server = http.createServer((_req, res) => { res.writeHead(502, { Connection: "close" }); res.end(); });
    this.server.on("connection", (socket: net.Socket) => {
      this.connections += 1;
      socket.on("data", (chunk: Buffer) => { this.received += chunk.toString("latin1"); });
      socket.on("error", () => undefined);
    });
    this.server.on("connect", (_req: http.IncomingMessage, socket: net.Socket) => {
      socket.on("error", () => undefined);
      socket.write("HTTP/1.1 200 Connection Established\r\n\r\n");
      socket.setTimeout(300, () => socket.destroy());
    });
  }
  async listen(): Promise<void> {
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    this.port = (this.server.address() as net.AddressInfo).port;
  }
  reset(): void { this.connections = 0; this.received = ""; }
  get markers(): number { return this.received.split(MARKER).length - 1; }
  close(): void { this.server.closeAllConnections(); this.server.close(); }
}

const target = new Sink();
const proxy = new ProxySink();
const targetMarkers = (): number => Buffer.concat(target.chunks).toString("latin1").split(MARKER).length - 1;

beforeAll(async () => {
  await Promise.all([target.listen(), proxy.listen()]);
  net.Socket.prototype.connect = shimConnect as never;
});
afterAll(() => {
  net.Socket.prototype.connect = realConnect;
  target.close();
  proxy.close();
});
beforeEach(() => {
  for (const name of NAMES) { saved[name] = process.env[name]; delete process.env[name]; }
  target.reset();
  proxy.reset();
  resetHttpWarnings();
  jest.spyOn(console, "warn").mockImplementation(() => undefined);
});
afterEach(() => {
  jest.restoreAllMocks();
  for (const name of NAMES) { if (saved[name] === undefined) delete process.env[name]; else process.env[name] = saved[name]; }
});

const SPREAD = (): Record<string, unknown> => ({ ...[["X-Api-Key", MARKER]] });
const ARRAY_LIKE = (): Record<string, unknown> => ({ ...["X-Api-Key", MARKER] });
const FUTURE = (): string => `http://api.futureagi.com:${target.port}`;
const REMOTE = (): string => `http://plain.example.test:${target.port}`;
const useProxy = (): void => {
  const url = `http://127.0.0.1:${proxy.port}`;
  Object.assign(process.env, { HTTP_PROXY: url, http_proxy: url, HTTPS_PROXY: url, https_proxy: url });
};
async function outcome(run: () => PromiseLike<unknown>): Promise<unknown> {
  try { await run(); } catch (error) { return error; }
  return undefined;
}
const client = (base: string, defaultHeaders?: unknown, allow?: boolean): HttpClient =>
  new HttpClient({ baseUrl: base, defaultHeaders: defaultHeaders as never, retryAttempts: 1, timeout: 3000, ...(allow === undefined ? {} : { allowInsecureHttp: allow }) });
const get = (c: HttpClient, headers?: unknown) => c.request({ method: HttpMethod.GET, url: "/probe", ...(headers === undefined ? {} : { headers: headers as never }) });

describe("a spread list of pairs", () => {
  it("is read by the names its pairs hold", () => {
    expect(normalizeHeaders(SPREAD() as never)).toEqual({ "X-Api-Key": MARKER });
    expect(normalizeHeaders({ ...[["X-Trace", "t1"]], "X-Other": "o1" } as never)).toEqual({ "X-Trace": "t1", "X-Other": "o1" });
  });
  it("makes the request keyed when a pair names a key header", () => {
    expect(headersCarryKey([SPREAD() as never], { env: {} })).toBe(true);
    expect(headersCarryKey([{ common: SPREAD() } as never], { env: {}, axiosMethod: "get" })).toBe(true);
  });
  it("as an array-like record of a name and a value is refused as unreadable and counts as keyed", () => {
    let error: unknown;
    try { normalizeHeaders(ARRAY_LIKE() as never); } catch (e) { error = e; }
    expect(error).toBeInstanceOf(ConfigurationError);
    expect((error as ConfigurationError).code).toBe("unreadable_headers");
    expect(headersCarryKey([ARRAY_LIKE() as never], { env: {} })).toBe(true);
  });
});

describe.each([
  ["a spread list of pairs", SPREAD],
  ["an array-like record", ARRAY_LIKE],
])("HttpClient headers held in %s with a key", (_form, build) => {
  it.each([
    ["without the opt-in", undefined, false],
    ["with allowInsecureHttp", true, false],
    ["with FI_ALLOW_INSECURE_HTTP=1", undefined, true],
  ])("are refused for a Future AGI host over http %s: no connection, no key byte", async (_mode, allow, env) => {
    if (env) process.env.FI_ALLOW_INSECURE_HTTP = "1";
    const defaults = await outcome(() => get(client(FUTURE(), build(), allow)));
    const perCall = await outcome(() => get(client(FUTURE(), undefined, allow), build()));
    expect(defaults).toBeInstanceOf(ConfigurationError);
    expect(perCall).toBeInstanceOf(ConfigurationError);
    expect([target.connections, targetMarkers(), proxy.connections, proxy.markers]).toEqual([0, 0, 0, 0]);
  });

  it("are refused for a Future AGI host over http with the opt-in and an environment proxy: the proxy gets no connection", async () => {
    useProxy();
    const defaults = await outcome(() => get(client(FUTURE(), build(), true)));
    const perCall = await outcome(() => get(client(FUTURE(), undefined, true), build()));
    expect(defaults).toBeInstanceOf(ConfigurationError);
    expect(perCall).toBeInstanceOf(ConfigurationError);
    expect([target.connections, targetMarkers(), proxy.connections, proxy.markers]).toEqual([0, 0, 0, 0]);
  });

  it("are refused for a host that is not loopback over http without the opt-in", async () => {
    useProxy();
    const defaults = await outcome(() => get(client(REMOTE(), build())));
    expect(defaults).toBeInstanceOf(ConfigurationError);
    expect([target.connections, targetMarkers(), proxy.connections, proxy.markers]).toEqual([0, 0, 0, 0]);
  });
});

describe("HttpClient headers held in a spread list of pairs, with the opt-in to a host that is not loopback", () => {
  it("go straight to the target under their own names, not to an environment proxy", async () => {
    useProxy();
    await outcome(() => get(client(REMOTE(), SPREAD(), true)));
    const head = Buffer.concat(target.chunks).toString("latin1").toLowerCase();
    expect(head).toContain(`\r\nx-api-key: ${MARKER}`);
    expect(head).not.toMatch(/\r\n0:/u);
    expect([proxy.connections, proxy.markers]).toEqual([0, 0]);
  });
});
