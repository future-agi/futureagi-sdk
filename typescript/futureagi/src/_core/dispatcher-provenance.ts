/**
 * Whether a dispatcher is proven to connect straight to the host: its `dispatch` is the one undici's own classes define,
 * compared by identity with the classes of the `undici` package or of the runtime's own copy of undici, not one a class
 * name, a `Proxy`, a getter, a prototype of its own, a `factory`, a `connect` function or a socket path put in its place.
 * Used by the plain-HTTP decision in `http-security.ts`.
 */

import { loadModule } from "./module-loader";

/** Class names of undici's proxy dispatchers: `ProxyAgent` and `EnvHttpProxyAgent`. */
export const PROXY_DISPATCHERS = new Set(["ProxyAgent", "EnvHttpProxyAgent"]);
/** The class name of undici's proxy agent an application builds itself (`NODE_USE_ENV_PROXY` installs `EnvHttpProxyAgent`). */
export const CALLER_PROXY = new Set(["ProxyAgent"]);
/** Class names of undici's dispatchers that connect straight to the host (and the in-process mocks of them). */
export const DIRECT_DISPATCHERS = new Set(["Agent", "Pool", "Client", "BalancedPool", "MockAgent", "MockPool", "MockClient"]);

type Loose = Record<string | symbol, unknown>;
type Classes = Record<string, unknown>;

/** The runtime's global dispatcher slot. */
const SLOT = Symbol.for("undici.globalDispatcher.1");
/** The record of the runtime's undici classes, shared by every copy of the SDK in the process (`runtimeClasses`). */
export const RUNTIME_UNDICI_RECORD = Symbol.for("@future-agi/sdk.runtime-undici");
/** Thrown by the descriptor reads below for a getter or setter, or a `Proxy`: what holds one is not proven. */
const UNPROVEN = new Error("not a data property");

const isProxy = (loadModule("node:util") as { types?: { isProxy?: (value: unknown) => boolean } } | undefined)?.types?.isProxy;
const EMITTER = (loadModule("node:events") as { EventEmitter?: { prototype?: unknown } } | undefined)?.EventEmitter?.prototype;

/** Whether `value` is a `Proxy`; `true` too when the runtime offers no way to tell, since a Proxy cannot be looked into. */
const isProxyObject = (value: object): boolean => { try { return typeof isProxy === "function" ? isProxy(value) : true; } catch { return true; } };
/** The value `target` holds itself under `key`, read from its descriptor; a getter or setter, or a Proxy, throws `UNPROVEN`. */
function ownData(target: object, key: string | symbol): unknown {
  if (isProxyObject(target)) throw UNPROVEN;
  const found = Object.getOwnPropertyDescriptor(target, key);
  if (found !== undefined && !("value" in found)) throw UNPROVEN;
  return found?.value;
}
/** The value `key` resolves to on `target`'s prototype chain, read as `ownData` reads at each level. */
function chainData(target: object, key: string | symbol): unknown {
  for (let at: object | null = target; at !== null; at = Object.getPrototypeOf(at) as object | null) {
    if (isProxyObject(at)) throw UNPROVEN;
    if (Object.prototype.hasOwnProperty.call(at, key)) return ownData(at, key);
  }
  return undefined;
}
/** The name of the class `target` defines itself (its own `constructor`; an inherited one says nothing about `target`). */
export function ownClassName(target: object): string | undefined {
  const constructor = Object.getOwnPropertyDescriptor(target, "constructor")?.value as unknown;
  if (typeof constructor !== "function" || (typeof isProxy === "function" && isProxyObject(constructor))) return undefined;
  const name = Object.getOwnPropertyDescriptor(constructor, "name")?.value as unknown;
  return typeof name === "string" ? name : undefined;
}

/** The `dispatch` symbols (undici routes `dispatch()` through its own symbol key) that `target` itself defines. */
const ownDispatchSymbols = (target: object): symbol[] => Object.getOwnPropertySymbols(target).filter((symbol) => symbol.description === "dispatch");
const ownsDispatch = (target: object): boolean => Object.prototype.hasOwnProperty.call(target, "dispatch") || ownDispatchSymbols(target).length > 0;
/** The dispatch functions `target` resolves (`"dispatch"` and each `dispatch` symbol on its chain), from data properties. */
function dispatchFunctions(target: object): unknown[] {
  const keys = new Set<string | symbol>(["dispatch"]);
  for (let at: object | null = target; at !== null; at = Object.getPrototypeOf(at) as object | null) {
    if (isProxyObject(at)) throw UNPROVEN;
    for (const symbol of ownDispatchSymbols(at)) keys.add(symbol);
  }
  return [...keys].map((key) => chainData(target, key)).filter((value) => value !== undefined);
}
/** The value `target` holds itself under the symbol described as `description`, read as `ownData` reads. */
const ownSlot = (target: object, description: string): unknown => {
  const symbol = Object.getOwnPropertySymbols(target).find((candidate) => candidate.description === description);
  return symbol === undefined ? undefined : ownData(target, symbol);
};
/** The class that defines `target`'s prototype (its own `constructor`, a data property). */
const classOf = (target: object): unknown => { const proto = Object.getPrototypeOf(target) as object | null; return proto === null ? undefined : ownData(proto, "constructor"); };

/**
 * What one copy of undici defines: its `Agent`; the dispatch functions of its direct classes, of `MockAgent` alone (`mock`)
 * and of `EnvHttpProxyAgent`; its default factories; and the source text of its default connector and interceptors.
 */
interface Reference {
  readonly Agent: new (options?: object) => object;
  readonly dispatch: Set<unknown>; readonly mock: Set<unknown>; readonly envDispatch: Set<unknown>; readonly factories: Set<unknown>;
  readonly connectors: Set<string>; readonly interceptors: Set<string>;
}

/** What one copy's classes define, read from its prototypes and from agents built with no options. */
function referenceOf(classes: Classes | null | undefined): Reference | null {
  try {
    const Agent = classes?.Agent;
    if (classes === null || classes === undefined || typeof Agent !== "function") return null;
    const found: Reference = { Agent: Agent as Reference["Agent"], dispatch: new Set(), mock: new Set(), envDispatch: new Set(), factories: new Set(), connectors: new Set(), interceptors: new Set() };
    const collect = (into: Set<unknown>, name: string): void => { for (const value of typeof classes[name] === "function" ? dispatchFunctions((classes[name] as { prototype: object }).prototype) : []) if (typeof value === "function") into.add(value); };
    for (const name of ["Agent", "Pool", "Client", "BalancedPool", "MockAgent"]) collect(found.dispatch, name);
    collect(found.mock, "MockAgent");
    collect(found.envDispatch, "EnvHttpProxyAgent");
    const samples: Loose[] = [new (Agent as new () => Loose)()];
    for (const name of ["Pool", "Client"]) if (typeof classes[name] === "function") samples.push(new (classes[name] as new (origin: string) => Loose)("http://localhost"));
    const source = (value: unknown): string => Function.prototype.toString.call(value);
    for (const sample of samples) {
      for (const symbol of Object.getOwnPropertySymbols(sample)) {
        const held = sample[symbol] as Loose | ((...args: never[]) => unknown) | undefined;
        if (symbol.description === "dispatch interceptors" && Array.isArray(held)) for (const entry of held) if (typeof entry === "function") found.interceptors.add(source(entry));
        if (symbol.description === "factory" && typeof held === "function") found.factories.add(held);
        if (symbol.description === "connector" && typeof held === "function") found.connectors.add(source(held));
        if (symbol.description === "options" && typeof (held as Loose | undefined)?.connect === "function") found.connectors.add(source((held as Loose).connect));
      }
      (sample.close as (() => Promise<void>) | undefined)?.call(sample).catch(() => undefined);
    }
    return found;
  } catch {
    return null;
  }
}

/**
 * The agent the runtime makes for this module: the slot is emptied for a moment, the runtime makes its agent with its
 * first `Request` when the slot is empty, and the slot is given back. `undefined` when the runtime makes none (its undici
 * was loaded before this module: a `Request`, a `fetch`, `NODE_USE_ENV_PROXY`, an ES module graph importing `node:http`).
 */
function runtimeOwnAgent(): unknown {
  const key = SLOT, host = globalThis as Record<symbol, unknown>;
  const saved = Object.getOwnPropertyDescriptor(globalThis, key);
  // a slot that is not configurable keeps its attributes, so the runtime can fill it only when it is not enumerable
  if (saved !== undefined && (!("value" in saved) || saved.writable !== true || (saved.configurable !== true && saved.enumerable !== false))) return undefined;
  let made: unknown;
  try {
    if (saved?.configurable === true) delete host[key];
    else if (saved !== undefined) host[key] = undefined;
    if (typeof Request === "function") new Request("http://127.0.0.1/");
    const filled = Object.getOwnPropertyDescriptor(globalThis, key);
    made = filled !== undefined && "value" in filled ? filled.value : undefined;
  } catch { made = undefined; } finally {
    if (saved !== undefined) {
      const now = Object.getOwnPropertyDescriptor(globalThis, key);
      if (now === undefined || now.configurable === true) Object.defineProperty(globalThis, key, saved);
      else host[key] = saved.value;
    }
  }
  return made !== undefined && made !== saved?.value ? made : undefined;
}

// The prototype chains of the runtime's own undici classes (Node 22 with undici 6, Node 24 with undici 7), each level
// with the union of the own keys it has there; node's own `EventEmitter` (by identity) follows `Dispatcher`.
const BASE = "close,closed,constructor,destroy,destroyed,dispatch,eventSourceOptions,interceptors,webSocketOptions,Symbol(Intercepted Dispatch)";
const DISPATCHER = "close,compose,connect,constructor,destroy,dispatch,pipeline,request,stream,upgrade";
const SHAPES: Record<string, Array<[string, Set<string>]>> = Object.fromEntries(Object.entries({
  Agent: [["Agent", "constructor,stats,Symbol(close),Symbol(destroy),Symbol(dispatch),Symbol(running)"]],
  EnvHttpProxyAgent: [["EnvHttpProxyAgent", "constructor,Symbol(close),Symbol(destroy),Symbol(dispatch)"]],
  Pool: [["Pool", "constructor,Symbol(get dispatcher)"], ["PoolBase", "constructor,stats,Symbol(add client),Symbol(busy),Symbol(close),Symbol(connected),Symbol(destroy),Symbol(dispatch),Symbol(free),Symbol(onDrain),Symbol(pending),Symbol(remove client),Symbol(running),Symbol(size)"]],
  Client: [["Client", "constructor,pipelining,stats,Symbol(busy),Symbol(close),Symbol(connect),Symbol(connected),Symbol(destroy),Symbol(dispatch),Symbol(pending),Symbol(running),Symbol(size)"]],
}).map(([name, own]) => [name, [...own, ["DispatcherBase", BASE], ["Dispatcher", DISPATCHER]].map(([level, keys]) => [level, new Set(keys.split(","))] as [string, Set<string>])]));

/**
 * Whether `Class` has the form of the runtime's undici class `name`, read from descriptors so nothing of it runs: data
 * `name`, the chain `SHAPES[name]` with no other own key, data dispatch keys, then node's `EventEmitter` (a subclass adds
 * a level). Returns the chain's `DispatcherBase` prototype (one per copy of undici), else `undefined`.
 */
function undiciShape(Class: unknown, name: string): object | undefined {
  try {
    if (typeof Class !== "function" || ownData(Class, "name") !== name) return undefined;
    let [at, base] = [ownData(Class, "prototype") as object | null, undefined as object | undefined];
    for (const [level, keys] of SHAPES[name] ?? []) {
      if (typeof at !== "object" || at === null || isProxyObject(at)) return undefined;
      const constructor = ownData(at, "constructor");
      if (typeof constructor !== "function" || ownData(constructor, "name") !== level || (level === name && constructor !== Class)) return undefined;
      if (Reflect.ownKeys(at).some((key) => !keys.has(String(key)))) return undefined;
      for (const key of [...ownDispatchSymbols(at), "dispatch"]) if (Object.prototype.hasOwnProperty.call(at, key) && typeof ownData(at, key) !== "function") return undefined;
      if (level === "DispatcherBase") base = at;
      at = Object.getPrototypeOf(at) as object | null;
    }
    return EMITTER !== undefined && at === EMITTER ? base : undefined;
  } catch {
    return undefined;
  }
}

/**
 * The `Agent`, default `Pool` and `Client` (and `EnvHttpProxyAgent`) of the undici copy whose agent `global` is (or holds
 * as its direct agent), else `null`. Each class has its undici form (`undiciShape`, one `DispatcherBase`), checked
 * before anything is built.
 */
function classesOf(global: unknown): Classes | null {
  const samples: Loose[] = [];
  try {
    if (typeof global !== "object" || global === null || isProxyObject(global)) return null;
    const inner = ownSlot(global, "no proxy agent");
    const agent = inner === undefined ? global : inner;
    if (typeof agent !== "object" || agent === null || isProxyObject(agent) || ownsDispatch(agent) || ownsDispatch(global)) return null;
    const [factory, Agent, Env] = [ownSlot(agent, "factory"), classOf(agent), inner === undefined ? undefined : classOf(global)];
    const base = undiciShape(Agent, "Agent");
    if (typeof factory !== "function" || base === undefined || (Env !== undefined && undiciShape(Env, "EnvHttpProxyAgent") !== base)) return null;
    samples.push(new (Agent as new () => Loose)());
    if (ownSlot(samples[0] as object, "factory") !== factory) return null;
    samples.push(...[{}, { connections: 1 }].map((options) => (factory as (origin: string, options: object) => Loose)("http://localhost", options)));
    const [Pool, Client] = [classOf(samples[1] as object), classOf(samples[2] as object)];
    if (undiciShape(Pool, "Pool") !== base || undiciShape(Client, "Client") !== base) return null;
    return { Agent, Pool, Client, EnvHttpProxyAgent: Env };
  } catch {
    return null;
  } finally {
    for (const sample of samples) (sample.close as (() => Promise<void>) | undefined)?.call(sample).catch(() => undefined);
  }
}

const NAMES = ["Agent", "Pool", "Client", "EnvHttpProxyAgent"] as const;
/**
 * The runtime's own undici classes, read at module evaluation from the agent it makes for this module and published in
 * the shared record (frozen, read-only, only when absent). The record is not read back: application code that runs
 * before the SDK can write it, so a copy that finds no agent of the runtime's own has no runtime classes.
 */
const runtimeClasses: Classes | null = ((): Classes | null => {
  const own = classesOf(runtimeOwnAgent());
  try {
    if (own !== null && Object.getOwnPropertyDescriptor(globalThis, RUNTIME_UNDICI_RECORD) === undefined) {
      const record = Object.freeze(Object.fromEntries(NAMES.map((name) => [name, own[name]])));
      Object.defineProperty(globalThis, RUNTIME_UNDICI_RECORD, { value: record, writable: false, enumerable: false, configurable: false });
    }
  } catch { /* a record that cannot be written is not needed: it is not read */ }
  return own;
})();

let references: Reference[] | undefined;
/** What the `undici` package (when the application can resolve it) and the runtime's own copy of undici define. */
function undiciReferences(): Reference[] {
  const found = references === undefined ? referenceOf(loadModule("undici") as Classes | undefined) : null;
  references ??= [found, found !== null && runtimeClasses?.Agent === found.Agent ? null : referenceOf(runtimeClasses)].filter((entry): entry is Reference => entry !== null);
  return references;
}

/** Whether an `interceptors` option lists any interceptor: one wraps `dispatch` and can send the request anywhere. */
function hasInterceptors(value: unknown): boolean {
  return typeof value === "object" && value !== null && (isProxyObject(value) || Reflect.ownKeys(value).some((key) => { const list = ownData(value, key); return Array.isArray(list) ? list.length > 0 : list !== undefined && list !== null; }));
}
/** Whether connect settings name a Unix socket (`socketPath`, or `path` in an object-valued `connect`) instead of the host. */
function namesSocket(options: object): boolean {
  const connect = ownData(options, "connect");
  const named = (value: unknown): boolean => value !== undefined && value !== null;
  return named(ownData(options, "socketPath")) || (typeof connect === "object" && connect !== null && (named(ownData(connect, "socketPath")) || named(ownData(connect, "path"))));
}

/**
 * Whether a dispatcher was built as undici builds by default: no other `factory`, `connect` function, Unix socket path or
 * interceptor decides where a request goes. These slots and the `agent` slot are read as data properties (`ownData`) on
 * the instance and its prototypes (a chain `dispatchFunctions` found free of Proxies); the instance's own values decide.
 */
function builtLikeUndici(dispatcher: Loose, known: Reference): boolean {
  const genuineConnector = (connect: unknown): boolean => known.connectors.has(Function.prototype.toString.call(connect));
  const genuineInterceptors = (list: unknown): boolean =>
    Array.isArray(list) && list.every((entry) => typeof entry === "function" && known.interceptors.has(Function.prototype.toString.call(entry)));
  for (let at: object | null = dispatcher; at !== null; at = Object.getPrototypeOf(at) as object | null) for (const symbol of Object.getOwnPropertySymbols(at)) {
    if (!["factory", "dispatch interceptors", "connector", "options", "agent"].includes(symbol.description ?? "")) continue;
    const held = ownData(at, symbol);
    if (at !== dispatcher) continue; // a prototype's slot is a method of its class: only a getter there counts
    if (symbol.description === "factory" && held !== undefined && !known.factories.has(held)) return false;
    if (symbol.description === "dispatch interceptors" && !genuineInterceptors(held)) return false;
    if (symbol.description === "connector" && typeof held === "function" && !genuineConnector(held)) return false;
    if (symbol.description === "options" && typeof held === "object" && held !== null) {
      const connect = ownData(held, "connect");
      if ((typeof connect === "function" && !genuineConnector(connect)) || hasInterceptors(ownData(held, "interceptors")) || namesSocket(held)) return false;
    }
  }
  return true;
}
/** The origin `target` holds in its own `url` slot, as undici's `Pool` and `Client` keep it (a `URL`, or a string). */
function slotOrigin(target: object): string | undefined {
  const held = ownSlot(target, "url") as object | string | undefined;
  const origin = typeof held === "object" && held !== null ? (Object.getPrototypeOf(held) === URL.prototype ? (held as URL).origin : undefined) : held;
  return typeof origin === "string" ? origin : undefined;
}

/**
 * A `Pool` or `Client` sends every request to its own origin: it is direct for `url` only when that is its origin and
 * every client it holds has it too. A `BalancedPool` is not proven for any URL. With no URL the class rules alone apply.
 */
function originAllows(dispatcher: object, url: string | undefined): boolean {
  if (url === undefined) return true;
  let pinned = false;
  for (let at: object | null = dispatcher; at !== null; at = Object.getPrototypeOf(at) as object | null) {
    const name = ownClassName(at);
    if (name === "BalancedPool") return false;
    if (name === "Pool" || name === "Client") pinned = true;
  }
  if (!pinned) return true;
  const clients = ownSlot(dispatcher, "clients");
  if (clients !== undefined && (!Array.isArray(clients) || isProxyObject(clients))) return false;
  const origins = [dispatcher, ...((clients ?? []) as unknown[])].map((entry) => (typeof entry === "object" && entry !== null ? slotOrigin(entry) : undefined));
  try {
    const wanted = new URL(url).origin;
    return origins.every((origin) => origin !== undefined && new URL(origin).origin === wanted);
  } catch {
    return false;
  }
}

/**
 * The `Agent` class the SDK's direct agents are made from: the `undici` package's when resolvable, else the runtime's
 * (`runtimeClasses`), else `undefined`. A class the caller supplies, or one a dispatcher holds, is not used.
 */
export function undiciAgentClass(): (new (options: object) => unknown) | undefined {
  return undiciReferences()[0]?.Agent;
}

/**
 * Whether `dispatcher` is undici's own `EnvHttpProxyAgent` (what `NODE_USE_ENV_PROXY` installs): chain `EnvHttpProxyAgent`,
 * `DispatcherBase`, `Dispatcher`, no dispatch of its own, and its dispatch undici's by identity, read from data properties.
 */
export function isUndiciEnvProxyAgent(dispatcher: unknown): boolean {
  if (typeof dispatcher !== "object" || dispatcher === null || isProxyObject(dispatcher) || ownsDispatch(dispatcher)) return false;
  try {
    let at: object | null = dispatcher;
    for (const name of ["EnvHttpProxyAgent", "DispatcherBase", "Dispatcher"]) {
      at = isProxyObject(at) ? null : (Object.getPrototypeOf(at) as object | null);
      if (at === null || ownClassName(at) !== name) return false;
    }
    const resolved = dispatchFunctions(dispatcher);
    if (resolved.length === 0 || !resolved.every((value) => typeof value === "function")) return false;
    return undiciReferences().some((known) => resolved.every((value) => known.envDispatch.has(value)));
  } catch {
    return false;
  }
}

/**
 * Whether `dispatcher` is proven to connect straight to the host: every dispatch function on its chain (data properties)
 * is one undici's own `Agent`, `Pool`, `Client`, `BalancedPool` or `MockAgent` defines, by identity, and it is built as
 * undici builds (`builtLikeUndici`); a `Proxy` or a getter is not proven. A `MockAgent` is direct only when the agent in
 * its own `agent` slot is. `envExempt`: an `EnvHttpProxyAgent` counts when it hands the request for `url` to its direct agent.
 */
export function provenDirect(dispatcher: object, envExempt: boolean, url?: string, depth = 0): boolean {
  try {
    if (depth > 4 || isProxyObject(dispatcher) || !originAllows(dispatcher, url)) return false;
    const [loose, resolved, inner] = [dispatcher as Loose, dispatchFunctions(dispatcher), ownSlot(dispatcher, "agent")];
    if (resolved.length === 0) return false;
    return undiciReferences().some((known) => (envExempt
      ? resolved.every((value) => known.envDispatch.has(value) || known.dispatch.has(value)) && envAgentSendsDirect(loose, url)
      : typeof chainData(dispatcher, "dispatch") === "function" && resolved.every((value) => known.dispatch.has(value)) && builtLikeUndici(loose, known)
        && (!resolved.some((value) => known.mock.has(value)) || (typeof inner === "object" && inner !== null && provenDirect(inner, false, url, depth + 1)))));
  } catch {
    return false;
  }
}

/**
 * Whether the class chain of `dispatcher` names one of undici's proxy agents (`ProxyAgent`, `EnvHttpProxyAgent`), or one
 * of `names` when given (`CALLER_PROXY`: the `ProxyAgent` an application sets up itself, which no environment variable
 * installs).
 */
export function namesProxyClass(dispatcher: unknown, names: ReadonlySet<string> = PROXY_DISPATCHERS): boolean {
  if ((typeof dispatcher !== "object" && typeof dispatcher !== "function") || dispatcher === null) return false;
  try {
    for (let at = Object.getPrototypeOf(dispatcher) as object | null; at !== null; at = Object.getPrototypeOf(at) as object | null) {
      const name = ownClassName(at);
      if (name !== undefined && names.has(name)) return true;
    }
    return false;
  } catch {
    return true;
  }
}
/** Every class undici's dispatchers derive from: a chain that names none of them is not a dispatcher of undici's. */
const UNDICI_DISPATCHERS = new Set([...DIRECT_DISPATCHERS, ...PROXY_DISPATCHERS, "Dispatcher", "DispatcherBase"]);

/**
 * Whether `dispatcher` (a global dispatcher slot's value) is a transport of the caller's that is none of undici's: not an
 * object, or an object whose class chain names none of undici's dispatcher classes. An empty slot is not one.
 */
export function namesNoUndiciClass(dispatcher: unknown): boolean {
  if (dispatcher === undefined || dispatcher === null) return false;
  if (typeof dispatcher !== "object" && typeof dispatcher !== "function") return true;
  return !namesProxyClass(dispatcher, UNDICI_DISPATCHERS);
}
const OBSERVER = Object.fromEntries(["onConnect", "onHeaders", "onData", "onComplete", "onError", "onUpgrade", "onBodySent", "onResponseStarted"].map((name) => [name, (): boolean => true]));

/**
 * Whether undici's own `EnvHttpProxyAgent` hands a request for `url` to its direct agent (itself proven direct): its
 * dispatch runs once with the agents it holds stood in for by a recorder, so the choice is seen and no request is made.
 */
function envAgentSendsDirect(agent: Loose, url: string | undefined): boolean {
  const direct = ownSlot(agent, "no proxy agent");
  if (url === undefined || typeof direct !== "object" || direct === null || !provenDirect(direct, false)) return false;
  const held = [...new Set(["no proxy agent", "http proxy agent", "https proxy agent"].map((slot) => ownSlot(agent, slot)))];
  if (!held.every((entry): entry is object => typeof entry === "object" && entry !== null && !isProxyObject(entry) && !Object.prototype.hasOwnProperty.call(entry, "dispatch"))) return false;
  let chosen: unknown;
  function record(this: unknown): boolean { chosen = this; return true; }
  try {
    for (const entry of held) Object.defineProperty(entry, "dispatch", { value: record, configurable: true, writable: true });
    const target = new URL(url);
    (chainData(agent, "dispatch") as (options: object, handler: object) => unknown).call(agent, { origin: target.origin, path: `${target.pathname}${target.search}`, method: "GET", headers: {} }, { ...OBSERVER });
  } catch {
    return false;
  } finally {
    for (const entry of held) delete (entry as Loose).dispatch;
  }
  return chosen === direct;
}
