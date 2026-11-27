// How HttpClient.request settles when axios gives an error with no HTTP response.
//
// Such an error (a stream body read before the call, a body-read timeout, a TLS certificate refusal, a proxy that
// refuses the CONNECT) is expected to reach the caller as the AxiosError itself, with its code, and a refusal is not
// sent again. An HTTP error response keeps its handling: a 500 gives ServerError after every retry attempt.
//
// Every listener is on the loopback address. The https target with a refused certificate has its own self-signed
// certificate, made per file with the openssl command line and not trusted by this process. The proxy sink answers
// every CONNECT with 502. Keys are random marker strings made per test; each test counts their bytes at every sink.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { spawnSync } from "node:child_process";
import { randomBytes } from "node:crypto";
import * as fs from "node:fs";
import * as http from "node:http";
import type * as net from "node:net";
import * as os from "node:os";
import * as path from "node:path";
import { Readable } from "node:stream";
import * as tls from "node:tls";

import { APIKeyAuth, HttpClient } from "../api/auth";
import { ServerError } from "../utils/errors";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

const SHIM_HOST: string = fx.SHIM_HOST;
const RETRY = { retryAttempts: 3, retryDelay: 10 };
const TLS_REFUSALS = [
  "DEPTH_ZERO_SELF_SIGNED_CERT",
  "SELF_SIGNED_CERT_IN_CHAIN",
  "UNABLE_TO_VERIFY_LEAF_SIGNATURE",
  "CERT_HAS_EXPIRED",
  "ERR_TLS_CERT_ALTNAME_INVALID",
];

// --- environment ---------------------------------------------------------------------------------------------

const ENV_NAMES = [
  "HTTP_PROXY",
  "HTTPS_PROXY",
  "ALL_PROXY",
  "NO_PROXY",
  "http_proxy",
  "https_proxy",
  "all_proxy",
  "no_proxy",
  "npm_config_https_proxy",
  "npm_config_http_proxy",
  "npm_config_proxy",
  "npm_config_no_proxy",
  "FI_ALLOW_INSECURE_HTTP",
];
let savedEnv = new Map<string, string | undefined>();
const cleanups: Array<() => void | Promise<void>> = [];
let undoLookup: () => void;

beforeAll(() => {
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
});

beforeEach(() => {
  savedEnv = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
});
afterEach(async () => {
  while (cleanups.length > 0) {
    const cleanup = cleanups.pop()!;
    try {
      await cleanup();
    } catch {
      /* continue with the others */
    }
  }
  for (const [name, value] of savedEnv) {
    if (value === undefined) delete process.env[name];
    else process.env[name] = value;
  }
});

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;

/** Bytes of every occurrence of each marker in `text`. */
function markerBytes(text: string, markers: string[]): number {
  let bytes = 0;
  for (const m of markers) {
    for (let at = text.indexOf(m); at >= 0; at = text.indexOf(m, at + m.length)) bytes += m.length;
  }
  return bytes;
}

// --- listeners -----------------------------------------------------------------------------------------------

interface Sink {
  origin: string;
  port: number;
  connections: number;
  requests: number;
  count(markers: string[]): number;
}

/** A plain-http loopback listener that reads each request to its end and answers with `status` and a JSON body. */
async function httpSink(status: number): Promise<Sink> {
  const chunks: string[] = [];
  const state = { connections: 0, requests: 0 };
  const server = http.createServer((req, res) => {
    state.requests++;
    chunks.push(JSON.stringify(req.headers));
    req.on("error", () => undefined);
    res.on("error", () => undefined);
    req.on("data", (chunk: Buffer) => chunks.push(chunk.toString("latin1")));
    req.on("end", () => {
      const reply = status === 200 ? JSON.stringify({ status: true, result: {} }) : JSON.stringify({ message: `status ${status}` });
      res.writeHead(status, { "Content-Type": "application/json", "Content-Length": String(Buffer.byteLength(reply)), Connection: "close" });
      res.end(reply);
    });
  });
  server.on("connection", () => state.connections++);
  server.on("clientError", (_error, socket) => socket.destroy());
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  cleanups.push(
    () =>
      new Promise<void>((resolve) => {
        server.closeAllConnections();
        server.close(() => resolve());
      }),
  );
  const port = (server.address() as net.AddressInfo).port;
  return {
    origin: `http://127.0.0.1:${port}`,
    port,
    get connections() {
      return state.connections;
    },
    get requests() {
      return state.requests;
    },
    count: (markers) => markerBytes(chunks.join(""), markers),
  };
}

let selfSigned: { key: string; cert: string } | undefined;

/** A self-signed certificate for 127.0.0.1, localhost and SHIM_HOST that this process does not trust. */
function selfSignedCertificate(): { key: string; cert: string } {
  if (selfSigned) return selfSigned;
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "fi-self-signed-"));
  try {
    const out = spawnSync(
      "openssl",
      [
        "req",
        "-x509",
        "-newkey",
        "ec",
        "-pkeyopt",
        "ec_paramgen_curve:prime256v1",
        "-nodes",
        "-keyout",
        "key.pem",
        "-out",
        "cert.pem",
        "-days",
        "2",
        "-subj",
        "/CN=127.0.0.1",
        "-addext",
        `subjectAltName=IP:127.0.0.1,DNS:localhost,DNS:${SHIM_HOST}`,
      ],
      { cwd: dir, encoding: "utf8" },
    );
    if (out.status !== 0) throw new Error(`openssl req failed: ${out.stderr}`);
    selfSigned = { key: fs.readFileSync(path.join(dir, "key.pem"), "utf8"), cert: fs.readFileSync(path.join(dir, "cert.pem"), "utf8") };
    return selfSigned;
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

interface TlsSink {
  port: number;
  /** TCP connections accepted. */
  connections: number;
  /** Handshakes that the client ended with an error. */
  handshakeErrors: number;
  /** Requests read after a completed handshake. */
  requests: number;
  count(markers: string[]): number;
}

/** An https loopback listener with the self-signed certificate; it answers 200 to any request it reads. */
async function selfSignedTarget(): Promise<TlsSink> {
  const { key, cert } = selfSignedCertificate();
  const chunks: string[] = [];
  const sockets = new Set<net.Socket>();
  const state = { connections: 0, handshakeErrors: 0, requests: 0 };
  const server = tls.createServer({ key, cert }, (socket) => {
    socket.on("error", () => undefined);
    socket.on("data", (data: Buffer) => {
      const text = data.toString("latin1");
      chunks.push(text);
      if (text.includes("\r\n\r\n")) {
        state.requests++;
        socket.end('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}');
      }
    });
  });
  server.on("connection", (socket: net.Socket) => {
    state.connections++;
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
  });
  server.on("tlsClientError", () => state.handshakeErrors++);
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  cleanups.push(
    () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  );
  return {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return state.connections;
    },
    get handshakeErrors() {
      return state.handshakeErrors;
    },
    get requests() {
      return state.requests;
    },
    count: (markers) => markerBytes(chunks.join(""), markers),
  };
}

/** A plain-http loopback listener that answers every request with a 302 to itself. */
async function selfRedirect(): Promise<Sink> {
  const chunks: string[] = [];
  const state = { connections: 0, requests: 0 };
  const server = http.createServer((req, res) => {
    state.requests++;
    chunks.push(JSON.stringify(req.headers));
    req.on("error", () => undefined);
    res.on("error", () => undefined);
    req.resume();
    req.on("end", () => {
      res.writeHead(302, { Location: `/v1/loop/${state.requests}`, "Content-Length": "0", Connection: "close" });
      res.end();
    });
  });
  server.on("connection", () => state.connections++);
  server.on("clientError", (_error, socket) => socket.destroy());
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  cleanups.push(
    () =>
      new Promise<void>((resolve) => {
        server.closeAllConnections();
        server.close(() => resolve());
      }),
  );
  const port = (server.address() as net.AddressInfo).port;
  return {
    origin: `http://127.0.0.1:${port}`,
    port,
    get connections() {
      return state.connections;
    },
    get requests() {
      return state.requests;
    },
    count: (markers) => markerBytes(chunks.join(""), markers),
  };
}

interface SilentProxy {
  port: number;
  connections: number;
  connects: number;
  count(markers: string[]): number;
}

/** A loopback proxy that accepts each connection and reads the CONNECT, with no answer at all. */
async function silentProxy(): Promise<SilentProxy> {
  const chunks: string[] = [];
  const sockets = new Set<net.Socket>();
  const state = { connections: 0, connects: 0 };
  const server = http.createServer((_req, res) => {
    res.destroy();
  });
  server.on("connection", (socket: net.Socket) => {
    state.connections++;
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
  });
  server.on("connect", (req: http.IncomingMessage, socket: net.Socket, head: Buffer) => {
    state.connects++;
    chunks.push(JSON.stringify(req.headers), head.toString("latin1"));
    socket.on("error", () => undefined);
    socket.on("data", (data: Buffer) => chunks.push(data.toString("latin1")));
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  cleanups.push(
    () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  );
  return {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return state.connections;
    },
    get connects() {
      return state.connects;
    },
    count: (markers) => markerBytes(chunks.join(""), markers),
  };
}

// --- settling ------------------------------------------------------------------------------------------------

type Settled = { settled: false; bound: number } | { settled: true; ok: boolean; value?: unknown; error?: any; ms: number };

/** `promise` raced against a bound of `ms`: { settled: false } when the bound passes first. */
/** Milliseconds from a monotonic clock. */
const clockMs = (): number => Number(process.hrtime.bigint()) / 1e6;

async function settleWithin(promise: Promise<unknown>, ms: number): Promise<Settled> {
  const start = clockMs();
  let timer: NodeJS.Timeout | undefined;
  const bound = new Promise<Settled>((resolve) => {
    timer = setTimeout(() => resolve({ settled: false, bound: ms }), ms);
  });
  const outcome = promise.then(
    (value): Settled => ({ settled: true, ok: true, value, ms: clockMs() - start }),
    (error): Settled => ({ settled: true, ok: false, error, ms: clockMs() - start }),
  );
  try {
    return await Promise.race([outcome, bound]);
  } finally {
    clearTimeout(timer);
  }
}

/** The parts of a rejection that the assertions read. */
function shape(outcome: Settled): { settled: boolean; rejected: boolean; serverError: boolean; isAxiosError: boolean; code: string; message: string } {
  if (!outcome.settled) return { settled: false, rejected: false, serverError: false, isAxiosError: false, code: "(not settled)", message: "" };
  if (outcome.ok) return { settled: true, rejected: false, serverError: false, isAxiosError: false, code: "(resolved)", message: "" };
  const error = outcome.error;
  return {
    settled: true,
    rejected: true,
    serverError: error instanceof ServerError,
    isAxiosError: error?.isAxiosError === true,
    code: typeof error?.code === "string" ? error.code : "(no code)",
    message: String(error?.message ?? ""),
  };
}

/** A client with three attempts and a 10 ms retry delay, sending `key` in X-Api-Key. */
function keyedClient(baseUrl: string, key: string, config: Record<string, unknown> = {}): HttpClient {
  return new HttpClient({ baseUrl, ...RETRY, timeout: 5_000, defaultHeaders: { "X-Api-Key": key }, ...config } as any);
}

// --- cases ---------------------------------------------------------------------------------------------------

describe("HttpClient.request with an error that has no HTTP response", () => {
  test("a stream body read to its end before the call rejects with the AxiosError code ERR_BAD_REQUEST, not ServerError, and makes no connection", async () => {
    const sink = await httpSink(200);
    const key = marker("key");
    const body = marker("body");
    const source = Readable.from([Buffer.from(`${body}\n`)]);
    cleanups.push(() => {
      source.destroy();
    });
    for await (const _chunk of source) {
      /* read to the end */
    }
    expect(source.readableEnded).toBe(true);
    const outcome = await settleWithin(
      keyedClient(sink.origin, key).request({ method: "POST", url: "/v1/upload", data: source, headers: { "Content-Type": "application/octet-stream" } } as any),
      5_000,
    );
    const seen = shape(outcome);
    expect({
      settled: seen.settled,
      rejected: seen.rejected,
      serverError: seen.serverError,
      isAxiosError: seen.isAxiosError,
      code: seen.code,
      messageIsHttp500: seen.message.startsWith("HTTP 500"),
      connections: sink.connections,
      sinkMarkerBytes: sink.count([key, body]),
    }).toEqual({
      settled: true,
      rejected: true,
      serverError: false,
      isAxiosError: true,
      code: "ERR_BAD_REQUEST",
      messageIsHttp500: false,
      connections: 0,
      sinkMarkerBytes: 0,
    });
  });

  test("a stream body whose source stalls, with timeout 500, rejects within 3 s with the AxiosError timeout code, not ServerError", async () => {
    const sink = await httpSink(200);
    const key = marker("key");
    const body = marker("body");
    const source = new Readable({ read() {} });
    source.push(Buffer.from(`${body}\n`));
    cleanups.push(() => {
      source.destroy();
    });
    const outcome = await settleWithin(
      keyedClient(sink.origin, key, { timeout: 500 }).request({
        method: "POST",
        url: "/v1/upload",
        data: source,
        headers: { "Content-Type": "application/octet-stream" },
      } as any),
      3_000,
    );
    const seen = shape(outcome);
    expect({
      settled: seen.settled,
      rejected: seen.rejected,
      serverError: seen.serverError,
      isAxiosError: seen.isAxiosError,
      timeoutCode: ["ECONNABORTED", "ETIMEDOUT"].includes(seen.code) ? "ECONNABORTED or ETIMEDOUT" : seen.code,
      messageIsHttp500: seen.message.startsWith("HTTP 500"),
      atMostOneConnection: sink.connections <= 1,
      sinkKeyBytesAtMostOnce: sink.count([key]) <= key.length,
    }).toEqual({
      settled: true,
      rejected: true,
      serverError: false,
      isAxiosError: true,
      timeoutCode: "ECONNABORTED or ETIMEDOUT",
      messageIsHttp500: false,
      atMostOneConnection: true,
      sinkKeyBytesAtMostOnce: true,
    });
  });

  test("an https target with a self-signed certificate that is not trusted rejects with the TLS code after one connection, not three", async () => {
    const target = await selfSignedTarget();
    const key = marker("key");
    const outcome = await settleWithin(keyedClient(`https://127.0.0.1:${target.port}`, key).request({ method: "GET", url: "/v1/probe" } as any), 10_000);
    const seen = shape(outcome);
    expect({
      settled: seen.settled,
      rejected: seen.rejected,
      serverError: seen.serverError,
      isAxiosError: seen.isAxiosError,
      tlsCode: TLS_REFUSALS.includes(seen.code) ? "a TLS certificate code" : seen.code,
      messageIsHttp500: seen.message.startsWith("HTTP 500"),
      connections: target.connections,
      requestsAfterHandshake: target.requests,
      targetMarkerBytes: target.count([key]),
    }).toEqual({
      settled: true,
      rejected: true,
      serverError: false,
      isAxiosError: true,
      tlsCode: "a TLS certificate code",
      messageIsHttp500: false,
      connections: 1,
      requestsAfterHandshake: 0,
      targetMarkerBytes: 0,
    });
  });

  test("a keyed https request through a proxy that answers CONNECT with 502 rejects with the proxy's code or message after one CONNECT, not ServerError", async () => {
    const target = await selfSignedTarget();
    const proxy = await fx.proxySink({ connectStatus: 502 });
    cleanups.push(() => proxy.close());
    process.env.HTTPS_PROXY = `http://127.0.0.1:${proxy.port}`;
    const key = marker("key");
    const outcome = await settleWithin(keyedClient(`https://${SHIM_HOST}:${target.port}`, key).request({ method: "GET", url: "/v1/probe" } as any), 10_000);
    const seen = shape(outcome);
    expect({
      settled: seen.settled,
      rejected: seen.rejected,
      serverError: seen.serverError,
      messageIsHttp500: seen.message.startsWith("HTTP 500"),
      carriesCodeOrProxyMessage: seen.code !== "(no code)" || /502|CONNECT|proxy/i.test(seen.message),
      connects: proxy.connects.length,
      proxyAbsolute: proxy.absolute.length,
      proxyKeyBytes: proxy.count([key]),
      targetConnections: target.connections,
      targetKeyBytes: target.count([key]),
    }).toEqual({
      settled: true,
      rejected: true,
      serverError: false,
      messageIsHttp500: false,
      carriesCodeOrProxyMessage: true,
      connects: 1,
      proxyAbsolute: 0,
      proxyKeyBytes: 0,
      targetConnections: 0,
      targetKeyBytes: 0,
    });
  });
});

describe("HttpClient.request with an HTTP error response", () => {
  test("a 500 answer gives ServerError after three attempts, each one reaching the listener with the key", async () => {
    const sink = await httpSink(500);
    const key = marker("key");
    const outcome = await settleWithin(keyedClient(sink.origin, key).request({ method: "GET", url: "/v1/probe" } as any), 10_000);
    const seen = shape(outcome);
    expect({
      settled: seen.settled,
      rejected: seen.rejected,
      serverError: seen.serverError,
      requests: sink.requests,
      sinkKeyBytes: sink.count([key]),
    }).toEqual({
      settled: true,
      rejected: true,
      serverError: true,
      requests: 3,
      sinkKeyBytes: 3 * key.length,
    });
  });
});

describe("HttpClient.request with a redirect loop", () => {
  test("a listener that answers 302 to itself rejects with the AxiosError code ERR_FR_TOO_MANY_REDIRECTS after one attempt of six requests (five redirects), not three attempts", async () => {
    const sink = await selfRedirect();
    const key = marker("key");
    const outcome = await settleWithin(keyedClient(sink.origin, key).request({ method: "GET", url: "/v1/loop" } as any), 10_000);
    const seen = shape(outcome);
    expect({
      settled: seen.settled,
      rejected: seen.rejected,
      serverError: seen.serverError,
      isAxiosError: seen.isAxiosError,
      code: seen.code,
      messageIsHttp3xx: /^HTTP 3\d\d/.test(seen.message),
      requests: sink.requests,
      sinkKeyBytes: sink.count([key]),
    }).toEqual({
      settled: true,
      rejected: true,
      serverError: false,
      isAxiosError: true,
      code: "ERR_FR_TOO_MANY_REDIRECTS",
      messageIsHttp3xx: false,
      requests: 6,
      sinkKeyBytes: 6 * key.length,
    });
  });
});

describe("A keyed https request through a proxy that does not answer the CONNECT", () => {
  test("with timeout 300 it rejects within 3 s with the code ETIMEDOUT or ECONNABORTED, and the proxy sees one CONNECT with no key", async () => {
    const proxy = await silentProxy();
    process.env.HTTPS_PROXY = `http://127.0.0.1:${proxy.port}`;
    const apiKey = marker("api");
    const secretKey = marker("secret");
    const client = new APIKeyAuth({ fiApiKey: apiKey, fiSecretKey: secretKey, fiBaseUrl: `https://${SHIM_HOST}:9443`, ...RETRY } as any);
    const outcome = await settleWithin((client as any)["_axiosInstance"].request({ method: "GET", url: "/v1/probe", timeout: 300 }), 3_000);
    const seen = shape(outcome);
    expect({
      settled: seen.settled,
      rejected: seen.rejected,
      timeoutCode: ["ETIMEDOUT", "ECONNABORTED"].includes(seen.code) ? "ETIMEDOUT or ECONNABORTED" : seen.code,
      connects: proxy.connects,
      proxyKeyBytes: proxy.count([apiKey, secretKey]),
    }).toEqual({
      settled: true,
      rejected: true,
      timeoutCode: "ETIMEDOUT or ECONNABORTED",
      connects: 1,
      proxyKeyBytes: 0,
    });
  });
});
