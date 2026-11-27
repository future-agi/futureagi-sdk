// A Proxy-Authorization header set by the caller on a keyed plain-http request that goes straight to its host.
//
// A keyed plain-http request is sent directly (no proxy) when its base URL is a loopback address, when the client is
// given allowInsecureHttp: true, or when FI_ALLOW_INSECURE_HTTP=1 is set. On that route no proxy is spoken to, so a
// Proxy-Authorization the caller sets (in defaultHeaders, in the headers of one request, or from a request interceptor
// on the client's axios instance) is taken off the request and does not reach the host.
//
// The origin is a plain-http loopback listener that records every byte it receives. HTTP_PROXY (or http_proxy) names
// a loopback proxy that records every connection; a lookup shim resolves guard-target.futureagi.com to 127.0.0.1, so a
// request to that name counts as a host that is not loopback while its bytes land in a listener of this file. Each
// case counts the planted marker bytes at the origin and the connections at the proxy.
//
// Controls: an unkeyed plain-http request under the same environment goes to the proxy (the proxy setting is in
// effect), and a keyed https request through a CONNECT tunnel carries the caller's value on the CONNECT and not to the
// target.

/* eslint-disable @typescript-eslint/no-explicit-any */
import * as net from "node:net";
import * as nodeTls from "node:tls";

import { APIKeyAuth, HttpClient } from "../api/auth";
import { Client } from "../platform/client";

/** node:tls with the CA functions of Node 22.19+ and 24.5+ (the installed @types/node does not declare them). */
const tls = nodeTls as typeof nodeTls & {
  getCACertificates(kind?: string): string[];
  setDefaultCACertificates(certificates: string[]): void;
};

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

const SHIM_HOST: string = fx.SHIM_HOST;
const REPLY_BODY: string = fx.REPLY_BODY;

interface Origin {
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

/** Run `run` with every variable of ENV_NAMES cleared except `vars`, then restore the environment. */
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
let caBefore: string[];
beforeAll(() => {
  caBefore = tls.getCACertificates("default");
  fx.certificates();
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
  tls.setDefaultCACertificates(caBefore);
});

const opened: Array<{ close(): Promise<void> }> = [];
const clients: HttpClient[] = [];
afterEach(async () => {
  while (clients.length > 0) await clients.pop()!.close();
  while (opened.length > 0) await opened.pop()!.close();
});

function countIn(all: string, markers: string[]): number {
  let bytes = 0;
  for (const marker of markers) {
    for (let at = all.indexOf(marker); at >= 0; at = all.indexOf(marker, at + marker.length)) bytes += marker.length;
  }
  return bytes;
}

/** A plain-http listener on 127.0.0.1 that records every byte it receives and answers each request 200 with a JSON
 * body on a connection it then closes. */
async function plainOrigin(): Promise<Origin> {
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
    socket.on("data", (data: Buffer) => {
      const text = data.toString("latin1");
      chunks.push(text);
      if (answered) return;
      head += text;
      if (!head.includes("\r\n\r\n")) return;
      answered = true;
      requests.push(head.split("\r\n\r\n")[0] + "\r\n\r\n");
      socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${REPLY_BODY.length}\r\nConnection: close\r\n\r\n${REPLY_BODY}`);
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const made: Origin = {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return state.connections;
    },
    requests,
    raw: () => chunks.join(""),
    count: (markers: string[]) => countIn(chunks.join(""), markers),
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
  opened.push(made);
  return made;
}

async function sink(): Promise<Sink> {
  const made: Sink = await fx.proxySink();
  opened.push(made);
  return made;
}

async function tlsTarget(): Promise<Origin> {
  const made: Origin = await fx.tlsTarget();
  opened.push(made);
  return made;
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

let planted = 0;
/** A planted marker string, distinct within this file. */
const marker = (tag: string) => `FIMARK-direct-${tag}-${++planted}`;
const basic = (user: string, password: string) => Buffer.from(`${user}:${password}`, "utf8").toString("base64");
const keys = () => ({ apiKey: marker("ak"), secretKey: marker("sk") });

/** A Proxy-Authorization value of the caller: Basic with a planted marker as the password. */
function callerProxyAuth(): { value: string; markers: string[] } {
  const password = marker("pa");
  const encoded = basic("caller", password);
  return { value: `Basic ${encoded}`, markers: [password, encoded] };
}

// --- the cases ------------------------------------------------------------------------------------------------

type DirectRoute = "a loopback base URL" | "allowInsecureHttp: true for a name that is not loopback" | "FI_ALLOW_INSECURE_HTTP=1 for a name that is not loopback";
const DIRECT_ROUTES: DirectRoute[] = [
  "a loopback base URL",
  "allowInsecureHttp: true for a name that is not loopback",
  "FI_ALLOW_INSECURE_HTTP=1 for a name that is not loopback",
];

type Placement = "defaultHeaders of the client config" | "the headers of the request" | "a request interceptor on the client's axios instance";
const AXIOS_PLACEMENTS: Placement[] = ["defaultHeaders of the client config", "the headers of the request", "a request interceptor on the client's axios instance"];
const PLATFORM_PLACEMENTS: Placement[] = ["defaultHeaders of the client config", "the headers of the request"];

const PROXY_VARS = ["HTTP_PROXY", "http_proxy"] as const;

type AxiosKind = "HttpClient" | "APIKeyAuth";

interface Outcome {
  status: number | string;
}

function failure(error: any): Outcome {
  const e = error as { code?: string; message?: string };
  return { status: `error ${String(e.code ?? "")} ${String(e.message ?? error)}`.trim() };
}

/** A keyed HttpClient (X-Api-Key in its defaultHeaders) or APIKeyAuth with the caller's Proxy-Authorization placed as
 * `placement` (`proxyAuthorization` undefined: none), and the per-request headers to send with. */
function axiosClient(
  kind: AxiosKind,
  baseUrl: string,
  placement: Placement,
  proxyAuthorization: string | undefined,
  pair: { apiKey: string; secretKey: string } | undefined,
  allowInsecureHttp: boolean | undefined,
): { client: HttpClient; headers: Record<string, string> | undefined } {
  const extra: Record<string, string> = proxyAuthorization === undefined ? {} : { "Proxy-Authorization": proxyAuthorization };
  const inDefaults = placement === "defaultHeaders of the client config" ? extra : {};
  const common = { baseUrl, retryAttempts: 1, timeout: 5000, ...(allowInsecureHttp === undefined ? {} : { allowInsecureHttp }) };
  const client =
    kind === "APIKeyAuth"
      ? new APIKeyAuth({ ...common, fiApiKey: pair!.apiKey, fiSecretKey: pair!.secretKey, defaultHeaders: inDefaults })
      : new HttpClient({ ...common, defaultHeaders: { ...(pair ? { "X-Api-Key": pair.apiKey, "X-Secret-Key": pair.secretKey } : {}), ...inDefaults } });
  clients.push(client);
  if (placement === "a request interceptor on the client's axios instance" && proxyAuthorization !== undefined) {
    (client as any)._axiosInstance.interceptors.request.use((config: any) => {
      config.headers.set("Proxy-Authorization", proxyAuthorization);
      return config;
    });
  }
  return { client, headers: placement === "the headers of the request" ? extra : undefined };
}

async function axiosGet(made: { client: HttpClient; headers: Record<string, string> | undefined }): Promise<Outcome> {
  try {
    const response: any = await made.client.request({ method: "GET", url: "/v1/probe", ...(made.headers ? { headers: made.headers } : {}) } as any);
    return { status: response.status };
  } catch (error) {
    return failure(error);
  }
}

async function platformGet(baseUrl: string, placement: Placement, proxyAuthorization: string, pair: { apiKey: string; secretKey: string }, allowInsecureHttp: boolean | undefined): Promise<Outcome> {
  const extra = { "Proxy-Authorization": proxyAuthorization };
  const client = new Client({
    apiKey: pair.apiKey,
    secretKey: pair.secretKey,
    baseUrl,
    maxRetries: 0,
    timeout: 5000,
    ...(allowInsecureHttp === undefined ? {} : { allowInsecureHttp }),
    ...(placement === "defaultHeaders of the client config" ? { defaultHeaders: extra } : {}),
  });
  try {
    await client.request("GET", "/v1/probe/", { unwrap: null }, placement === "the headers of the request" ? { headers: extra } : undefined);
    return { status: 200 };
  } catch (error) {
    return failure(error);
  }
}

/** The base URL, the client option and the environment of a direct route to `origin`, with `proxyVar` naming `proxy`. */
function directSetting(route: DirectRoute, origin: Origin, proxy: Sink, proxyVar: string): { baseUrl: string; allowInsecureHttp: boolean | undefined; vars: Record<string, string> } {
  const vars: Record<string, string> = { [proxyVar]: `http://127.0.0.1:${proxy.port}` };
  if (route === "a loopback base URL") {
    return { baseUrl: `http://127.0.0.1:${origin.port}`, allowInsecureHttp: undefined, vars };
  }
  if (route === "allowInsecureHttp: true for a name that is not loopback") {
    return { baseUrl: `http://${SHIM_HOST}:${origin.port}`, allowInsecureHttp: true, vars };
  }
  return { baseUrl: `http://${SHIM_HOST}:${origin.port}`, allowInsecureHttp: undefined, vars: { ...vars, FI_ALLOW_INSECURE_HTTP: "1" } };
}

/** What the origin and the proxy received for one direct request. */
function directRecord(outcome: Outcome, origin: Origin, proxy: Sink, caller: { markers: string[] }, pair: { apiKey: string }, path: string) {
  return {
    status: outcome.status,
    originRequestLines: origin.requests.map((head) => head.split("\r\n")[0]),
    originMarkerBytes: origin.count(caller.markers),
    originProxyAuthorizationLines: origin.requests.flatMap((head) => headerValues(head, "proxy-authorization")).length,
    originApiKeyReached: origin.count([pair.apiKey]) > 0,
    proxyConnections: proxy.connections,
    path,
  };
}

const directExpected = (path: string) => ({
  status: 200,
  originRequestLines: [`GET ${path} HTTP/1.1`],
  originMarkerBytes: 0,
  originProxyAuthorizationLines: 0,
  originApiKeyReached: true,
  proxyConnections: 0,
  path,
});

const AXIOS_MATRIX: Array<[AxiosKind, DirectRoute, Placement, string]> = [];
for (const kind of ["HttpClient", "APIKeyAuth"] as AxiosKind[]) {
  for (const route of DIRECT_ROUTES) {
    for (const placement of AXIOS_PLACEMENTS) {
      for (const proxyVar of PROXY_VARS) AXIOS_MATRIX.push([kind, route, placement, proxyVar]);
    }
  }
}

describe("HttpClient and APIKeyAuth on the direct plain-http route with a Proxy-Authorization header set by the caller", () => {
  test.each(AXIOS_MATRIX)(
    "%s, %s, header in %s, %s naming a loopback proxy: the origin receives no Proxy-Authorization of the caller, the proxy receives no connection, and the request succeeds",
    async (kind, route, placement, proxyVar) => {
      const origin = await plainOrigin();
      const proxy = await sink();
      const caller = callerProxyAuth();
      const pair = keys();
      const setting = directSetting(route, origin, proxy, proxyVar);
      const outcome = await withEnv(setting.vars, () => axiosGet(axiosClient(kind, setting.baseUrl, placement, caller.value, pair, setting.allowInsecureHttp)));
      expect(directRecord(outcome, origin, proxy, caller, pair, "/v1/probe")).toEqual(directExpected("/v1/probe"));
    },
  );

  test.each(PROXY_VARS)(
    "control: an HttpClient request without a key to plain http for a name that is not loopback goes to the proxy that %s names, and not to the origin",
    async (proxyVar) => {
      const origin = await plainOrigin();
      const proxy = await sink();
      const outcome = await withEnv({ [proxyVar]: `http://127.0.0.1:${proxy.port}` }, () =>
        axiosGet(axiosClient("HttpClient", `http://${SHIM_HOST}:${origin.port}`, "the headers of the request", undefined, undefined, undefined)),
      );
      expect({
        status: outcome.status,
        absoluteLines: proxy.absolute.map((head) => head.split("\r\n")[0]),
        originConnections: origin.connections,
      }).toEqual({
        status: 200,
        absoluteLines: [`GET http://${SHIM_HOST}:${origin.port}/v1/probe HTTP/1.1`],
        originConnections: 0,
      });
    },
  );
});

const PLATFORM_MATRIX: Array<[DirectRoute, Placement, string]> = [];
for (const route of DIRECT_ROUTES) {
  for (const placement of PLATFORM_PLACEMENTS) {
    for (const proxyVar of PROXY_VARS) PLATFORM_MATRIX.push([route, placement, proxyVar]);
  }
}

describe("the platform Client on the direct plain-http route with a Proxy-Authorization header set by the caller", () => {
  test.each(PLATFORM_MATRIX)(
    "%s, header in %s, %s naming a loopback proxy: the origin receives no Proxy-Authorization of the caller, the proxy receives no connection, and the request succeeds",
    async (route, placement, proxyVar) => {
      const origin = await plainOrigin();
      const proxy = await sink();
      const caller = callerProxyAuth();
      const pair = keys();
      const setting = directSetting(route, origin, proxy, proxyVar);
      const outcome = await withEnv(setting.vars, () => platformGet(setting.baseUrl, placement, caller.value, pair, setting.allowInsecureHttp));
      expect(directRecord(outcome, origin, proxy, caller, pair, "/v1/probe/")).toEqual(directExpected("/v1/probe/"));
    },
  );
});

// --- control: the tunnel route --------------------------------------------------------------------------------

type Sender = "HttpClient" | "APIKeyAuth" | "the platform Client";
const TUNNEL_MATRIX: Array<[Sender, Placement]> = [
  ...(["HttpClient", "APIKeyAuth"] as Sender[]).flatMap((sender) => AXIOS_PLACEMENTS.map((placement) => [sender, placement] as [Sender, Placement])),
  ...PLATFORM_PLACEMENTS.map((placement) => ["the platform Client", placement] as [Sender, Placement]),
];

describe("control: a keyed https request through a CONNECT tunnel with a Proxy-Authorization header set by the caller", () => {
  test.each(TUNNEL_MATRIX)(
    "%s, header in %s: the CONNECT carries the caller's value, the request inside the tunnel carries none, and it succeeds",
    async (sender, placement) => {
      const target = await tlsTarget();
      const proxy = await sink();
      const caller = callerProxyAuth();
      const pair = keys();
      const baseUrl = `https://${SHIM_HOST}:${target.port}`;
      const vars = { HTTPS_PROXY: `http://${SHIM_HOST}:${proxy.port}`, HTTP_PROXY: `http://${SHIM_HOST}:${proxy.port}` };
      const outcome = await withEnv(vars, () =>
        sender === "the platform Client"
          ? platformGet(baseUrl, placement, caller.value, pair, undefined)
          : axiosGet(axiosClient(sender as AxiosKind, baseUrl, placement, caller.value, pair, undefined)),
      );
      const connectMarkerBytes = countIn(proxy.connects.join(""), caller.markers);
      expect({
        status: outcome.status,
        connectLines: proxy.connects.map((head) => head.split("\r\n")[0]),
        connectProxyAuthorization: proxy.connects.map((head) => headerValues(head, "proxy-authorization")),
        connectMarkerBytes,
        proxyMarkerBytesOutsideConnect: proxy.count(caller.markers) - connectMarkerBytes,
        proxyAbsolute: proxy.absolute.length,
        proxyKeyBytes: proxy.count([pair.apiKey, pair.secretKey]),
        targetRequests: target.requests.length,
        targetMarkerBytes: target.count(caller.markers),
        targetProxyAuthorizationLines: target.requests.flatMap((head) => headerValues(head, "proxy-authorization")).length,
        targetApiKeyReached: target.count([pair.apiKey]) > 0,
      }).toEqual({
        status: 200,
        connectLines: [`CONNECT ${SHIM_HOST}:${target.port} HTTP/1.1`],
        connectProxyAuthorization: [[caller.value]],
        connectMarkerBytes: caller.markers[1].length,
        proxyMarkerBytesOutsideConnect: 0,
        proxyAbsolute: 0,
        proxyKeyBytes: 0,
        targetRequests: 1,
        targetMarkerBytes: 0,
        targetProxyAuthorizationLines: 0,
        targetApiKeyReached: true,
      });
    },
  );
});
