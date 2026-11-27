// Proxy resolution for keyed requests sent by HttpClient, and keyed requests to plain-http targets.
//
// Every listener here is on the loopback address. The shim name of the support module resolves to 127.0.0.1, so a
// target or proxy addressed by that name counts as a host that is not loopback while its bytes land in a listener of
// this file.
// Keys are random marker strings made per test. A keyed request through a proxy is expected to reach the proxy only
// as a CONNECT request: zero marker bytes at the proxy, no request in absolute form, and no key header in any CONNECT
// head. Requests without a key keep the proxy behaviour of axios.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
import * as net from "node:net";
import { types } from "node:util";

import { HttpClient } from "../api/auth";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30000);

const SHIM_HOST: string = fx.SHIM_HOST;
const CODE = "insecure_http_origin";
const REPLY_BODY = JSON.stringify({ status: true, result: {} });

interface Recorder {
  port: number;
  connections: number;
  raw(): string;
  count(markers: string[]): number;
  close(): Promise<void>;
}

interface TlsTarget extends Recorder {
  requests: string[];
}

interface ProxySink extends Recorder {
  connects: string[];
  absolute: string[];
}

let undoLookup: () => void;
beforeAll(() => {
  fx.certificates();
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
});

/** A plain-http listener that records every connection and byte and answers each request with a JSON body. */
async function plainTarget(): Promise<Recorder> {
  const chunks: string[] = [];
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
      socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${REPLY_BODY.length}\r\nConnection: close\r\n\r\n${REPLY_BODY}`);
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return state.connections;
    },
    raw: () => chunks.join(""),
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

const open: Recorder[] = [];
async function track<T extends Recorder>(made: Promise<T>): Promise<T> {
  const recorder = await made;
  open.push(recorder);
  return recorder;
}
afterEach(async () => {
  await Promise.all(open.splice(0).map((recorder) => recorder.close()));
});

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;

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

/** Run `run` with every proxy variable cleared except those in `vars`, then restore the environment. */
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

function client(baseUrl: string, config: Record<string, unknown> = {}): HttpClient {
  return new HttpClient({ baseUrl, retryAttempts: 1, timeout: 5000, ...config } as any);
}

const keyed = (key: string, config: Record<string, unknown> = {}) => ({ defaultHeaders: { "X-Api-Key": key }, ...config });

const get = (http: HttpClient) => http.request({ method: "GET", url: "/v1/probe" } as any);

async function outcome(run: () => Promise<unknown>): Promise<unknown> {
  return run().then(
    () => undefined,
    (error: unknown) => error,
  );
}

/** An Error (of this realm or of Node's own) with the code insecure_http_origin. */
function expectRefusal(error: unknown): void {
  expect({ isError: error instanceof Error || types.isNativeError(error), code: (error as { code?: unknown } | undefined)?.code }).toEqual({ isError: true, code: CODE });
}

const KEY_HEADER_NAMES = new Set(["x-api-key", "x-secret-key", "authorization", "cookie"]);

/** Names of the key headers found in the CONNECT heads the proxy received. */
function keyHeadersInConnects(proxy: ProxySink): string[] {
  return proxy.connects.flatMap((head) =>
    head
      .split("\r\n")
      .slice(1)
      .filter((line) => line.includes(":"))
      .map((line) => line.slice(0, line.indexOf(":")).trim().toLowerCase())
      .filter((name) => KEY_HEADER_NAMES.has(name)),
  );
}

/** The keyed request reached the proxy only as CONNECT, and (when `reached`) the key arrived at the target. */
function expectTunnelOnly(proxy: ProxySink, target: Recorder, keys: string[], reached = true): void {
  expect({
    proxyKeyBytes: proxy.count(keys),
    absolute: proxy.absolute.length,
    tunnelled: proxy.connects.length >= 1,
    keyHeadersInConnect: keyHeadersInConnects(proxy),
  }).toEqual({ proxyKeyBytes: 0, absolute: 0, tunnelled: true, keyHeadersInConnect: [] });
  if (reached) {
    expect(target.count(keys)).toBeGreaterThan(0);
  }
}

const shimProxy = (proxy: ProxySink) => `http://${SHIM_HOST}:${proxy.port}`;
const shimHttps = (target: Recorder) => `https://${SHIM_HOST}:${target.port}`;
const shimHttp = (target: Recorder) => `http://${SHIM_HOST}:${target.port}`;

describe("NO_PROXY for a keyed https request", () => {
  const bypassing: Array<[string, (target: Recorder) => string]> = [
    ["the exact target host", () => SHIM_HOST],
    ["a domain with a leading dot", () => ".futureagi.com"],
    ["a domain with a leading star", () => "*.futureagi.com"],
    ["the target host and port", (target) => `${SHIM_HOST}:${target.port}`],
    ["a single star", () => "*"],
  ];

  test.each(bypassing)("NO_PROXY naming %s sends the keyed request straight to the target", async (_name, entry) => {
    const key = marker("npb");
    const target: TlsTarget = await track(fx.tlsTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    await withEnv({ HTTPS_PROXY: shimProxy(proxy), NO_PROXY: entry(target) }, () => get(client(shimHttps(target), keyed(key))));
    expect({ proxyConnections: proxy.connections, proxyKeyBytes: proxy.count([key]) }).toEqual({ proxyConnections: 0, proxyKeyBytes: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });

  const notBypassing: Array<[string, (target: Recorder) => string]> = [
    ["another host", () => "other-host.example.org"],
    ["the target host with another port", (target) => `${SHIM_HOST}:${target.port + 1}`],
  ];

  test.each(notBypassing)("NO_PROXY naming %s leaves the keyed request to reach the proxy only as CONNECT", async (_name, entry) => {
    const key = marker("npc");
    const target: TlsTarget = await track(fx.tlsTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    await withEnv({ HTTPS_PROXY: shimProxy(proxy), NO_PROXY: entry(target) }, () => get(client(shimHttps(target), keyed(key))));
    expectTunnelOnly(proxy, target, [key]);
  });
});

describe("proxy given by environment or by the axios proxy option", () => {
  test("a keyed https request through a loopback https_proxy reaches the proxy only as CONNECT", async () => {
    const [apiKey, secretKey] = [marker("lpa"), marker("lps")];
    const target: TlsTarget = await track(fx.tlsTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    await withEnv({ https_proxy: `http://127.0.0.1:${proxy.port}` }, () =>
      get(client(shimHttps(target), { defaultHeaders: { "X-Api-Key": apiKey, "X-Secret-Key": secretKey } })),
    );
    expectTunnelOnly(proxy, target, [apiKey, secretKey]);
  });

  test("a keyed https request with an axios proxy object on the client defaults reaches that proxy only as CONNECT", async () => {
    const key = marker("pxd");
    const target: TlsTarget = await track(fx.tlsTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    const http = client(shimHttps(target), keyed(key));
    (http as any)._axiosInstance.defaults.proxy = { protocol: "http", host: SHIM_HOST, port: proxy.port };
    await withEnv({}, () => get(http));
    expectTunnelOnly(proxy, target, [key]);
  });

  test("a keyed https request with an axios proxy object set per request reaches that proxy only as CONNECT", async () => {
    const key = marker("pxr");
    const target: TlsTarget = await track(fx.tlsTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    const http = client(shimHttps(target), keyed(key));
    (http as any)._axiosInstance.interceptors.request.use((config: any) => {
      config.proxy = { protocol: "http", host: SHIM_HOST, port: proxy.port };
      return config;
    });
    await withEnv({}, () => get(http));
    expectTunnelOnly(proxy, target, [key]);
  });

  test("proxy credentials in the axios proxy object go in Proxy-Authorization on the CONNECT only", async () => {
    const key = marker("pxa");
    const password = marker("pxp");
    const basic = Buffer.from(`fiuser:${password}`).toString("base64");
    const target: TlsTarget = await track(fx.tlsTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    const http = client(shimHttps(target), keyed(key));
    (http as any)._axiosInstance.defaults.proxy = { protocol: "http", host: SHIM_HOST, port: proxy.port, auth: { username: "fiuser", password } };
    await withEnv({}, () => get(http));
    expectTunnelOnly(proxy, target, [key]);
    expect(proxy.connects.map((head) => head.toLowerCase().includes(`\r\nproxy-authorization: basic ${basic.toLowerCase()}\r\n`))).toEqual(
      proxy.connects.map(() => true),
    );
    expect({ targetCredentialBytes: target.count([basic, password]), targetProxyAuthorization: /\r\nproxy-authorization:/i.test(target.raw()) }).toEqual({
      targetCredentialBytes: 0,
      targetProxyAuthorization: false,
    });
  });

  test("a caller proxy option of false keeps a keyed request away from HTTPS_PROXY", async () => {
    const key = marker("pxf");
    const target: TlsTarget = await track(fx.tlsTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    const http = client(shimHttps(target), keyed(key));
    (http as any)._axiosInstance.defaults.proxy = false;
    await withEnv({ HTTPS_PROXY: shimProxy(proxy) }, () => get(http));
    expect({ proxyConnections: proxy.connections, proxyKeyBytes: proxy.count([key]) }).toEqual({ proxyConnections: 0, proxyKeyBytes: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });

  test("an unkeyed https request through HTTPS_PROXY reaches the proxy in absolute form, as axios sends it", async () => {
    const target: TlsTarget = await track(fx.tlsTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    await withEnv({ HTTPS_PROXY: shimProxy(proxy) }, () => get(client(shimHttps(target))));
    expect(proxy.connects).toHaveLength(0);
    expect(proxy.absolute.map((head) => head.split("\r\n")[0])).toEqual([`GET ${shimHttps(target)}/v1/probe HTTP/1.1`]);
    expect(target.connections).toBe(0);
  });

  test("a keyed https request through a socks5 proxy is refused with insecure_http_origin", async () => {
    const key = marker("pxs");
    const target: TlsTarget = await track(fx.tlsTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    const error = await withEnv({ HTTPS_PROXY: `socks5://${SHIM_HOST}:${proxy.port}` }, () => outcome(() => get(client(shimHttps(target), keyed(key)))));
    expectRefusal(error);
    expect({ proxyConnections: proxy.connections, targetConnections: target.connections }).toEqual({ proxyConnections: 0, targetConnections: 0 });
  });
});

describe("keyed requests to plain-http targets with a proxy set", () => {
  test("an opted-in keyed plain-http request with HTTP_PROXY set goes directly to the target, not to the proxy", async () => {
    const key = marker("phc");
    const target = await track(plainTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    await withEnv({ HTTP_PROXY: shimProxy(proxy) }, () => get(client(shimHttp(target), keyed(key, { allowInsecureHttp: true }))));
    expect({ proxyConnections: proxy.connections, proxyKeyBytes: proxy.count([key]) }).toEqual({ proxyConnections: 0, proxyKeyBytes: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });

  test("a keyed plain-http request without the opt-in is refused with no connection to the proxy or the target", async () => {
    const key = marker("phr");
    const target = await track(plainTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    const error = await withEnv({ HTTP_PROXY: shimProxy(proxy) }, () => outcome(() => get(client(shimHttp(target), keyed(key)))));
    expectRefusal(error);
    expect({ proxyConnections: proxy.connections, targetConnections: target.connections, targetKeyBytes: target.count([key]) }).toEqual({
      proxyConnections: 0,
      targetConnections: 0,
      targetKeyBytes: 0,
    });
  });

  test("a keyed plain-http request to a loopback target is sent directly with HTTP_PROXY set", async () => {
    const key = marker("phl");
    const target = await track(plainTarget());
    const proxy: ProxySink = await track(fx.proxySink());
    await withEnv({ HTTP_PROXY: shimProxy(proxy) }, () => get(client(`http://127.0.0.1:${target.port}`, keyed(key))));
    expect({ proxyConnections: proxy.connections, proxyKeyBytes: proxy.count([key]) }).toEqual({ proxyConnections: 0, proxyKeyBytes: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });
});
