// Keyed https requests of HttpClient and APIKeyAuth (axios http adapter) under proxy variables.
//
// The proxy is a loopback listener reached through a host name that a lookup shim resolves to the loopback address,
// so it counts as a proxy that is not loopback. The target is an https listener with a certificate from a scratch CA
// trusted by this process. A keyed request is expected to reach the proxy only as a CONNECT request (TLS from the
// client to the target through the tunnel), so the proxy holds no key bytes and the target receives the key.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";

import { APIKeyAuth, HttpClient } from "../api/auth";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

const SHIM_HOST: string = fx.SHIM_HOST;

interface Target {
  port: number;
  connections: number;
  requests: string[];
  raw(): string;
  count(markers: string[]): number;
  close(): Promise<void>;
}

interface Proxy {
  port: number;
  connections: number;
  connects: string[];
  absolute: string[];
  raw(): string;
  count(markers: string[]): number;
  close(): Promise<void>;
}

let undoLookup: () => void;
beforeAll(() => {
  fx.certificates();
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
});

let target: Target;
let proxy: Proxy | undefined;
beforeEach(async () => {
  target = await fx.tlsTarget();
  proxy = undefined;
});
afterEach(async () => {
  await target.close();
  if (proxy) await proxy.close();
});

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;
const basic = (user: string, password: string) => Buffer.from(`${user}:${password}`).toString("base64");
const targetUrl = () => `https://${SHIM_HOST}:${target.port}`;
const proxyUrl = (p: Proxy, credentials = "") => `http://${credentials}${SHIM_HOST}:${p.port}`;

async function startProxy(options: Record<string, unknown> = {}): Promise<Proxy> {
  proxy = await fx.proxySink(options);
  return proxy as Proxy;
}

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

/** Run `run` with every proxy variable cleared except `vars`, then restore the environment. */
async function withEnv<T>(vars: Record<string, string>, run: () => Promise<T>): Promise<T> {
  const saved = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  Object.assign(process.env, vars);
  try {
    return await run();
  } finally {
    for (const [name, value] of saved) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
}

function client(config: Record<string, unknown> = {}): HttpClient {
  return new HttpClient({ baseUrl: targetUrl(), retryAttempts: 1, timeout: 5000, ...config } as any);
}

function keyClient(fiApiKey: string, fiSecretKey: string): APIKeyAuth {
  return new APIKeyAuth({ fiApiKey, fiSecretKey, baseUrl: targetUrl(), retryAttempts: 1, timeout: 5000 });
}

const get = (c: HttpClient, headers?: Record<string, string>) =>
  c.request({ method: "GET", url: "/v1/probe", ...(headers === undefined ? {} : { headers }) } as any);

/** Header names (lower case) of a request head. */
function headerNames(head: string): string[] {
  return head
    .split("\r\n\r\n")[0]
    .split("\r\n")
    .slice(1)
    .map((line) => line.slice(0, line.indexOf(":")).trim().toLowerCase());
}

/** A header value of a request head, or undefined. */
function headerValue(head: string, name: string): string | undefined {
  for (const line of head.split("\r\n\r\n")[0].split("\r\n").slice(1)) {
    const at = line.indexOf(":");
    if (line.slice(0, at).trim().toLowerCase() === name) return line.slice(at + 1).trim();
  }
  return undefined;
}

const KEY_HEADERS = ["x-api-key", "x-secret-key", "authorization", "cookie"];

/** The keyed request reached the proxy only as CONNECT to the target, and the key reached the target. */
function expectTunnelled(p: Proxy, markers: string[]): void {
  expect({
    proxyKeyBytes: p.count(markers),
    absolute: p.absolute.length,
    connectsAtLeastOne: p.connects.length >= 1,
    targetReached: target.count(markers) > 0,
  }).toEqual({ proxyKeyBytes: 0, absolute: 0, connectsAtLeastOne: true, targetReached: true });
  for (const head of p.connects) {
    expect(head.split("\r\n")[0]).toBe(`CONNECT ${SHIM_HOST}:${target.port} HTTP/1.1`);
    expect(headerNames(head)).toContain("host");
    expect(headerNames(head).filter((name) => KEY_HEADERS.includes(name))).toEqual([]);
  }
}

describe("HttpClient and APIKeyAuth: a keyed https request through an env proxy goes inside a CONNECT tunnel", () => {
  test("a keyed https request through HTTPS_PROXY reaches the proxy only as CONNECT: X-Api-Key and X-Secret-Key of APIKeyAuth", async () => {
    const p = await startProxy();
    const [apiKey, secretKey] = [marker("tk"), marker("ts")];
    await withEnv({ HTTPS_PROXY: proxyUrl(p) }, () => get(keyClient(apiKey, secretKey)));
    expectTunnelled(p, [apiKey, secretKey]);
    expect(target.count([apiKey])).toBeGreaterThan(0);
    expect(target.count([secretKey])).toBeGreaterThan(0);
  });

  test("a keyed https request through HTTPS_PROXY reaches the proxy only as CONNECT: X-Secret-Key alone", async () => {
    const p = await startProxy();
    const secretKey = marker("tx");
    await withEnv({ HTTPS_PROXY: proxyUrl(p) }, () => get(client({ defaultHeaders: { "X-Secret-Key": secretKey } })));
    expectTunnelled(p, [secretKey]);
  });

  test("a keyed https request through HTTPS_PROXY reaches the proxy only as CONNECT: Authorization Bearer", async () => {
    const p = await startProxy();
    const token = marker("tb");
    await withEnv({ HTTPS_PROXY: proxyUrl(p) }, () => get(client({ defaultHeaders: { Authorization: `Bearer ${token}` } })));
    expectTunnelled(p, [token]);
  });

  test("a keyed https request through HTTPS_PROXY reaches the proxy only as CONNECT: per-call Authorization Basic header", async () => {
    const p = await startProxy();
    const password = marker("th");
    const encoded = basic("u", password);
    await withEnv({ HTTPS_PROXY: proxyUrl(p) }, () => get(client(), { Authorization: `Basic ${encoded}` }));
    expectTunnelled(p, [encoded]);
  });

  test("a keyed https request through HTTPS_PROXY reaches the proxy only as CONNECT: axios auth option set per request", async () => {
    const p = await startProxy();
    const password = marker("ta");
    const encoded = basic("u", password);
    const c = client();
    (c as any)._axiosInstance.interceptors.request.use((cfg: any) => {
      cfg.auth = { username: "u", password };
      return cfg;
    });
    await withEnv({ HTTPS_PROXY: proxyUrl(p) }, () => get(c));
    expect(p.count([password])).toBe(0);
    expectTunnelled(p, [encoded]);
  });

  test("a keyed https request through lowercase https_proxy reaches the proxy only as CONNECT", async () => {
    const p = await startProxy();
    const key = marker("tl");
    await withEnv({ https_proxy: proxyUrl(p) }, () => get(client({ defaultHeaders: { "X-Api-Key": key } })));
    expectTunnelled(p, [key]);
  });

  test("a keyed https request through ALL_PROXY reaches the proxy only as CONNECT", async () => {
    const p = await startProxy();
    const key = marker("tp");
    await withEnv({ ALL_PROXY: proxyUrl(p) }, () => get(client({ defaultHeaders: { "X-Api-Key": key } })));
    expectTunnelled(p, [key]);
  });

  test("credentials in the proxy URL go in the CONNECT as Proxy-Authorization and do not reach the target", async () => {
    const p = await startProxy();
    const key = marker("tc");
    const proxyPassword = marker("pw");
    const proxyEncoded = basic("puser", proxyPassword);
    await withEnv({ HTTPS_PROXY: proxyUrl(p, `puser:${proxyPassword}@`) }, () => get(client({ defaultHeaders: { "X-Api-Key": key } })));
    expectTunnelled(p, [key]);
    for (const head of p.connects) expect(headerValue(head, "proxy-authorization")).toBe(`Basic ${proxyEncoded}`);
    expect(target.count([proxyPassword, proxyEncoded])).toBe(0);
    expect(target.requests.length).toBeGreaterThan(0);
    for (const head of target.requests) expect(headerNames(head)).not.toContain("proxy-authorization");
  });

  test("8 concurrent keyed requests from 8 clients each reach the target through the tunnel with their own keys", async () => {
    const p = await startProxy();
    const pairs = Array.from({ length: 8 }, (_, i) => [marker(`m${i}a`), marker(`m${i}s`)] as const);
    const all = pairs.flatMap(([a, s]) => [a, s]);
    await withEnv({ HTTPS_PROXY: proxyUrl(p) }, () => Promise.all(pairs.map(([a, s]) => get(keyClient(a, s)))));
    expect(p.count(all)).toBe(0);
    expect(p.absolute.length).toBe(0);
    expect(p.connects.length).toBeGreaterThanOrEqual(1);
    for (const head of p.connects) expect(headerNames(head).filter((name) => KEY_HEADERS.includes(name))).toEqual([]);
    expect(target.requests).toHaveLength(8);
    const owners = target.requests.map((head) => pairs.map(([a, s], i) => (head.includes(a) || head.includes(s) ? i : -1)).filter((i) => i >= 0));
    for (const [index, found] of owners.entries()) {
      expect({ head: index, clients: found.length }).toEqual({ head: index, clients: 1 });
      const [a, s] = pairs[found[0]];
      expect(target.requests[index].includes(a) && target.requests[index].includes(s)).toBe(true);
    }
    expect(owners.map((found) => found[0]).sort((x, y) => x - y)).toEqual([0, 1, 2, 3, 4, 5, 6, 7]);
  });

  test("a proxy that answers CONNECT with 407 makes the keyed request fail with no key bytes at the proxy and no connection to the target", async () => {
    const p = await startProxy({ connectStatus: 407 });
    const key = marker("tr");
    const error = await withEnv({ HTTPS_PROXY: proxyUrl(p) }, () =>
      get(client({ defaultHeaders: { "X-Api-Key": key } })).then(
        () => undefined,
        (e: unknown) => e,
      ),
    );
    expect({ proxyKeyBytes: p.count([key]), absolute: p.absolute.length, targetConnections: target.connections }).toEqual({
      proxyKeyBytes: 0,
      absolute: 0,
      targetConnections: 0,
    });
    expect(error).toBeInstanceOf(Error);
  });
});
