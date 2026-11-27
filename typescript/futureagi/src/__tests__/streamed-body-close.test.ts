// A streamed request body longer than the copy kept for a 307 or 308 resend (10 MiB when maxBodyLength is not set).
//
// Past that copy the client passes the rest of the source on as it arrives. These cases cover a source that is
// destroyed without an error after about 11 MiB (it emits close and no end): the request settles with an error soon
// after, whatever its timeout, and does not wait for the timeout. A source of the same length that ends normally is
// sent in full (a control).
//
// The target is a loopback plain-http listener (http://127.0.0.1:port) that counts the body bytes as they arrive and
// answers only once the body has ended. Every request carries a planted marker key, so it is sent directly; the proxy
// variables of the environment point at a loopback proxy sink with NO_PROXY removed, and the bytes of the key marker
// and of the body marker are counted at the target and at the proxy. Each settling check races the request against
// its own bound (settleWithin), so a request that does not settle shows as { settled: false } in the assertion.

/* eslint-disable @typescript-eslint/no-var-requires, @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
import * as http from "node:http";
import type * as net from "node:net";
import { Readable } from "node:stream";

import { HttpClient } from "../api/auth";

const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

const KiB = 1024;
const MiB = 1024 * KiB;
const BODY_BYTES = 11 * MiB;
const CHUNK = 64 * KiB;

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
  "FI_ALLOW_INSECURE_HTTP",
];
let savedEnv = new Map<string, string | undefined>();
const cleanups: Array<() => void | Promise<void>> = [];

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

const marker = (tag: string) => `fi-marker-${tag}-${randomBytes(8).toString("hex")}`;

/** Bytes of every occurrence of each marker in `text`. */
function markerBytes(text: string, markers: string[]): number {
  let bytes = 0;
  for (const one of markers) {
    for (let at = text.indexOf(one); at >= 0; at = text.indexOf(one, at + one.length)) bytes += one.length;
  }
  return bytes;
}

// --- loopback target and proxy sink ------------------------------------------------------------------------------

interface Target {
  origin: string;
  /** Head lines (request line and headers) of every request, as latin1 text. */
  heads: string[];
  /** Body bytes received so far, over every request. */
  bodyBytes(): number;
  /** The first body bytes received (enough to hold the body marker). */
  bodyStart(): string;
  /** Requests whose body reached its end. */
  completed(): number;
}

/** A plain-http loopback listener that reads each request body and answers 200 once the body has ended. */
async function target(): Promise<Target> {
  const heads: string[] = [];
  const state = { bytes: 0, start: "", completed: 0 };
  const server = http.createServer((req, res) => {
    heads.push(`${req.method} ${req.url}\r\n${req.rawHeaders.map((v, i) => (i % 2 === 0 ? `${v}: ` : `${v}\r\n`)).join("")}`);
    req.on("error", () => undefined);
    res.on("error", () => undefined);
    req.on("data", (chunk: Buffer) => {
      if (state.start.length < 256) state.start += chunk.subarray(0, 256).toString("latin1");
      state.bytes += chunk.length;
    });
    req.on("end", () => {
      state.completed++;
      const reply = JSON.stringify({ status: true, result: {} });
      res.writeHead(200, { "Content-Type": "application/json", "Content-Length": String(Buffer.byteLength(reply)), Connection: "close" });
      res.end(reply);
    });
  });
  server.on("clientError", (_error, socket) => socket.destroy());
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  cleanups.push(
    () =>
      new Promise<void>((resolve) => {
        server.closeAllConnections();
        server.close(() => resolve());
      }),
  );
  return {
    origin: `http://127.0.0.1:${(server.address() as net.AddressInfo).port}`,
    heads,
    bodyBytes: () => state.bytes,
    bodyStart: () => state.start,
    completed: () => state.completed,
  };
}

/** A loopback proxy sink named by every proxy variable (both cases), with NO_PROXY removed. */
async function proxyEverywhere(): Promise<{ raw(): string; connections: number }> {
  const proxy = await fx.proxySink();
  cleanups.push(() => proxy.close());
  const url = `http://127.0.0.1:${proxy.port}`;
  for (const name of ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]) process.env[name] = url;
  delete process.env.NO_PROXY;
  delete process.env.no_proxy;
  return proxy;
}

// --- sources -----------------------------------------------------------------------------------------------------

interface Source {
  stream: Readable;
  /** Bytes handed to the stream so far. */
  pushed(): number;
  ended(): boolean;
  closed(): boolean;
}

/**
 * A Readable of `total` bytes in 64 KiB chunks, the first of which starts with `tag`. With `ending` "end" it ends
 * normally; with "close" it is destroyed without an error once every chunk is handed over (close, and no end).
 */
function source(total: number, tag: string, ending: "end" | "close"): Source {
  const state = { pushed: 0, ended: false, closed: false };
  const stream = new Readable({
    highWaterMark: CHUNK,
    read() {
      if (state.pushed >= total) {
        if (ending === "end") this.push(null);
        else setImmediate(() => this.destroy());
        return;
      }
      const size = Math.min(CHUNK, total - state.pushed);
      const chunk = Buffer.alloc(size, 0x63);
      if (state.pushed === 0) chunk.write(tag, 0, "latin1");
      state.pushed += size;
      this.push(chunk);
    },
  });
  stream.on("end", () => {
    state.ended = true;
  });
  stream.on("close", () => {
    state.closed = true;
  });
  cleanups.push(() => {
    stream.destroy();
  });
  return { stream, pushed: () => state.pushed, ended: () => state.ended, closed: () => state.closed };
}

// --- settling ----------------------------------------------------------------------------------------------------

type Settled = { settled: false; bound: number } | { settled: true; ok: boolean; value?: any; error?: any; ms: number };

/** `promise` raced against a bound of `ms`: { settled: false } when the bound passes first. */
async function settleWithin(promise: Promise<any>, ms: number): Promise<Settled> {
  const start = process.hrtime();
  const elapsed = () => {
    const [seconds, nanos] = process.hrtime(start);
    return Math.trunc(seconds * 1000 + nanos / 1e6);
  };
  let timer: NodeJS.Timeout | undefined;
  const bound = new Promise<Settled>((resolve) => {
    timer = setTimeout(() => resolve({ settled: false, bound: ms }), ms);
  });
  const outcome = promise.then(
    (value): Settled => ({ settled: true, ok: true, value, ms: elapsed() }),
    (error): Settled => ({ settled: true, ok: false, error, ms: elapsed() }),
  );
  try {
    return await Promise.race([outcome, bound]);
  } finally {
    clearTimeout(timer);
  }
}

/** What the outcome was, for the assertion and its message. */
function describeOutcome(outcome: Settled): Record<string, any> {
  if (!outcome.settled) return { settled: false, rejected: false, within3s: false, ms: `> ${outcome.bound}`, code: "(not settled)" };
  const error = outcome.error as { code?: string; name?: string; message?: string } | undefined;
  return {
    settled: true,
    rejected: !outcome.ok,
    within3s: outcome.ms < 3_000,
    ms: outcome.ms,
    code: outcome.ok ? "(resolved)" : (error?.code ?? `(no code: ${error?.name}: ${error?.message})`),
  };
}

const keyedClient = (baseUrl: string, key: string, timeout: number) =>
  new HttpClient({ baseUrl, retryAttempts: 1, retryDelay: 50, timeout, defaultHeaders: { "X-Api-Key": key } });

// --- cases -------------------------------------------------------------------------------------------------------

describe("a streamed body over the 10 MiB copy whose source closes without an error and without end", () => {
  test("HttpClient.request with timeout 20000: settles with an error within 3 s and does not wait for the timeout; the proxy receives no marker byte", async () => {
    const proxy = await proxyEverywhere();
    const sink = await target();
    const key = marker("key");
    const tag = marker("body");
    const body = source(BODY_BYTES, tag, "close");
    const client = keyedClient(sink.origin, key, 20_000);
    const outcome = await settleWithin(
      client.request({ method: "POST" as any, url: "/v1/upload", data: body.stream, timeout: 20_000, headers: { "Content-Type": "application/octet-stream" } }),
      3_000,
    );
    const seen = describeOutcome(outcome);
    // eslint-disable-next-line no-console
    console.log("close source via HttpClient.request", {
      ...seen,
      pushed: body.pushed(),
      targetBodyBytes: sink.bodyBytes(),
      targetKeyBytes: markerBytes(sink.heads.join(""), [key]),
      targetTagBytes: markerBytes(sink.bodyStart(), [tag]),
      proxyMarkerBytes: markerBytes(proxy.raw(), [key, tag]),
    });
    expect({
      sourceClosedWithoutEnd: body.closed() && !body.ended(),
      pastCopyLimit: body.pushed() > 10 * MiB,
      settled: seen.settled,
      rejected: seen.rejected,
      within3s: seen.within3s,
      targetBodiesCompleted: sink.completed(),
      targetTagBytes: markerBytes(sink.bodyStart(), [tag]),
      proxyMarkerBytes: markerBytes(proxy.raw(), [key, tag]),
      proxyConnections: proxy.connections,
      code: seen.code,
      ms: seen.ms,
    }).toEqual({
      sourceClosedWithoutEnd: true,
      pastCopyLimit: true,
      settled: true,
      rejected: true,
      within3s: true,
      targetBodiesCompleted: 0,
      targetTagBytes: tag.length,
      proxyMarkerBytes: 0,
      proxyConnections: 0,
      code: seen.code,
      ms: seen.ms,
    });
  });

  test("the client's axios instance with timeout 0: settles with an error within 3 s instead of waiting with no bound; the proxy receives no marker byte", async () => {
    const proxy = await proxyEverywhere();
    const sink = await target();
    const key = marker("key");
    const tag = marker("body");
    const body = source(BODY_BYTES, tag, "close");
    const client = keyedClient(sink.origin, key, 20_000);
    const outcome = await settleWithin(
      (client as any)._axiosInstance.request({ method: "POST", url: "/v1/upload", data: body.stream, timeout: 0, headers: { "Content-Type": "application/octet-stream" } }),
      3_000,
    );
    const seen = describeOutcome(outcome);
    // eslint-disable-next-line no-console
    console.log("close source via the axios instance", {
      ...seen,
      pushed: body.pushed(),
      targetBodyBytes: sink.bodyBytes(),
      targetKeyBytes: markerBytes(sink.heads.join(""), [key]),
      targetTagBytes: markerBytes(sink.bodyStart(), [tag]),
      proxyMarkerBytes: markerBytes(proxy.raw(), [key, tag]),
    });
    expect({
      sourceClosedWithoutEnd: body.closed() && !body.ended(),
      pastCopyLimit: body.pushed() > 10 * MiB,
      settled: seen.settled,
      rejected: seen.rejected,
      within3s: seen.within3s,
      targetBodiesCompleted: sink.completed(),
      targetTagBytes: markerBytes(sink.bodyStart(), [tag]),
      proxyMarkerBytes: markerBytes(proxy.raw(), [key, tag]),
      proxyConnections: proxy.connections,
      code: seen.code,
      ms: seen.ms,
    }).toEqual({
      sourceClosedWithoutEnd: true,
      pastCopyLimit: true,
      settled: true,
      rejected: true,
      within3s: true,
      targetBodiesCompleted: 0,
      targetTagBytes: tag.length,
      proxyMarkerBytes: 0,
      proxyConnections: 0,
      code: seen.code,
      ms: seen.ms,
    });
  });

  test("control: an 11 MiB source that ends normally is sent in full through HttpClient.request and the call resolves; the proxy receives no marker byte", async () => {
    const proxy = await proxyEverywhere();
    const sink = await target();
    const key = marker("key");
    const tag = marker("body");
    const body = source(BODY_BYTES, tag, "end");
    const client = keyedClient(sink.origin, key, 20_000);
    const outcome = await settleWithin(
      client.request({ method: "POST" as any, url: "/v1/upload", data: body.stream, timeout: 20_000, headers: { "Content-Type": "application/octet-stream" } }),
      15_000,
    );
    const seen = describeOutcome(outcome);
    // eslint-disable-next-line no-console
    console.log("ending source via HttpClient.request", {
      ...seen,
      targetBodyBytes: sink.bodyBytes(),
      targetKeyBytes: markerBytes(sink.heads.join(""), [key]),
      targetTagBytes: markerBytes(sink.bodyStart(), [tag]),
      proxyMarkerBytes: markerBytes(proxy.raw(), [key, tag]),
    });
    expect({
      code: seen.code,
      status: outcome.settled && outcome.ok ? (outcome.value as { status?: number }).status : undefined,
      targetBodiesCompleted: sink.completed(),
      targetBodyBytes: sink.bodyBytes(),
      targetKeyBytes: markerBytes(sink.heads.join(""), [key]),
      targetTagBytes: markerBytes(sink.bodyStart(), [tag]),
      proxyMarkerBytes: markerBytes(proxy.raw(), [key, tag]),
      proxyConnections: proxy.connections,
    }).toEqual({
      code: "(resolved)",
      status: 200,
      targetBodiesCompleted: 1,
      targetBodyBytes: BODY_BYTES,
      targetKeyBytes: key.length,
      targetTagBytes: tag.length,
      proxyMarkerBytes: 0,
      proxyConnections: 0,
    });
  });
});

// --- old-style sources ---------------------------------------------------------------------------------------------

interface LegacySource {
  stream: any;
  /** Bytes emitted so far. */
  emitted(): number;
  /** How many data listeners were attached (a reader of the body, or a pipe). */
  starts(): number;
}

/**
 * An old-style stream (a plain `require("node:stream").Stream`, an EventEmitter with pipe and on, plus pause and
 * resume methods that do nothing; without readableDidRead, destroy or _released) that emits `total` bytes in 64 KiB
 * chunks, the first of which starts with `tag`, once a data listener is attached. With `ending` "end" it emits end and
 * then close; with "close" it emits close only.
 */
function legacySource(total: number, tag: string, ending: "end" | "close"): LegacySource {
  const { Stream } = require("node:stream");
  const stream = new Stream();
  stream.pause = () => undefined;
  stream.resume = () => undefined;
  const state = { emitted: 0, starts: 0, started: false, stopped: false };
  const step = () => {
    if (state.stopped) return;
    if (state.emitted >= total) {
      state.stopped = true;
      if (ending === "end") stream.emit("end");
      stream.emit("close");
      return;
    }
    const size = Math.min(CHUNK, total - state.emitted);
    const chunk = Buffer.alloc(size, 0x6c);
    if (state.emitted === 0) chunk.write(tag, 0, "latin1");
    state.emitted += size;
    stream.emit("data", chunk);
    setImmediate(step);
  };
  stream.on("newListener", (name: string) => {
    if (name !== "data") return;
    state.starts++;
    if (state.started) return;
    state.started = true;
    setImmediate(step);
  });
  cleanups.push(() => {
    state.stopped = true;
  });
  return { stream, emitted: () => state.emitted, starts: () => state.starts };
}

/** A plain-http loopback listener that reads each request body and answers 500 once the body has ended. */
async function failingTarget(): Promise<{ origin: string; requests(): number; bodyBytes(): number }> {
  const state = { requests: 0, bytes: 0 };
  const server = http.createServer((req, res) => {
    state.requests++;
    req.on("error", () => undefined);
    res.on("error", () => undefined);
    req.on("data", (chunk: Buffer) => {
      state.bytes += chunk.length;
    });
    req.on("end", () => {
      const reply = JSON.stringify({ status: false, message: "server error" });
      res.writeHead(500, { "Content-Type": "application/json", "Content-Length": String(Buffer.byteLength(reply)), Connection: "close" });
      res.end(reply);
    });
  });
  server.on("clientError", (_error, socket) => socket.destroy());
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  cleanups.push(
    () =>
      new Promise<void>((resolve) => {
        server.closeAllConnections();
        server.close(() => resolve());
      }),
  );
  return {
    origin: `http://127.0.0.1:${(server.address() as net.AddressInfo).port}`,
    requests: () => state.requests,
    bodyBytes: () => state.bytes,
  };
}

const retryingClient = (baseUrl: string, key: string) =>
  new HttpClient({ baseUrl, retryAttempts: 3, retryDelay: 50, timeout: 20_000, defaultHeaders: { "X-Api-Key": key } });

describe("an old-style stream body (a plain Stream with pipe and on) is not sent again by a retry once its reading has started", () => {
  test("with retryAttempts 3 and timeout 20000, an 11 MiB old-style stream that closes without end settles within 3 s with ERR_STREAM_PREMATURE_CLOSE and is sent once", async () => {
    const sink = await target();
    const key = marker("key");
    const tag = marker("body");
    const body = legacySource(BODY_BYTES, tag, "close");
    const client = retryingClient(sink.origin, key);
    const outcome = await settleWithin(
      client.request({ method: "POST" as any, url: "/v1/upload", data: body.stream, timeout: 20_000, headers: { "Content-Type": "application/octet-stream" } }),
      3_000,
    );
    const seen = describeOutcome(outcome);
    // eslint-disable-next-line no-console
    console.log("old-style close source via HttpClient.request with retries", {
      ...seen,
      emitted: body.emitted(),
      dataListeners: body.starts(),
      targetBodyBytes: sink.bodyBytes(),
      targetRequests: sink.heads.length,
    });
    expect({
      pastCopyLimit: body.emitted() > 10 * MiB,
      settled: seen.settled,
      rejected: seen.rejected,
      within3s: seen.within3s,
      code: seen.code,
      targetBodiesCompleted: sink.completed(),
      targetRequests: sink.heads.length,
    }).toEqual({
      pastCopyLimit: true,
      settled: true,
      rejected: true,
      within3s: true,
      code: "ERR_STREAM_PREMATURE_CLOSE",
      targetBodiesCompleted: 0,
      targetRequests: 1,
    });
  });

  test("with retryAttempts 3, a 1 KiB old-style stream that ends is sent once to a server answering 500 and the call rejects with ServerError", async () => {
    const sink = await failingTarget();
    const key = marker("key");
    const tag = marker("body");
    const body = legacySource(KiB, tag, "end");
    const client = retryingClient(sink.origin, key);
    const outcome = await settleWithin(
      client.request({ method: "POST" as any, url: "/v1/upload", data: body.stream, timeout: 20_000, headers: { "Content-Type": "application/octet-stream" } }),
      3_000,
    );
    const seen = describeOutcome(outcome);
    const errorName = outcome.settled && !outcome.ok ? (outcome.error as { name?: string; constructor?: { name?: string } })?.constructor?.name : "(none)";
    // eslint-disable-next-line no-console
    console.log("old-style ending source via HttpClient.request against 500", {
      ...seen,
      errorName,
      emitted: body.emitted(),
      dataListeners: body.starts(),
      serverRequests: sink.requests(),
      serverBodyBytes: sink.bodyBytes(),
    });
    expect({
      settled: seen.settled,
      rejected: seen.rejected,
      within3s: seen.within3s,
      errorName,
      serverRequests: sink.requests(),
      serverBodyBytes: sink.bodyBytes(),
      dataListeners: body.starts(),
    }).toEqual({
      settled: true,
      rejected: true,
      within3s: true,
      errorName: "ServerError",
      serverRequests: 1,
      serverBodyBytes: KiB,
      dataListeners: 1,
    });
  });
});
