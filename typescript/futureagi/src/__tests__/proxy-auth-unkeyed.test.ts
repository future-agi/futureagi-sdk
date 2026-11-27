// Requests through a proxy that has its own user name and password.
//
// axios adds a Proxy-Authorization header made from the proxy's own user name and password ("Basic " and the base64
// of user:password) to a request it sends to a proxy in absolute form. That header belongs to the proxy, not to the
// caller: a request whose only credential header is that value is a request without a key, and is sent as axios sends
// it. A Proxy-Authorization the caller sets with any other value is a key.
//
// The proxy is a loopback listener that records every request it receives (CONNECT or absolute form, raw bytes
// included) and answers an absolute-form request itself with 200. The https target is a loopback listener trusted
// through a scratch CA; a lookup shim of this file resolves guard-target.futureagi.com and guard-other.futureagi.com
// to 127.0.0.1, so each counts as a host that is not loopback. Keys and the proxy password are random markers made per
// test, and every listener counts the marker bytes it receives.
//
// Each case runs with the proxy given three ways: HTTP_PROXY and HTTPS_PROXY in the environment, ALL_PROXY in the
// environment, and the axios proxy option with auth {username, password} on the client's axios defaults.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const dns = require("node:dns") as typeof import("node:dns");
import * as net from "node:net";

import { APIKeyAuth, HttpClient } from "../api/auth";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

type Target = { port: number; connections: number; requests: string[]; raw(): string; count(markers: string[]): number; close(): Promise<void> };
type ProxySink = { port: number; connections: number; connects: string[]; absolute: string[]; raw(): string; count(markers: string[]): number; close(): Promise<void> };

const SHIM: string = fx.SHIM_HOST;
const OTHER = "guard-other.futureagi.com";
const PROXY_USER = "fiproxy";

// --- name lookup and the scratch CA ---------------------------------------------------------------------------

let realLookup: typeof dns.lookup;
let undoShim: () => void = () => undefined;
beforeAll(() => {
  fx.certificates();
  undoShim = fx.shimLookup();
  realLookup = dns.lookup;
  const below = dns.lookup;
  (dns as any).lookup = function lookup(hostname: string, options: any, callback: any) {
    if (typeof options === "function") {
      callback = options;
      options = {};
    }
    if (String(hostname).toLowerCase() === OTHER) {
      const all = typeof options === "object" && options !== null && options.all === true;
      process.nextTick(() => (all ? callback(null, [{ address: "127.0.0.1", family: 4 }]) : callback(null, "127.0.0.1", 4)));
      return {};
    }
    return (below as any).call(dns, hostname, options, callback);
  };
});
afterAll(() => {
  (dns as any).lookup = realLookup;
  undoShim();
});

// --- listeners and clients, closed after each test ------------------------------------------------------------

const open: Array<{ close(): Promise<void> }> = [];
const clients: HttpClient[] = [];
afterEach(async () => {
  while (clients.length) {
    const made = clients.pop()!;
    await Promise.race([made.close(), new Promise((resolve) => setTimeout(resolve, 2000))]);
  }
  while (open.length) await open.pop()!.close();
});

async function tlsTarget(respond?: (head: string, index: number) => string | undefined): Promise<Target> {
  const made: Target = await fx.tlsTarget(respond);
  open.push(made);
  return made;
}

async function proxySink(): Promise<ProxySink> {
  const made: ProxySink = await fx.proxySink();
  open.push(made);
  return made;
}

/** A plain-http listener on 127.0.0.1 that records the bytes it receives and answers 200. */
async function httpTarget(): Promise<Target> {
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
    socket.on("data", (data) => {
      const text = data.toString("latin1");
      chunks.push(text);
      head += text;
      if (!head.includes("\r\n\r\n")) return;
      requests.push(head);
      head = "";
      const body: string = fx.REPLY_BODY;
      socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${body.length}\r\nConnection: close\r\n\r\n${body}`);
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const made: Target = {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return state.connections;
    },
    requests,
    raw: () => chunks.join(""),
    count: (markers) => {
      const all = chunks.join("");
      return markers.reduce((total, item) => total + (all.split(item).length - 1) * item.length, 0);
    },
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
  open.push(made);
  return made;
}

// --- environment ----------------------------------------------------------------------------------------------

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

/** Run `run` with every variable of ENV_NAMES cleared and then `set` applied; restore the environment afterwards. */
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

// --- the three ways of naming the proxy -----------------------------------------------------------------------

interface ProxyCredentials {
  password: string;
  /** The Proxy-Authorization value axios makes from the proxy's own user name and password. */
  basic: string;
}

function proxyCredentials(): ProxyCredentials {
  const password = marker("pp");
  return { password, basic: `Basic ${Buffer.from(`${PROXY_USER}:${password}`, "utf8").toString("base64")}` };
}

interface Way {
  name: string;
  env(proxy: ProxySink, creds: ProxyCredentials): Record<string, string>;
  apply(client: HttpClient, proxy: ProxySink, creds: ProxyCredentials): void;
}

const proxyUrl = (proxy: ProxySink, creds: ProxyCredentials) => `http://${PROXY_USER}:${creds.password}@127.0.0.1:${proxy.port}`;

const WAYS: Way[] = [
  {
    name: "HTTP_PROXY and HTTPS_PROXY with a user name and password",
    env: (proxy, creds) => ({ HTTP_PROXY: proxyUrl(proxy, creds), HTTPS_PROXY: proxyUrl(proxy, creds) }),
    apply: () => undefined,
  },
  {
    name: "ALL_PROXY with a user name and password",
    env: (proxy, creds) => ({ ALL_PROXY: proxyUrl(proxy, creds) }),
    apply: () => undefined,
  },
  {
    name: "the axios proxy option with auth",
    env: () => ({}),
    apply: (client, proxy, creds) => {
      (client as any)._axiosInstance.defaults.proxy = {
        protocol: "http",
        host: "127.0.0.1",
        port: proxy.port,
        auth: { username: PROXY_USER, password: creds.password },
      };
    },
  },
];

// --- helpers --------------------------------------------------------------------------------------------------

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;

function unkeyedClient(baseUrl: string, headers: Record<string, string> = {}): HttpClient {
  const made = new HttpClient({ baseUrl, retryAttempts: 1, timeout: 5000, defaultHeaders: headers });
  clients.push(made);
  return made;
}

function keyedClient(baseUrl: string, apiKey: string, secretKey: string): HttpClient {
  const made = new APIKeyAuth({ fiApiKey: apiKey, fiSecretKey: secretKey, baseUrl, retryAttempts: 1, timeout: 5000 });
  clients.push(made);
  return made;
}

/** "status <n>" for a response, or the code (or message) of what the request rejected with. */
async function outcome(run: () => Promise<unknown>): Promise<string> {
  return run().then(
    (response: any) => `status ${response?.status}`,
    (e: any) => (e instanceof Error ? ((e as { code?: string }).code ?? e.message) : "(not an Error)"),
  );
}

const get = (c: HttpClient, url = "/v1/probe") => c.request({ method: "GET", url } as any);
const firstLine = (head: string) => head.split("\r\n")[0];
const headerValues = (head: string, name: string) =>
  head
    .split("\r\n")
    .slice(1)
    .filter((line) => line.toLowerCase().startsWith(`${name.toLowerCase()}:`))
    .map((line) => line.slice(line.indexOf(":") + 1).trim());
const redirect = (status: number, location: string) => `HTTP/1.1 ${status} Redirect\r\nLocation: ${location}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n`;
const KEY_HEADER = /^(x-api-key|x-secret-key|authorization|cookie)\s*:/im;

function record(label: string, data: Record<string, unknown>): void {
  // eslint-disable-next-line no-console
  console.log(`${label}: ${JSON.stringify(data)}`);
}

// --- requests without a key -----------------------------------------------------------------------------------

describe.each(WAYS.map((way) => [way.name, way] as const))("a proxy named by %s", (_name, way) => {
  test("an unkeyed GET to https through the proxy with its own user name and password succeeds with 200 in absolute form", async () => {
    const creds = proxyCredentials();
    const target = await tlsTarget();
    const proxy = await proxySink();
    const base = `https://${SHIM}:${target.port}`;
    const client = unkeyedClient(base);
    way.apply(client, proxy, creds);
    const result = await withEnv(way.env(proxy, creds), () => outcome(() => get(client)));
    const seen = {
      result,
      connects: proxy.connects.length,
      absolute: proxy.absolute.map(firstLine),
      proxyAuthorization: proxy.absolute.map((head) => headerValues(head, "proxy-authorization")),
      proxyPasswordBytesAtTarget: target.count([creds.password, creds.basic]),
      targetConnections: target.connections,
    };
    record(`unkeyed https, ${way.name}`, seen);
    expect(seen).toEqual({
      result: "status 200",
      connects: 0,
      absolute: [`GET ${base}/v1/probe HTTP/1.1`],
      proxyAuthorization: [[creds.basic]],
      proxyPasswordBytesAtTarget: 0,
      targetConnections: 0,
    });
  });

  test("an unkeyed GET to http on a host that is not loopback through the proxy with its own user name and password succeeds with 200", async () => {
    const creds = proxyCredentials();
    const target = await httpTarget();
    const proxy = await proxySink();
    const base = `http://${OTHER}:${target.port}`;
    const client = unkeyedClient(base);
    way.apply(client, proxy, creds);
    const result = await withEnv(way.env(proxy, creds), () => outcome(() => get(client)));
    const seen = {
      result,
      connects: proxy.connects.length,
      absolute: proxy.absolute.map(firstLine),
      proxyAuthorization: proxy.absolute.map((head) => headerValues(head, "proxy-authorization")),
      proxyPasswordBytesAtTarget: target.count([creds.password, creds.basic]),
      targetConnections: target.connections,
    };
    record(`unkeyed http, ${way.name}`, seen);
    expect(seen).toEqual({
      result: "status 200",
      connects: 0,
      absolute: [`GET ${base}/v1/probe HTTP/1.1`],
      proxyAuthorization: [[creds.basic]],
      proxyPasswordBytesAtTarget: 0,
      targetConnections: 0,
    });
  });

  // --- keyed requests -----------------------------------------------------------------------------------------

  test("a keyed GET to https redirected with 302 to another origin ends with 200, the keyed request reaching the proxy only as CONNECT and the hop carrying no key", async () => {
    const creds = proxyCredentials();
    const [apiKey, secretKey] = [marker("pa"), marker("ps")];
    const markers = [apiKey, secretKey];
    const other = await tlsTarget();
    const otherOrigin = `https://localhost:${other.port}`;
    const first = await tlsTarget((_head, index) => (index === 0 ? redirect(302, `${otherOrigin}/v1/next`) : undefined));
    const proxy = await proxySink();
    const base = `https://${SHIM}:${first.port}`;
    const client = keyedClient(base, apiKey, secretKey);
    way.apply(client, proxy, creds);
    const result = await withEnv(way.env(proxy, creds), () => outcome(() => get(client)));
    const seen = {
      result,
      connectAuthorities: [...new Set(proxy.connects.map((head) => firstLine(head).split(" ")[1]))].filter((item) => item === `${SHIM}:${first.port}`),
      connectsWithProxyAuth: proxy.connects.every((head) => headerValues(head, "proxy-authorization").join() === creds.basic),
      absoluteToFirstOrigin: proxy.absolute.filter((head) => firstLine(head).includes(SHIM)).length,
      absoluteWithKeyHeaders: proxy.absolute.filter((head) => KEY_HEADER.test(head.split("\r\n").slice(1).join("\r\n"))).length,
      proxyKeyBytes: proxy.count(markers),
      firstTargetKeyed: markers.every((item) => first.requests[0]?.includes(item)),
      otherOriginKeyBytes: other.count(markers),
    };
    record(`keyed https redirected to another origin, ${way.name}`, {
      ...seen,
      absolute: proxy.absolute.map(firstLine),
      connects: proxy.connects.map(firstLine),
    });
    expect(seen).toEqual({
      result: "status 200",
      connectAuthorities: [`${SHIM}:${first.port}`],
      connectsWithProxyAuth: true,
      absoluteToFirstOrigin: 0,
      absoluteWithKeyHeaders: 0,
      proxyKeyBytes: 0,
      firstTargetKeyed: true,
      otherOriginKeyBytes: 0,
    });
  });

  test("a keyed GET to https through the proxy with its own user name and password goes only through CONNECT, with no key bytes at the proxy", async () => {
    const creds = proxyCredentials();
    const [apiKey, secretKey] = [marker("pa"), marker("ps")];
    const markers = [apiKey, secretKey];
    const target = await tlsTarget();
    const proxy = await proxySink();
    const client = keyedClient(`https://${SHIM}:${target.port}`, apiKey, secretKey);
    way.apply(client, proxy, creds);
    const result = await withEnv(way.env(proxy, creds), () => outcome(() => get(client)));
    const seen = {
      result,
      connects: proxy.connects.map(firstLine),
      connectProxyAuthorization: proxy.connects.map((head) => headerValues(head, "proxy-authorization")),
      absolute: proxy.absolute.length,
      proxyKeyBytes: proxy.count(markers),
      targetKeyed: markers.every((item) => target.count([item]) > 0),
      proxyPasswordBytesAtTarget: target.count([creds.password, creds.basic]),
    };
    record(`keyed https, ${way.name}`, seen);
    expect(seen).toEqual({
      result: "status 200",
      connects: [`CONNECT ${SHIM}:${target.port} HTTP/1.1`],
      connectProxyAuthorization: [[creds.basic]],
      absolute: 0,
      proxyKeyBytes: 0,
      targetKeyed: true,
      proxyPasswordBytesAtTarget: 0,
    });
  });

  test("a caller-set Proxy-Authorization with another value on an unkeyed https request is a key: it does not reach the proxy in absolute form", async () => {
    const creds = proxyCredentials();
    const callerToken = marker("pz");
    const callerValue = `Bearer ${callerToken}`;
    const target = await tlsTarget();
    const proxy = await proxySink();
    const client = unkeyedClient(`https://${SHIM}:${target.port}`, { "Proxy-Authorization": callerValue });
    way.apply(client, proxy, creds);
    const result = await withEnv(way.env(proxy, creds), () => outcome(() => get(client)));
    const seen = {
      tunnelledOrRefused: result === "status 200" ? proxy.connects.length > 0 : result === "insecure_http_origin",
      absolute: proxy.absolute.length,
      proxyCallerBytes: proxy.count([callerToken]),
    };
    record(`caller Proxy-Authorization on unkeyed https, ${way.name}`, {
      result,
      ...seen,
      connects: proxy.connects.map(firstLine),
      targetCallerBytes: target.count([callerToken]),
    });
    expect(seen).toEqual({ tunnelledOrRefused: true, absolute: 0, proxyCallerBytes: 0 });
  });
});
