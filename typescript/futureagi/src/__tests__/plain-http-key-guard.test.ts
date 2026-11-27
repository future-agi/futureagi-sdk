// Requests that carry a Future AGI key, sent to a plain-http address.
//
// Every sink here is a loopback listener. The host name below resolves to the loopback address through a lookup
// shim, so a request to it counts as "a host that is not loopback" while its bytes land in a listener of this file.
// Keys are random marker strings made per test; a refusal case asserts zero connections and zero marker bytes at
// every sink. The cases that need undici's ProxyAgent read the module from FI_TEST_UNDICI (a directory holding it).

/* eslint-disable @typescript-eslint/no-explicit-any */
import axios from "axios";
import { spawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import * as http from "node:http";
import * as https from "node:https";
import * as net from "node:net";
import * as path from "node:path";
import * as tenantFs from "node:fs";
import * as tenantOs from "node:os";

import { APIKeyAuth, HttpClient } from "../api/auth";
import { Client } from "../platform/client";
import type { FetchLike } from "../platform/transport";
import { ProviderAPIKeyClient, getAPIKeyManager, APIKeyManager } from "../api/apikeys";
import { KnowledgeBase as KbClient } from "../kb/client";
import { Dataset } from "../datasets/dataset";
import { Prompt } from "../prompt/client";
import { Annotation } from "../annotations/annotation";
import { AnnotationQueue } from "../queues/client";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const dns: typeof import("node:dns") = require("node:dns");

const SHIM_HOST = "guard-target.futureagi.com";
const CODE = "insecure_http_origin";
const REPLY_BODY = JSON.stringify({ status: true, result: {} });

// --- lookup shim ----------------------------------------------------------------------------------------------

const realLookup = dns.lookup;
beforeAll(() => {
  (dns as any).lookup = function lookup(hostname: string, options: any, callback: any) {
    if (typeof options === "function") {
      callback = options;
      options = {};
    }
    if (String(hostname).toLowerCase() === SHIM_HOST) {
      const all = typeof options === "object" && options !== null && options.all === true;
      process.nextTick(() => (all ? callback(null, [{ address: "127.0.0.1", family: 4 }]) : callback(null, "127.0.0.1", 4)));
      return {};
    }
    return (realLookup as any).call(dns, hostname, options, callback);
  };
});
afterAll(() => {
  (dns as any).lookup = realLookup;
});

// --- sinks ----------------------------------------------------------------------------------------------------

interface Sink {
  port: number;
  connections: number;
  raw(): string;
  count(markers: string[]): number;
  close(): Promise<void>;
}

/** A raw listener that records every connection and byte. It answers a plain request with a JSON body and a
 * CONNECT request with an established tunnel, so it can stand in for a target or for a CONNECT-aware proxy. */
async function sink(): Promise<Sink> {
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
      if (head.startsWith("CONNECT ")) {
        socket.write("HTTP/1.1 200 Connection Established\r\n\r\n");
      } else {
        socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${REPLY_BODY.length}\r\nConnection: close\r\n\r\n${REPLY_BODY}`);
      }
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

let target: Sink;
let proxy: Sink;
beforeEach(async () => {
  target = await sink();
  proxy = await sink();
});
afterEach(async () => {
  await target.close();
  await proxy.close();
});

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;
const targetUrl = () => `http://${SHIM_HOST}:${target.port}`;
const loopbackUrl = () => `http://127.0.0.1:${target.port}`;
const proxyUrl = () => `http://127.0.0.1:${proxy.port}`;

function expectQuiet(markers: string[]): void {
  expect({ proxyBytes: proxy.count(markers), targetBytes: target.count(markers) }).toEqual({ proxyBytes: 0, targetBytes: 0 });
  expect({ proxyConnections: proxy.connections, targetConnections: target.connections }).toEqual({ proxyConnections: 0, targetConnections: 0 });
}

async function expectRefusal(run: () => Promise<unknown>): Promise<void> {
  const error = await run().then(
    () => undefined,
    (e: unknown) => e,
  );
  expect(error).toBeInstanceOf(Error);
  expect((error as { code?: string }).code).toBe(CODE);
}

const ENV_NAMES = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_ALLOW_INSECURE_HTTP"];

/** Run `run` with the proxy variables pointing at the proxy sink and no exemptions (or with none set), then restore the environment. */
async function withProxyEnv<T>(run: () => Promise<T>, extra: Record<string, string> = {}, proxied = true): Promise<T> {
  const saved = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  if (proxied) {
    process.env.HTTP_PROXY = proxyUrl();
    process.env.http_proxy = proxyUrl();
    process.env.NO_PROXY = "";
    process.env.no_proxy = "";
  }
  Object.assign(process.env, extra);
  try {
    return await run();
  } finally {
    for (const [name, value] of saved) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
}

// --- the axios sender -----------------------------------------------------------------------------------------

function axiosClient(baseUrl: string, config: Record<string, unknown> = {}): HttpClient {
  return new HttpClient({ baseUrl, retryAttempts: 1, timeout: 5000, ...config } as any);
}

const get = (client: HttpClient, headers?: unknown) => client.request({ method: "GET", url: "/v1/probe", ...(headers === undefined ? {} : { headers }) } as any);

const layers = (key: string): Array<[string, any]> => [
  ["common X-Api-Key", { common: { "X-Api-Key": key } }],
  ["method-layer X-Api-Key", { get: { "X-Api-Key": key } }],
  ["common Authorization Bearer", { common: { Authorization: `Bearer ${key}` } }],
];

describe("axios sender: a key in a header layer", () => {
  test.each(layers("placeholder").map(([name]) => name))("client default headers, %s", async (name) => {
    const key = marker("axl");
    const headers = layers(key).find(([n]) => n === name)![1];
    await withProxyEnv(() => get(axiosClient(targetUrl(), { defaultHeaders: headers })).catch(() => undefined));
    expectQuiet([key]);
  });

  test.each(layers("placeholder").map(([name]) => name))("per-call headers, %s", async (name) => {
    const key = marker("axc");
    const headers = layers(key).find(([n]) => n === name)![1];
    await withProxyEnv(() => get(axiosClient(targetUrl()), headers).catch(() => undefined));
    expectQuiet([key]);
  });

  test("a layer for another method does not make the request keyed", async () => {
    const key = marker("axo");
    await withProxyEnv(() => get(axiosClient(targetUrl(), { defaultHeaders: { post: { "X-Api-Key": key } } })), {}, false);
    expect(target.connections).toBe(1);
    expect(target.count([key])).toBe(0);
  });

  test("per-call header pairs", async () => {
    const key = marker("axp");
    await withProxyEnv(() => get(axiosClient(targetUrl()), [["X-Api-Key", key]]).catch(() => undefined));
    expectQuiet([key]);
  });

  test("the key and secret of the client", async () => {
    const [apiKey, secretKey] = [marker("axa"), marker("axs")];
    await withProxyEnv(() => get(new APIKeyAuth({ fiApiKey: apiKey, fiSecretKey: secretKey, baseUrl: targetUrl(), retryAttempts: 1, timeout: 5000 })).catch(() => undefined));
    expectQuiet([apiKey, secretKey]);
  });

  test("the refusal is an Error with the code, raised without a retry", async () => {
    const key = marker("axe");
    const started = process.hrtime.bigint();
    await expectRefusal(() => get(axiosClient(targetUrl(), { retryAttempts: 3, retryDelay: 2000, defaultHeaders: { "X-Api-Key": key } })));
    expect(Number(process.hrtime.bigint() - started) / 1e6).toBeLessThan(1500);
    expectQuiet([key]);
  });
});

describe("axios sender: loopback, https and unkeyed requests", () => {
  test("a keyed request to a loopback host is sent directly, whatever the proxy variables say", async () => {
    const key = marker("axd");
    await withProxyEnv(() => get(axiosClient(loopbackUrl(), { defaultHeaders: { "X-Api-Key": key } })));
    expect({ proxyBytes: proxy.count([key]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });

  test("a keyed request to localhost is sent directly, whatever the proxy variables say", async () => {
    const key = marker("axh");
    await withProxyEnv(() => get(axiosClient(`http://localhost:${target.port}`, { defaultHeaders: { "X-Api-Key": key } })));
    expect({ proxyBytes: proxy.count([key]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });

  test("a redirect from a loopback host to another plain-http host is not followed", async () => {
    const key = marker("axr");
    const other = await sink();
    try {
      const redirector = await sink();
      // answer the first request with a redirect to the other host
      const net_ = net.createServer((socket) => {
        socket.on("error", () => undefined);
        socket.once("data", () => socket.end(`HTTP/1.1 302 Found\r\nLocation: http://${SHIM_HOST}:${other.port}/x\r\nContent-Length: 0\r\nConnection: close\r\n\r\n`));
      });
      await new Promise<void>((resolve) => net_.listen(0, "127.0.0.1", resolve));
      const port = (net_.address() as net.AddressInfo).port;
      await withProxyEnv(() => get(axiosClient(`http://127.0.0.1:${port}`, { defaultHeaders: { "X-Api-Key": key } })).catch(() => undefined), {}, false);
      expect({ otherBytes: other.count([key]), otherConnections: other.connections }).toEqual({ otherBytes: 0, otherConnections: 0 });
      await new Promise((resolve) => net_.close(resolve));
      await redirector.close();
    } finally {
      await other.close();
    }
  });

  test("a request without a key to another plain-http host is unchanged", async () => {
    await withProxyEnv(() => get(axiosClient(targetUrl())), {}, false);
    expect(target.connections).toBe(1);
  });

  test("a keyed request to an https host is handed to the adapter with its proxy setting and agents as given, and a transport of the SDK that checks the agent axios picks", async () => {
    const key = marker("axt");
    const seen: any[] = [];
    const client = axiosClient("https://guard-target.futureagi.com", { defaultHeaders: { "X-Api-Key": key } });
    (client as any)._axiosInstance.defaults.adapter = async (config: any) => {
      seen.push(config);
      return { data: {}, status: 200, statusText: "OK", headers: {}, config };
    };
    await withProxyEnv(() => get(client), {}, false);
    expect(seen).toHaveLength(1);
    expect(seen[0].proxy).toBeUndefined();
    // The agents stay as the caller set them (none here). The request is read again when it is created, on the agent
    // axios picks for it, for a proxy or an agent that an adapter function sets at that point.
    expect(seen[0].httpAgent).toBeUndefined();
    expect(seen[0].httpsAgent).toBeUndefined();
    expect(typeof seen[0].transport?.request).toBe("function");
    expect(seen[0].transport).not.toBe(http);
    expect(seen[0].transport).not.toBe(https);
  });
});

// --- the platform client --------------------------------------------------------------------------------------

function platform(baseUrl: string, config: Record<string, unknown> = {}): Client {
  return new Client({ apiKey: marker("pk"), secretKey: marker("ps"), baseUrl, maxRetries: 0, timeout: 5000, ...config } as any);
}

const probe = (client: Client, options?: unknown) => client.request("GET", "/v1/probe/", {}, options as any);

describe("platform client", () => {
  test("the client keys", async () => {
    const [apiKey, secretKey] = [marker("pa"), marker("pb")];
    await withProxyEnv(() => probe(platform(targetUrl(), { apiKey, secretKey })).catch(() => undefined));
    expectQuiet([apiKey, secretKey]);
  });

  test("a bearer token in the default headers", async () => {
    const token = marker("pt");
    await withProxyEnv(() => probe(platform(targetUrl(), { defaultHeaders: { Authorization: `Bearer ${token}` } })).catch(() => undefined));
    expectQuiet([token]);
  });

  test("per-call header pairs", async () => {
    const key = marker("pp");
    await withProxyEnv(() => probe(platform(targetUrl()), { headers: [["X-Api-Key", key]] }).catch(() => undefined));
    expectQuiet([key]);
  });

  test("per-call header pairs reach a loopback host as named headers", async () => {
    const key = marker("pq");
    await probe(platform(loopbackUrl()), { headers: [["X-Api-Key", key]] });
    const raw = target.raw().toLowerCase();
    expect(raw).toContain(`x-api-key: ${key}`);
    expect(raw).not.toMatch(/^0: /m);
  });

  test("per-call Headers and Map objects are read as headers", async () => {
    const [a, b] = [marker("ph"), marker("pm")];
    await probe(platform(loopbackUrl()), { headers: new Headers({ "X-Workspace-Id": a }) });
    await probe(platform(loopbackUrl()), { headers: new Map([["X-Request-Tag", b]]) });
    const raw = target.raw().toLowerCase();
    expect(raw).toContain(`x-workspace-id: ${a}`);
    expect(raw).toContain(`x-request-tag: ${b}`);
  });

  test("a caller-supplied fetch is not called for a plain-http host that is not loopback", async () => {
    const calls: string[] = [];
    const fetch: FetchLike = async (url) => {
      calls.push(url);
      return new Response(REPLY_BODY, { status: 200, headers: { "content-type": "application/json" } });
    };
    await probe(platform("http://backend.example", { fetch })).catch(() => undefined);
    expect(calls).toEqual([]);
  });

  test("a caller-supplied fetch is called for https and for loopback", async () => {
    const calls: string[] = [];
    const fetch: FetchLike = async (url) => {
      calls.push(url);
      return new Response(REPLY_BODY, { status: 200, headers: { "content-type": "application/json" } });
    };
    await probe(platform("https://backend.example", { fetch }));
    await probe(platform("http://127.0.0.1:9", { fetch }));
    await probe(platform("http://localhost:9", { fetch }));
    await probe(platform("http://[::1]:9", { fetch }));
    expect(calls).toHaveLength(4);
  });

  test("a keyed request to a loopback host is sent directly", async () => {
    const [apiKey, secretKey] = [marker("pl"), marker("pm")];
    await probe(platform(loopbackUrl(), { apiKey, secretKey }));
    expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
    expect(proxy.connections).toBe(0);
  });
});

// --- the opt-in -----------------------------------------------------------------------------------------------

describe("opt-in", () => {
  test.each(["false", "0", "true", "yes", " 1", ""])("FI_ALLOW_INSECURE_HTTP=%j does not enable it (axios)", async (value) => {
    const key = marker("oe");
    await withProxyEnv(() => get(axiosClient(targetUrl(), { defaultHeaders: { "X-Api-Key": key } })).catch(() => undefined), { FI_ALLOW_INSECURE_HTTP: value });
    expectQuiet([key]);
  });

  test.each(["false", "0", "true", "yes", " 1", ""])("FI_ALLOW_INSECURE_HTTP=%j does not enable it (platform)", async (value) => {
    const key = marker("of");
    await withProxyEnv(() => probe(platform(targetUrl(), { apiKey: key })).catch(() => undefined), { FI_ALLOW_INSECURE_HTTP: value });
    expectQuiet([key]);
  });

  test.each([["false"], ["0"], ["true"], [1], [{}], [null as unknown as boolean], [0]])("allowInsecureHttp: %j does not enable it", async (value) => {
    const [a, b] = [marker("og"), marker("oh")];
    await withProxyEnv(async () => {
      await get(axiosClient(targetUrl(), { allowInsecureHttp: value, defaultHeaders: { "X-Api-Key": a } })).catch(() => undefined);
      await probe(platform(targetUrl(), { allowInsecureHttp: value, apiKey: b })).catch(() => undefined);
    });
    // `null` falls back to the environment, which is unset here.
    expectQuiet([a, b]);
  });

  test("FI_ALLOW_INSECURE_HTTP=1 sends the request directly, not through the proxy variables (axios)", async () => {
    const key = marker("oi");
    await withProxyEnv(() => get(axiosClient(targetUrl(), { defaultHeaders: { "X-Api-Key": key } })), { FI_ALLOW_INSECURE_HTTP: "1" });
    expect({ proxyBytes: proxy.count([key]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });

  test("allowInsecureHttp: true sends the request directly, not through the proxy variables (axios)", async () => {
    const key = marker("oj");
    await withProxyEnv(() => get(axiosClient(targetUrl(), { allowInsecureHttp: true, defaultHeaders: { "X-Api-Key": key } })));
    expect({ proxyBytes: proxy.count([key]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });

  test("allowInsecureHttp: true sends the request directly (platform)", async () => {
    const key = marker("ok");
    await withProxyEnv(() => probe(platform(targetUrl(), { allowInsecureHttp: true, apiKey: key })));
    expect({ proxyBytes: proxy.count([key]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });

  test("allowInsecureHttp: \"1\" enables it, whatever the environment says", async () => {
    const key = marker("ol");
    await withProxyEnv(() => get(axiosClient(targetUrl(), { allowInsecureHttp: "1", defaultHeaders: { "X-Api-Key": key } })), { FI_ALLOW_INSECURE_HTTP: "0" });
    expect(target.count([key])).toBeGreaterThan(0);
    expect(proxy.connections).toBe(0);
  });
});

// --- real child processes -------------------------------------------------------------------------------------

const PACKAGE_DIR = path.resolve(__dirname, "..", "..");
const CHILD = path.join(__dirname, "support", "child-request.mts");
const SHIM = path.join(__dirname, "support", "name-shim.cjs");

function child(spec: Record<string, unknown>, env: Record<string, string>): Promise<{ ok: boolean; code: string | null }> {
  return new Promise((resolve, reject) => {
    const clean: Record<string, string | undefined> = { ...process.env };
    for (const name of ENV_NAMES) delete clean[name];
    const proc = spawn(process.execPath, ["--require", SHIM, "--import", "tsx", CHILD], {
      cwd: PACKAGE_DIR,
      env: { ...clean, ...env, FI_CHILD_CASE: JSON.stringify(spec) },
      stdio: ["ignore", "pipe", "pipe"],
    });
    let out = "";
    proc.stdout.on("data", (d) => (out += d));
    proc.stderr.on("data", () => undefined);
    const timer = setTimeout(() => proc.kill("SIGKILL"), 60_000);
    proc.on("error", reject);
    proc.on("close", () => {
      clearTimeout(timer);
      const line = out.split("\n").find((l) => l.startsWith("RESULT:"));
      line === undefined ? reject(new Error("the child printed no result")) : resolve(JSON.parse(line.slice("RESULT:".length)));
    });
  });
}

/** Like `child`, and also how long the process took to exit after it printed its result. */
function timedChild(spec: Record<string, unknown>, env: Record<string, string>): Promise<{ result: { ok: boolean; code: string | null }; exitMs: number }> {
  return new Promise((resolve, reject) => {
    const clean: Record<string, string | undefined> = { ...process.env };
    for (const name of ENV_NAMES) delete clean[name];
    const proc = spawn(process.execPath, ["--require", SHIM, "--import", "tsx", CHILD], {
      cwd: PACKAGE_DIR,
      env: { ...clean, ...env, FI_CHILD_CASE: JSON.stringify({ ...spec, noExit: true }) },
      stdio: ["ignore", "pipe", "pipe"],
    });
    let out = "";
    let printedAt: bigint | undefined;
    proc.stdout.on("data", (d) => {
      out += d;
      if (printedAt === undefined && out.includes("RESULT:") && out.slice(out.indexOf("RESULT:")).includes("\n")) printedAt = process.hrtime.bigint();
    });
    proc.stderr.on("data", () => undefined);
    const timer = setTimeout(() => proc.kill("SIGKILL"), 60_000);
    proc.on("error", reject);
    proc.on("exit", () => {
      const exitedAt = process.hrtime.bigint();
      clearTimeout(timer);
      const line = out.split("\n").find((l) => l.startsWith("RESULT:"));
      if (line === undefined || printedAt === undefined) return reject(new Error("the child printed no result"));
      resolve({ result: JSON.parse(line.slice("RESULT:".length)), exitMs: Number(exitedAt - printedAt) / 1e6 });
    });
  });
}

describe("separate processes", () => {
  jest.setTimeout(90_000);

  const proxied = (extra: Record<string, string> = {}) => ({ HTTP_PROXY: proxyUrl(), HTTPS_PROXY: proxyUrl(), NO_PROXY: "", ...extra });

  test.each([[false], [true]])("a keyed axios request, NODE_USE_ENV_PROXY=%s", async (useEnvProxy) => {
    const [apiKey, secretKey] = [marker("c1"), marker("c2")];
    const env = proxied(useEnvProxy ? { NODE_USE_ENV_PROXY: "1" } : {});
    const result = await child({ kind: "axios", baseUrl: targetUrl(), apiKey, secretKey }, env);
    expectQuiet([apiKey, secretKey]);
    expect(result).toEqual({ ok: false, code: CODE });
  });

  test("a keyed platform fetch with NODE_USE_ENV_PROXY=1", async () => {
    const [apiKey, secretKey] = [marker("c3"), marker("c4")];
    const result = await child({ kind: "fetch", baseUrl: targetUrl(), apiKey, secretKey }, proxied({ NODE_USE_ENV_PROXY: "1" }));
    expectQuiet([apiKey, secretKey]);
    expect(result).toEqual({ ok: false, code: CODE });
  });

  test.each([["axios"], ["fetch"]])("a keyed %s request to a loopback host with NODE_USE_ENV_PROXY=1 is sent directly", async (kind) => {
    const [apiKey, secretKey] = [marker("c5"), marker("c6")];
    const result = await child({ kind, baseUrl: loopbackUrl(), apiKey, secretKey }, proxied({ NODE_USE_ENV_PROXY: "1" }));
    expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
    expect(result.ok).toBe(true);
  });

  test.each([["axios"], ["fetch"]])("with the opt-in, a keyed %s request goes direct under NODE_USE_ENV_PROXY=1", async (kind) => {
    const [apiKey, secretKey] = [marker("c7"), marker("c8")];
    const result = await child({ kind, baseUrl: targetUrl(), apiKey, secretKey }, proxied({ NODE_USE_ENV_PROXY: "1", FI_ALLOW_INSECURE_HTTP: "1" }));
    expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
    expect(result.ok).toBe(true);
  });
});

// --- a global proxy dispatcher installed by the caller -----------------------------------------------------------
// The runtime's fetch reads its dispatcher from the main context, so these cases run in a separate process.

const undiciDir = process.env.FI_TEST_UNDICI;
const underUndici = undiciDir ? describe : describe.skip;

underUndici("platform client under a global ProxyAgent", () => {
  jest.setTimeout(90_000);

  const installed = (extra: Record<string, unknown>) => ({ kind: "fetch", undici: undiciDir, proxyAgent: proxyUrl(), ...extra });

  test("a bearer token in the default headers", async () => {
    const token = marker("u1");
    const result = await child(installed({ baseUrl: targetUrl(), apiKey: "x", secretKey: "y", defaultHeaders: { Authorization: `Bearer ${token}` } }), {});
    expectQuiet([token]);
    expect(result).toEqual({ ok: false, code: CODE });
  });

  test("the client keys", async () => {
    const [apiKey, secretKey] = [marker("u2"), marker("u3")];
    const result = await child(installed({ baseUrl: targetUrl(), apiKey, secretKey }), {});
    expectQuiet([apiKey, secretKey]);
    expect(result).toEqual({ ok: false, code: CODE });
  });

  test("with the opt-in, the request does not go through the proxy dispatcher", async () => {
    const [apiKey, secretKey] = [marker("u4"), marker("u5")];
    await child(installed({ baseUrl: targetUrl(), apiKey, secretKey, allowInsecureHttp: true }), {});
    expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
  });

  test("a loopback host is sent directly", async () => {
    const [apiKey, secretKey] = [marker("u6"), marker("u7")];
    const result = await child(installed({ baseUrl: loopbackUrl(), apiKey, secretKey }), {});
    expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
    expect(result.ok).toBe(true);
  });
});

describe("axios sender: Basic credentials that axios derives when it sends the request make it keyed", () => {
  const basic = (user: string, password: string) => Buffer.from(`${user}:${password}`).toString("base64");

  /** Under the proxy variables, `run` is refused with the code, and no sink sees a connection or a credential byte. */
  async function expectQuietRefusal(run: () => Promise<unknown>, markers: string[]): Promise<void> {
    const failed = await withProxyEnv(() => expectRefusal(run).then(() => undefined, (e: unknown) => e));
    expectQuiet(markers);
    if (failed !== undefined) throw failed;
  }

  test("user and password in the base URL", async () => {
    const password = marker("ub");
    const client = axiosClient(`http://u:${password}@${SHIM_HOST}:${target.port}`);
    await expectQuietRefusal(() => get(client), [password, basic("u", password)]);
  });

  test("user and password in the per-call url", async () => {
    const password = marker("uc");
    const client = axiosClient(targetUrl());
    const run = () => client.request({ method: "GET", url: `http://u:${password}@${SHIM_HOST}:${target.port}/v1/probe` } as any);
    await expectQuietRefusal(run, [password, basic("u", password)]);
  });

  test("the auth option in the instance defaults", async () => {
    const password = marker("ud");
    const client = axiosClient(targetUrl());
    (client as any)._axiosInstance.defaults.auth = { username: "u", password };
    await expectQuietRefusal(() => get(client), [password, basic("u", password)]);
  });

  test("user and password in a loopback base URL are sent directly, whatever the proxy variables say", async () => {
    const password = marker("ul");
    const encoded = basic("u", password);
    await withProxyEnv(() => get(axiosClient(`http://u:${password}@127.0.0.1:${target.port}`)).catch(() => undefined));
    expect({ proxyBytes: proxy.count([password, encoded]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([encoded])).toBeGreaterThan(0);
  });
});

describe("an Authorization header of any scheme makes a request keyed", () => {
  jest.setTimeout(90_000);

  const schemes = ["Token", "Custom"];
  // The platform client requires its own key and secret; blank ones put no key on the wire, so the Authorization
  // header is the only credential of the request.
  const blank = { apiKey: " ", secretKey: " " };

  /** Run `run` under the proxy variables and return what it rejected with (undefined when it resolved). */
  const outcome = (run: () => Promise<unknown>) =>
    withProxyEnv(() =>
      run().then(
        () => undefined,
        (e: unknown) => e,
      ),
    );

  const expectCode = (error: unknown) => {
    expect(error).toBeInstanceOf(Error);
    expect((error as { code?: string }).code).toBe(CODE);
  };

  test.each(schemes)("axios sender, client default headers, Authorization %s: refused for a plain-http host that is not loopback", async (scheme) => {
    const key = marker("as1");
    const error = await outcome(() => get(axiosClient(targetUrl(), { defaultHeaders: { Authorization: `${scheme} ${key}` } })));
    expectQuiet([key]);
    expectCode(error);
  });

  test.each(schemes)("axios sender, per-call headers, Authorization %s: refused for a plain-http host that is not loopback", async (scheme) => {
    const key = marker("as2");
    const error = await outcome(() => get(axiosClient(targetUrl()), { Authorization: `${scheme} ${key}` }));
    expectQuiet([key]);
    expectCode(error);
  });

  test.each(schemes)("platform client, default headers, Authorization %s: refused for a plain-http host that is not loopback", async (scheme) => {
    const key = marker("as3");
    const error = await outcome(() => probe(platform(targetUrl(), { ...blank, defaultHeaders: { Authorization: `${scheme} ${key}` } })));
    expectQuiet([key]);
    expectCode(error);
  });

  test("axios sender, Authorization Token to a loopback host: sent directly, whatever the proxy variables say", async () => {
    const key = marker("as4");
    await outcome(() => get(axiosClient(loopbackUrl(), { defaultHeaders: { Authorization: `Token ${key}` } })));
    expect({ proxyBytes: proxy.count([key]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });

  (undiciDir ? test : test.skip)("platform client, Authorization Token to a loopback host: sent directly, whatever the global dispatcher is", async () => {
    const key = marker("as5");
    const spec = { kind: "fetch", undici: undiciDir, proxyAgent: proxyUrl(), baseUrl: loopbackUrl(), ...blank, defaultHeaders: { Authorization: `Token ${key}` } };
    await child(spec, { HTTP_PROXY: proxyUrl(), HTTPS_PROXY: proxyUrl(), NO_PROXY: "" });
    expect({ proxyBytes: proxy.count([key]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });
});

describe("axios sender: a redirect from a loopback host to another plain-http host", () => {
  /** A raw listener that answers every request with a redirect to `location` and counts the requests it reads. */
  async function redirector(location: string): Promise<{ url: string; requests(): number; close(): Promise<void> }> {
    const chunks: string[] = [];
    const sockets = new Set<net.Socket>();
    const server = net.createServer((socket) => {
      sockets.add(socket);
      socket.on("close", () => sockets.delete(socket));
      socket.on("error", () => undefined);
      let head = "";
      socket.on("data", (data) => {
        const text = data.toString("latin1");
        chunks.push(text);
        head += text;
        while (head.includes("\r\n\r\n")) {
          head = head.slice(head.indexOf("\r\n\r\n") + 4);
          socket.write(`HTTP/1.1 302 Found\r\nLocation: ${location}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n`);
          socket.end();
        }
      });
    });
    await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
    return {
      url: `http://127.0.0.1:${(server.address() as net.AddressInfo).port}`,
      requests: () => (chunks.join("").match(/^[A-Z]+ \S+ HTTP\/1\.[01]\r$/gm) ?? []).length,
      close: () =>
        new Promise<void>((resolve) => {
          for (const socket of sockets) socket.destroy();
          server.close(() => resolve());
        }),
    };
  }

  test.each([
    ["without proxy variables", false],
    ["with proxy variables", true],
  ])("%s: the request rejects with the code, the first hop is sent once and the redirect target sees nothing", async (_name, proxied) => {
    const key = marker("axf");
    const first = await redirector(`${targetUrl()}/x`);
    try {
      const client = axiosClient(first.url, { retryAttempts: 3, retryDelay: 50, defaultHeaders: { "X-Api-Key": key } });
      await withProxyEnv(() => expectRefusal(() => get(client)), {}, proxied as boolean);
      expect(first.requests()).toBe(1);
      expectQuiet([key]);
    } finally {
      await first.close();
    }
  });
});

describe("axios sender: a key added after the client's own request step is judged when the request is sent", () => {
  jest.setTimeout(90_000);

  type AddKey = (client: HttpClient, key: string) => void;

  const additions: Array<[string, AddKey]> = [
    [
      "an interceptor that runs after the client's own",
      (client, key) => {
        (client as any)._axiosInstance.interceptors.request.handlers.unshift({
          fulfilled: (cfg: any) => {
            cfg.headers["X-Api-Key"] = key;
            return cfg;
          },
          rejected: undefined,
          synchronous: false,
          runWhen: null,
        });
      },
    ],
    [
      "a request transform appended to the instance defaults",
      (client, key) => {
        const defaults = (client as any)._axiosInstance.defaults;
        const base = Array.isArray(defaults.transformRequest) ? defaults.transformRequest : [defaults.transformRequest];
        defaults.transformRequest = [
          ...base,
          (data: unknown, headers: any) => {
            headers["X-Api-Key"] = key;
            return data;
          },
        ];
      },
    ],
    [
      "a wrapper around the instance adapter",
      (client, key) => {
        const defaults = (client as any)._axiosInstance.defaults;
        const base = defaults.adapter;
        defaults.adapter = (config: any) => {
          config.headers["X-Api-Key"] = key;
          return (axios as any).getAdapter(base)(config);
        };
      },
    ],
    [
      "a wrapper around the http adapter",
      (client, key) => {
        const http = (axios as any).getAdapter("http");
        (client as any)._axiosInstance.defaults.adapter = (config: any) => {
          config.headers["X-Api-Key"] = key;
          return http(config);
        };
      },
    ],
  ];

  test.each(additions.map(([name]) => name))("%s: a plain-http host that is not loopback is refused", async (name) => {
    const add = additions.find(([n]) => n === name)![1];
    const key = marker("ka");
    const client = axiosClient(targetUrl());
    add(client, key);
    await withProxyEnv(() => expectRefusal(() => get(client)));
    expectQuiet([key]);
  });

  test.each(additions.map(([name]) => name))("%s: a loopback host is sent directly, not through the proxy variables", async (name) => {
    const add = additions.find(([n]) => n === name)![1];
    const key = marker("kb");
    const client = axiosClient(loopbackUrl());
    add(client, key);
    await withProxyEnv(() => get(client).catch(() => undefined));
    expect({ proxyBytes: proxy.count([key]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([key])).toBeGreaterThan(0);
  });

  // axios.defaults.adapter = "fetch" is set in the child before the client is made.
  const proxiedEnv = (extra: Record<string, string> = {}) => ({ HTTP_PROXY: proxyUrl(), HTTPS_PROXY: proxyUrl(), NO_PROXY: "", ...extra });

  underUndici("with the fetch adapter as the axios default, under a global ProxyAgent", () => {
    test("a keyed request to a loopback host is sent directly", async () => {
      const [apiKey, secretKey] = [marker("kc"), marker("kd")];
      const result = await child({ kind: "axios", axiosAdapter: "fetch", undici: undiciDir, proxyAgent: proxyUrl(), baseUrl: loopbackUrl(), apiKey, secretKey }, {});
      expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
      expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
      expect(result.ok).toBe(true);
    });

    test("a keyed request to a plain-http host that is not loopback is refused", async () => {
      const [apiKey, secretKey] = [marker("ke"), marker("kf")];
      const result = await child({ kind: "axios", axiosAdapter: "fetch", undici: undiciDir, proxyAgent: proxyUrl(), baseUrl: targetUrl(), apiKey, secretKey }, {});
      expectQuiet([apiKey, secretKey]);
      expect(result).toEqual({ ok: false, code: CODE });
    });
  });

  describe("with the fetch adapter as the axios default, under NODE_USE_ENV_PROXY=1", () => {
    test("a keyed request to a loopback host is sent directly", async () => {
      const [apiKey, secretKey] = [marker("kg"), marker("kh")];
      const result = await child({ kind: "axios", axiosAdapter: "fetch", baseUrl: loopbackUrl(), apiKey, secretKey }, proxiedEnv({ NODE_USE_ENV_PROXY: "1" }));
      expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
      expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
      expect(result.ok).toBe(true);
    });

    test("a keyed request to a plain-http host that is not loopback is refused", async () => {
      const [apiKey, secretKey] = [marker("ki"), marker("kj")];
      const result = await child({ kind: "axios", axiosAdapter: "fetch", baseUrl: targetUrl(), apiKey, secretKey }, proxiedEnv({ NODE_USE_ENV_PROXY: "1" }));
      expectQuiet([apiKey, secretKey]);
      expect(result).toEqual({ ok: false, code: CODE });
    });
  });
});

underUndici("platform client under a global fetch wrapper that sends through a proxy", () => {
  jest.setTimeout(90_000);

  // The wrapper drops the dispatcher it is given and sends every request through a ProxyAgent to the proxy sink.
  const wrapped = (fetchWrapper: string, extra: Record<string, unknown>) => ({ kind: "fetch", undici: undiciDir, proxyAgent: proxyUrl(), fetchWrapper, ...extra });

  describe.each([
    ["installed after the SDK is imported", "after-import"],
    ["installed before the SDK is imported", "before-import"],
  ])("wrapper %s", (_label, fetchWrapper) => {
    test("a keyed request to a loopback host is sent directly, not through the wrapper", async () => {
      const [apiKey, secretKey] = [marker("w1"), marker("w2")];
      const result = await child(wrapped(fetchWrapper, { baseUrl: loopbackUrl(), apiKey, secretKey }), {});
      expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
      expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
      expect(result.ok).toBe(true);
    });

    test("with the opt-in, a keyed request to another plain-http host is sent directly, not through the wrapper", async () => {
      const [apiKey, secretKey] = [marker("w3"), marker("w4")];
      const result = await child(wrapped(fetchWrapper, { baseUrl: targetUrl(), apiKey, secretKey, allowInsecureHttp: true }), {});
      expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
      expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
      expect(result.ok).toBe(true);
    });
  });
});

underUndici("platform client: a sent keyed plain-http request goes direct whatever the global dispatcher, and the process exits promptly", () => {
  jest.setTimeout(90_000);

  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const undici: any = require(undiciDir as string);
  // A composed dispatcher needs Dispatcher.prototype.compose; an undici version without it skips those cases.
  const composeAvailable = typeof undici.Agent?.prototype?.compose === "function";
  const whereCases = ["loopback", "opt-in"];
  const plainKinds = ["named-agent", "proxy-wrapped-agent", "pool"].flatMap((kind) => whereCases.map((where) => ({ kind, where })));
  const composedKinds = ["compose-proxy", "composed-pool"].flatMap((kind) => whereCases.map((where) => ({ kind, where })));

  const spec = (kind: string, where: string, apiKey: string, secretKey: string) => ({
    kind: "fetch",
    ...(where === "loopback" ? { baseUrl: loopbackUrl() } : { baseUrl: targetUrl(), allowInsecureHttp: true }),
    apiKey,
    secretKey,
    undici: undiciDir,
    proxyAgent: proxyUrl(),
    dispatcher: kind,
  });

  async function expectDirect(kind: string, where: string): Promise<void> {
    const [apiKey, secretKey] = [marker("gd"), marker("ge")];
    const result = await child(spec(kind, where, apiKey, secretKey), {});
    expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
    expect(result.ok).toBe(true);
  }

  test.each(plainKinds)("global dispatcher $kind: a keyed request ($where) reaches the destination directly, none of it at the proxy", async ({ kind, where }) => {
    await expectDirect(kind, where);
  });

  (composeAvailable ? test.each(composedKinds) : test.skip.each(composedKinds))(
    "global dispatcher $kind: a keyed request ($where) reaches the destination directly, none of it at the proxy",
    async ({ kind, where }) => {
      await expectDirect(kind, where);
    },
  );

  test.each([["fetch"], ["axios"]])("pin: a process that made one direct keyed %s request to a loopback host exits within 1500 ms of printing its result", async (kind) => {
    const [apiKey, secretKey] = [marker("gx"), marker("gy")];
    const { result, exitMs } = await timedChild({ kind, baseUrl: loopbackUrl(), apiKey, secretKey }, {});
    expect(result.ok).toBe(true);
    expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
    expect(exitMs).toBeLessThan(1500);
  });

  test("under a global dispatcher named Agent that proxies, a process that made one keyed loopback request sends it directly and exits within 1500 ms", async () => {
    const [apiKey, secretKey] = [marker("gz"), marker("gw")];
    const { result, exitMs } = await timedChild(spec("named-agent", "loopback", apiKey, secretKey), {});
    expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(result.ok).toBe(true);
    expect(exitMs).toBeLessThan(1500);
  });

  describe("pin: a caller-supplied fetch", () => {
    const callerFetch = () => {
      const calls: Array<{ url: string; init: RequestInit }> = [];
      const fetch: FetchLike = async (url, init) => {
        calls.push({ url, init });
        return new Response(REPLY_BODY, { status: 200, headers: { "content-type": "application/json" } });
      };
      return { calls, fetch };
    };

    test("pin: a keyed loopback request is passed to the caller's fetch once, with no dispatcher in its init", async () => {
      const { calls, fetch } = callerFetch();
      await probe(platform(loopbackUrl(), { fetch, apiKey: marker("gf") }));
      expect(calls).toHaveLength(1);
      expect(Object.prototype.hasOwnProperty.call(calls[0].init, "dispatcher")).toBe(false);
    });

    test("pin: a keyed non-loopback plain-http request is refused even with allowInsecureHttp: true, and the caller's fetch is not called", async () => {
      const { calls, fetch } = callerFetch();
      const apiKey = marker("gg");
      await expectRefusal(() => probe(platform(targetUrl(), { fetch, apiKey, allowInsecureHttp: true })));
      expect(calls).toEqual([]);
      expectQuiet([apiKey]);
    });
  });
});

describe("platform client: a process-wide wrapper of http.request does not choose the route of a direct request", () => {
  jest.setTimeout(90_000);

  const forced = (extra: Record<string, unknown>) => ({ kind: "fetch", forcedHttpAgent: true, proxyAgent: proxyUrl(), ...extra });

  test("a keyed request to a loopback host reaches it directly, none of it at the proxy", async () => {
    const [apiKey, secretKey] = [marker("g1"), marker("g2")];
    const result = await child(forced({ baseUrl: loopbackUrl(), apiKey, secretKey }), {});
    expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
    expect(result.ok).toBe(true);
  });

  test("with the opt-in, a keyed request to another plain-http host reaches it directly, none of it at the proxy", async () => {
    const [apiKey, secretKey] = [marker("g3"), marker("g4")];
    const result = await child(forced({ baseUrl: targetUrl(), apiKey, secretKey, allowInsecureHttp: true }), {});
    expect({ proxyBytes: proxy.count([apiKey, secretKey]), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    expect(target.count([apiKey, secretKey])).toBeGreaterThan(0);
    expect(result.ok).toBe(true);
  });

  test("a request without a key still goes through the wrapper's agent", async () => {
    // control: the wrapper is in effect for requests the plain-http rule leaves alone
    const result = await child({ kind: "probe-unkeyed", forcedHttpAgent: true, proxyAgent: proxyUrl(), baseUrl: loopbackUrl() }, {});
    expect(result.ok).toBe(true);
    expect(proxy.connections).toBe(1);
    expect(target.connections).toBe(0);
  });
});

// --- redirects of keyed requests --------------------------------------------------------------------------------
// The first request goes to an https origin on a loopback listener (a throwaway self-signed certificate made in
// beforeAll, accepted through NODE_TLS_REJECT_UNAUTHORIZED=0 while a test runs). That origin answers with a redirect.
// Expected end behaviour, hop by hop: a hop to the same origin (scheme, host and port of the first request) is followed
// with the keys; a hop to any other origin carries none of X-Api-Key, X-Secret-Key or Authorization, and a plain-http
// hop is refused with the code (no connection to that host) unless it is loopback and allowInsecureHttp is set, in
// which case it is followed without the keys.

describe("redirects of keyed requests: the key goes only to the configured origin", () => {
  jest.setTimeout(60_000);

  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const tls: typeof import("node:tls") = require("node:tls");
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const fs: typeof import("node:fs") = require("node:fs");
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const os: typeof import("node:os") = require("node:os");
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const { spawnSync }: typeof import("node:child_process") = require("node:child_process");

  /** A second name that the lookup resolves to the loopback address, so a hop to it is a hop to another host. */
  const OTHER_HOST = "guard-other.futureagi.com";
  const STATUSES = [301, 302, 303, 307, 308];
  const basic = (user: string, password: string) => Buffer.from(`${user}:${password}`).toString("base64");

  // --- a second lookup name, chained to the lookup in place when this block starts ---
  let lookupBefore: typeof dns.lookup;
  beforeAll(() => {
    lookupBefore = dns.lookup;
    (dns as any).lookup = function lookup(hostname: string, options: any, callback: any) {
      if (typeof options === "function") {
        callback = options;
        options = {};
      }
      if (String(hostname).toLowerCase() === OTHER_HOST) {
        const all = typeof options === "object" && options !== null && options.all === true;
        process.nextTick(() => (all ? callback(null, [{ address: "127.0.0.1", family: 4 }]) : callback(null, "127.0.0.1", 4)));
        return {};
      }
      return (lookupBefore as any).call(dns, hostname, options, callback);
    };
  });
  afterAll(() => {
    (dns as any).lookup = lookupBefore;
  });

  // --- a throwaway certificate ---
  let certDir = "";
  let keyPem = "";
  let certPem = "";
  beforeAll(() => {
    certDir = fs.mkdtempSync(path.join(os.tmpdir(), "fi-redirect-tls-"));
    const keyPath = path.join(certDir, "key.pem");
    const certPath = path.join(certDir, "cert.pem");
    const made = spawnSync(
      "openssl",
      ["req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes", "-keyout", keyPath, "-out", certPath, "-days", "1", "-subj", "/CN=localhost"],
      { stdio: "ignore" },
    );
    if (made.status !== 0) throw new Error("openssl could not make the test certificate");
    keyPem = fs.readFileSync(keyPath, "utf8");
    certPem = fs.readFileSync(certPath, "utf8");
  });
  afterAll(() => {
    if (certDir) fs.rmSync(certDir, { recursive: true, force: true });
  });

  // --- https listeners ---
  interface Site {
    port: number;
    connections: number;
    origin(host?: string): string;
    /** Marker bytes in everything the listener read, or only in the requests for `requestPath`. */
    count(markers: string[], requestPath?: string): number;
    /** Marker bytes in the first request the listener read (the hop to the configured origin). */
    countFirst(markers: string[]): number;
    close(): Promise<void>;
  }

  function countIn(text: string, markers: string[]): number {
    let bytes = 0;
    for (const m of markers) {
      for (let at = text.indexOf(m); at >= 0; at = text.indexOf(m, at + m.length)) bytes += m.length;
    }
    return bytes;
  }

  const okReply = () => `HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${REPLY_BODY.length}\r\nConnection: close\r\n\r\n${REPLY_BODY}`;
  const redirectReply = (status: number, location: string) => `HTTP/1.1 ${status} Redirect\r\nLocation: ${location}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n`;

  /** An https listener that records every connection and decrypted byte, and answers each request with `answer(path)`. */
  async function tlsSite(answer: (requestPath: string) => string): Promise<Site> {
    const chunks: string[] = [];
    const requests: Array<{ path: string; head: string }> = [];
    const sockets = new Set<net.Socket>();
    const state = { connections: 0 };
    const server = tls.createServer({ key: keyPem, cert: certPem }, (socket) => {
      socket.on("error", () => undefined);
      let head = "";
      let answered = false;
      socket.on("data", (data: Buffer) => {
        const text = data.toString("latin1");
        chunks.push(text);
        if (answered) return;
        head += text;
        const end = head.indexOf("\r\n\r\n");
        if (end < 0) return;
        answered = true;
        const one = head.slice(0, end);
        const requestPath = one.split(" ")[1] ?? "";
        requests.push({ path: requestPath, head: one });
        socket.end(answer(requestPath));
      });
    });
    server.on("connection", (socket: net.Socket) => {
      state.connections++;
      sockets.add(socket);
      socket.on("close", () => sockets.delete(socket));
      socket.on("error", () => undefined);
    });
    server.on("tlsClientError", () => undefined);
    await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
    const port = (server.address() as net.AddressInfo).port;
    return {
      port,
      get connections() {
        return state.connections;
      },
      origin: (host = SHIM_HOST) => `https://${host}:${port}`,
      count: (markers, requestPath) =>
        countIn(requestPath === undefined ? chunks.join("") : requests.filter((r) => r.path === requestPath).map((r) => r.head).join("\n"), markers),
      countFirst: (markers) => countIn(requests[0]?.head ?? "", markers),
      close: () =>
        new Promise<void>((resolve) => {
          for (const socket of sockets) socket.destroy();
          server.close(() => resolve());
        }),
    };
  }

  /** A site that redirects the first request (any path under /v1/probe) to `location` and answers every other path with 200. */
  const redirecting = (status: number, location: () => string) => tlsSite((requestPath) => (requestPath.startsWith("/v1/probe") ? redirectReply(status, location()) : okReply()));

  // --- running a request ---
  // Jest gives a test file its own copy of process.env, and Node's tls module reads NODE_TLS_REJECT_UNAUTHORIZED from
  // the runtime's process object, so the variable is set there (and restored after each request).
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const runtimeEnv: Record<string, string | undefined> = new (require("node:vm").Script)("process").runInThisContext().env;

  /** Run `run` with no proxy variables, no opt-in variable and the test certificate accepted; resolve to what it rejected with. */
  async function settle(run: () => Promise<any>): Promise<any> {
    const saved = runtimeEnv.NODE_TLS_REJECT_UNAUTHORIZED;
    runtimeEnv.NODE_TLS_REJECT_UNAUTHORIZED = "0";
    try {
      return await withProxyEnv(
        () =>
          run().then(
            () => undefined,
            (e: any) => e,
          ),
        {},
        false,
      );
    } finally {
      if (saved === undefined) delete runtimeEnv.NODE_TLS_REJECT_UNAUTHORIZED;
      else runtimeEnv.NODE_TLS_REJECT_UNAUTHORIZED = saved;
    }
  }

  const codeOf = (error: any) => (error instanceof Error ? ((error as { code?: string }).code ?? "(no code)") : error === undefined ? "(resolved)" : "(not an Error)");

  /** An axios HttpClient whose adapter is axios's fetch adapter (axios.defaults.adapter is "fetch" while it is made). */
  function fetchAdapterClient(baseUrl: string, config: Record<string, any> = {}): HttpClient {
    const saved = axios.defaults.adapter;
    axios.defaults.adapter = "fetch";
    try {
      return axiosClient(baseUrl, config);
    } finally {
      axios.defaults.adapter = saved;
    }
  }

  type Make = (baseUrl: string, config?: Record<string, any>) => HttpClient;
  const adapters: Array<[string, Make]> = [
    ["fetch adapter", fetchAdapterClient],
    ["default http adapter", axiosClient],
  ];
  const makerOf = (name: string) => adapters.find(([n]) => n === name)![1];

  /** One key form on its own: the header that carries it and the strings of it that can go on the wire. */
  function oneKey(form: string): { headers: Record<string, string>; markers: string[] } {
    const key = marker("rd");
    switch (form) {
      case "X-Api-Key":
        return { headers: { "X-Api-Key": key }, markers: [key] };
      case "X-Secret-Key":
        return { headers: { "X-Secret-Key": key }, markers: [key] };
      case "Authorization Bearer":
        return { headers: { Authorization: `Bearer ${key}` }, markers: [key] };
      default:
        return { headers: { Authorization: `Basic ${basic("u", key)}` }, markers: [basic("u", key), key] };
    }
  }
  const FORMS = ["X-Api-Key", "X-Secret-Key", "Authorization Bearer", "Authorization Basic"];

  /** X-Api-Key, X-Secret-Key and an Authorization header of `scheme` on one request, with the markers of each. */
  function allKeys(scheme: "Bearer" | "Basic"): { headers: Record<string, string>; markers: Record<string, string[]> } {
    const [apiKey, secretKey, auth] = [marker("ra"), marker("rs"), marker("rz")];
    const authorization = scheme === "Bearer" ? `Bearer ${auth}` : `Basic ${basic("u", auth)}`;
    return {
      headers: { "X-Api-Key": apiKey, "X-Secret-Key": secretKey, Authorization: authorization },
      markers: { apiKeyBytes: [apiKey], secretKeyBytes: [secretKey], authorizationBytes: scheme === "Bearer" ? [auth] : [basic("u", auth), auth] },
    };
  }
  const record = (pairs: Array<[string, any]>) => pairs.reduce<Record<string, any>>((acc, [name, value]) => ((acc[name] = value), acc), {});
  const bytesOf = (markers: Record<string, string[]>, count: (m: string[]) => number) => record(Object.entries(markers).map(([name, m]) => [name, count(m)]));
  const zeroOf = (markers: Record<string, string[]>) => record(Object.keys(markers).map((name) => [name, 0]));
  const reachedOf = (markers: Record<string, string[]>, count: (m: string[]) => number) => record(Object.entries(markers).map(([name, m]) => [name, count(m) > 0]));
  const allTrue = (markers: Record<string, string[]>) => record(Object.keys(markers).map((name) => [name, true]));
  const flat = (markers: Record<string, string[]>) => Object.values(markers).flat();

  /** The two cross-origin https destinations: another port on the same name, and another name on the same port. */
  const DESTINATIONS = ["another port", "another host name"];

  describe("axios HttpClient with the fetch adapter", () => {
    test.each(STATUSES.flatMap((status) => FORMS.map((form) => [status, form] as [number, string])))(
      "https origin answers %i with a plain-http host that is not loopback, key in %s: rejected with the code, the second host receives no connection and none of the key",
      async (status, form) => {
        const { headers, markers } = oneKey(form);
        const first = await redirecting(status, () => `http://${SHIM_HOST}:${target.port}/x`);
        try {
          const error = await settle(() => get(fetchAdapterClient(first.origin(), { defaultHeaders: headers })));
          expect({ code: codeOf(error), firstHostKeyed: first.count(markers) > 0, secondHostBytes: target.count(markers), secondHostConnections: target.connections }).toEqual({
            code: CODE,
            firstHostKeyed: true,
            secondHostBytes: 0,
            secondHostConnections: 0,
          });
        } finally {
          await first.close();
        }
      },
    );

    test("https origin answers 302 with http://127.0.0.1 (loopback), no opt-in: rejected with the code, the loopback host receives no connection and none of the key", async () => {
      const { headers, markers } = allKeys("Bearer");
      const first = await redirecting(302, () => `http://127.0.0.1:${target.port}/x`);
      try {
        const error = await settle(() => get(fetchAdapterClient(first.origin(), { defaultHeaders: headers })));
        expect({ code: codeOf(error), firstHostKeyed: first.countFirst(flat(markers)) > 0, ...bytesOf(markers, (m) => target.count(m)), secondHostConnections: target.connections }).toEqual({
          code: CODE,
          firstHostKeyed: true,
          ...zeroOf(markers),
          secondHostConnections: 0,
        });
      } finally {
        await first.close();
      }
    });

    test("https origin answers 302 with http://127.0.0.1 (loopback), allowInsecureHttp: true: followed, the loopback host receives the request and none of the key", async () => {
      const { headers, markers } = allKeys("Bearer");
      const first = await redirecting(302, () => `http://127.0.0.1:${target.port}/x`);
      try {
        const error = await settle(() => get(fetchAdapterClient(first.origin(), { allowInsecureHttp: true, defaultHeaders: headers })));
        expect({ code: codeOf(error), firstHostKeyed: first.countFirst(flat(markers)) > 0, ...bytesOf(markers, (m) => target.count(m)), secondHostReached: target.connections > 0 }).toEqual({
          code: "(resolved)",
          firstHostKeyed: true,
          ...zeroOf(markers),
          secondHostReached: true,
        });
      } finally {
        await first.close();
      }
    });
  });

  describe.each(adapters.map(([name]) => [name]))("axios HttpClient, %s", (adapterName) => {
    const make = (baseUrl: string, config?: Record<string, any>) => makerOf(adapterName)(baseUrl, config);

    test("https origin answers 302 with a plain-http host that is not loopback, X-Api-Key and X-Secret-Key: rejected with the code, the second host receives no connection and none of the keys", async () => {
      const [apiKey, secretKey] = [marker("rk"), marker("rl")];
      const first = await redirecting(302, () => `http://${SHIM_HOST}:${target.port}/x`);
      try {
        const error = await settle(() => get(make(first.origin(), { defaultHeaders: { "X-Api-Key": apiKey, "X-Secret-Key": secretKey } })));
        expect({ code: codeOf(error), firstHostKeyed: first.countFirst([apiKey, secretKey]) > 0, secondHostBytes: target.count([apiKey, secretKey]), secondHostConnections: target.connections }).toEqual({
          code: CODE,
          firstHostKeyed: true,
          secondHostBytes: 0,
          secondHostConnections: 0,
        });
      } finally {
        await first.close();
      }
    });

    test.each(DESTINATIONS.flatMap((where) => (["Bearer", "Basic"] as const).map((scheme) => [where, scheme] as [string, "Bearer" | "Basic"])))(
      "https origin answers 302 with an https URL on %s, X-Api-Key, X-Secret-Key and Authorization %s: the second host receives none of the keys",
      async (where, scheme) => {
        const { headers, markers } = allKeys(scheme);
        const second = await tlsSite(() => okReply());
        let first: Site | undefined;
        try {
          first = await redirecting(302, () => (where === "another port" ? `${second.origin()}/x` : `${first!.origin(OTHER_HOST)}/x`));
          await settle(() => get(make(first!.origin(), { defaultHeaders: headers })));
          // The second host is the other listener, or the same listener addressed by the other name (its /x requests).
          const atSecond = (m: string[]) => (where === "another port" ? second.count(m) : first!.count(m, "/x"));
          expect({ firstHostKeyed: first!.countFirst(flat(markers)) > 0, ...bytesOf(markers, atSecond) }).toEqual({ firstHostKeyed: true, ...zeroOf(markers) });
        } finally {
          await first?.close();
          await second.close();
        }
      },
    );

    test("https origin answers 302 with a path on the same origin: the request resolves and every key reaches that path", async () => {
      const { headers, markers } = allKeys("Bearer");
      let first: Site | undefined;
      try {
        first = await redirecting(302, () => `${first!.origin()}/x`);
        const error = await settle(() => get(make(first!.origin(), { defaultHeaders: headers })));
        expect({ code: codeOf(error), ...reachedOf(markers, (m) => first!.count(m, "/x")) }).toEqual({ code: "(resolved)", ...allTrue(markers) });
      } finally {
        await first?.close();
      }
    });
  });

  describe("platform client (follows only redirects within its own origin)", () => {
    const keys = () => {
      const [apiKey, secretKey, token] = [marker("pv"), marker("pw"), marker("px")];
      return {
        config: { apiKey, secretKey, defaultHeaders: { Authorization: `Bearer ${token}` } },
        markers: { apiKeyBytes: [apiKey], secretKeyBytes: [secretKey], authorizationBytes: [token] },
      };
    };

    test("https origin answers 302 with a plain-http host that is not loopback: rejected, the second host receives no connection and none of the keys", async () => {
      const { config, markers } = keys();
      const first = await redirecting(302, () => `http://${SHIM_HOST}:${target.port}/x`);
      try {
        const error = await settle(() => probe(platform(first.origin(), config)));
        expect({ rejected: error instanceof Error, firstHostKeyed: first.countFirst(flat(markers)) > 0, ...bytesOf(markers, (m) => target.count(m)), secondHostConnections: target.connections }).toEqual({
          rejected: true,
          firstHostKeyed: true,
          ...zeroOf(markers),
          secondHostConnections: 0,
        });
      } finally {
        await first.close();
      }
    });

    test.each(DESTINATIONS)("https origin answers 302 with an https URL on %s: the second host receives none of the keys", async (where) => {
      const { config, markers } = keys();
      const second = await tlsSite(() => okReply());
      let first: Site | undefined;
      try {
        first = await redirecting(302, () => (where === "another port" ? `${second.origin()}/x` : `${first!.origin(OTHER_HOST)}/x`));
        await settle(() => probe(platform(first!.origin(), config)));
        const atSecond = (m: string[]) => (where === "another port" ? second.count(m) : first!.count(m, "/x"));
        expect({ firstHostKeyed: first!.countFirst(flat(markers)) > 0, ...bytesOf(markers, atSecond) }).toEqual({ firstHostKeyed: true, ...zeroOf(markers) });
      } finally {
        await first?.close();
        await second.close();
      }
    });

    test("https origin answers 302 with a path on the same origin: the request resolves and every key reaches that path", async () => {
      const { config, markers } = keys();
      let first: Site | undefined;
      try {
        first = await redirecting(302, () => `${first!.origin()}/x`);
        const error = await settle(() => probe(platform(first!.origin(), config)));
        expect({ code: codeOf(error), ...reachedOf(markers, (m) => first!.count(m, "/x")) }).toEqual({ code: "(resolved)", ...allTrue(markers) });
      } finally {
        await first?.close();
      }
    });
  });

  describe("redirect chains, an upgrade to https and a streamed body", () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const http: typeof import("node:http") = require("node:http");
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const FormDataStream = require("form-data");

    interface PlainSite {
      origin: string;
      requests: Array<{ method: string; path: string; head: string; body: string }>;
      close(): Promise<void>;
    }

    /** A plain-http loopback listener that answers each request with `answer(method, path)` as [status, headers]. */
    async function plainSite(answer: (method: string, requestPath: string) => [number, Record<string, string>]): Promise<PlainSite> {
      const requests: PlainSite["requests"] = [];
      const server = http.createServer((req, res) => {
        const chunks: Buffer[] = [];
        req.on("data", (chunk: Buffer) => chunks.push(chunk));
        req.on("end", () => {
          const head = Object.entries(req.headers).map(([name, value]) => `${name}: ${String(value)}`).join("\n");
          requests.push({ method: req.method ?? "", path: req.url ?? "", head, body: Buffer.concat(chunks).toString("latin1") });
          const [status, headers] = answer(req.method ?? "", req.url ?? "");
          res.writeHead(status, { "Content-Type": "application/json", Connection: "close", ...headers });
          res.end(status === 200 ? REPLY_BODY : "");
        });
      });
      await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
      return {
        origin: `http://127.0.0.1:${(server.address() as net.AddressInfo).port}`,
        requests,
        close: () =>
          new Promise<void>((resolve) => {
            server.closeAllConnections();
            server.close(() => resolve());
          }),
      };
    }

    test.each(adapters.map(([name]) => [name]))(
      "%s: https origin, then another https origin, then a plain-http host that is not loopback: rejected with the code, the plain-http host receives no connection",
      async (name) => {
        const { headers, markers } = allKeys("Bearer");
        const second = await tlsSite(() => redirectReply(302, `http://${SHIM_HOST}:${target.port}/z`));
        const first = await redirecting(302, () => `${second.origin(OTHER_HOST)}/y`);
        try {
          const error = await settle(() => get(makerOf(name)(first.origin(), { defaultHeaders: headers })));
          expect({
            code: codeOf(error),
            firstHostKeyed: first.countFirst(flat(markers)) > 0,
            secondHostReached: second.connections > 0,
            secondHostBytes: second.count(flat(markers)),
            plainHostConnections: target.connections,
            plainHostBytes: target.count(flat(markers)),
          }).toEqual({ code: CODE, firstHostKeyed: true, secondHostReached: true, secondHostBytes: 0, plainHostConnections: 0, plainHostBytes: 0 });
        } finally {
          await first.close();
          await second.close();
        }
      },
    );

    test.each(adapters.map(([name]) => [name]))(
      "%s: a keyed request to a loopback http host answered with 301 to https on another port: followed, the https host receives the request and none of the key",
      async (name) => {
        const { headers, markers } = allKeys("Bearer");
        const secure = await tlsSite(() => okReply());
        const first = await plainSite(() => [301, { Location: `https://127.0.0.1:${secure.port}/x` }]);
        try {
          const error = await settle(() => get(makerOf(name)(first.origin, { defaultHeaders: headers })));
          expect({
            code: codeOf(error),
            firstHostKeyed: first.requests.length > 0 && countIn(first.requests[0].head, flat(markers)) > 0,
            secureHostReached: secure.connections > 0,
            secureHostBytes: secure.count(flat(markers)),
          }).toEqual({ code: "(resolved)", firstHostKeyed: true, secureHostReached: true, secureHostBytes: 0 });
        } finally {
          await first.close();
          await secure.close();
        }
      },
    );

    test.each([307, 308].flatMap((status) => adapters.map(([name]) => [status, name] as [number, string])))(
      "a streamed form body answered with %i to a path on the same origin (%s): sent again to that path with the key",
      async (status, name) => {
        const key = marker("rb");
        const payload = marker("body");
        const site = await plainSite((_method, requestPath) => (requestPath.startsWith("/v1/upload") ? [status, { Location: "/v1/done" }] : [200, {}]));
        try {
          const file = path.join(certDir, `rows-${status}-${name.split(" ")[0]}.txt`);
          fs.writeFileSync(file, `${payload}\n`.repeat(64));
          const form = new FormDataStream();
          form.append("file", fs.createReadStream(file));
          form.append("name", "rows");
          const client = makerOf(name)(site.origin, { defaultHeaders: { "X-Api-Key": key } });
          const error = await settle(() => client.request({ method: "POST", url: "/v1/upload", data: form, headers: form.getHeaders() } as any));
          const upload = site.requests.filter((r) => r.path === "/v1/upload");
          const done = site.requests.filter((r) => r.path === "/v1/done");
          expect({
            code: codeOf(error),
            uploadBodyHasPayload: upload.length > 0 && upload[0].body.includes(payload),
            donePosts: done.filter((r) => r.method === "POST").length,
            doneKeyed: done.length > 0 && countIn(done[0].head, [key]) > 0,
            doneBodyHasPayload: done.length > 0 && done[0].body.includes(payload),
          }).toEqual({ code: "(resolved)", uploadBodyHasPayload: true, donePosts: 1, doneKeyed: true, doneBodyHasPayload: true });
        } finally {
          await site.close();
        }
      },
    );
  });
});

describe("axios sender: a process-wide wrapper of http.request and http.get does not choose the route of a direct keyed request", () => {
  jest.setTimeout(90_000);

  // The wrapper is installed in the child before the SDK is imported (globalAgentWrapper in support/child-request.mts).
  // It replaces http.request and http.get with functions that copy the options and put their own agent in them,
  // whatever agent the caller gave (the call shape of global-agent under forceGlobalAgent); that agent sends every
  // request to the proxy sink in absolute form.
  // For a keyed request the plain-http rule sends directly, either result is accepted: the request reaches the
  // target with the SDK's own agent, or it is refused with the code. In both, the proxy sink sees no connection and
  // none of the key.
  const forced = (extra: Record<string, any>) => ({ globalAgentWrapper: true, proxyAgent: proxyUrl(), ...extra });

  function expectDirectOrRefusal(result: { ok: boolean; code: string | null }, markers: string[]): void {
    expect({ proxyBytes: proxy.count(markers), proxyConnections: proxy.connections }).toEqual({ proxyBytes: 0, proxyConnections: 0 });
    if (result.ok) expect(target.count(markers)).toBeGreaterThan(0);
    else expect(result).toEqual({ ok: false, code: CODE });
  }

  test("a keyed loopback request (client key and secret) reaches the target directly or is refused, and the proxy sees no connection and none of the key", async () => {
    const [apiKey, secretKey] = [marker("sw1"), marker("sw2")];
    const result = await child(forced({ kind: "axios", baseUrl: loopbackUrl(), apiKey, secretKey }), {});
    expectDirectOrRefusal(result, [apiKey, secretKey]);
  });

  test("with allowInsecureHttp: true, a keyed request to another plain-http host reaches it directly or is refused, and the proxy sees none of the key", async () => {
    const [apiKey, secretKey] = [marker("sw3"), marker("sw4")];
    const result = await child(forced({ kind: "axios", baseUrl: targetUrl(), apiKey, secretKey, allowInsecureHttp: true }), {});
    expectDirectOrRefusal(result, [apiKey, secretKey]);
  });

  test("a loopback request with an Authorization Bearer header reaches the target directly or is refused, and the proxy sees no connection and none of the token", async () => {
    const token = marker("sw5");
    const result = await child(forced({ kind: "axios-http-client", baseUrl: loopbackUrl(), apiKey: "", secretKey: "", defaultHeaders: { Authorization: `Bearer ${token}` } }), {});
    expectDirectOrRefusal(result, [token]);
  });

  test("an axios request without a key goes through the wrapper's agent", async () => {
    // control: the wrapper is in effect for requests the plain-http rule leaves alone
    const result = await child(forced({ kind: "axios-http-client", baseUrl: loopbackUrl(), apiKey: "", secretKey: "" }), {});
    expect(result.ok).toBe(true);
    expect({ proxyConnections: proxy.connections, targetConnections: target.connections }).toEqual({ proxyConnections: 1, targetConnections: 0 });
  });

  test("in this process: a keyed loopback request reaches the target directly or is refused, and the proxy sees no connection and none of the key", async () => {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const http: any = require("node:http");
    const via = new URL(proxyUrl());
    class ForcedProxyAgent extends http.Agent {
      addRequest(request: any, options: any): void {
        request.path = `http://${options.host}:${options.port}${request.path}`;
        super.addRequest(request, { ...options, host: via.hostname, port: Number(via.port) });
      }
    }
    const agent = new ForcedProxyAgent();
    const originals = { request: http.request, get: http.get };
    // the call shape of global-agent under forceGlobalAgent: the options are copied, the agent set, the callback kept
    for (const name of ["request", "get"] as const) {
      const original = originals[name];
      http[name] = function (...args: any[]) {
        if (typeof args[0] === "string" || args[0] instanceof URL) {
          const [options, callback] = typeof args[1] === "function" ? [{}, args[1]] : [{ ...(args[1] ?? {}) }, args[2]];
          return original.call(http, args[0], { ...options, agent }, callback);
        }
        return original.call(http, { ...(args[0] ?? {}), agent }, args[1]);
      };
    }
    const [apiKey, secretKey] = [marker("sw6"), marker("sw7")];
    let result: { ok: boolean; code: string | null };
    try {
      const client = new APIKeyAuth({ fiApiKey: apiKey, fiSecretKey: secretKey, baseUrl: loopbackUrl(), retryAttempts: 1, timeout: 5000 });
      result = await get(client).then(
        () => ({ ok: true, code: null }),
        (e: any) => ({ ok: false, code: e?.code ?? null }),
      );
    } finally {
      http.request = originals.request;
      http.get = originals.get;
      agent.destroy();
    }
    expectDirectOrRefusal(result, [apiKey, secretKey]);
  });
});

// --- two or more clients in one process ---------------------------------------------------------------------
// Each client is built with its own planted marker keys. Every sender (the axios clients, the platform client, the
// KB and upload helpers, the static helpers that take options) must put only the keys of the client that
// makes the request on the wire: a request from client A carries A's keys and none of B's, whichever client was built
// or used last.

interface TenantKeys {
  apiKey: string;
  secretKey: string;
}

const tenantKeys = (first: string, second: string): TenantKeys => ({ apiKey: marker(first), secretKey: marker(second) });
const keysOf = (keys: TenantKeys) => [keys.apiKey, keys.secretKey];

/** A loopback listener like `sink()` that keeps the bytes of each connection apart, so a request can be told from
 * the others by its connection (every reply closes the connection). */
interface ConnSink {
  port: number;
  url: string;
  connections: string[];
  close(): Promise<void>;
}

async function connSink(): Promise<ConnSink> {
  const connections: string[] = [];
  const sockets = new Set<net.Socket>();
  const server = net.createServer((socket) => {
    const at = connections.push("") - 1;
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
    socket.on("error", () => undefined);
    let head = "";
    let replied = false;
    socket.on("data", (data) => {
      const text = data.toString("latin1");
      connections[at] += text;
      if (replied) return;
      head += text;
      if (!head.includes("\r\n\r\n")) return;
      replied = true;
      socket.end(`HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: ${REPLY_BODY.length}\r\nConnection: close\r\n\r\n${REPLY_BODY}`);
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const port = (server.address() as net.AddressInfo).port;
  return {
    port,
    url: `http://127.0.0.1:${port}`,
    connections,
    close: () =>
      new Promise<void>((resolve) => {
        for (const socket of sockets) socket.destroy();
        server.close(() => resolve());
      }),
  };
}

/** Marker bytes in `text`, counted the way `sink().count` counts them. */
function markerBytes(text: string, markers: string[]): number {
  let bytes = 0;
  for (const value of markers) {
    for (let at = text.indexOf(value); at >= 0; at = text.indexOf(value, at + value.length)) bytes += value.length;
  }
  return bytes;
}

type Send = () => Promise<any>;

/** One way to send a request: `make` builds the client (or binds the helper's options) for `keys` and `baseUrl`. */
interface Sender {
  name: string;
  make(keys: TenantKeys, baseUrl: string, scratchDir: string): Promise<Send>;
}

const axiosOptions = (keys: TenantKeys, baseUrl: string) => ({ fiApiKey: keys.apiKey, fiSecretKey: keys.secretKey, fiBaseUrl: baseUrl, retryAttempts: 1, timeout: 5000 });

const SENDERS: Sender[] = [
  {
    name: "APIKeyAuth",
    make: async (keys, baseUrl) => {
      const client = new APIKeyAuth({ fiApiKey: keys.apiKey, fiSecretKey: keys.secretKey, baseUrl, retryAttempts: 1, timeout: 5000 });
      return () => get(client);
    },
  },
  {
    name: "HttpClient with key headers",
    make: async (keys, baseUrl) => {
      const client = axiosClient(baseUrl, { defaultHeaders: { "X-Api-Key": keys.apiKey, "X-Secret-Key": keys.secretKey } });
      return () => get(client);
    },
  },
  {
    name: "platform Client",
    make: async (keys, baseUrl) => {
      const client = platform(baseUrl, { apiKey: keys.apiKey, secretKey: keys.secretKey });
      return () => probe(client);
    },
  },
  {
    name: "platform KB resource create",
    make: async (keys, baseUrl) => {
      const client = platform(baseUrl, { apiKey: keys.apiKey, secretKey: keys.secretKey });
      return () => client.knowledgeBases.create({ name: "kb", chunk_size: 100 });
    },
  },
  {
    name: "platform file KB resource create with a file upload",
    make: async (keys, baseUrl) => {
      const client = platform(baseUrl, { apiKey: keys.apiKey, secretKey: keys.secretKey });
      return () => client.fileKnowledgeBases.create({ name: "kb", file: [{ name: "notes.txt", data: "file body" }] });
    },
  },
  {
    name: "KB client listKbs",
    make: async (keys, baseUrl) => {
      const kb = new KbClient(undefined, { fiApiKey: keys.apiKey, fiSecretKey: keys.secretKey, fiBaseUrl: baseUrl, timeout: 5000 });
      return () => kb.listKbs();
    },
  },
  {
    name: "KB client createKb with a file upload",
    make: async (keys, baseUrl, scratchDir) => {
      const file = path.join(scratchDir, `upload-${randomBytes(4).toString("hex")}.txt`);
      tenantFs.writeFileSync(file, "file body");
      const kb = new KbClient(undefined, { fiApiKey: keys.apiKey, fiSecretKey: keys.secretKey, fiBaseUrl: baseUrl, timeout: 5000 });
      return () => kb.createKb("kb", [file]);
    },
  },
  {
    name: "ProviderAPIKeyClient.listApiKeys",
    make: async (keys, baseUrl) => () => ProviderAPIKeyClient.listApiKeys({ fiApiKey: keys.apiKey, fiSecretKey: keys.secretKey, fiBaseUrl: baseUrl }),
  },
  {
    name: "Dataset.getDatasetConfig",
    make: async (keys, baseUrl) => () => Dataset.getDatasetConfig("dataset", axiosOptions(keys, baseUrl)),
  },
  {
    name: "Prompt.listTemplates",
    make: async (keys, baseUrl) => () => Prompt.listTemplates(axiosOptions(keys, baseUrl)),
  },
  {
    name: "Prompt.open",
    make: async (keys, baseUrl) => {
      const prompt = new Prompt({ name: "template", messages: [] } as any, axiosOptions(keys, baseUrl));
      return () => {
        prompt.template = { name: "template", messages: [] } as any; // open() adopts the reply as its template
        return prompt.open();
      };
    },
  },
  {
    name: "Annotation.getLabels",
    make: async (keys, baseUrl) => {
      const annotation = new Annotation({ fiApiKey: keys.apiKey, fiSecretKey: keys.secretKey, fiBaseUrl: baseUrl, timeout: 5000 });
      return () => annotation.getLabels();
    },
  },
  {
    name: "AnnotationQueue.list",
    make: async (keys, baseUrl) => {
      const queue = new AnnotationQueue(axiosOptions(keys, baseUrl));
      return () => queue.list();
    },
  },
];

const quietly = (send: Send) => send().catch(() => undefined); // only the bytes on the wire matter here

describe("each client sends its own keys", () => {
  jest.setTimeout(60_000);

  let scratchDir: string;
  let second: Sink;
  beforeAll(() => {
    scratchDir = tenantFs.mkdtempSync(path.join(tenantOs.tmpdir(), "fi-tenants-"));
  });
  afterAll(() => {
    tenantFs.rmSync(scratchDir, { recursive: true, force: true });
  });
  beforeEach(async () => {
    second = await sink();
  });
  afterEach(async () => {
    await second.close();
  });
  const secondUrl = () => `http://127.0.0.1:${second.port}`;

  test.each(SENDERS.map((sender) => [sender.name]))("%s: client A, built before client B, sends A's keys and none of B's", async (name) => {
    const sender = SENDERS.find((candidate) => candidate.name === name)!;
    const tenantA = tenantKeys("ta1", "ta2");
    const tenantB = tenantKeys("tb1", "tb2");
    const sendA = await sender.make(tenantA, loopbackUrl(), scratchDir);
    const sendB = await sender.make(tenantB, secondUrl(), scratchDir);
    // A sends, then B, then A again: a request from A carries A's keys whichever client sent last.
    await quietly(sendA);
    await quietly(sendB);
    await quietly(sendA);
    expect({ targetBytesOfA: target.count(keysOf(tenantA)) > 0, targetBytesOfB: target.count(keysOf(tenantB)) }).toEqual({ targetBytesOfA: true, targetBytesOfB: 0 });
    expect({ secondHostBytesOfB: second.count(keysOf(tenantB)) > 0, secondHostBytesOfA: second.count(keysOf(tenantA)) }).toEqual({ secondHostBytesOfB: true, secondHostBytesOfA: 0 });
    expect(target.connections).toBeGreaterThanOrEqual(2);
  });

  test.each(SENDERS.map((sender) => [sender.name]))("%s: client B, built after client A, sends B's keys and none of A's", async (name) => {
    const sender = SENDERS.find((candidate) => candidate.name === name)!;
    const tenantA = tenantKeys("ta1", "ta2");
    const tenantB = tenantKeys("tb1", "tb2");
    const sendA = await sender.make(tenantA, secondUrl(), scratchDir);
    const sendB = await sender.make(tenantB, loopbackUrl(), scratchDir);
    await quietly(sendA);
    await quietly(sendB);
    expect({ targetBytesOfB: target.count(keysOf(tenantB)) > 0, targetBytesOfA: target.count(keysOf(tenantA)) }).toEqual({ targetBytesOfB: true, targetBytesOfA: 0 });
    expect({ secondHostBytesOfA: second.count(keysOf(tenantA)) > 0, secondHostBytesOfB: second.count(keysOf(tenantB)) }).toEqual({ secondHostBytesOfA: true, secondHostBytesOfB: 0 });
  });

  describe("a client that read its keys from the environment keeps them when the environment and other clients differ", () => {
    const KEY_ENV = ["FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL"];
    let savedEnv: Map<string, string | undefined>;
    beforeEach(() => {
      savedEnv = new Map(KEY_ENV.map((name) => [name, process.env[name]]));
    });
    afterEach(() => {
      APIKeyManager.resetInstance();
      for (const [name, value] of savedEnv) {
        if (value === undefined) delete process.env[name];
        else process.env[name] = value;
      }
    });
    const useEnv = (keys: TenantKeys, baseUrl: string) => {
      process.env.FI_API_KEY = keys.apiKey;
      process.env.FI_SECRET_KEY = keys.secretKey;
      process.env.FI_BASE_URL = baseUrl;
    };

    test("APIKeyAuth from the environment sends A's keys after client B is built with B's keys", async () => {
      const tenantA = tenantKeys("ta1", "ta2");
      const tenantB = tenantKeys("tb1", "tb2");
      useEnv(tenantA, loopbackUrl());
      const clientA = new APIKeyAuth({ retryAttempts: 1, timeout: 5000 });
      useEnv(tenantB, secondUrl());
      const clientB = new APIKeyAuth({ retryAttempts: 1, timeout: 5000 });
      await quietly(() => get(clientA));
      await quietly(() => get(clientB));
      expect({ targetBytesOfA: target.count(keysOf(tenantA)) > 0, targetBytesOfB: target.count(keysOf(tenantB)) }).toEqual({ targetBytesOfA: true, targetBytesOfB: 0 });
      expect({ secondHostBytesOfB: second.count(keysOf(tenantB)) > 0, secondHostBytesOfA: second.count(keysOf(tenantA)) }).toEqual({ secondHostBytesOfB: true, secondHostBytesOfA: 0 });
    });

    test("platform Client from the environment sends A's keys after client B is built with B's keys", async () => {
      const tenantA = tenantKeys("ta1", "ta2");
      const tenantB = tenantKeys("tb1", "tb2");
      useEnv(tenantA, loopbackUrl());
      const clientA = new Client({ maxRetries: 0, timeout: 5000 });
      useEnv(tenantB, secondUrl());
      const clientB = new Client({ maxRetries: 0, timeout: 5000 });
      await quietly(() => probe(clientA));
      await quietly(() => probe(clientB));
      expect({ targetBytesOfA: target.count(keysOf(tenantA)) > 0, targetBytesOfB: target.count(keysOf(tenantB)) }).toEqual({ targetBytesOfA: true, targetBytesOfB: 0 });
      expect({ secondHostBytesOfB: second.count(keysOf(tenantB)) > 0, secondHostBytesOfA: second.count(keysOf(tenantA)) }).toEqual({ secondHostBytesOfB: true, secondHostBytesOfA: 0 });
    });

    test("the APIKeyManager sends the keys of the environment it read and none of a client built with B's keys", async () => {
      const tenantA = tenantKeys("ta1", "ta2");
      const tenantB = tenantKeys("tb1", "tb2");
      useEnv(tenantA, loopbackUrl());
      const manager = getAPIKeyManager();
      await quietly(() => ProviderAPIKeyClient.listApiKeys({ fiApiKey: tenantB.apiKey, fiSecretKey: tenantB.secretKey, fiBaseUrl: secondUrl() }));
      await quietly(() => manager.listProviderApiKeys());
      expect({ targetBytesOfA: target.count(keysOf(tenantA)) > 0, targetBytesOfB: target.count(keysOf(tenantB)) }).toEqual({ targetBytesOfA: true, targetBytesOfB: 0 });
      expect({ secondHostBytesOfB: second.count(keysOf(tenantB)) > 0, secondHostBytesOfA: second.count(keysOf(tenantA)) }).toEqual({ secondHostBytesOfB: true, secondHostBytesOfA: 0 });
    });
  });
});

describe("each of eight clients built at once sends only its own keys", () => {
  jest.setTimeout(60_000);

  let scratchDir: string;
  beforeAll(() => {
    scratchDir = tenantFs.mkdtempSync(path.join(tenantOs.tmpdir(), "fi-tenants-"));
  });
  afterAll(() => {
    tenantFs.rmSync(scratchDir, { recursive: true, force: true });
  });

  const EIGHT = [0, 1, 2, 3, 4, 5, 6, 7];

  /** The keys of every client but `index`. */
  const othersOf = (all: TenantKeys[], index: number) => all.filter((_, at) => at !== index).flatMap(keysOf);

  const pathSenders: Array<[string, (keys: TenantKeys, baseUrl: string, index: number) => Promise<Send>]> = [
    [
      "APIKeyAuth",
      async (keys, baseUrl, index) => {
        const client = new APIKeyAuth({ fiApiKey: keys.apiKey, fiSecretKey: keys.secretKey, baseUrl, retryAttempts: 1, timeout: 5000 });
        return () => client.request({ method: "GET", url: `/v1/tenant/${index}` } as any);
      },
    ],
    [
      "platform Client",
      async (keys, baseUrl, index) => {
        const client = platform(baseUrl, { apiKey: keys.apiKey, secretKey: keys.secretKey });
        return () => client.request("GET", `/v1/tenant/${index}/`);
      },
    ],
  ];

  test.each(pathSenders.map(([name]) => [name]))("%s: eight clients on one host, each request carries only the keys of the client that sent it", async (name) => {
    const factory = pathSenders.find(([candidate]) => candidate === name)![1];
    const listener = await connSink();
    try {
      const all = EIGHT.map((index) => tenantKeys(`tn${index}a`, `tn${index}b`));
      const sends = await Promise.all(EIGHT.map(async (index) => factory(all[index], listener.url, index)));
      await Promise.all(sends.map((send) => quietly(send)));
      expect(listener.connections).toHaveLength(8);
      const seen = EIGHT.map((index) => {
        const wire = listener.connections.find((text) => text.includes(`/v1/tenant/${index}`)) ?? "";
        return { index, ownBytes: markerBytes(wire, keysOf(all[index])) > 0, otherClientsBytes: markerBytes(wire, othersOf(all, index)) };
      });
      expect(seen).toEqual(EIGHT.map((index) => ({ index, ownBytes: true, otherClientsBytes: 0 })));
    } finally {
      await listener.close();
    }
  });

  test("eight different senders, each with its own host, send only their own keys", async () => {
    const chosen = ["APIKeyAuth", "platform Client", "platform file KB resource create with a file upload", "KB client createKb with a file upload", "ProviderAPIKeyClient.listApiKeys", "Dataset.getDatasetConfig", "Prompt.listTemplates", "AnnotationQueue.list"];
    const senders = chosen.map((name) => SENDERS.find((candidate) => candidate.name === name)!);
    const listeners = await Promise.all(EIGHT.map(() => connSink()));
    try {
      const all = EIGHT.map((index) => tenantKeys(`tm${index}a`, `tm${index}b`));
      const sends = await Promise.all(EIGHT.map(async (index) => senders[index].make(all[index], listeners[index].url, scratchDir)));
      await Promise.all(sends.map((send) => quietly(send)));
      const seen = EIGHT.map((index) => {
        const wire = listeners[index].connections.join("");
        return { sender: chosen[index], ownBytes: markerBytes(wire, keysOf(all[index])) > 0, otherClientsBytes: markerBytes(wire, othersOf(all, index)) };
      });
      expect(seen).toEqual(EIGHT.map((index) => ({ sender: chosen[index], ownBytes: true, otherClientsBytes: 0 })));
    } finally {
      await Promise.all(listeners.map((listener) => listener.close()));
    }
  });

  test("eight APIKeyAuth clients built at once while the environment holds other keys send only their own keys", async () => {
    const saved = [process.env.FI_API_KEY, process.env.FI_SECRET_KEY];
    const envKeys = tenantKeys("te1", "te2");
    process.env.FI_API_KEY = envKeys.apiKey;
    process.env.FI_SECRET_KEY = envKeys.secretKey;
    const listener = await connSink();
    try {
      const all = EIGHT.map((index) => tenantKeys(`tk${index}a`, `tk${index}b`));
      const sends = await Promise.all(
        EIGHT.map(async (index) => {
          await new Promise((resolve) => setImmediate(resolve));
          const client = new APIKeyAuth({ fiApiKey: all[index].apiKey, fiSecretKey: all[index].secretKey, baseUrl: listener.url, retryAttempts: 1, timeout: 5000 });
          return () => client.request({ method: "GET", url: `/v1/tenant/${index}` } as any);
        }),
      );
      await Promise.all(sends.map((send) => quietly(send)));
      const seen = EIGHT.map((index) => {
        const wire = listener.connections.find((text) => text.includes(`/v1/tenant/${index}`)) ?? "";
        return { index, ownBytes: markerBytes(wire, keysOf(all[index])) > 0, otherBytes: markerBytes(wire, [...othersOf(all, index), ...keysOf(envKeys)]) };
      });
      expect(seen).toEqual(EIGHT.map((index) => ({ index, ownBytes: true, otherBytes: 0 })));
    } finally {
      await listener.close();
      if (saved[0] === undefined) delete process.env.FI_API_KEY;
      else process.env.FI_API_KEY = saved[0];
      if (saved[1] === undefined) delete process.env.FI_SECRET_KEY;
      else process.env.FI_SECRET_KEY = saved[1];
    }
  });
});
