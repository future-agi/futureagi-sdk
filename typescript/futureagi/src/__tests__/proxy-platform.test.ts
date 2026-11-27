// The platform client (runtime fetch) under a proxy set in the environment.
//
// Every listener here is on the loopback address. The shim host name resolves to 127.0.0.1 in this process, so a
// target or proxy named by it counts as a host that is not loopback while its bytes land in a listener of this file.
// Keys are random marker strings made per test. A keyed request for which a proxy applies is expected to reach the
// proxy only as a CONNECT request (the keys travel inside the tunnel), and to reach the target with both keys.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
import * as net from "node:net";

import { Client } from "../platform/client";
import type { FetchLike } from "../platform/transport";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30000);

const ENVELOPE = { status: true, result: {} };
const KEY_HEADERS = ["x-api-key", "x-secret-key", "authorization", "cookie"];
const ENV_NAMES = [
  "HTTP_PROXY",
  "http_proxy",
  "HTTPS_PROXY",
  "https_proxy",
  "ALL_PROXY",
  "all_proxy",
  "NO_PROXY",
  "no_proxy",
  "npm_config_https_proxy",
  "npm_config_http_proxy",
  "npm_config_proxy",
  "npm_config_no_proxy",
  "FI_ALLOW_INSECURE_HTTP",
];

let undoLookup: () => void;
beforeAll(() => {
  fx.certificates();
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
});

// --- listeners ------------------------------------------------------------------------------------------------

let target: any;
let proxy: any;
let plain: PlainTarget | undefined;
beforeEach(async () => {
  target = await fx.tlsTarget();
  proxy = await fx.proxySink();
  plain = undefined;
});
afterEach(async () => {
  await target.close();
  await proxy.close();
  if (plain) await plain.close();
});

interface PlainTarget {
  port: number;
  connections: number;
  requests: string[];
  count(markers: string[]): number;
  close(): Promise<void>;
}

/** A plain-http listener that records every byte it receives and answers each request with the JSON envelope. */
async function plainTarget(): Promise<PlainTarget> {
  const chunks: string[] = [];
  const requests: string[] = [];
  const sockets = new Set<net.Socket>();
  const state = { connections: 0 };
  const server = net.createServer((socket) => {
    state.connections++;
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
    let head = "";
    let answered = false;
    socket.on("data", (data) => {
      const text = data.toString("latin1");
      chunks.push(text);
      if (answered) return;
      head += text;
      if (!head.includes("\r\n\r\n")) return;
      answered = true;
      requests.push(head);
      socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${fx.REPLY_BODY.length}\r\nConnection: close\r\n\r\n${fx.REPLY_BODY}`);
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return state.connections;
    },
    requests,
    count(markers: string[]) {
      const all = chunks.join("");
      let bytes = 0;
      for (const marker of markers) {
        for (let at = all.indexOf(marker); at >= 0; at = all.indexOf(marker, at + marker.length)) bytes += marker.length;
      }
      return bytes;
    },
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
}

// --- helpers --------------------------------------------------------------------------------------------------

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;
const targetUrl = () => `https://${fx.SHIM_HOST}:${target.port}`;
const shimProxyUrl = () => `http://${fx.SHIM_HOST}:${proxy.port}`;
const loopbackProxyUrl = () => `http://127.0.0.1:${proxy.port}`;

/** Run `run` with every proxy variable cleared and then `set` applied, and restore the environment afterwards. */
async function withEnv<T>(set: Record<string, string>, run: () => Promise<T>): Promise<T> {
  const saved = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  Object.assign(process.env, set);
  try {
    return await run();
  } finally {
    for (const [name, value] of saved) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
}

function platform(baseUrl: string, apiKey: string, secretKey: string, config: Record<string, unknown> = {}): Client {
  return new Client({ apiKey, secretKey, baseUrl, maxRetries: 0, timeout: 5000, ...config } as any);
}

const probe = (client: Client) => client.request("GET", "/v1/probe/", { unwrap: null });

/** The header names of a request head, lower case. */
function headerNames(head: string): string[] {
  return head
    .split("\r\n")
    .slice(1)
    .filter((line) => line.includes(":"))
    .map((line) => line.slice(0, line.indexOf(":")).trim().toLowerCase());
}

/** The keys reached the proxy only as CONNECT: no key bytes, no absolute-form request, no key header in a CONNECT. */
function expectOnlyConnect(keys: string[]): void {
  expect({ proxyKeyBytes: proxy.count(keys), absolute: proxy.absolute.length }).toEqual({ proxyKeyBytes: 0, absolute: 0 });
  expect(proxy.connects.length).toBeGreaterThanOrEqual(1);
  for (const head of proxy.connects as string[]) {
    expect(headerNames(head).filter((name) => KEY_HEADERS.includes(name))).toEqual([]);
  }
}

/** Every key reached the target in full. */
function expectAtTarget(keys: string[], count: (markers: string[]) => number = target.count): void {
  for (const key of keys) {
    expect({ key, bytes: count([key]) }).toEqual({ key, bytes: key.length });
  }
}

// --- tests ----------------------------------------------------------------------------------------------------

describe("platform client under an environment proxy", () => {
  test.each([
    ["HTTPS_PROXY", "HTTPS_PROXY"],
    ["https_proxy", "https_proxy"],
    ["ALL_PROXY", "ALL_PROXY"],
  ])("a keyed https request through %s reaches the proxy only as CONNECT", async (_label, variable) => {
    const [apiKey, secretKey] = [marker("pa"), marker("ps")];
    const result = await withEnv({ [variable]: shimProxyUrl() }, () => probe(platform(targetUrl(), apiKey, secretKey)));
    expectOnlyConnect([apiKey, secretKey]);
    expect(proxy.connects[0].split("\r\n")[0]).toBe(`CONNECT ${fx.SHIM_HOST}:${target.port} HTTP/1.1`);
    expectAtTarget([apiKey, secretKey]);
    expect(result).toEqual(ENVELOPE);
  });

  test("a keyed https request to a host named in NO_PROXY goes to the target directly", async () => {
    const [apiKey, secretKey] = [marker("pa"), marker("ps")];
    const result = await withEnv({ HTTPS_PROXY: shimProxyUrl(), NO_PROXY: fx.SHIM_HOST }, () => probe(platform(targetUrl(), apiKey, secretKey)));
    expect({ proxyConnections: proxy.connections, proxyKeyBytes: proxy.count([apiKey, secretKey]) }).toEqual({ proxyConnections: 0, proxyKeyBytes: 0 });
    expectAtTarget([apiKey, secretKey]);
    expect(result).toEqual(ENVELOPE);
  });

  test("a keyed https request through a loopback proxy reaches the proxy only as CONNECT", async () => {
    const [apiKey, secretKey] = [marker("pa"), marker("ps")];
    const result = await withEnv({ HTTPS_PROXY: loopbackProxyUrl() }, () => probe(platform(targetUrl(), apiKey, secretKey)));
    expectOnlyConnect([apiKey, secretKey]);
    expectAtTarget([apiKey, secretKey]);
    expect(result).toEqual(ENVELOPE);
  });

  test("proxy credentials in the proxy URL go in Proxy-Authorization on the CONNECT and not to the target", async () => {
    const [apiKey, secretKey, password] = [marker("pa"), marker("ps"), marker("pp")];
    const basic = Buffer.from(`fiuser:${password}`).toString("base64");
    const proxyWithCredentials = `http://fiuser:${password}@${fx.SHIM_HOST}:${proxy.port}`;
    const result = await withEnv({ HTTPS_PROXY: proxyWithCredentials }, () => probe(platform(targetUrl(), apiKey, secretKey)));
    expectOnlyConnect([apiKey, secretKey]);
    expect(proxy.connects[0]).toMatch(new RegExp(`\\r\\nproxy-authorization: Basic ${basic}\\r\\n`, "i"));
    expect({ targetPasswordBytes: target.count([password, basic]) }).toEqual({ targetPasswordBytes: 0 });
    for (const head of target.requests as string[]) {
      expect(headerNames(head)).not.toContain("proxy-authorization");
    }
    expectAtTarget([apiKey, secretKey]);
    expect(result).toEqual(ENVELOPE);
  });

  test("concurrent keyed requests from separate clients each reach the target with their own keys inside a tunnel", async () => {
    const pairs = Array.from({ length: 8 }, (_, index) => [marker(`ca${index}`), marker(`cs${index}`)] as const);
    const results = await withEnv({ HTTPS_PROXY: shimProxyUrl() }, () => Promise.all(pairs.map(([apiKey, secretKey]) => probe(platform(targetUrl(), apiKey, secretKey)))));
    const keys = pairs.flat();
    expectOnlyConnect(keys);
    expect(results).toEqual(pairs.map(() => ENVELOPE));
    const heads = target.requests as string[];
    expect(heads).toHaveLength(pairs.length);
    for (const [apiKey, secretKey] of pairs) {
      const own = heads.filter((head) => head.includes(apiKey));
      expect(own).toHaveLength(1);
      expect(own[0]).toContain(secretKey);
      expect(keys.filter((key) => own[0].includes(key)).sort()).toEqual([apiKey, secretKey].sort());
    }
  });

  test("an opted-in keyed plain-http request with HTTP_PROXY set goes directly to the target, not to the proxy", async () => {
    plain = await plainTarget();
    const [apiKey, secretKey] = [marker("pa"), marker("ps")];
    const url = `http://${fx.SHIM_HOST}:${plain.port}`;
    const result = await withEnv({ HTTP_PROXY: shimProxyUrl() }, () => probe(platform(url, apiKey, secretKey, { allowInsecureHttp: true })));
    expect({ proxyConnections: proxy.connections, proxyKeyBytes: proxy.count([apiKey, secretKey]) }).toEqual({ proxyConnections: 0, proxyKeyBytes: 0 });
    expect(plain.requests.map((head) => head.split("\r\n")[0])).toEqual(["GET /v1/probe/ HTTP/1.1"]);
    const counter = plain;
    expectAtTarget([apiKey, secretKey], (markers) => counter.count(markers));
    expect(result).toEqual(ENVELOPE);
  });

  test("a fetch given in the client options receives the keyed request under HTTPS_PROXY", async () => {
    const [apiKey, secretKey] = [marker("pa"), marker("ps")];
    const calls: Array<{ url: string; headers: Headers }> = [];
    const fetch: FetchLike = async (url, init) => {
      calls.push({ url, headers: new Headers(init.headers) });
      return new Response(fx.REPLY_BODY, { status: 200, headers: { "Content-Type": "application/json" } });
    };
    const result = await withEnv({ HTTPS_PROXY: shimProxyUrl() }, () => probe(platform(targetUrl(), apiKey, secretKey, { fetch })));
    expect(calls.map((call) => call.url)).toEqual([`${targetUrl()}/v1/probe/`]);
    expect(calls[0].headers.get("x-api-key")).toBe(apiKey);
    expect(calls[0].headers.get("x-secret-key")).toBe(secretKey);
    expect({ proxyConnections: proxy.connections, targetConnections: target.connections }).toEqual({ proxyConnections: 0, targetConnections: 0 });
    expect(result).toEqual(ENVELOPE);
  });
});
