// A Proxy-Authorization header set by the caller on a keyed https request that goes through a CONNECT tunnel.
//
// The header is meant for the proxy: it belongs on the CONNECT request and is taken off the request that travels
// inside the tunnel to the API host. When the proxy address has no user name or password of its own, the CONNECT
// carries the caller's value; when it has its own, the CONNECT carries the proxy's own Basic auth (axios gives the
// proxy auth precedence) and the caller's value is sent to neither the proxy nor the target.
//
// The target is an https listener (scratch CA trusted by this process) reached through a host name that a lookup shim
// resolves to the loopback address; HTTPS_PROXY names a loopback CONNECT-aware proxy by the same name. Some cases put
// a gate in front of that proxy which answers 407 unless the CONNECT carries the expected Proxy-Authorization value.
// Every case counts the planted marker bytes at the proxy and at the target.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
import * as net from "node:net";

import { APIKeyAuth } from "../api/auth";
import { Client } from "../platform/client";

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

interface Sink {
  port: number;
  connections: number;
  connects: string[];
  absolute: string[];
  raw(): string;
  count(markers: string[]): number;
  close(): Promise<void>;
}

/** A proxy that answers 407 to a CONNECT whose Proxy-Authorization is not `expected`, and hands an accepted CONNECT
 * (with every byte after it) to a CONNECT-aware sink. */
interface Gate {
  port: number;
  connects: string[];
  refused: number;
  count(markers: string[]): number;
  close(): Promise<void>;
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
  "FI_API_KEY",
  "FI_SECRET_KEY",
  "FI_BASE_URL",
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

let undoLookup: () => void;
beforeAll(() => {
  fx.certificates();
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
});

const opened: Array<{ close(): Promise<void> }> = [];
let target: Target;
beforeEach(async () => {
  target = await fx.tlsTarget();
  opened.push(target);
});
afterEach(async () => {
  while (opened.length > 0) await opened.pop()!.close();
});

async function sink(): Promise<Sink> {
  const made: Sink = await fx.proxySink();
  opened.push(made);
  return made;
}

async function gate(expected: string): Promise<{ gate: Gate; sink: Sink }> {
  const inner = await sink();
  const chunks: string[] = [];
  const connects: string[] = [];
  const sockets = new Set<net.Socket>();
  const state = { refused: 0 };
  const server = net.createServer((socket) => {
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
    let head = Buffer.alloc(0);
    let decided = false;
    const onData = (data: Buffer) => {
      chunks.push(data.toString("latin1"));
      if (decided) return;
      head = Buffer.concat([head, data]);
      const end = head.indexOf("\r\n\r\n");
      if (end < 0) return;
      decided = true;
      const text = head.subarray(0, end + 4).toString("latin1");
      connects.push(text);
      if (!text.startsWith("CONNECT ") || headerValues(text, "proxy-authorization").join("\n") !== expected) {
        state.refused++;
        socket.end('HTTP/1.1 407 Proxy Authentication Required\r\nProxy-Authenticate: Basic realm="fi"\r\nContent-Length: 0\r\nConnection: close\r\n\r\n');
        return;
      }
      const upstream = net.connect(inner.port, "127.0.0.1", () => {
        upstream.write(head);
        socket.on("data", (more: Buffer) => upstream.write(more));
        upstream.pipe(socket);
        socket.on("end", () => upstream.end());
      });
      upstream.on("error", () => socket.destroy());
      sockets.add(upstream);
      upstream.on("close", () => sockets.delete(upstream));
    };
    socket.on("data", onData);
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const made: Gate = {
    port: (server.address() as net.AddressInfo).port,
    connects,
    get refused() {
      return state.refused;
    },
    count: (markers: string[]) => countIn(chunks.join(""), markers),
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
  opened.push(made);
  return { gate: made, sink: inner };
}

function countIn(all: string, markers: string[]): number {
  let bytes = 0;
  for (const marker of markers) {
    for (let at = all.indexOf(marker); at >= 0; at = all.indexOf(marker, at + marker.length)) bytes += marker.length;
  }
  return bytes;
}

/** Every value of a header in a request head (lower-case name). */
function headerValues(head: string, name: string): string[] {
  const values: string[] = [];
  for (const line of head.split("\r\n\r\n")[0].split("\r\n").slice(1)) {
    const at = line.indexOf(":");
    if (at > 0 && line.slice(0, at).trim().toLowerCase() === name) values.push(line.slice(at + 1).trim());
  }
  return values;
}

const marker = (tag: string) => `fi-marker-${tag}-${randomBytes(8).toString("hex")}`;
const basic = (user: string, password: string) => Buffer.from(`${user}:${password}`, "utf8").toString("base64");
const targetUrl = () => `https://${SHIM_HOST}:${target.port}`;
const proxyUrl = (port: number, credentials = "") => `http://${credentials}${SHIM_HOST}:${port}`;

/** A Proxy-Authorization value of the caller: Basic with a planted marker as the password. */
function callerProxyAuth(): { value: string; markers: string[] } {
  const password = marker("pa");
  const encoded = basic("caller", password);
  return { value: `Basic ${encoded}`, markers: [password, encoded] };
}

type Placement = "defaultHeaders of the client config" | "the headers of the request";
const PLACEMENTS: Placement[] = ["defaultHeaders of the client config", "the headers of the request"];

interface Outcome {
  status: number | string;
}

/** One keyed GET of APIKeyAuth with the caller's Proxy-Authorization placed as `placement`. */
async function keyedGet(placement: Placement, proxyAuthorization: string, keys: { apiKey: string; secretKey: string }): Promise<Outcome> {
  const extra = { "Proxy-Authorization": proxyAuthorization };
  const client = new APIKeyAuth({
    fiApiKey: keys.apiKey,
    fiSecretKey: keys.secretKey,
    baseUrl: targetUrl(),
    retryAttempts: 1,
    timeout: 5000,
    ...(placement === "defaultHeaders of the client config" ? { defaultHeaders: extra } : {}),
  });
  try {
    const response: any = await client.request({
      method: "GET",
      url: "/v1/probe",
      ...(placement === "the headers of the request" ? { headers: extra } : {}),
    } as any);
    return { status: response.status };
  } catch (error) {
    const e = error as { code?: string; message?: string };
    return { status: `error ${String(e.code ?? "")} ${String(e.message ?? error)}`.trim() };
  } finally {
    await client.close();
  }
}

const keys = () => ({ apiKey: marker("ak"), secretKey: marker("sk") });

describe("APIKeyAuth through a CONNECT tunnel with a Proxy-Authorization header set by the caller", () => {
  test.each(PLACEMENTS)(
    "the request inside the tunnel to the API host carries no Proxy-Authorization of the caller (header in %s), and it succeeds",
    async (placement) => {
      const proxy = await sink();
      const caller = callerProxyAuth();
      const outcome = await withEnv({ HTTPS_PROXY: proxyUrl(proxy.port) }, () => keyedGet(placement, caller.value, keys()));
      expect({
        status: outcome.status,
        targetRequests: target.requests.length,
        targetMarkerBytes: target.count(caller.markers),
        targetProxyAuthorizationLines: target.requests.flatMap((head) => headerValues(head, "proxy-authorization")).length,
        proxyAbsolute: proxy.absolute.length,
      }).toEqual({ status: 200, targetRequests: 1, targetMarkerBytes: 0, targetProxyAuthorizationLines: 0, proxyAbsolute: 0 });
    },
  );

  test.each(PLACEMENTS)(
    "the CONNECT to a proxy without credentials of its own carries the Proxy-Authorization of the caller (header in %s)",
    async (placement) => {
      const caller = callerProxyAuth();
      const { gate: proxy, sink: inner } = await gate(caller.value);
      const outcome = await withEnv({ HTTPS_PROXY: proxyUrl(proxy.port) }, () => keyedGet(placement, caller.value, keys()));
      expect({
        connectProxyAuthorization: proxy.connects.map((head) => headerValues(head, "proxy-authorization")),
        refused: proxy.refused,
        status: outcome.status,
        targetMarkerBytes: target.count(caller.markers),
        absolute: inner.absolute.length,
      }).toEqual({
        connectProxyAuthorization: [[caller.value]],
        refused: 0,
        status: 200,
        targetMarkerBytes: 0,
        absolute: 0,
      });
      // The caller's value reaches the proxy once: in the CONNECT head and in no other bytes.
      expect(proxy.count([caller.value])).toBe(caller.value.length);
      expect(proxy.connects[0].split("\r\n")[0]).toBe(`CONNECT ${SHIM_HOST}:${target.port} HTTP/1.1`);
    },
  );

  test.each(PLACEMENTS)(
    "the CONNECT to a proxy with a user name and password of its own carries the proxy's own Basic auth, and the target receives neither value (header in %s)",
    async (placement) => {
      const caller = callerProxyAuth();
      const ownPassword = marker("pp");
      const ownEncoded = basic("puser", ownPassword);
      const { gate: proxy, sink: inner } = await gate(`Basic ${ownEncoded}`);
      const outcome = await withEnv({ HTTPS_PROXY: proxyUrl(proxy.port, `puser:${ownPassword}@`) }, () => keyedGet(placement, caller.value, keys()));
      expect({
        connectProxyAuthorization: proxy.connects.map((head) => headerValues(head, "proxy-authorization")),
        refused: proxy.refused,
        status: outcome.status,
        proxyCallerMarkerBytes: proxy.count(caller.markers),
        targetCallerMarkerBytes: target.count(caller.markers),
        targetOwnMarkerBytes: target.count([ownPassword, ownEncoded]),
        targetProxyAuthorizationLines: target.requests.flatMap((head) => headerValues(head, "proxy-authorization")).length,
        absolute: inner.absolute.length,
      }).toEqual({
        connectProxyAuthorization: [[`Basic ${ownEncoded}`]],
        refused: 0,
        status: 200,
        proxyCallerMarkerBytes: 0,
        targetCallerMarkerBytes: 0,
        targetOwnMarkerBytes: 0,
        targetProxyAuthorizationLines: 0,
        absolute: 0,
      });
    },
  );

  test.each(PLACEMENTS)(
    "X-Api-Key and X-Secret-Key reach the target and not the proxy when the caller sets Proxy-Authorization (header in %s)",
    async (placement) => {
      const proxy = await sink();
      const caller = callerProxyAuth();
      const pair = keys();
      await withEnv({ HTTPS_PROXY: proxyUrl(proxy.port) }, () => keyedGet(placement, caller.value, pair));
      expect({
        proxyKeyBytes: proxy.count([pair.apiKey, pair.secretKey]),
        proxyAbsolute: proxy.absolute.length,
        connects: proxy.connects.length,
        targetApiKeyReached: target.count([pair.apiKey]) > 0,
        targetSecretKeyReached: target.count([pair.secretKey]) > 0,
      }).toEqual({ proxyKeyBytes: 0, proxyAbsolute: 0, connects: 1, targetApiKeyReached: true, targetSecretKeyReached: true });
    },
  );
});

/** The path of each request head, in order. */
const pathsOf = (heads: string[]) => heads.map((head) => head.split("\r\n")[0].split(" ")[1]);

/** An extra https target on its own port (another origin than `target`), answered by `respond`. */
async function extraTarget(respond: (head: string, index: number) => string | undefined): Promise<Target> {
  const made: Target = await fx.tlsTarget(respond);
  opened.push(made);
  return made;
}

/** A 302 to `location` on a connection that the target closes, so the next hop opens a new tunnel. */
const found = (location: string) => `HTTP/1.1 302 Found\r\nLocation: ${location}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n`;

/** One keyed GET of APIKeyAuth to `baseUrl` + /v1/probe with the caller's Proxy-Authorization placed as `placement`. */
async function keyedGetAt(baseUrl: string, placement: Placement, proxyAuthorization: string, pair: { apiKey: string; secretKey: string }): Promise<Outcome> {
  const extra = { "Proxy-Authorization": proxyAuthorization };
  const client = new APIKeyAuth({
    fiApiKey: pair.apiKey,
    fiSecretKey: pair.secretKey,
    baseUrl,
    retryAttempts: 1,
    timeout: 5000,
    ...(placement === "defaultHeaders of the client config" ? { defaultHeaders: extra } : {}),
  });
  try {
    const response: any = await client.request({
      method: "GET",
      url: "/v1/probe",
      ...(placement === "the headers of the request" ? { headers: extra } : {}),
    } as any);
    return { status: response.status };
  } catch (error) {
    const e = error as { code?: string; message?: string };
    return { status: `error ${String(e.code ?? "")} ${String(e.message ?? error)}`.trim() };
  } finally {
    await client.close();
  }
}

describe("APIKeyAuth redirect hops through a CONNECT tunnel with a Proxy-Authorization header set by the caller", () => {
  test.each(PLACEMENTS)(
    "the CONNECT of a second hop within the same origin carries the Proxy-Authorization of the caller, and a proxy that accepts only that value lets both hops through (header in %s)",
    async (placement) => {
      const caller = callerProxyAuth();
      const origin = await extraTarget((_head, index) => (index === 0 ? found("/v1/next") : undefined));
      const { gate: proxy, sink: inner } = await gate(caller.value);
      const outcome = await withEnv({ HTTPS_PROXY: proxyUrl(proxy.port) }, () =>
        keyedGetAt(`https://${SHIM_HOST}:${origin.port}`, placement, caller.value, keys()),
      );
      expect({
        status: outcome.status,
        connectProxyAuthorization: proxy.connects.map((head) => headerValues(head, "proxy-authorization")),
        refused: proxy.refused,
        paths: pathsOf(origin.requests),
        targetMarkerBytes: origin.count(caller.markers),
        targetProxyAuthorizationLines: origin.requests.flatMap((head) => headerValues(head, "proxy-authorization")).length,
        absolute: inner.absolute.length,
      }).toEqual({
        status: 200,
        connectProxyAuthorization: [[caller.value], [caller.value]],
        refused: 0,
        paths: ["/v1/probe", "/v1/next"],
        targetMarkerBytes: 0,
        targetProxyAuthorizationLines: 0,
        absolute: 0,
      });
      expect(proxy.count([caller.value])).toBe(2 * caller.value.length);
    },
  );

  test.each(PLACEMENTS)(
    "after a hop within the same origin, the CONNECT of a hop to another origin carries no Proxy-Authorization of the caller (header in %s)",
    async (placement) => {
      const caller = callerProxyAuth();
      const far = `https://${SHIM_HOST}:${target.port}/v1/far`;
      const origin = await extraTarget((_head, index) => found(index === 0 ? "/v1/next" : far));
      const proxy = await sink();
      const outcome = await withEnv({ HTTPS_PROXY: proxyUrl(proxy.port) }, () =>
        keyedGetAt(`https://${SHIM_HOST}:${origin.port}`, placement, caller.value, keys()),
      );
      expect({
        status: outcome.status,
        connectLines: proxy.connects.map((head) => head.split("\r\n")[0]),
        connectProxyAuthorization: proxy.connects.map((head) => headerValues(head, "proxy-authorization")),
        originPaths: pathsOf(origin.requests),
        farPaths: pathsOf(target.requests),
        originMarkerBytes: origin.count(caller.markers),
        farMarkerBytes: target.count(caller.markers),
        proxyMarkerBytes: proxy.count([caller.value]),
        absolute: proxy.absolute.length,
      }).toEqual({
        status: 200,
        connectLines: [
          `CONNECT ${SHIM_HOST}:${origin.port} HTTP/1.1`,
          `CONNECT ${SHIM_HOST}:${origin.port} HTTP/1.1`,
          `CONNECT ${SHIM_HOST}:${target.port} HTTP/1.1`,
        ],
        connectProxyAuthorization: [[caller.value], [caller.value], []],
        originPaths: ["/v1/probe", "/v1/next"],
        farPaths: ["/v1/far"],
        originMarkerBytes: 0,
        farMarkerBytes: 0,
        proxyMarkerBytes: 2 * caller.value.length,
        absolute: 0,
      });
    },
  );
});

/** One GET of the platform Client (runtime fetch, keyed by its API key headers) with the caller's Proxy-Authorization
 * placed as `placement`. */
async function platformGet(placement: Placement, proxyAuthorization: string, pair: { apiKey: string; secretKey: string }): Promise<Outcome> {
  const extra = { "Proxy-Authorization": proxyAuthorization };
  const client = new Client({
    apiKey: pair.apiKey,
    secretKey: pair.secretKey,
    baseUrl: targetUrl(),
    maxRetries: 0,
    timeout: 5000,
    ...(placement === "defaultHeaders of the client config" ? { defaultHeaders: extra } : {}),
  });
  try {
    await client.request("GET", "/v1/probe/", { unwrap: null }, placement === "the headers of the request" ? { headers: extra } : undefined);
    return { status: 200 };
  } catch (error) {
    const e = error as { code?: string; message?: string };
    return { status: `error ${String(e.code ?? "")} ${String(e.message ?? error)}`.trim() };
  }
}

describe("the platform Client through a CONNECT tunnel with a Proxy-Authorization header set by the caller", () => {
  test.each(PLACEMENTS)(
    "the request inside the tunnel to the API host carries no Proxy-Authorization of the caller (header in %s), and it succeeds",
    async (placement) => {
      const proxy = await sink();
      const caller = callerProxyAuth();
      const outcome = await withEnv({ HTTPS_PROXY: proxyUrl(proxy.port) }, () => platformGet(placement, caller.value, keys()));
      expect({
        status: outcome.status,
        targetRequests: target.requests.length,
        targetMarkerBytes: target.count(caller.markers),
        targetProxyAuthorizationLines: target.requests.flatMap((head) => headerValues(head, "proxy-authorization")).length,
        connects: proxy.connects.length,
        proxyAbsolute: proxy.absolute.length,
      }).toEqual({ status: 200, targetRequests: 1, targetMarkerBytes: 0, targetProxyAuthorizationLines: 0, connects: 1, proxyAbsolute: 0 });
    },
  );

  test.each(PLACEMENTS)(
    "the CONNECT to a proxy without credentials of its own carries the Proxy-Authorization of the caller, and the request inside the tunnel carries none (header in %s)",
    async (placement) => {
      const caller = callerProxyAuth();
      const pair = keys();
      const { gate: proxy, sink: inner } = await gate(caller.value);
      const outcome = await withEnv({ HTTPS_PROXY: proxyUrl(proxy.port) }, () => platformGet(placement, caller.value, pair));
      expect({
        status: outcome.status,
        connectProxyAuthorization: proxy.connects.map((head) => headerValues(head, "proxy-authorization")),
        refused: proxy.refused,
        targetRequests: target.requests.length,
        targetMarkerBytes: target.count(caller.markers),
        targetProxyAuthorizationLines: target.requests.flatMap((head) => headerValues(head, "proxy-authorization")).length,
        targetApiKeyReached: target.count([pair.apiKey]) > 0,
        proxyKeyBytes: proxy.count([pair.apiKey, pair.secretKey]),
        absolute: inner.absolute.length,
      }).toEqual({
        status: 200,
        connectProxyAuthorization: [[caller.value]],
        refused: 0,
        targetRequests: 1,
        targetMarkerBytes: 0,
        targetProxyAuthorizationLines: 0,
        targetApiKeyReached: true,
        proxyKeyBytes: 0,
        absolute: 0,
      });
      expect(proxy.count([caller.value])).toBe(caller.value.length);
    },
  );

  test.each(PLACEMENTS)(
    "the CONNECT to a proxy with a user name and password of its own carries the proxy's own Basic auth, and the target receives neither value (header in %s)",
    async (placement) => {
      const caller = callerProxyAuth();
      const ownPassword = marker("pp");
      const ownEncoded = basic("puser", ownPassword);
      const { gate: proxy, sink: inner } = await gate(`Basic ${ownEncoded}`);
      const outcome = await withEnv({ HTTPS_PROXY: proxyUrl(proxy.port, `puser:${ownPassword}@`) }, () => platformGet(placement, caller.value, keys()));
      expect({
        status: outcome.status,
        connectProxyAuthorization: proxy.connects.map((head) => headerValues(head, "proxy-authorization")),
        refused: proxy.refused,
        proxyCallerMarkerBytes: proxy.count(caller.markers),
        targetCallerMarkerBytes: target.count(caller.markers),
        targetOwnMarkerBytes: target.count([ownPassword, ownEncoded]),
        targetProxyAuthorizationLines: target.requests.flatMap((head) => headerValues(head, "proxy-authorization")).length,
        absolute: inner.absolute.length,
      }).toEqual({
        status: 200,
        connectProxyAuthorization: [[`Basic ${ownEncoded}`]],
        refused: 0,
        proxyCallerMarkerBytes: 0,
        targetCallerMarkerBytes: 0,
        targetOwnMarkerBytes: 0,
        targetProxyAuthorizationLines: 0,
        absolute: 0,
      });
    },
  );
});
