// A keyed https request under a proxy that is aborted while its CONNECT tunnel is being opened.
//
// The proxy is a loopback listener reached through a host name that a lookup shim resolves to the loopback address
// (so it counts as a proxy that is not loopback). It reads the CONNECT request and does not answer it, and records
// when each of its sockets closes. The request is aborted (AbortSignal, axios CancelToken, or the platform client's
// per-call timeout) while the tunnel is unanswered: the call rejects, and the socket to the proxy is expected to be
// closed promptly, with no key bytes at the proxy.

/* eslint-disable @typescript-eslint/no-explicit-any */
import axios from "axios";
import { randomBytes } from "node:crypto";
import * as net from "node:net";

import { APIKeyAuth } from "../api/auth";
import { Client } from "../platform/client";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(20_000);

const SHIM_HOST: string = fx.SHIM_HOST;
/** The target port: the CONNECT names it, nothing listens on it (the tunnel is not opened). */
const TARGET_PORT = 8443;
const ABORT_AFTER_MS = 300;
const CLOSE_BOUND_MS = 1000;
const KEY_HEADERS = ["x-api-key", "x-secret-key", "authorization", "cookie", "proxy-authorization"];

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

interface SilentProxy {
  port: number;
  connections: number;
  /** The head of every CONNECT request received. */
  connects: string[];
  /** For each accepted socket: when its CONNECT head was complete and when the socket closed (ms on `clock`). */
  sockets: { connectAt?: number; closedAt?: number }[];
  raw(): string;
  count(markers: string[]): number;
  close(): Promise<void>;
}

/** A proxy on 127.0.0.1 that reads each CONNECT request and sends no answer. */
async function silentProxy(): Promise<SilentProxy> {
  const chunks: string[] = [];
  const connects: string[] = [];
  const records: { connectAt?: number; closedAt?: number }[] = [];
  const open = new Set<net.Socket>();
  const server = net.createServer((socket) => {
    const record: { connectAt?: number; closedAt?: number } = {};
    records.push(record);
    open.add(socket);
    socket.on("error", () => undefined);
    socket.on("close", () => {
      record.closedAt = clock();
      open.delete(socket);
    });
    let head = "";
    socket.on("data", (data) => {
      const text = data.toString("latin1");
      chunks.push(text);
      if (record.connectAt !== undefined) return;
      head += text;
      const end = head.indexOf("\r\n\r\n");
      if (end < 0) return;
      record.connectAt = clock();
      connects.push(head.slice(0, end + 4));
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    port: (server.address() as net.AddressInfo).port,
    get connections() {
      return records.length;
    },
    connects,
    sockets: records,
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
        for (const socket of open) socket.destroy();
        server.close(() => resolve());
      }),
  };
}

let undoLookup: () => void;
beforeAll(() => {
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
});

let proxy: SilentProxy;
let savedEnv: Map<string, string | undefined>;
beforeEach(async () => {
  proxy = await silentProxy();
  savedEnv = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  process.env.HTTPS_PROXY = `http://${SHIM_HOST}:${proxy.port}`;
});
afterEach(async () => {
  for (const [name, value] of savedEnv) {
    if (value === undefined) delete process.env[name];
    else process.env[name] = value;
  }
  await proxy.close();
});

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;
const targetUrl = () => `https://${SHIM_HOST}:${TARGET_PORT}`;
/** Milliseconds on a monotonic clock. */
const clock = () => process.uptime() * 1000;
const pause = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

/** Wait (bounded) for `check` to hold; resolves to whether it held. */
async function waitFor(check: () => boolean, boundMs: number): Promise<boolean> {
  const end = clock() + boundMs;
  while (!check()) {
    if (clock() >= end) return false;
    await pause(10);
  }
  return true;
}

/** Wait for the proxy to hold a complete CONNECT head, then for the rest of `ABORT_AFTER_MS` after `started`. */
async function toAbortPoint(started: number): Promise<boolean> {
  const reached = await waitFor(() => proxy.connects.length >= 1, 5000);
  const left = started + ABORT_AFTER_MS - clock();
  if (left > 0) await pause(left);
  return reached;
}

/** Milliseconds from `abortAt` to the close of the first proxy socket, or null when it is open after the bound. */
async function closeDelay(abortAt: number): Promise<number | null> {
  const closed = await waitFor(() => proxy.sockets[0]?.closedAt !== undefined, CLOSE_BOUND_MS);
  return closed ? (proxy.sockets[0].closedAt as number) - abortAt : null;
}

/** Header names (lower case) of a request head. */
function headerNames(head: string): string[] {
  return head
    .split("\r\n\r\n")[0]
    .split("\r\n")
    .slice(1)
    .filter((line) => line.includes(":"))
    .map((line) => line.slice(0, line.indexOf(":")).trim().toLowerCase());
}

function keyClient(fiApiKey: string, fiSecretKey: string): APIKeyAuth {
  return new APIKeyAuth({ fiApiKey, fiSecretKey, baseUrl: targetUrl(), retryAttempts: 1, timeout: 5000 });
}

const axiosOf = (c: APIKeyAuth): any => (c as any)["_axiosInstance"];

describe("an abort while the proxy tunnel is being opened", () => {
  test("an axios request with an AbortSignal and no timeout rejects as canceled and the socket to the proxy closes within 1000 ms", async () => {
    const keys = [marker("aa"), marker("as")];
    const controller = new AbortController();
    const started = clock();
    const call = axiosOf(keyClient(keys[0], keys[1]))
      .request({ method: "GET", url: "/v1/probe", timeout: 0, signal: controller.signal })
      .then(
        (response: any) => ({ outcome: "resolved", status: response.status }),
        (error: any) => ({ outcome: "rejected", code: error?.code }),
      );
    const connectSeen = await toAbortPoint(started);
    const abortAt = clock();
    controller.abort();
    const result = await Promise.race([call, pause(CLOSE_BOUND_MS * 3).then(() => ({ outcome: "pending" }))]);
    const delay = await closeDelay(abortAt);
    expect({
      connectSeen,
      result,
      proxyKeyBytes: proxy.count(keys),
      proxySocketClosedWithinBound: delay !== null && delay <= CLOSE_BOUND_MS,
      closeDelayMs: delay === null ? `open after ${CLOSE_BOUND_MS} ms` : "within bound",
    }).toEqual({
      connectSeen: true,
      result: { outcome: "rejected", code: "ERR_CANCELED" },
      proxyKeyBytes: 0,
      proxySocketClosedWithinBound: true,
      closeDelayMs: "within bound",
    });
  });

  test("an axios request canceled through a CancelToken with no timeout rejects as canceled and the socket to the proxy closes within 1000 ms", async () => {
    const keys = [marker("ca"), marker("cs")];
    const source = axios.CancelToken.source();
    const started = clock();
    const call = axiosOf(keyClient(keys[0], keys[1]))
      .request({ method: "GET", url: "/v1/probe", timeout: 0, cancelToken: source.token })
      .then(
        (response: any) => ({ outcome: "resolved", status: response.status }),
        (error: any) => ({ outcome: "rejected", canceled: axios.isCancel(error) }),
      );
    const connectSeen = await toAbortPoint(started);
    const abortAt = clock();
    source.cancel("stopped by the test");
    const result = await Promise.race([call, pause(CLOSE_BOUND_MS * 3).then(() => ({ outcome: "pending" }))]);
    const delay = await closeDelay(abortAt);
    expect({
      connectSeen,
      result,
      proxyKeyBytes: proxy.count(keys),
      proxySocketClosedWithinBound: delay !== null && delay <= CLOSE_BOUND_MS,
      closeDelayMs: delay === null ? `open after ${CLOSE_BOUND_MS} ms` : "within bound",
    }).toEqual({
      connectSeen: true,
      result: { outcome: "rejected", canceled: true },
      proxyKeyBytes: 0,
      proxySocketClosedWithinBound: true,
      closeDelayMs: "within bound",
    });
  });

  test("a platform client call that times out while the tunnel is unanswered rejects and the socket to the proxy closes within 1000 ms", async () => {
    // The client timeout (which also bounds the tunnel) is long; the per-call timeout ends the call at ~300 ms.
    const keys = [marker("pa"), marker("ps")];
    const client = new Client({ apiKey: keys[0], secretKey: keys[1], baseUrl: targetUrl(), maxRetries: 0, timeout: 60_000 });
    const started = clock();
    let settledAt = 0;
    const call = client.request("GET", "/v1/probe/", { unwrap: null }, { timeout: ABORT_AFTER_MS }).then(
      () => ({ outcome: "resolved" }),
      (error: any) => ({ outcome: "rejected", name: error?.name }),
    );
    const timed = call.then((value) => {
      settledAt = clock();
      return value;
    });
    const result = await Promise.race([timed, pause(CLOSE_BOUND_MS * 3).then(() => ({ outcome: "pending" }))]);
    const abortAt = settledAt || started + ABORT_AFTER_MS;
    const delay = await closeDelay(abortAt);
    expect({
      connectSeen: proxy.connects.length >= 1,
      result,
      rejectedAfterAbortPoint: settledAt - started >= ABORT_AFTER_MS - 50,
      proxyKeyBytes: proxy.count(keys),
      proxySocketClosedWithinBound: delay !== null && delay <= CLOSE_BOUND_MS,
      closeDelayMs: delay === null ? `open after ${CLOSE_BOUND_MS} ms` : "within bound",
    }).toEqual({
      connectSeen: true,
      result: { outcome: "rejected", name: "APIConnectionError" },
      rejectedAfterAbortPoint: true,
      proxyKeyBytes: 0,
      proxySocketClosedWithinBound: true,
      closeDelayMs: "within bound",
    });
  });

  test("the proxy receives only the CONNECT line and Host, with no key bytes, from an aborted keyed request", async () => {
    const keys = [marker("ka"), marker("ks")];
    const controller = new AbortController();
    const started = clock();
    const call = axiosOf(keyClient(keys[0], keys[1]))
      .request({ method: "GET", url: "/v1/probe", timeout: 0, signal: controller.signal })
      .then(
        () => "resolved",
        () => "rejected",
      );
    const connectSeen = await toAbortPoint(started);
    controller.abort();
    const outcome = await Promise.race([call, pause(CLOSE_BOUND_MS * 3).then(() => "pending")]);
    const head = proxy.connects[0] ?? "";
    expect({
      connectSeen,
      outcome,
      connects: proxy.connects.length,
      requestLine: head.split("\r\n")[0],
      headerNames: headerNames(head),
      keyHeaders: headerNames(head).filter((name) => KEY_HEADERS.includes(name)),
      proxyKeyBytes: proxy.count(keys),
      proxyBytesAfterConnectHead: proxy.raw().length - head.length,
    }).toEqual({
      connectSeen: true,
      outcome: "rejected",
      connects: 1,
      requestLine: `CONNECT ${SHIM_HOST}:${TARGET_PORT} HTTP/1.1`,
      headerNames: ["host"],
      keyHeaders: [],
      proxyKeyBytes: 0,
      proxyBytesAfterConnectHead: 0,
    });
  });
});
