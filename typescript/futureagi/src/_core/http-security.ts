/** Plain-HTTP policy, independent of credential provenance and retry routing. */
import { ConfigurationError } from "./errors";
import { isLoopbackUrl, keyedLoopbackRoute, loopbackRefusalText } from "./loopback";
import { runtimeLoadingUnavailable } from "./module-loader";
import { CALLER_PROXY, DIRECT_DISPATCHERS, namesNoUndiciClass, namesProxyClass, ownClassName, PROXY_DISPATCHERS, provenDirect, isUndiciEnvProxyAgent, undiciAgentClass } from "./dispatcher-provenance";

/**
 * Whether the host of `raw`, the URL text as it was written, is the local machine, by the one loopback rule
 * (tests/fixtures/loopback/hosts.json): a short, hex, integer or trailing-dot form is not loopback.
 */
export function isLoopback(raw: string): boolean {
  return isLoopbackUrl(raw);
}

/** Plain HTTP to anything other than loopback, by the host as written. */
export function isInsecureHttp(raw: string): boolean {
  let protocol: string;
  try { protocol = new URL(raw).protocol; } catch { return false; }
  return protocol === "http:" && !isLoopback(raw);
}

/** Whether the authority of `raw`, the URL text as written, holds user info (an `@` before the host). */
function writesUserInfo(raw: string): boolean {
  const prefix = SCHEME.exec(raw.replace(TRIM, ""));
  if (prefix === null) return false;
  const rest = raw.replace(TRIM, "").slice(prefix[0].length);
  return (rest.split(/[/?#]/u, 1)[0] ?? "").includes("@");
}

/**
 * The URL text for a request URL that a URL parser has already rewritten: when the request goes to the origin of
 * `base`, the base as written followed by the rest of the request URL, so the host is the one the caller wrote;
 * otherwise the request URL itself.
 */
export function writtenUrl(requestUrl: string, base: string | undefined): string {
  if (base === undefined) return requestUrl;
  try {
    const target = new URL(requestUrl);
    if (new URL(base).origin !== target.origin) return requestUrl;
    // A base that writes user info is judged as written: slicing at the origin would join pieces of two different URLs.
    if (writesUserInfo(base)) return base;
    return base.replace(/\/+$/u, "") + requestUrl.slice(target.origin.length);
  } catch {
    return requestUrl;
  }
}

/** The warning is shared by every copy of this module in the process. */
const WARNED = Symbol.for("futureagi.insecureHttpWarned");

function hostOf(url: URL): string {
  // every trailing dot goes, in any spelling the URL parser may leave: `api.futureagi.com..` is `api.futureagi.com`
  return url.hostname.toLowerCase().replace(/[.\u3002\uff0e\uff61]+$/u, "");
}

/** Whether `url` is a Future AGI host (futureagi.com or any name below it). */
export function isFutureAgiHost(url: URL): boolean {
  const host = hostOf(url);
  return host === "futureagi.com" || host.endsWith(".futureagi.com");
}

type Env = Record<string, string | undefined>;

/** Python's `str.strip()` set, so the NO_PROXY entries are trimmed the same way in both clients. */
const SPACE = "\\t\\n\\v\\f\\r\\x1c-\\x1f \\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";
const TRIM = new RegExp(`^[${SPACE}]+|[${SPACE}]+$`, "gu");

/**
 * The port written in the authority of `text`, as the ASCII digits written (leading zeros kept, `08` is not `8`), else
 * `null`. A default port written out (`:80`) counts; an empty port (`host:`) does not.
 */
function writtenPort(text: string): string | null {
  const at = text.indexOf("://");
  const rest = at >= 0 ? text.slice(at + 3) : text;
  const full = rest.split(/[/?#]/u, 1)[0] ?? "";
  const authority = full.slice(full.lastIndexOf("@") + 1);
  let port: string;
  if (authority.startsWith("[")) {
    const end = authority.indexOf("]");
    const tail = end >= 0 ? authority.slice(end + 1) : "";
    port = tail.startsWith(":") ? tail.slice(1) : "";
  } else {
    port = authority.includes(":") ? authority.slice(authority.lastIndexOf(":") + 1) : "";
  }
  return /^[0-9]+$/u.test(port) ? port : null;
}

/**
 * The NO_PROXY value as CPython's `getproxies_environment` reads it: a variable named `no_proxy` in any letter case
 * with a non-empty value sets it (the last such); a variable whose name ends in lower-case `_proxy` (`no_proxy`,
 * `NO_proxy`) then replaces it, and when its value is empty removes it, so an empty `no_proxy` wins over `NO_PROXY`.
 */
function noProxyValue(env: Env): string | undefined {
  const named = Object.entries(env).filter(([name]) => name.length === 8 && name.toLowerCase() === "no_proxy");
  let value: string | undefined;
  for (const [, text] of named) if (text) value = text;
  for (const [name, text] of named) if (name.endsWith("_proxy")) value = text ? text : undefined;
  return value;
}

/**
 * Whether NO_PROXY names the host, the rule of CPython's `urllib.request.proxy_bypass_environment`: `hostPort` is the
 * lower-case host with `:port` as written, the trailing dot of a name kept. The whole value `*` bypasses every host;
 * otherwise each comma-separated entry (trimmed, without leading dots, lower-case) bypasses the host when it equals
 * the host with or without the port, or is a dot-separated suffix of either. A `*` inside a longer list or a name is
 * a literal character. CIDR ranges are not supported.
 */
function bypassed(hostPort: string, noProxy: string): boolean {
  if (noProxy === "*") return true;
  const split = /^([\s\S]*):([0-9]*)$/u.exec(hostPort);
  const hostOnly = split ? (split[1] as string) : hostPort;
  for (const item of noProxy.split(",")) {
    const trimmed = item.replace(TRIM, "");
    if (trimmed === "") continue;
    const name = trimmed.replace(/^\.+/u, "").toLowerCase();
    if (hostOnly === name || hostPort === name) return true;
    if (hostOnly.endsWith(`.${name}`) || hostPort.endsWith(`.${name}`)) return true;
  }
  return false;
}

/**
 * Whether an environment proxy routes an `http://` request to `target` (the URL text as written): `HTTP_PROXY`,
 * `http_proxy`, `ALL_PROXY` or `all_proxy` (any letter case, a non-empty value) routes it; `HTTPS_PROXY` alone does
 * not. NO_PROXY (`noProxyValue`) then exempts hosts as `bypassed` says. The host is lower-case ASCII with the trailing
 * dot of a name kept, an IPv6 address in brackets, then `:port` when the URL as written has a port, as written. The
 * rows are in tests/fixtures/loopback/proxy_env.json, shared with the Python client. The Python client also asks the
 * routers of httpx and requests; the runtime's fetch has no router of its own to ask.
 */
export function envProxyRoutes(target: URL | string, env: Env = processEnv()): boolean {
  if (!Object.entries(env).some(([name, value]) => ["http_proxy", "all_proxy"].includes(name.toLowerCase()) && !!value)) return false;
  try {
    const text = typeof target === "string" ? target : target.href;
    const noProxy = noProxyValue(env);
    if (noProxy === undefined) return true;
    const host = new URL(text).hostname.toLowerCase();
    const port = writtenPort(text);
    return !bypassed(port === null ? host : `${host}:${port}`, noProxy);
  } catch {
    return true;
  }
}

function processEnv(): Env {
  return (globalThis as { process?: { env?: Env } }).process?.env ?? {};
}

/**
 * Whether `dispatcher` may send through a proxy: undici's `ProxyAgent` or a class derived from it, `EnvHttpProxyAgent`,
 * and any dispatcher that is not proven direct, because a dispatcher that cannot be looked into counts as proxied.
 * Proven direct means a dispatcher of undici's `Agent`, `Pool`, `Client`, `BalancedPool` or `MockAgent` family whose
 * `dispatch` is the function undici itself defines (`provenDirect`): a class that only carries one of those names, a
 * subclass or instance that overrides `dispatch`, a prototype of its own, a `Proxy`, and an agent built with a `factory`
 * or a `connect` function of its own are not. A subclass that leaves `dispatch` alone stays direct. `EnvHttpProxyAgent`
 * routes by the proxy variables it reads itself, so it counts unless `url` is given, a proxy variable is set and the
 * shared NO_PROXY rule exempts that host (the agent then sends it directly). A dispatcher that wraps another one (a
 * composed or intercepted agent) is not looked into: it counts.
 */
export function dispatcherProxies(dispatcher: unknown, url?: string, env: Env = processEnv()): boolean {
  if (dispatcher === undefined || dispatcher === null) return false;
  if (typeof dispatcher !== "object" && typeof dispatcher !== "function") return true;
  let direct = false;
  let envExempt = false;
  for (let proto: unknown = Object.getPrototypeOf(dispatcher); proto !== null && proto !== undefined; proto = Object.getPrototypeOf(proto)) {
    const name = ownClassName(proto as object);
    if (name === "EnvHttpProxyAgent") {
      // a class that only carries the name is not undici's agent: it cannot be looked into
      if (!isUndiciEnvProxyAgent(dispatcher)) return true;
      const routed = url === undefined || envProxyRoutes(url, env) || !Object.entries(env).some(([n, v]) => ["http_proxy", "all_proxy"].includes(n.toLowerCase()) && !!v);
      if (routed) return true;
      direct = true;
      envExempt = true;
    } else if (name !== undefined && PROXY_DISPATCHERS.has(name)) return true;
    else if (name !== undefined && DIRECT_DISPATCHERS.has(name)) direct = true;
  }
  return !(direct && provenDirect(dispatcher, envExempt, url));
}

/**
 * Whether the runtime's global dispatcher is a proxy dispatcher the application installed (`dispatcherProxies`): every
 * request through the runtime's own `fetch` then goes through that proxy. It is read on each call, so a dispatcher
 * set after a client was built counts. A `fetch` passed in the client options is the caller's own and is not looked
 * into.
 */
export function callerProxyDispatcher(url?: string): boolean {
  const global = (globalThis as Record<symbol, unknown>)[Symbol.for("undici.globalDispatcher.1")];
  return global === undefined ? false : dispatcherProxies(global, url);
}

/**
 * How a keyed plain `http://` request through the runtime's own fetch is routed, for the plain-HTTP decision. The SDK
 * sends it through a direct dispatcher, so the proxy variables cannot route it (`proxiesDisabled`), unless something the
 * caller brought routes it: a per-call `dispatcher` or the global dispatcher that may proxy (`callerProxied`). The global
 * `EnvHttpProxyAgent` that `NODE_USE_ENV_PROXY` installs is the environment, not the caller: the SDK replaces it with a
 * direct agent for this request (`loopbackInit`). A loopback request through the global dispatcher follows
 * `keyedLoopbackRoute`: the SDK's own transport disables the proxies; a global `ProxyAgent` is `caller_proxy`, as is a
 * global none of undici's (`refusal` "foreign") or a runtime with no transport of the SDK's ("unproven"). Anything but
 * `http://` is neither.
 */
export function plainHttpRouting(
  raw: string,
  caller: { fetchSupplied: boolean; dispatcher?: unknown },
): { callerProxied: boolean; proxiesDisabled: boolean; refusal?: "unproven" | "foreign" } {
  if (!/^[\t\n\v\f\r ]*http:/iu.test(raw)) return { callerProxied: false, proxiesDisabled: false };
  // A `fetch` the caller supplies is the caller's own transport and is not looked into: the environment check applies.
  if (caller.fetchSupplied) return { callerProxied: false, proxiesDisabled: false };
  if (caller.dispatcher !== undefined) return { callerProxied: dispatcherProxies(caller.dispatcher, raw), proxiesDisabled: false };
  if (isLoopback(raw)) {
    // the shared rule table refuses a caller's `ProxyAgent`, or a global none of undici's, for plain http to loopback too
    const global = (globalThis as Record<symbol, unknown>)[Symbol.for("undici.globalDispatcher.1")];
    if (namesProxyClass(global, CALLER_PROXY)) return { callerProxied: true, proxiesDisabled: false };
    if (namesNoUndiciClass(global)) return { callerProxied: true, proxiesDisabled: false, refusal: "foreign" };
    const route = keyedLoopbackRoute(raw).kind;
    if (route === "direct" || route === "global") return { callerProxied: false, proxiesDisabled: true };
    return { callerProxied: true, proxiesDisabled: false, refusal: route };
  }
  const global = (globalThis as Record<symbol, unknown>)[Symbol.for("undici.globalDispatcher.1")];
  if (global === undefined) return { callerProxied: false, proxiesDisabled: true };
  // undici's own agent (the environment's), by its class chain and dispatch: a class that carries the name is not it.
  // The direct agent that replaces it is built from undici's own `Agent` alone; with none known the send is refused.
  if (isUndiciEnvProxyAgent(global)) return undiciAgentClass() === undefined ? { callerProxied: true, proxiesDisabled: false } : { callerProxied: false, proxiesDisabled: true };
  return { callerProxied: dispatcherProxies(global, raw), proxiesDisabled: !dispatcherProxies(global, raw) };
}

const SCHEME = /^[A-Za-z][A-Za-z0-9+.-]*:\/\//u;

/**
 * Why the host of an `http://` URL text is not the one every reader would find, else `null`: no host at all; a
 * backslash or a percent-encoded backslash in the part before the path (readers split there differently); user info
 * in the authority (a key-carrying URL has none; the message names the shape, not its text); an `@` after the
 * authority (a path, query or fragment holding one).
 */
function hostShapeProblem(raw: string): string | null {
  const text = raw.replace(TRIM, "");
  const prefix = SCHEME.exec(text);
  if (prefix === null) return "has no host";
  const rest = text.slice(prefix[0].length);
  const authority = rest.split(/[/?#]/u, 1)[0] ?? "";
  const hostPort = authority.slice(authority.lastIndexOf("@") + 1);
  const host = hostPort.startsWith("[") ? hostPort.slice(0, hostPort.indexOf("]") + 1) : hostPort.slice(0, hostPort.includes(":") ? hostPort.lastIndexOf(":") : undefined);
  if (host === "" || host === "[") return "has no host";
  // An empty label (`a..b`, `.a`, or a second trailing dot) is a host that readers split differently; one trailing dot
  // is the fully qualified form. The dot spellings the URL parser reads as a dot count as dots.
  if (!host.startsWith("[") && host.replace(/%2e|[\u3002\uff0e\uff61]/giu, ".").replace(/\.$/u, "").split(".").includes("")) return "has an empty label in its host";
  // The host the URL parser reads too: it drops some characters (a soft hyphen, a zero-width space), which can leave one.
  let parsedHost = "";
  try { parsedHost = new URL(text).hostname; } catch { /* the text is judged as written */ }
  if (parsedHost !== "" && !parsedHost.startsWith("[") && parsedHost.replace(/\.$/u, "").split(".").includes("")) return "has an empty label in its host";
  if (authority.includes("\\") || authority.toLowerCase().includes("%5c")) return "writes its host with a backslash";
  if (/[[\]]|%5[bd]/iu.test(authority.slice(0, Math.max(0, authority.lastIndexOf("@"))))) return "has brackets in its user info";
  if (authority.includes("@")) return "has user info before the host";
  if (!/^https:/iu.test(text) && rest.slice(authority.length).includes("@")) return "has an @ after the host";
  return null;
}

export type PlaintextReason =
  | "not_plain_http" | "loopback" | "ambiguous_host" | "future_agi_host" | "not_opted_in" | "env_proxy" | "caller_proxy" | "opted_in" | "unparsable";

/** Whether `FI_ALLOW_INSECURE_HTTP` is exactly `1`; any other value is not an opt-in. */
export function insecureHttpFromEnv(env: Env = processEnv()): boolean {
  return env.FI_ALLOW_INSECURE_HTTP === "1";
}

/** Whether a written `allowInsecureHttp` is the opt-in: the boolean `true`, or the exact string `"1"` (untyped callers). */
function isWrittenOptIn(value: unknown): boolean {
  return value === true || value === "1";
}

/**
 * Whether credentials may go to `raw` (the URL text as written), with no output and no side effect. Anything but plain
 * HTTP passes, and so does loopback (judged on the host as written). Plain HTTP to another host passes only with the
 * opt-in (`allowInsecureHttp` when not null or undefined: only `true` or the exact string `"1"` opts in, any other value
 * does not; else `FI_ALLOW_INSECURE_HTTP` exactly `1` in `env`), not to a
 * Future AGI host, and not when an environment proxy (`envProxyRoutes`) or the caller's own proxy (`callerProxied`)
 * routes the request. The same decision as the Python client's `plaintext_decision`
 * (tests/fixtures/loopback/proxy_env.json).
 */
export function plaintextDecision(
  raw: string,
  options: { allowInsecureHttp?: boolean | null; env?: Env; callerProxied?: boolean; proxiesDisabled?: boolean } = {},
): { allowed: boolean; reason: PlaintextReason } {
  let parsed: URL | null = null;
  try { parsed = new URL(raw); } catch { /* an http:// text is judged on its shape below */ }
  // The scheme the URL parser reads (it drops tabs and newlines and leading control characters); the text's own when it does not parse.
  const scheme = parsed !== null ? parsed.protocol.slice(0, -1) : /^[\t\n\v\f\r ]*(https?):/iu.exec(raw)?.[1]?.toLowerCase();
  if (scheme !== "http" && scheme !== "https") return parsed === null ? { allowed: true, reason: "unparsable" } : { allowed: true, reason: "not_plain_http" };
  // A host written two ways, or none, is refused whatever the scheme: readers of the URL find different hosts in it.
  if (hostShapeProblem(raw) !== null) return { allowed: false, reason: "ambiguous_host" };
  if (scheme !== "http") return { allowed: true, reason: "not_plain_http" };
  if (parsed === null) return { allowed: true, reason: "unparsable" };
  const url = parsed;
  // A request a proxy of the caller carries is not direct, loopback or not.
  if (isLoopback(raw)) return options.callerProxied === true ? { allowed: false, reason: "caller_proxy" } : { allowed: true, reason: "loopback" };
  if (isFutureAgiHost(url)) return { allowed: false, reason: "future_agi_host" };
  const env = options.env ?? processEnv();
  const optedIn = options.allowInsecureHttp === undefined || options.allowInsecureHttp === null ? insecureHttpFromEnv(env) : isWrittenOptIn(options.allowInsecureHttp);
  if (!optedIn) return { allowed: false, reason: "not_opted_in" };
  if (options.proxiesDisabled !== true && envProxyRoutes(raw, env)) return { allowed: false, reason: "env_proxy" };
  if (options.callerProxied === true) return { allowed: false, reason: "caller_proxy" };
  return { allowed: true, reason: "opted_in" };
}

/**
 * Run only after credentials and their provenance have been checked, before any transport call. `raw` is the URL text
 * as written. Plain http:// to a host that is not loopback is refused unless `allowInsecureHttp` is true or, when it
 * is not given, FI_ALLOW_INSECURE_HTTP is exactly `1`. The opt-in does not apply to a Future AGI host, to a request
 * an HTTP_PROXY or ALL_PROXY routes, or to one the caller's proxy dispatcher routes. With the opt-in on, one warning
 * per process names the setting and the origin. `initDispatcher`: the dispatcher judged is the call's own (`proxyRemedy`); `env`: the environment the opt-in is read from.
 */
export function checkHttpSecurity(
  raw: string,
  mode: "keys" | "bearer",
  allowInsecureHttp?: boolean,
  callerProxied = false,
  proxiesDisabled = false,
  refusal?: "unproven" | "foreign", initDispatcher = false, env?: Env,
): void {
  const { allowed, reason } = plaintextDecision(raw, { allowInsecureHttp, callerProxied, proxiesDisabled, env });
  if (reason === "opted_in") return warnOnce(new URL(raw));
  if (allowed) return;
  if (reason === "ambiguous_host") throw ambiguousHost(raw, mode);
  const url = new URL(raw);
  const what = mode === "bearer" ? "a Bearer token" : "API keys";
  const head = `Refusing to send ${what} over http:// to ${url.host}`;
  const https = "Set the base URL to an https:// address.";
  if (reason === "future_agi_host") throw new ConfigurationError(`${head}: allowInsecureHttp does not apply to a Future AGI host, and neither does FI_ALLOW_INSECURE_HTTP. ${https}`, "insecure_http_origin");
  if (reason === "caller_proxy" && refusal !== undefined) throw new ConfigurationError(`${head}: ${loopbackRefusalText(refusal)}`, "insecure_http_origin");
  if (reason === "env_proxy" || reason === "caller_proxy") throw new ConfigurationError(`${head}: ${proxyRemedy(reason, callerProxied, initDispatcher)}`, "insecure_http_origin");
  const envOptIn = allowInsecureHttp == null ? " (or FI_ALLOW_INSECURE_HTTP=1)" : "";
  throw new ConfigurationError(
    `${head}, which is not loopback. Set the base URL to an https:// address, or set allowInsecureHttp: true${envOptIn} to use plain HTTP.`,
    "insecure_http_origin",
  );
}

/** Why a proxy refusal applies and the remedies that clear it: a dispatcher the SDK proves direct also takes the request off the proxy variables, except a call's own (`plainHttpRouting`). */
function proxyRemedy(reason: "env_proxy" | "caller_proxy", callerProxied: boolean, initDispatcher: boolean): string {
  const env = "unset every proxy variable that routes it (HTTP_PROXY, ALL_PROXY, in any letter case) or add the host to NO_PROXY as well as to every other letter-case spelling of it that is set (no_proxy, NO_proxy)";
  const named = initDispatcher ? "pass an Agent of the undici package as the call's dispatcher" : "install an Agent of the undici package with that package's setGlobalDispatcher";
  const agent = runtimeLoadingUnavailable() ? `Load the SDK as CommonJS and ${named}` : `${named.charAt(0).toUpperCase()}${named.slice(1)}`;
  const https = `or set the base URL to an https:// address${runtimeLoadingUnavailable() ? " on a host that is not loopback" : ""}.`;
  const carrier = initDispatcher ? "the call's dispatcher is a proxy dispatcher (undici ProxyAgent) or another dispatcher the SDK does not prove direct" : "a proxy dispatcher (undici ProxyAgent) routes the request, or another global dispatcher the SDK does not prove direct (an undici EnvHttpProxyAgent it cannot replace with a direct agent, which NODE_USE_ENV_PROXY may install, or the runtime's own agent when the SDK has not read its classes)";
  if (reason === "env_proxy" && !callerProxied) return `allowInsecureHttp does not apply when HTTP_PROXY or ALL_PROXY routes the request. ${env.charAt(0).toUpperCase()}${env.slice(1)}, ${https}`;
  if (reason === "env_proxy") return `allowInsecureHttp does not apply when HTTP_PROXY or ALL_PROXY routes the request and ${carrier}. ${agent}${initDispatcher ? ` and ${env}` : ""}, ${https}`;
  return `allowInsecureHttp does not apply when ${carrier}. ${agent}, ${https}`;
}

function ambiguousHost(raw: string, mode: "keys" | "bearer"): ConfigurationError {
  const problem = hostShapeProblem(raw);
  const https = problem === "has an @ after the host" ? " Switching this URL to https:// also works." : "";
  return new ConfigurationError(
    `Refusing to send ${mode === "bearer" ? "a Bearer token" : "API keys"} to a URL that ${problem ?? "has no host"}: ` +
      "readers of the URL find different hosts in it, and the opt-in does not apply. " +
      `Use a base URL with a single plain host (no user info, no backslash, no empty label, and no @ after the host).${https}`,
    "insecure_http_origin",
  );
}

/**
 * The URL-shape rule alone: a URL with no host, a backslash or brackets in its authority, or an `@` after the authority
 * (http://) is refused with `insecure_http_origin`. A send through a caller-supplied `fetch` with the
 * `customFetchReceivesKeys` opt-in is judged by `checkHttpSecurity` without the proxy rules, which includes this rule.
 */
export function checkUrlShape(raw: string, mode: "keys" | "bearer" = "keys"): void {
  if (plaintextDecision(raw, { allowInsecureHttp: true, proxiesDisabled: true }).reason === "ambiguous_host") throw ambiguousHost(raw, mode);
}

/** The error code of a key-carrying send through a caller-supplied `fetch` without `customFetchReceivesKeys: true`. */
export const CUSTOM_FETCH_CODE = "custom_fetch_not_opted_in";

/**
 * The refusal for a key-carrying send through a caller-supplied `fetch`: the SDK cannot inspect that transport (a
 * ProxyAgent inside it is opaque), so keys, or a Bearer token with `mode` "bearer", go through it only with
 * `customFetchReceivesKeys: true`. No key text.
 */
export function customFetchRefusal(mode: "keys" | "bearer" = "keys"): ConfigurationError {
  const what = mode === "bearer" ? "a Bearer token" : "API keys";
  return new ConfigurationError(
    `Refusing to send ${what} through the caller-supplied fetch option: that transport cannot be inspected, and a proxy ` +
      `inside it would receive ${mode === "bearer" ? "the token" : "the keys"}. Remove the fetch option, or set customFetchReceivesKeys: true if you own the ` +
      "transport (the proxy rules do not apply to that fetch; plain http to a host that is not loopback needs allowInsecureHttp).",
    CUSTOM_FETCH_CODE,
  );
}

function warnOnce(url: URL): void {
  const g = globalThis as Record<symbol, unknown>;
  if (g[WARNED] === true) return;
  g[WARNED] = true;
  console.warn(`futureagi: sending credentials (API keys or a Bearer token) over plain HTTP to ${url.origin} because allowInsecureHttp or FI_ALLOW_INSECURE_HTTP=1 is set. Use an https:// base URL to turn this off.`);
}

/** Test seam shared with the origin guard. */
export function resetHttpWarnings(): void {
  (globalThis as Record<symbol, unknown>)[WARNED] = false;
}
