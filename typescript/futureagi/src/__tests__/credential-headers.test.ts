// Credential-named headers in an axios HttpClient request, from every source the request takes headers from.
//
// A header whose name matches /api[-_]?key|secret|token|passw|credential|auth|session|cookie/i is read as a key,
// whether it comes from the headers of one request, the instance defaults (common or per method), an interceptor, or
// fetchOptions.headers of axios's fetch adapter. Such a request is refused over plain http to a host that is not
// loopback, with no connection made, and a redirect to another origin is followed without any of those headers.
//
// Every listener is on the loopback address. The name SHIM resolves to 127.0.0.1 through a lookup shim, so a request
// to it counts as a host that is not loopback while its bytes land in a listener of this file. The https listeners
// are trusted through a scratch CA and record what they read after TLS. Values are random marker strings per test.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
import * as net from "node:net";

import { HttpClient } from "../api/auth";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

const SHIM: string = fx.SHIM_HOST;
const CODE = "insecure_http_origin";
const BOUND_MS = 8_000;
const REFUSAL_MS = 1_500;

type Target = { port: number; connections: number; requests: string[]; raw(): string; count(markers: string[]): number; close(): Promise<void> };
type PlainSink = { port: number; connections: number; count(markers: string[]): number; close(): Promise<void> };

// --- the lookup shim and the scratch CA -----------------------------------------------------------------------

let undoLookup: () => void = () => undefined;
beforeAll(() => {
  fx.certificates();
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
});

// --- listeners, closed after each test ------------------------------------------------------------------------

const open: Array<{ close(): Promise<void> }> = [];

async function tlsTarget(respond?: (head: string, index: number) => string | undefined): Promise<Target> {
  const made: Target = await fx.tlsTarget(respond);
  open.push(made);
  return made;
}

/** A raw plain-http listener that records every connection and byte and answers each request with a JSON body. */
async function plainSink(): Promise<PlainSink> {
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
      socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${fx.REPLY_BODY.length}\r\nConnection: close\r\n\r\n${fx.REPLY_BODY}`);
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const made: PlainSink = {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return state.connections;
    },
    count: countIn(chunks),
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
  open.push(made);
  return made;
}

function countIn(chunks: string[]): (markers: string[]) => number {
  return (markers) => {
    const all = chunks.join("");
    let bytes = 0;
    for (const marker of markers) {
      for (let at = all.indexOf(marker); at >= 0; at = all.indexOf(marker, at + marker.length)) bytes += marker.length;
    }
    return bytes;
  };
}

afterEach(async () => {
  while (open.length) await open.pop()!.close();
});

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

/** Run `run` with every proxy variable and FI_ALLOW_INSECURE_HTTP cleared; restore the environment afterwards. */
async function withCleanEnv<T>(run: () => Promise<T>): Promise<T> {
  const saved = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  try {
    return await run();
  } finally {
    for (const [name, value] of saved) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
}

// --- settling -------------------------------------------------------------------------------------------------

type Settled = { settled: false } | { settled: true; code: string; elapsedMs: number };

/** Race `promise` against `ms`: {settled:false} when the bound passes first, else the outcome ("(resolved)" or the
 * code, or message, of the rejection) and the elapsed time. */
async function settleWithin(promise: Promise<unknown>, ms: number): Promise<Settled> {
  const started = process.hrtime.bigint();
  const elapsed = () => Math.round(Number(process.hrtime.bigint() - started) / 1e6);
  let timer: NodeJS.Timeout | undefined;
  const bound = new Promise<Settled>((resolve) => {
    timer = setTimeout(() => resolve({ settled: false }), ms);
  });
  const outcome = promise.then(
    (): Settled => ({ settled: true, code: "(resolved)", elapsedMs: elapsed() }),
    (e: any): Settled => ({ settled: true, code: e instanceof Error ? ((e as { code?: string }).code ?? e.message) : "(not an Error)", elapsedMs: elapsed() }),
  );
  try {
    return await Promise.race([outcome, bound]);
  } finally {
    clearTimeout(timer);
  }
}

const codeOf = (result: Settled) => (result.settled ? result.code : "(unsettled)");

// --- clients and requests -------------------------------------------------------------------------------------

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;

function client(baseUrl: string, defaultHeaders: Record<string, any> = {}): HttpClient {
  return new HttpClient({ baseUrl, retryAttempts: 1, timeout: 5000, defaultHeaders } as any);
}

/** A client whose requests go through axios's fetch adapter. */
function fetchClient(baseUrl: string, defaultHeaders: Record<string, any> = {}): HttpClient {
  const made = client(baseUrl, defaultHeaders);
  (made as any)._axiosInstance.defaults.adapter = "fetch";
  return made;
}

/** Instance-level fetchOptions with these headers (merged into every request's config by axios). */
function setFetchOptionHeaders(made: HttpClient, headers: Record<string, string>): void {
  (made as any)._axiosInstance.defaults.fetchOptions = { headers };
}

const get = (c: HttpClient, headers?: Record<string, string>) => c.request({ method: "GET", url: "/v1/probe", ...(headers ? { headers } : {}) } as any);

const redirect = (status: number, location: string) => `HTTP/1.1 ${status} Redirect\r\nLocation: ${location}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n`;

/** An https listener that answers its first request with `status` to `location`, then 200. */
const redirecting = (status: number, location: () => string) => tlsTarget((_head, index) => (index === 0 ? redirect(status, location()) : undefined));

// --- fetchOptions.headers -------------------------------------------------------------------------------------

describe("a key in fetchOptions.headers of axios's fetch adapter", () => {
  test.each([[302], [307]])(
    "https origin answered with %i to another https host: the other host receives the request and none of the key",
    async (status) => {
      const key = marker("fo");
      const other = await tlsTarget();
      const first = await redirecting(status, () => `https://${SHIM}:${other.port}/v1/next`);
      const made = fetchClient(`https://127.0.0.1:${first.port}`);
      setFetchOptionHeaders(made, { "X-Api-Key": key });
      const result = await withCleanEnv(() => settleWithin(get(made), BOUND_MS));
      expect({
        code: codeOf(result),
        firstHostKeyed: first.count([key]) > 0,
        otherHostReached: other.requests.length > 0,
        otherHostKeyBytes: other.count([key]),
      }).toEqual({ code: "(resolved)", firstHostKeyed: true, otherHostReached: true, otherHostKeyBytes: 0 });
    },
  );

  test("a first request to a plain-http host that is not loopback: refused with the code, no connection is made", async () => {
    const key = marker("fp");
    const sink = await plainSink();
    const made = fetchClient(`http://${SHIM}:${sink.port}`);
    setFetchOptionHeaders(made, { "X-Api-Key": key });
    const result = await withCleanEnv(() => settleWithin(get(made), BOUND_MS));
    expect({ code: codeOf(result), connections: sink.connections, keyBytes: sink.count([key]) }).toEqual({ code: CODE, connections: 0, keyBytes: 0 });
    expect(result.settled && result.elapsedMs).toBeLessThan(REFUSAL_MS);
  });

  test("the key reaches the first https host", async () => {
    const key = marker("fh");
    const site = await tlsTarget();
    const made = fetchClient(`https://127.0.0.1:${site.port}`);
    setFetchOptionHeaders(made, { "X-Api-Key": key });
    const result = await withCleanEnv(() => settleWithin(get(made), BOUND_MS));
    expect({ code: codeOf(result), requests: site.requests.length, keyed: site.requests.length > 0 && site.requests[0].includes(key) }).toEqual({
      code: "(resolved)",
      requests: 1,
      keyed: true,
    });
  });
});

// --- instance defaults and interceptors -----------------------------------------------------------------------

type Layer = [string, (made: HttpClient, value: string) => void];

const LAYERS: Layer[] = [
  ["X-Auth-Token in defaults.headers.common", (made, value) => ((made as any)._axiosInstance.defaults.headers.common["X-Auth-Token"] = value)],
  ["Cookie in defaults.headers.common", (made, value) => ((made as any)._axiosInstance.defaults.headers.common.Cookie = `sid=${value}`)],
  ["X-Auth-Token in defaults.headers.get", (made, value) => ((made as any)._axiosInstance.defaults.headers.get["X-Auth-Token"] = value)],
  ["X-Session-Id in defaults.headers.common", (made, value) => ((made as any)._axiosInstance.defaults.headers.common["X-Session-Id"] = value)],
  [
    "X-Auth-Token added by a request interceptor",
    (made, value) =>
      (made as any)._axiosInstance.interceptors.request.use((config: any) => {
        config.headers.set("X-Auth-Token", value);
        return config;
      }),
  ],
];

describe("a credential-named header from the instance or an interceptor", () => {
  test.each(LAYERS.map(([name]) => [name]))("%s, first request to a plain-http host that is not loopback: refused with the code, no connection is made", async (name) => {
    const value = marker("dl");
    const sink = await plainSink();
    const made = client(`http://${SHIM}:${sink.port}`);
    LAYERS.find(([n]) => n === name)![1](made, value);
    const result = await withCleanEnv(() => settleWithin(get(made), BOUND_MS));
    expect({ code: codeOf(result), connections: sink.connections, valueBytes: sink.count([value]) }).toEqual({ code: CODE, connections: 0, valueBytes: 0 });
    expect(result.settled && result.elapsedMs).toBeLessThan(REFUSAL_MS);
  });

  test("X-Api-Key in defaults.headers.common, first request to a plain-http host that is not loopback: refused with the code, no connection is made", async () => {
    const key = marker("dk");
    const sink = await plainSink();
    const made = client(`http://${SHIM}:${sink.port}`);
    (made as any)._axiosInstance.defaults.headers.common["X-Api-Key"] = key;
    const result = await withCleanEnv(() => settleWithin(get(made), BOUND_MS));
    expect({ code: codeOf(result), connections: sink.connections, keyBytes: sink.count([key]) }).toEqual({ code: CODE, connections: 0, keyBytes: 0 });
    expect(result.settled && result.elapsedMs).toBeLessThan(REFUSAL_MS);
  });

  test("X-Api-Key in defaults.headers.common, request to a loopback plain-http host: sent with the key", async () => {
    const key = marker("dd");
    const sink = await plainSink();
    const made = client(`http://127.0.0.1:${sink.port}`);
    (made as any)._axiosInstance.defaults.headers.common["X-Api-Key"] = key;
    const result = await withCleanEnv(() => settleWithin(get(made), BOUND_MS));
    expect({ code: codeOf(result), connections: sink.connections, keyed: sink.count([key]) > 0 }).toEqual({ code: "(resolved)", connections: 1, keyed: true });
  });

  test("X-Api-Key in defaults.headers.common, https origin answered with 302 to another https host: the other host receives none of the key", async () => {
    const key = marker("dr");
    const other = await tlsTarget();
    const first = await redirecting(302, () => `https://${SHIM}:${other.port}/v1/next`);
    const made = client(`https://127.0.0.1:${first.port}`);
    (made as any)._axiosInstance.defaults.headers.common["X-Api-Key"] = key;
    const result = await withCleanEnv(() => settleWithin(get(made), BOUND_MS));
    expect({
      code: codeOf(result),
      firstHostKeyed: first.count([key]) > 0,
      otherHostReached: other.requests.length > 0,
      otherHostKeyBytes: other.count([key]),
    }).toEqual({ code: "(resolved)", firstHostKeyed: true, otherHostReached: true, otherHostKeyBytes: 0 });
  });
});

// --- headers of one request -----------------------------------------------------------------------------------

describe("a credential-named header in the headers of one request", () => {
  test.each([["http adapter"], ["fetch adapter"]])(
    "%s: X-Auth-Token, https origin answered with 302 to another https host: the other host receives the request and none of the value",
    async (adapter) => {
      const value = marker("rq");
      const other = await tlsTarget();
      const first = await redirecting(302, () => `https://${SHIM}:${other.port}/v1/next`);
      const base = `https://127.0.0.1:${first.port}`;
      const made = adapter === "fetch adapter" ? fetchClient(base) : client(base);
      const result = await withCleanEnv(() => settleWithin(get(made, { "X-Auth-Token": value }), BOUND_MS));
      expect({
        code: codeOf(result),
        firstHostHasValue: first.count([value]) > 0,
        otherHostReached: other.requests.length > 0,
        otherHostValueBytes: other.count([value]),
      }).toEqual({ code: "(resolved)", firstHostHasValue: true, otherHostReached: true, otherHostValueBytes: 0 });
    },
  );
});
