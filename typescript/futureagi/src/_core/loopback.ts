/**
 * The one loopback rule for the client, and the direct connection it gets. A request whose host is the local
 * machine (the exact name `localhost`, an address in 127.0.0.0/8 or `::1`) does not use an environment proxy:
 * with `NODE_USE_ENV_PROXY` and `HTTP_PROXY`, the runtime's global dispatcher is a proxy agent, and a credential
 * meant for this machine (a bearer token, a channel token) would be handed to that proxy because an environment
 * variable is set. Every other host keeps the runtime's proxy, `NO_PROXY` included.
 */

import { isUndiciEnvProxyAgent, namesProxyClass, ownClassName, provenDirect, undiciAgentClass } from "./dispatcher-provenance";
import { loadModule, runtimeLoadingUnavailable } from "./module-loader";
import { ConfigurationError } from "./errors";

/**
 * Whether `host` is the local machine: the exact name `localhost`, an address in 127.0.0.0/8 or `::1`. `host` is a
 * URL host as the URL text gives it, or a bare address (lower case is not required); a name with a trailing dot is
 * not `localhost`, because it would go to name resolution, and only the canonical dotted quad passes (no short, hex
 * or integer form, no leading zeros). The same table as Python's `fi._core.loopback.is_loopback_host`
 * (tests/fixtures/loopback/hosts.json).
 */
export function isLoopbackHost(host: string): boolean {
  const name = host.toLowerCase();
  if (name === "localhost") return true;
  // A dotted quad in canonical form: four plain decimal numbers, no leading zeros, no short or hex form.
  const parts = /^(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})$/u.exec(name);
  if (parts !== null) return Number(parts[1]) === 127 && parts.slice(1).every((p) => Number(p) <= 255);
  // An IPv6 literal, bare or in brackets, is read by the URL parser, which only turns one spelling into another:
  // only ::1 is loopback (an IPv4-mapped address and a scoped one are not).
  const literal = /^[0-9a-f:.]+$/u.test(name) && name.includes(":") ? `[${name}]` : name;
  if (/^\[[0-9a-f:.]+\]$/u.test(literal)) {
    try { return new URL(`ws://${literal}`).hostname === "[::1]"; } catch { return false; }
  }
  return false;
}

/**
 * The host as the URL text writes it, before the URL parser rewrites it (the parser turns `0x7f.1`, `2130706433` and
 * a full-width `localhost` into other names): the part of the authority after any credential and before the port.
 */
export function writtenHost(url: string): string {
  const authority = /^[A-Za-z][A-Za-z0-9+.-]*:\/\/([^/?#\\]*)/u.exec(url)?.[1] ?? "";
  const host = authority.slice(authority.lastIndexOf("@") + 1);
  if (host.startsWith("[")) return host.slice(0, host.indexOf("]") + 1);
  return host.replace(/:\d*$/u, "");
}

/**
 * Whether `url`'s host, as the URL text writes it, is the local machine: the one rule for a channel URL's plain
 * `ws://` and for the direct connection a loopback request or channel gets.
 */
export function isLoopbackUrl(url: string): boolean {
  return isLoopbackHost(writtenHost(url));
}

/**
 * The name resolution of a loopback connection. The only name that reaches it is `localhost` (every other loopback host
 * is an address, which is connected to as it is): it is answered here, as 127.0.0.1 and then ::1, and is not handed to
 * the system resolver, whose answer for it need not be this machine. A name that is not `localhost` is refused.
 */
export function loopbackLookup(
  hostname: string,
  options: unknown,
  callback: (error: Error | null, address?: string | { address: string; family: number }[], family?: number) => void,
): void {
  const done = typeof options === "function" ? (options as typeof callback) : callback;
  const settings = (typeof options === "object" && options !== null ? options : {}) as { family?: number | string; all?: boolean };
  const family = typeof options === "number" ? options : settings.family === "IPv4" ? 4 : settings.family === "IPv6" ? 6 : Number(settings.family ?? 0);
  if (hostname.toLowerCase() !== "localhost") {
    const error = Object.assign(new Error(`getaddrinfo ENOTFOUND ${hostname}`), { code: "ENOTFOUND", hostname });
    queueMicrotask(() => { done(error); });
    return;
  }
  const answers = [{ address: "127.0.0.1", family: 4 }, { address: "::1", family: 6 }].filter((entry) => family === 0 || entry.family === family);
  queueMicrotask(() => {
    if (settings.all === true) done(null, answers);
    else done(null, answers[0]?.address, answers[0]?.family);
  });
}

type Cached = { proxy: unknown; dispatcher: unknown };
const direct: { plain?: Cached; local?: Cached; name?: Cached } = {};
let ownKeyed: { dispatcher: unknown; node: boolean } | undefined;

/** The runtime's global dispatcher, when it has one (it is created with the first `Request` or `fetch`). */
function globalDispatcher(): unknown {
  const key = Symbol.for("undici.globalDispatcher.1");
  const slots = globalThis as Record<symbol, unknown>;
  if (slots[key] === undefined && typeof Request === "function") {
    try { new Request("http://127.0.0.1/"); } catch { /* the runtime has no global dispatcher to read */ }
  }
  return slots[key];
}

/**
 * The runtime's default agent (`Agent`, the global dispatcher when no environment proxy is on) as a copy that resolves
 * `localhost` itself (`loopbackLookup`) and keeps every other option the global agent was made with. `undefined` for a
 * global agent whose `connect` is a function of the application's own, which is left in place.
 */
function localhostAgent(global: object, Agent: unknown): unknown {
  const cached = direct.name;
  if (cached !== undefined && cached.proxy === global) return cached.dispatcher;
  try {
    const slot = Object.getOwnPropertySymbols(global).find((symbol) => symbol.description === "options");
    const options = ((slot === undefined ? undefined : (global as Record<symbol, unknown>)[slot]) ?? {}) as { connect?: unknown };
    if (typeof options.connect === "function") return undefined;
    const connect = { ...(typeof options.connect === "object" && options.connect !== null ? options.connect : {}), lookup: loopbackLookup };
    const dispatcher = new (Agent as new (options: object) => unknown)({ ...options, connect });
    direct.name = { proxy: global, dispatcher };
    return dispatcher;
  } catch {
    return undefined;
  }
}

/**
 * A dispatcher for the runtime's fetch or WebSocket that connects directly, or `undefined` when there is nothing to
 * replace. The runtime's environment-proxy agent (`EnvHttpProxyAgent`, which `NODE_USE_ENV_PROXY` installs as the global
 * dispatcher) is replaced by a direct agent, built once per global proxy agent and reused, so loopback requests share
 * one connection pool. With `loopback` set the agent resolves `localhost` itself (`loopbackLookup`), for a request whose
 * host is loopback as written; without it names are resolved by the system, for a plain-HTTP host the opt-in allows.
 * The runtime's default agent (no environment proxy) is replaced only for the name `localhost` (`localhostName`), the one
 * host a loopback request hands to the resolver. A dispatcher the application installed itself (a composed one, a mock,
 * one with its own CA) is left in place, since it reads no environment proxy.
 */
export function directDispatcher(loopback = false, localhostName = false): unknown {
  const global = globalDispatcher();
  if (typeof global !== "object" || global === null) return undefined;
  // The agent is built from undici's own `Agent` alone: the `undici` package's, or the class of the agent the runtime
  // makes while the SDK loads, as `undiciAgentClass` finds it. The class of the global dispatcher, or of an agent it
  // holds, is not constructed, since the caller can supply it; with no `Agent` of undici's own there is no direct agent.
  const Agent = undiciAgentClass();
  if (Agent === undefined) return undefined;
  if (ownClassName(Object.getPrototypeOf(global) as object) === "Agent" && loopback && localhostName && provenDirect(global, false)) return localhostAgent(global, Agent);
  if (!isUndiciEnvProxyAgent(global)) return undefined;
  const slot = loopback ? "local" : "plain";
  const cached = direct[slot];
  if (cached !== undefined && cached.proxy === global) return cached.dispatcher;
  try {
    const connect = loopback ? { connect: { lookup: loopbackLookup } } : {};
    const dispatcher = new Agent(connect);
    direct[slot] = { proxy: global, dispatcher };
    return dispatcher;
  } catch {
    return undefined;
  }
}

/**
 * Whether the runtime's global dispatcher is a proxy agent by its class chain (`ProxyAgent` or `EnvHttpProxyAgent`, as
 * `NODE_USE_ENV_PROXY` installs one) that `directDispatcher` cannot replace, because no class of undici's own proves it.
 */
export function globalDispatcherProxies(): boolean {
  return namesProxyClass(globalDispatcher());
}

/** A response header list as undici's handlers take it: names and values in turn, as bytes. */
function rawHeaderBytes(list: readonly string[] | undefined): Uint8Array[] {
  return (list ?? []).map((entry) => Buffer.from(entry, "latin1"));
}

/** The request headers a dispatch carries (an object, a flat list of names and values, or a list of pairs), as pairs. */
function headerPairs(headers: unknown): Array<[string, string]> {
  const pairs: Array<[string, string]> = [];
  const add = (name: unknown, value: unknown): void => {
    if (value === undefined || value === null) return;
    for (const item of Array.isArray(value) ? value : [value]) pairs.push([String(name), String(item)]);
  };
  if (Array.isArray(headers)) {
    if (headers.every((entry) => Array.isArray(entry))) for (const [name, value] of headers as unknown[][]) add(name, value);
    else for (let at = 0; at + 1 < headers.length; at += 2) add(headers[at], headers[at + 1]);
  } else if (typeof headers === "object" && headers !== null) {
    if (typeof (headers as { [Symbol.iterator]?: unknown })[Symbol.iterator] === "function") for (const [name, value] of headers as Iterable<[unknown, unknown]>) add(name, value);
    else for (const [name, value] of Object.entries(headers)) add(name, value);
  }
  return pairs;
}

interface DispatchHandler {
  onConnect?: (abort: (reason?: unknown) => void) => void;
  onHeaders?: (status: number, headers: Uint8Array[], resume: () => void, statusText: string) => boolean | void;
  onData?: (chunk: Uint8Array) => boolean | void;
  onComplete?: (trailers: Uint8Array[]) => void;
  onError?: (error: Error) => void;
}
interface NodeRequestModule { request: (options: object) => NodeClientRequest; Agent: new (options: object) => unknown }
interface NodeClientRequest {
  on<A extends unknown[]>(event: string, listener: (...args: A) => void): unknown;
  setHeader(name: string, value: string | string[]): void; getHeader(name: string): unknown;
  write(chunk: unknown): boolean; end(chunk?: unknown): void; destroy(error?: unknown): void;
}
interface NodeResponse {
  statusCode?: number; statusMessage?: string; rawHeaders?: string[]; rawTrailers?: string[];
  on<A extends unknown[]>(event: string, listener: (...args: A) => void): unknown; pause(): void; resume(): void; destroy(error?: unknown): void;
}

/**
 * A dispatcher the runtime's fetch takes (`dispatch(options, handler)`), built on `node:http` and `node:https` with
 * agents of its own that resolve `localhost` themselves (`loopbackLookup`) and are given no proxy setting, so no
 * environment proxy and no global dispatcher take part. It carries a request to a loopback origin only; any other
 * origin is answered with an error before a connection. `undefined` when the runtime has no `node:http` and `node:https`.
 */
function nodeDirectDispatcher(): object | undefined {
  const http = loadModule("node:http") as NodeRequestModule | undefined;
  const https = loadModule("node:https") as NodeRequestModule | undefined;
  if (typeof http?.request !== "function" || typeof https?.request !== "function" || typeof http.Agent !== "function" || typeof https.Agent !== "function") return undefined;
  const agents = { "http:": new http.Agent({ keepAlive: true, lookup: loopbackLookup }), "https:": new https.Agent({ keepAlive: true, lookup: loopbackLookup }) };
  const modules = { "http:": http, "https:": https };
  const dispatch = (options: { origin?: unknown; path?: string; method?: string; headers?: unknown; body?: unknown; upgrade?: unknown }, handler: DispatchHandler): boolean => {
    let settled = false;
    const fail = (error: unknown): void => {
      if (settled) return;
      settled = true;
      handler.onError?.(error instanceof Error ? error : new Error(String(error)));
    };
    let target: URL;
    try {
      target = new URL(String(options.origin));
    } catch (error) {
      queueMicrotask(() => { fail(error); });
      return true;
    }
    const scheme = target.protocol as "http:" | "https:";
    if ((scheme !== "http:" && scheme !== "https:") || !isLoopbackHost(target.hostname) || options.upgrade !== undefined && options.upgrade !== null || options.method === "CONNECT") {
      queueMicrotask(() => { fail(new Error("the SDK's direct transport carries plain requests to a loopback origin only")); });
      return true;
    }
    const request = modules[scheme].request({
      protocol: scheme, hostname: target.hostname.replace(/^\[|\]$/gu, ""), port: target.port === "" ? undefined : Number(target.port),
      path: options.path ?? "/", method: options.method ?? "GET", agent: agents[scheme],
    });
    for (const [name, value] of headerPairs(options.headers)) {
      const held = request.getHeader(name);
      request.setHeader(name, held === undefined ? value : [...(Array.isArray(held) ? held.map(String) : [String(held)]), value]);
    }
    handler.onConnect?.((reason?: unknown) => { request.destroy(reason instanceof Error ? reason : new Error("the request was aborted")); });
    request.on("error", (error: Error) => { fail(error); });
    request.on("response", (response: NodeResponse) => {
      response.on("error", (error: Error) => { fail(error); });
      const resume = (): void => { response.resume(); };
      if (handler.onHeaders?.(response.statusCode ?? 0, rawHeaderBytes(response.rawHeaders), resume, response.statusMessage ?? "") === false) response.pause();
      response.on("data", (chunk: Uint8Array) => { if (!settled && handler.onData?.(chunk) === false) response.pause(); });
      response.on("end", () => {
        if (settled) return;
        settled = true;
        handler.onComplete?.(rawHeaderBytes(response.rawTrailers));
      });
    });
    const body = options.body;
    void (async (): Promise<void> => {
      try {
        if (body === undefined || body === null) request.end();
        else if (typeof body === "string" || body instanceof Uint8Array) request.end(body);
        else if (typeof (body as { [Symbol.asyncIterator]?: unknown })[Symbol.asyncIterator] === "function" || typeof (body as { [Symbol.iterator]?: unknown })[Symbol.iterator] === "function") {
          for await (const chunk of body as AsyncIterable<unknown>) request.write(chunk);
          request.end();
        } else throw new Error("a request body the SDK's direct transport cannot write");
      } catch (error) {
        request.destroy(error);
        fail(error);
      }
    })();
    return true;
  };
  return { dispatch, close: (): Promise<void> => Promise.resolve(), destroy: (): Promise<void> => Promise.resolve() };
}

/**
 * The direct transport the SDK builds itself for every keyed loopback send, built once and reused: an agent of undici's
 * own `Agent` (`undiciAgentClass`: the `undici` package's, or the runtime's as this copy read it) that resolves `localhost`
 * itself, else, with no such class, a dispatcher on `node:http` and `node:https` (`nodeDirectDispatcher`). `undefined`
 * when the runtime has neither. The global dispatcher is not used and its class is not constructed.
 */
function ownDirectAgent(): { dispatcher: unknown; node: boolean } | undefined {
  if (ownKeyed !== undefined) return ownKeyed;
  const Agent = undiciAgentClass();
  try {
    if (Agent !== undefined) ownKeyed = { dispatcher: new Agent({ connect: { lookup: loopbackLookup } }), node: false };
  } catch {
    ownKeyed = undefined;
  }
  if (ownKeyed === undefined) {
    const node = nodeDirectDispatcher();
    if (node !== undefined) ownKeyed = { dispatcher: node, node: true };
  }
  return ownKeyed;
}

let ownPlain: { dispatcher: unknown } | undefined;

/**
 * The direct agent the SDK builds itself, once, for a keyed plain-http send to a host that is not loopback when the
 * runtime's global dispatcher slot holds no dispatcher: an agent of undici's own `Agent` (`undiciAgentClass`) with no
 * proxy setting, whose names the system resolves. `undefined` when there is no such class.
 */
export function ownPlainHttpAgent(): unknown {
  if (ownPlain !== undefined) return ownPlain.dispatcher;
  const Agent = undiciAgentClass();
  if (Agent === undefined) return undefined;
  try {
    ownPlain = { dispatcher: new Agent({}) };
  } catch {
    return undefined;
  }
  return ownPlain.dispatcher;
}

/**
 * How a keyed send through the runtime's own fetch to a loopback URL goes: see `keyedLoopbackRoute`. `node`: the
 * dispatcher is the SDK's `node:http` / `node:https` one, which carries fetch requests and not a WebSocket.
 */
export type KeyedLoopbackRoute = { kind: "direct"; dispatcher: unknown; node: boolean } | { kind: "global" } | { kind: "unproven" };

/**
 * The one rule for a keyed send (API keys, a Bearer token, a channel token) through the runtime's own fetch to a
 * loopback `url`, `https://` included: the SDK's own direct transport (`ownDirectAgent`), whatever the global dispatcher
 * is (a proxy agent, a composed or wrapped one, a mock, or an agent whose pool holds a proxy agent is not used). `global`
 * for a runtime with no global dispatcher slot (no undici, so no environment proxy in it) and no transport of the SDK's;
 * `unproven` when a slot is there but the SDK has no transport of its own (the caller refuses).
 */
export function keyedLoopbackRoute(_url: string): KeyedLoopbackRoute {
  const own = ownDirectAgent();
  if (own !== undefined) return { kind: "direct", dispatcher: own.dispatcher, node: own.node };
  const global = globalDispatcher();
  return global === undefined || global === null ? { kind: "global" } : { kind: "unproven" };
}

/**
 * The extra fetch init for a request to `url` through the runtime's own fetch: a direct dispatcher when the host is
 * loopback or the URL is plain `http://` (a request the plain-HTTP opt-in allows is not handed to an environment
 * proxy), nothing otherwise. A fetch the caller passed in is the caller's: it gets no extra init. A `keyed` request to a
 * loopback host goes through the SDK's own direct transport (`keyedLoopbackRoute`), and is refused with
 * `insecure_http_origin` before any connection when the runtime offers the SDK none. An unkeyed request carries nothing
 * for a proxy to read: it gets the direct dispatcher `directDispatcher` gives, or the global dispatcher as it is (an
 * `EnvHttpProxyAgent` applies `NO_PROXY` itself).
 */
export function loopbackInit(url: string, usesRuntimeFetch: boolean, keyed = true): { dispatcher?: unknown } {
  if (!usesRuntimeFetch || !(isLoopbackUrl(url) || /^[\t\n\v\f\r ]*http:/iu.test(url))) return {};
  const loopback = isLoopbackUrl(url);
  if (loopback && keyed) {
    const route = keyedLoopbackRoute(url);
    if (route.kind === "unproven") throw loopbackRefusal("unproven");
    return route.kind === "direct" ? { dispatcher: route.dispatcher } : {};
  }
  const dispatcher = directDispatcher(loopback, loopback && writtenHost(url).toLowerCase() === "localhost");
  return dispatcher === undefined ? {} : { dispatcher };
}

/** The remedy when the SDK has no direct transport of its own for a keyed loopback send. */
export const NO_AGENT_REMEDY =
  "Install the undici package for the application, or run the SDK on a runtime that provides node:http and node:https.";

/**
 * Why a keyed loopback send is refused: `unproven`, the runtime has a global dispatcher and the SDK has no direct
 * transport of its own (no `Agent` of undici's own, no `node:http`); `foreign`, a global dispatcher that names none of
 * undici's dispatcher classes, which the SDK cannot inspect. No key text.
 */
export const LOOPBACK_REFUSALS = {
  unproven: "the SDK has no direct transport of its own on this runtime (the SDK needs an undici Agent or both node:http " +
    "and node:https), and it does not " +
    `hand the request to the runtime's global dispatcher. ${NO_AGENT_REMEDY}`,
  foreign: "the runtime's global dispatcher is none of undici's dispatcher classes, so the SDK cannot inspect it or prove " +
    "that it connects directly, and a proxy inside it would receive the request. Remove that dispatcher, or " +
    "install an Agent of the undici package with that package's setGlobalDispatcher.",
} as const;

/**
 * The same reasons when this build loads no package and no `node:` built-in at run time (`runtimeLoadingUnavailable`: an
 * ES module build on a runtime without `process.getBuiltinModule`): only the remedies that clear the refusal there.
 */
export const LOOPBACK_REFUSALS_WITHOUT_LOADING = {
  unproven: "the SDK has no direct transport of its own on this runtime: its ES module build cannot load the undici " +
    "package, node:http or node:https on a Node.js without process.getBuiltinModule, and it does not hand the request to " +
    "the runtime's global dispatcher. Load the SDK as CommonJS, or run it on a Node.js that provides process.getBuiltinModule.",
  foreign: "the SDK cannot read the runtime's global dispatcher: its ES module build cannot load the undici package on a " +
    "Node.js without process.getBuiltinModule, so it cannot prove that the dispatcher connects directly, and a proxy " +
    "inside it would receive the request. Load the SDK as CommonJS and install an Agent of the undici package with that " +
    "package's setGlobalDispatcher.",
} as const;

/** The text of a keyed loopback refusal for `reason`, with the remedies that clear it in this build on this runtime. */
export function loopbackRefusalText(reason: keyof typeof LOOPBACK_REFUSALS): string {
  return (runtimeLoadingUnavailable() ? LOOPBACK_REFUSALS_WITHOUT_LOADING : LOOPBACK_REFUSALS)[reason];
}

/** The refusal of a keyed loopback request for one of the reasons in `LOOPBACK_REFUSALS`. No key text. */
function loopbackRefusal(reason: keyof typeof LOOPBACK_REFUSALS): ConfigurationError {
  return new ConfigurationError(`Refusing to send credentials to a loopback host: ${loopbackRefusalText(reason)}`, "insecure_http_origin");
}
