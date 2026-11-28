/**
 * Run as a child process, with the `undici` package unresolvable (the resolver refuses it, as in an application that
 * does not install it). The runtime's own fetch runs first, so the runtime's copy of undici is loaded and its agent sits
 * in the global dispatcher slot. The application then reads the runtime's `Agent` class off that agent, writes
 * `class ProxyingAgent extends Agent` whose dispatch hands every request to the parent's proxy sink, and puts a
 * dispatcher shaped as undici's `EnvHttpProxyAgent` in the global slot, holding a `ProxyingAgent` in its
 * "no proxy agent" slot. A keyed plain-http send follows, and the probe prints its outcome and how many times a
 * `ProxyingAgent` was constructed after the application built its own one.
 *
 * PROBE_HOST: "plain" (an opted-in plain-http name the shim answers with 127.0.0.1) or "loopback" (127.0.0.1 as written).
 * PROBE_SHAPE: "method" (plain classes named as undici's; `ProxyingAgent` overrides `dispatch` and sends an absolute-form
 *   request to the proxy) or "symbol" (the dispatcher extends the runtime's `DispatcherBase`; `ProxyingAgent` overrides
 *   the symbol-keyed dispatch and opens a CONNECT tunnel to the proxy).
 * PROBE_ORDER: "dispatcherFirst" (the dispatcher is in the slot when the SDK is loaded) or "sdkFirst" (the SDK is loaded
 *   before the dispatcher is put in the slot).
 */
import Module, { createRequire } from "node:module";
import net from "node:net";

import { installNameShim } from "./name-shim";

/* eslint-disable @typescript-eslint/no-explicit-any */
const SLOT = Symbol.for("undici.globalDispatcher.1");
const slots = globalThis as Record<symbol, any>;
const proxyPort = Number(process.env.PROBE_PROXY_PORT ?? "0");
const targetPort = process.env.PROBE_TARGET_PORT ?? "";
const KEYS = { apiKey: process.env.PROBE_KEY ?? "", secretKey: process.env.PROBE_SECRET ?? "" };

/** The resolver refuses `undici` and every path inside it. */
function refuseUndici(): void {
  const loader = Module as unknown as { _resolveFilename: (request: string, ...rest: unknown[]) => string };
  const resolve = loader._resolveFilename;
  loader._resolveFilename = function resolveFilename(this: unknown, request: string, ...rest: unknown[]): string {
    if (request === "undici" || request.startsWith("undici/")) {
      const error = new Error(`Cannot find module '${request}'`) as Error & { code?: string };
      error.code = "MODULE_NOT_FOUND";
      throw error;
    }
    return resolve.call(this, request, ...rest);
  };
}

function undiciResolvable(): boolean {
  try { createRequire(`${process.cwd()}/`)("undici"); return true; } catch { return false; }
}

/** Writes the request through a CONNECT tunnel to the proxy sink and answers the handler with an error once it closes. */
function tunnel(options: { origin?: unknown; path?: unknown; method?: unknown; headers?: unknown }, handler: Record<string, unknown>): boolean {
  const authority = new URL(String(options.origin)).host;
  if (typeof handler.onConnect === "function") (handler.onConnect as (abort: () => void) => void)(() => undefined);
  const socket = net.connect(proxyPort, "127.0.0.1", () => {
    socket.write(`CONNECT ${authority} HTTP/1.1\r\nHost: ${authority}\r\n\r\n`);
    socket.end(`${String(options.method)} ${String(options.path)} HTTP/1.1\r\nHost: ${authority}\r\nx-carried: ${JSON.stringify(options.headers)}\r\n\r\n`);
  });
  socket.on("error", () => undefined);
  socket.on("close", () => {
    const failure = new Error("closed");
    try {
      if (typeof handler.onResponseError === "function") (handler.onResponseError as (c: unknown, e: Error) => void)({}, failure);
      else if (typeof handler.onError === "function") (handler.onError as (e: Error) => void)(failure);
    } catch { /* the runtime's handler may refuse a second answer */ }
  });
  return true;
}

const built = { count: 0 };

/** The dispatcher the application puts in the global slot, for the shape PROBE_SHAPE names. */
function forgedDispatcher(Agent: new (options?: object) => any): object {
  const NO_PROXY = Symbol("no proxy agent");
  const HTTP = Symbol("http proxy agent");
  const HTTPS = Symbol("https proxy agent");
  const proxyOrigin = `http://127.0.0.1:${proxyPort}`;
  if (process.env.PROBE_SHAPE === "symbol") {
    let dispatchKey: symbol | undefined;
    for (let at: object | null = Agent.prototype; at !== null && dispatchKey === undefined; at = Object.getPrototypeOf(at) as object | null) {
      dispatchKey = Object.getOwnPropertySymbols(at).find((candidate) => candidate.description === "dispatch");
    }
    if (dispatchKey === undefined) throw new Error("the runtime's Agent has no symbol-keyed dispatch");
    const key = dispatchKey;
    class ProxyingAgent extends (Agent as new (options?: object) => any) {
      constructor(options?: object) { super(options); built.count += 1; }
      [key](options: object, handler: Record<string, unknown>): boolean { return tunnel(options, handler); }
    }
    const DispatcherBase = Object.getPrototypeOf(Agent) as new () => any;
    const inner = new ProxyingAgent();
    class EnvHttpProxyAgent extends DispatcherBase {
      constructor() { super(); Object.assign(this, { [NO_PROXY]: inner, [HTTP]: inner, [HTTPS]: inner }); }
      [key](options: object, handler: object): boolean { return inner.dispatch(options, handler); }
    }
    return new EnvHttpProxyAgent();
  }
  class ProxyingAgent extends (Agent as new (options?: object) => any) {
    constructor(options?: object) { super(options); built.count += 1; }
    dispatch(options: { origin?: unknown; path?: unknown }, handler: object): boolean {
      return super.dispatch({ ...options, origin: proxyOrigin, path: `${String(options.origin)}${String(options.path)}` }, handler);
    }
  }
  const inner = new ProxyingAgent();
  class Dispatcher {}
  class DispatcherBase extends Dispatcher {}
  class EnvHttpProxyAgent extends DispatcherBase {
    [NO_PROXY] = inner;
    [HTTP] = inner;
    [HTTPS] = inner;
    dispatch(options: object, handler: object): boolean { return this[NO_PROXY].dispatch(options, handler); }
    close(): Promise<void> { return Promise.resolve(); }
  }
  return new EnvHttpProxyAgent();
}

function loadSdk(): Promise<typeof import("../../platform/client")> {
  return import("../../platform/client");
}

async function main(): Promise<void> {
  refuseUndici();
  await fetch("http://127.0.0.1:1/").catch(() => undefined);
  const Agent = Object.getPrototypeOf(slots[SLOT]).constructor as new (options?: object) => any;
  const forged = forgedDispatcher(Agent);
  const sdkFirst = process.env.PROBE_ORDER === "sdkFirst";
  built.count = 0;
  let sdk: Awaited<ReturnType<typeof loadSdk>> | undefined = sdkFirst ? await loadSdk() : undefined;
  slots[SLOT] = forged;
  if (sdk === undefined) sdk = await loadSdk();
  const shim = installNameShim({ "plain.example.test": "127.0.0.1" });
  const base = process.env.PROBE_HOST === "loopback" ? `http://127.0.0.1:${targetPort}` : `http://plain.example.test:${targetPort}`;
  let outcome: string;
  let timer: ReturnType<typeof setTimeout> | undefined;
  // a handler the tunnel does not answer keeps no handle open: the deadline keeps the process alive and ends the wait
  const late = new Promise<never>((_resolve, reject) => { timer = setTimeout(() => { reject(new Error("no answer in 4 seconds")); }, 4000); });
  try {
    const client = new sdk.Client({ ...KEYS, baseUrl: base, maxRetries: 0, timeout: 3000, allowInsecureHttp: true });
    await Promise.race([client.request("GET", "/probe"), late]);
    outcome = "status:ok";
  } catch (error) {
    outcome = `error:${(error as Error).name}`;
    if (process.env.PROBE_DEBUG !== undefined) process.stderr.write(`${String(error).slice(0, 400)} ${String((error as { cause?: { stack?: unknown } }).cause?.stack ?? "").slice(0, 900)}\n`);
  }
  clearTimeout(timer);
  shim.restore();
  process.stdout.write(`${JSON.stringify({ outcome, constructed: built.count, undiciResolvable: undiciResolvable() })}\n`);
  process.exit(0);
}
void main();

export {};
