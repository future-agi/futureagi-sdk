// Plain-http policy for requests that carry a Future AGI key.
//
// A request is keyed when what goes on the wire holds a key: an X-Api-Key, X-Secret-Key or Authorization header (any
// scheme) or another credential-named header (see `isCredentialHeader`), or a user name or password in the URL. A keyed request to an https address is sent as the client sends it,
// except that through a proxy it goes only inside a CONNECT tunnel, with TLS to the host inside the tunnel (see
// "proxies" below). A keyed request to a loopback address over plain http is sent directly. A keyed request to any
// other plain-http address is refused unless the opt-in is set (`allowInsecureHttp: true` in the client options, or
// FI_ALLOW_INSECURE_HTTP=1), and with the opt-in it is sent directly as well. A request without a key is not looked at.

export const INSECURE_HTTP_CODE = "insecure_http_origin";

/** Names of the axios header layers: the `common` layer and the layer named for the method are part of a request. */
const AXIOS_LAYERS = new Set(["common", "delete", "get", "head", "options", "post", "put", "patch"]);

const isObject = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null;

function asText(value: unknown): string {
  return typeof value === "string" ? value : value === undefined || value === null ? "" : String(value);
}

function* entriesOf(source: unknown, axiosMethod?: string): Generator<[string, string]> {
  if (!isObject(source)) {
    return;
  }
  if (typeof (source as { forEach?: unknown }).forEach === "function" && typeof (source as { get?: unknown }).get === "function") {
    const pairs: Array<[string, string]> = [];
    (source as { forEach(callback: (value: unknown, name: string) => void): void }).forEach((value, name) => {
      pairs.push([String(name), asText(value)]);
    });
    yield* pairs;
    return;
  }
  if (source instanceof Map) {
    for (const [name, value] of source) {
      yield [String(name), asText(value)];
    }
    return;
  }
  if (Array.isArray(source)) {
    for (const pair of source) {
      if (Array.isArray(pair) && pair.length === 2) {
        yield [String(pair[0]), asText(pair[1])];
      }
    }
    return;
  }
  for (const [name, value] of Object.entries(source)) {
    const layer = name.trim().toLowerCase();
    if (axiosMethod !== undefined && AXIOS_LAYERS.has(layer) && isObject(value)) {
      if (layer === "common" || layer === axiosMethod.toLowerCase()) {
        yield* entriesOf(value);
      }
      continue;
    }
    yield [name, asText(value)];
  }
}

/** The headers of several layers as one record: a `Headers`, a `Map`, a list of [name, value] pairs or a record each,
 * later layers replacing earlier ones whatever the letter case of the name. With `axiosMethod` the layers are axios
 * header sets, and the nested `common` layer and the one for that method are merged in. */
export function flattenHeaders(layers: readonly unknown[], axiosMethod?: string): Record<string, string> {
  const byName = new Map<string, [string, string]>();
  for (const layer of layers) {
    for (const [name, value] of entriesOf(layer, axiosMethod)) {
      byName.set(name.trim().toLowerCase(), [name, value]);
    }
  }
  return Object.fromEntries(byName.values());
}

const KEY_HEADERS = new Set(["x-api-key", "x-secret-key", "authorization", "proxy-authorization", "cookie"]);
const CREDENTIAL_NAME = /api[-_]?key|secret|token|passw|credential|auth|session|cookie/i;

/** Whether a header name names a credential: X-Api-Key, X-Secret-Key, Authorization, Proxy-Authorization, Cookie, or
 * any name holding "api-key" (or api_key, apikey), "secret", "token", "passw", "credential", "auth", "session" or
 * "cookie" in any letter case. */
export function isCredentialHeader(name: string): boolean {
  const lower = name.trim().toLowerCase();
  return KEY_HEADERS.has(lower) || CREDENTIAL_NAME.test(lower);
}

/** Whether these (already merged) headers carry a key: a credential-named header (see `isCredentialHeader`) with a
 * value that is not empty. */
export function carriesKey(headers: Record<string, unknown>): boolean {
  for (const [name, value] of Object.entries(headers)) {
    if (isCredentialHeader(name) && asText(Array.isArray(value) ? value.join(",") : value).trim() !== "") {
      return true;
    }
  }
  return false;
}

/** Whether the URL holds a user name or password (sent as an Authorization header by most HTTP clients). */
export function hasUserinfo(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.username !== "" || parsed.password !== "";
  } catch {
    return /^[a-z][a-z0-9+.-]*:\/\/[^/?#]*@/i.test(url);
  }
}

/** Whether the URL names this machine: `localhost`, an address of 127.0.0.0/8, or `::1`. */
export function isLoopback(url: URL): boolean {
  const host = url.hostname.toLowerCase();
  return host === "localhost" || host === "[::1]" || /^127(\.\d{1,3}){3}$/.test(host);
}

/** The opt-in: the option when it is given (only `true` or the exact string "1" enable it), else FI_ALLOW_INSECURE_HTTP
 * equal to the exact string "1". */
export function insecureHttpAllowed(option: unknown): boolean {
  if (option !== undefined && option !== null) {
    return option === true || option === "1";
  }
  const env = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env;
  return env?.FI_ALLOW_INSECURE_HTTP === "1";
}

export function insecureHttpError(message: string): Error {
  return Object.assign(new Error(message), { code: INSECURE_HTTP_CODE });
}

export type PlainHttpRoute = "unchanged" | "direct";

/**
 * How a request to `url` is sent. `unchanged`: the request is not keyed (by `keyed` or by a user name or password in
 * the URL), or the URL is not plain http. `direct`: a keyed
 * plain-http request that goes straight to its host, with no proxy. Throws an Error with code `insecure_http_origin`
 * for a keyed plain-http request to a host that is not loopback without the opt-in.
 */
export function plainHttpRoute(url: string, keyed: boolean, option: unknown): PlainHttpRoute {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return "unchanged";
  }
  if (parsed.protocol !== "http:" || !(keyed || parsed.username !== "" || parsed.password !== "")) {
    return "unchanged";
  }
  if (isLoopback(parsed) || insecureHttpAllowed(option)) {
    return "direct";
  }
  throw insecureHttpError(
    `Requests that carry credentials are not sent over plain http to ${parsed.host}. Use an https:// base URL, ` +
      "or set allowInsecureHttp: true (or FI_ALLOW_INSECURE_HTTP=1) to send over plain http.",
  );
}

/** Whether a URL text is plain http to this machine (see `isLoopback`). */
export function isLoopbackUrl(url: string): boolean {
  try {
    return isLoopback(new URL(url));
  } catch {
    return false;
  }
}

/** The Error with code `insecure_http_origin` in `error` or in its chain of causes (an HTTP client may wrap it). */
export function insecureHttpCause(error: unknown): Error | undefined {
  const seen = new Set<unknown>();
  for (let current = error; isObject(current) && !seen.has(current); current = (current as { cause?: unknown }).cause) {
    seen.add(current);
    if ((current as { code?: unknown }).code === INSECURE_HTTP_CODE && current instanceof Error) {
      return current;
    }
  }
  return undefined;
}

type NodeHttp = typeof import("node:http");

let sharedDirectAgent: import("node:http").Agent | undefined;

/** The one agent for keyed plain-http requests that are sent: a new Node `http.Agent` of the SDK's own, which connects
 * to the host itself (no proxy, no global agent or dispatcher). Idle sockets are unref'd, so they do not keep the
 * process running. */
export function directHttpAgent(http: NodeHttp): import("node:http").Agent {
  sharedDirectAgent = sharedDirectAgent || new http.Agent({ keepAlive: true });
  return sharedDirectAgent;
}

const runtimeFetchConfigs = new WeakSet<object>();

/** Record that `config` uses the runtime's fetch because the caller gave none. */
export function markRuntimeFetch<T extends object>(config: T): T {
  runtimeFetchConfigs.add(config);
  return config;
}

/** Whether `config` uses the runtime's fetch because the caller gave none (see `markRuntimeFetch`). */
export function usesRuntimeFetch(config: object): boolean {
  return runtimeFetchConfigs.has(config);
}

export interface DirectInit {
  method: string;
  headers: Record<string, string>;
  body?: unknown;
  signal?: AbortSignal;
  /** Milliseconds a connection (a proxy tunnel included) may take to open. */
  timeout?: number;
}

/**
 * Send one request with Node's http module and answer it as a fetch `Response` (redirects are not followed): straight
 * to its host with the agent of `directHttpAgent`, or, with `proxy`, inside a CONNECT tunnel through that proxy (see
 * `tunnelAgent`). `null` when the runtime has no `node:http` (or, for a tunnel, no `node:https`, `node:net` or `node:tls`).
 */
export async function sendDirect(url: string, init: DirectInit, proxy?: ProxyEndpoint): Promise<Response | null> {
  let http: NodeHttp;
  let agent: import("node:http").Agent;
  const target = new URL(url);
  try {
    http = await import("node:http");
    if (proxy === undefined) {
      agent = directHttpAgent(http);
    } else {
      const [https, net, tls] = await Promise.all([import("node:https"), import("node:net"), import("node:tls")]);
      agent = tunnelAgent({ http, https, net, tls }, proxy, target.protocol === "https:");
    }
  } catch (error) {
    if (insecureHttpCause(error)) {
      throw error;
    }
    return null;
  }
  if (target.username !== "" || target.password !== "") {
    throw new TypeError(`Request cannot be constructed from a URL that includes credentials: ${url}`);
  }
  const prepared = init.body === undefined || init.body === null ? undefined : new Response(init.body as ConstructorParameters<typeof Response>[0]);
  const payload = prepared === undefined ? undefined : new Uint8Array(await prepared.arrayBuffer());
  const headers: Record<string, string> = { ...init.headers };
  const named = new Set(Object.keys(headers).map((name) => name.toLowerCase()));
  const type = prepared?.headers.get("content-type");
  if (type && !named.has("content-type")) {
    headers["content-type"] = type;
  }
  if (!named.has("accept")) {
    headers.accept = "*/*";
  }
  if (payload !== undefined && !named.has("content-length")) {
    headers["content-length"] = String(payload.byteLength);
  }
  const { status, statusText, received, body } = await new Promise<{ status: number; statusText: string; received: Record<string, string | string[] | undefined>; body: Uint8Array }>(
    (resolve, reject) => {
      // ClientRequest itself, not http.request: a process-wide wrapper of http.request may replace the agent.
      const options = {
        protocol: target.protocol,
        hostname: target.hostname.replace(/^\[|\]$/g, ""),
        port: target.port === "" ? (target.protocol === "https:" ? 443 : 80) : Number(target.port),
        path: target.pathname + target.search,
        method: init.method,
        headers,
        agent,
        signal: init.signal,
        timeout: init.timeout,
      };
      const request = new http.ClientRequest(options, (response) => {
        const chunks: Uint8Array[] = [];
        response.on("data", (chunk: Uint8Array) => chunks.push(chunk));
        response.on("error", (error) => reject(init.signal?.aborted ? init.signal.reason : error));
        response.on("aborted", () => reject(new Error("the response was cut short")));
        response.on("end", () => {
          const size = chunks.reduce((total, chunk) => total + chunk.byteLength, 0);
          const all = new Uint8Array(size);
          let at = 0;
          for (const chunk of chunks) {
            all.set(chunk, at);
            at += chunk.byteLength;
          }
          resolve({ status: response.statusCode ?? 0, statusText: response.statusMessage ?? "", received: response.headers, body: all });
        });
      });
      request.on("error", (error) => reject(init.signal?.aborted ? init.signal.reason : error));
      // An abort while the request waits for its connection (a tunnel being opened) settles the call too.
      init.signal?.addEventListener("abort", () => reject(init.signal?.reason), { once: true });
      if ((request as unknown as { agent?: unknown }).agent !== agent) {
        request.destroy();
        reject(insecureHttpError(`The request to ${target.host} cannot be sent ${proxy === undefined ? "directly over plain http" : "through the proxy tunnel"}: the HTTP agent was replaced.`));
        return;
      }
      request.end(payload);
    },
  );
  const responseHeaders = new Headers();
  for (const [name, value] of Object.entries(received)) {
    for (const item of Array.isArray(value) ? value : value === undefined ? [] : [value]) {
      try {
        responseHeaders.append(name, item);
      } catch {
        /* a value fetch would not accept either */
      }
    }
  }
  const empty = init.method.toUpperCase() === "HEAD" || status === 204 || status === 205 || status === 304;
  const decoded = empty ? null : await decodeBody(body, responseHeaders.get("content-encoding"));
  return new Response(decoded as ConstructorParameters<typeof Response>[0], { status, statusText, headers: responseHeaders });
}

/** The body as fetch would give it: gzip, deflate and br content codings are undone. */
async function decodeBody(body: Uint8Array, encoding: string | null): Promise<Uint8Array> {
  const codings = (encoding ?? "").split(",").map((coding) => coding.trim().toLowerCase()).filter((coding) => coding !== "" && coding !== "identity");
  if (codings.length === 0 || body.byteLength === 0) {
    return body;
  }
  const zlib = await import("node:zlib");
  let data = body;
  for (const coding of codings.reverse()) {
    if (coding === "gzip" || coding === "x-gzip") {
      data = zlib.gunzipSync(data);
    } else if (coding === "deflate") {
      try {
        data = zlib.inflateSync(data);
      } catch {
        data = zlib.inflateRawSync(data); // a deflate body without the zlib wrapper, as fetch accepts
      }
    } else if (coding === "br") {
      data = zlib.brotliDecompressSync(data);
    } else {
      return body;
    }
  }
  return data;
}

// --- proxies ------------------------------------------------------------------------------------------------------
//
// A keyed request for which a proxy applies goes to that proxy only as `CONNECT host:port`, and the request itself
// travels inside the tunnel (TLS from end to end for an https address). The CONNECT carries a Host header and, when the
// proxy address or config holds a user name or password, a Proxy-Authorization header; no other header of the request.

/** A proxy as the SDK reaches it. `auth` is the `user:password` text of axios (sent as Basic on the CONNECT only).
 * `authorization`: a Proxy-Authorization value the caller set on the request, sent on the CONNECT only, and only when
 * the proxy has no `auth` of its own. */
export interface ProxyEndpoint {
  protocol: string;
  hostname: string;
  port: number;
  auth?: string;
  authorization?: string;
}

/** The Proxy-Authorization value axios builds from the proxy's own user name and password, or `undefined`. */
export function ownProxyAuthorization(proxy: ProxyEndpoint | null): string | undefined {
  return proxy?.auth === undefined ? undefined : `Basic ${Buffer.from(proxy.auth, "utf8").toString("base64")}`;
}

/** Errors of a proxy that answered CONNECT with a status other than 200. */
const tunnelRefusals = new WeakSet<object>();

/** Whether `error` (or its cause) is such an answer of a proxy (see `tunnelRefusals`). */
export function isTunnelRefusal(error: unknown): boolean {
  for (let current = error, depth = 0; isObject(current) && depth < 5; current = (current as { cause?: unknown }).cause, depth++) {
    if (tunnelRefusals.has(current)) {
      return true;
    }
  }
  return false;
}

const DEFAULT_PORTS: Record<string, number> = { ftp: 21, gopher: 70, http: 80, https: 443, ws: 80, wss: 443 };

function envText(name: string): string {
  const env = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
  return env[name.toLowerCase()] || env[name.toUpperCase()] || "";
}

/** Whether NO_PROXY (or no_proxy, npm_config_no_proxy) lets `hostname`:`port` be reached without a proxy: `*`, a
 * host, or a domain written with a leading `.` or `*`, each with an optional `:port`, read as axios reads them. */
function bypassed(hostname: string, port: number): boolean {
  const list = (envText("npm_config_no_proxy") || envText("no_proxy")).toLowerCase();
  if (!list) {
    return false;
  }
  if (list === "*") {
    return true;
  }
  return !list.split(/[,\s]/).every((entry) => {
    if (!entry) {
      return true;
    }
    const withPort = entry.match(/^(.+):(\d+)$/);
    let name = withPort ? withPort[1] : entry;
    const entryPort = withPort ? parseInt(withPort[2], 10) : 0;
    if (entryPort && entryPort !== port) {
      return true;
    }
    if (!/^[.*]/.test(name)) {
      return hostname !== name;
    }
    if (name.charAt(0) === "*") {
      name = name.slice(1);
    }
    return !hostname.endsWith(name);
  });
}

/** The proxy address the environment names for `url`, as axios reads it (npm_config_<scheme>_proxy, <scheme>_proxy,
 * npm_config_proxy, all_proxy, each in lower or upper case, unless NO_PROXY exempts the host), or "". */
export function envProxyFor(url: string): string {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return "";
  }
  const scheme = parsed.protocol.split(":", 1)[0];
  const hostname = parsed.host.replace(/:\d*$/, "");
  if (!hostname) {
    return "";
  }
  const port = parseInt(parsed.port, 10) || DEFAULT_PORTS[scheme] || 0;
  if (bypassed(hostname, port)) {
    return "";
  }
  const proxy = envText(`npm_config_${scheme}_proxy`) || envText(`${scheme}_proxy`) || envText("npm_config_proxy") || envText("all_proxy");
  return proxy && !proxy.includes("://") ? `${scheme}://${proxy}` : proxy;
}

/** The axios `proxy` setting: `false`, an object with `protocol`, `host` (or `hostname`), `port` and `auth`. */
interface AxiosProxyLike {
  protocol?: string;
  host?: string;
  hostname?: string;
  port?: number | string;
  username?: string;
  password?: string;
  auth?: string | { username?: string; password?: string };
}

/**
 * The proxy a request to `url` goes through, chosen as the axios http adapter chooses it: none for `proxy: false`;
 * the `proxy` object when one is given (NO_PROXY is not read for it, and without a `protocol` the proxy is spoken to
 * with the scheme of `url`); else the proxy the environment names (see `envProxyFor`). `null` when there is none.
 * Throws the refusal when the proxy address cannot be read.
 */
export function proxyFor(url: string, configProxy?: unknown): ProxyEndpoint | null {
  if (configProxy === false) {
    return null;
  }
  let proxy: AxiosProxyLike;
  if (isObject(configProxy)) {
    proxy = configProxy as AxiosProxyLike;
  } else {
    const named = envProxyFor(url);
    if (!named) {
      return null;
    }
    try {
      proxy = new URL(named);
    } catch {
      throw insecureHttpError("A request that carries credentials is not sent: the proxy address in the environment cannot be read.");
    }
  }
  let protocol = proxy.protocol ? (proxy.protocol.includes(":") ? proxy.protocol : `${proxy.protocol}:`) : new URL(url).protocol;
  protocol = protocol.toLowerCase();
  const hostname = String(proxy.hostname || proxy.host || "").replace(/^\[|\]$/g, "");
  let auth: string | undefined;
  if (proxy.username) {
    auth = `${proxy.username || ""}:${proxy.password || ""}`;
  } else if (isObject(proxy.auth)) {
    auth = proxy.auth.username || proxy.auth.password ? `${proxy.auth.username || ""}:${proxy.auth.password || ""}` : undefined;
  } else if (typeof proxy.auth === "string" && proxy.auth !== "") {
    auth = proxy.auth;
  }
  const scheme = protocol.replace(/:$/, "");
  return { protocol, hostname, port: Number(proxy.port) || DEFAULT_PORTS[scheme] || 80, auth };
}

/** Throws the refusal unless `proxy` can carry a tunnel: an http or https proxy with a host. */
export function assertTunnelProxy(proxy: ProxyEndpoint): void {
  if ((proxy.protocol !== "http:" && proxy.protocol !== "https:") || proxy.hostname === "") {
    throw insecureHttpError(
      `A request that carries credentials is not sent through the ${proxy.protocol.replace(/:$/, "")} proxy ${proxy.hostname}: ` +
        "only an http or https proxy carries it, inside a CONNECT tunnel.",
    );
  }
}

/** The Node modules a tunnel is made with. */
export interface TunnelModules {
  http: typeof import("node:http");
  https: typeof import("node:https");
  net: typeof import("node:net");
  tls: typeof import("node:tls");
}

/** TLS settings of a caller's `https.Agent` that the tunnel uses for the connection to the target. */
const TLS_KEYS = [
  "ca", "cert", "key", "pfx", "passphrase", "rejectUnauthorized", "checkServerIdentity", "ciphers", "ecdhCurve", "crl",
  "minVersion", "maxVersion", "secureProtocol", "secureOptions", "sigalgs", "honorCipherOrder", "dhparam", "privateKeyEngine",
  "privateKeyIdentifier", "clientCertEngine", "sessionIdContext", "ALPNProtocols",
];

/** The TLS settings of `agent` (a caller's `https.Agent`), or `undefined`. */
export function tlsSettingsOf(agent: unknown): Record<string, unknown> | undefined {
  const options = isObject(agent) ? (agent as { options?: unknown }).options : undefined;
  if (!isObject(options)) {
    return undefined;
  }
  const picked: Record<string, unknown> = {};
  for (const name of TLS_KEYS) {
    if (options[name] !== undefined) {
      picked[name] = options[name];
    }
  }
  return Object.keys(picked).length > 0 ? picked : undefined;
}

/** The most tunnel agents kept in one cache (see `tunnelAgent`): the least recently used one past it is let go. */
const TUNNEL_AGENT_LIMIT = 16;

const tunnelAgents = new Map<string, import("node:http").Agent>();
/** Where a tunnel agent finds, in the options of a connection, the hook of the request that waits for it. */
const WATCH = Symbol("futureagi.tunnelWatch");
const tunnelAgentsBySettings = new WeakMap<object, Map<string, import("node:http").Agent>>();

/** The CONNECT authority for a host and port (an IPv6 address in brackets). */
function authority(host: string, port: number): string {
  const bare = host.replace(/^\[|\]$/g, "");
  return `${bare.includes(":") ? `[${bare}]` : bare}:${port}`;
}

/** Let go of a tunnel agent that left its cache: its idle connections close, and each connection in use closes when its
 * request ends (a request waiting for that agent is given one of them first). */
function retire(agent: import("node:http").Agent): void {
  (agent as unknown as { keepSocketAlive(socket: unknown): boolean }).keepSocketAlive = () => false;
  for (const sockets of Object.values(agent.freeSockets)) {
    for (const socket of sockets ?? []) {
      socket.destroy();
    }
  }
}

/**
 * An agent of the SDK whose connections are CONNECT tunnels through `proxy`: for a `secure` target, TLS to the target
 * runs inside the tunnel (with the default CAs, or the TLS settings of the caller's agent given as `tlsSettings`).
 * Keep-alive; one agent per proxy, Proxy-Authorization value, kind of target and settings, and at most
 * `TUNNEL_AGENT_LIMIT` of them kept per cache, the least recently used one let go first.
 */
export function tunnelAgent(modules: TunnelModules, proxy: ProxyEndpoint, secure: boolean, tlsSettings?: Record<string, unknown>, settingsOwner?: object): import("node:http").Agent {
  assertTunnelProxy(proxy);
  const connectAuthorization = proxy.auth !== undefined ? `Basic ${Buffer.from(proxy.auth, "utf8").toString("base64")}` : proxy.authorization;
  if (connectAuthorization !== undefined && /[\r\n]/.test(connectAuthorization)) {
    throw insecureHttpError("A request that carries credentials is not sent: its Proxy-Authorization value holds a line break.");
  }
  const id = `${proxy.protocol}//${connectAuthorization ?? ""}@${authority(proxy.hostname, proxy.port)}|${secure ? "https" : "http"}`;
  const cache = settingsOwner === undefined ? tunnelAgents : tunnelAgentsBySettings.get(settingsOwner) ?? new Map<string, import("node:http").Agent>();
  if (settingsOwner !== undefined) {
    tunnelAgentsBySettings.set(settingsOwner, cache);
  }
  const cached = cache.get(id);
  if (cached) {
    cache.delete(id);
    cache.set(id, cached); // the most recently used last
    return cached;
  }
  const { net, tls } = modules;
  const Base = (secure ? modules.https.Agent : modules.http.Agent) as typeof import("node:http").Agent;
  const where = authority(proxy.hostname, proxy.port);
  class TunnelAgent extends Base {
    addRequest(request: import("node:http").ClientRequest, options: Record<string | symbol, unknown>): void {
      // A request destroyed (aborted, canceled, timed out) while its tunnel is being opened closes that connection.
      const watch: { gone?: () => void } = {};
      const destroy = request.destroy;
      request.destroy = function (this: import("node:http").ClientRequest, error?: Error) {
        watch.gone?.();
        return destroy.call(this, error);
      } as typeof request.destroy;
      (Base.prototype as unknown as { addRequest(request: unknown, options: unknown): void }).addRequest.call(this, request, { ...options, [WATCH]: watch });
    }

    createConnection(options: Record<string, unknown>, callback: (error: Error | null, socket?: import("node:net").Socket) => void): undefined {
      const host = String(options.host || options.hostname || "localhost");
      const port = Number(options.port) || (secure ? 443 : 80);
      const target = authority(host, port);
      const toProxy: import("node:net").Socket =
        proxy.protocol === "https:"
          ? tls.connect({ host: proxy.hostname, port: proxy.port, servername: net.isIP(proxy.hostname) ? undefined : proxy.hostname })
          : net.connect({ host: proxy.hostname, port: proxy.port });
      let settled = false;
      const watch = options[WATCH as unknown as string] as { gone?: () => void } | undefined;
      const fail = (error: Error) => {
        if (!settled) {
          settled = true;
          if (watch) {
            watch.gone = undefined;
          }
          toProxy.destroy();
          callback(error);
        }
      };
      if (watch) {
        watch.gone = () => fail(new Error(`The request was canceled before the tunnel to ${target} through the proxy at ${where} was open.`));
      }
      toProxy.once("error", fail);
      const onClose = () => fail(new Error(`The proxy at ${where} closed the connection before the tunnel to ${target} was open.`));
      toProxy.once("close", onClose);
      const timeout = Number(options.timeout);
      if (timeout > 0) {
        toProxy.setTimeout(timeout, () =>
          fail(Object.assign(new Error(`The tunnel to ${target} through the proxy at ${where} was not open after ${timeout} ms.`), { code: "ETIMEDOUT" })),
        );
      }
      toProxy.once(proxy.protocol === "https:" ? "secureConnect" : "connect", () => {
        const lines = [`CONNECT ${target} HTTP/1.1`, `Host: ${target}`];
        if (connectAuthorization !== undefined) {
          lines.push(`Proxy-Authorization: ${connectAuthorization}`);
        }
        toProxy.write(`${lines.join("\r\n")}\r\n\r\n`);
      });
      let received = Buffer.alloc(0);
      const onData = (chunk: Buffer) => {
        received = Buffer.concat([received, chunk]);
        const end = received.indexOf("\r\n\r\n");
        if (end < 0) {
          if (received.length > 65536) {
            fail(new Error(`The proxy at ${where} sent no complete answer to CONNECT ${target}.`));
          }
          return;
        }
        toProxy.removeListener("data", onData);
        const status = Number(received.subarray(0, received.indexOf("\r\n")).toString("latin1").split(" ")[1]);
        if (status !== 200) {
          const refusal = new Error(`The proxy at ${where} answered ${status || "without a status"} to CONNECT ${target}; the request was not sent.`);
          tunnelRefusals.add(refusal);
          fail(refusal);
          return;
        }
        settled = true;
        if (watch) {
          watch.gone = undefined;
        }
        toProxy.removeListener("close", onClose);
        toProxy.removeListener("error", fail);
        toProxy.setTimeout(0);
        const rest = received.subarray(end + 4);
        if (rest.length > 0) {
          toProxy.unshift(rest);
        }
        if (!secure) {
          callback(null, toProxy);
          return;
        }
        const servername = typeof options.servername === "string" && options.servername !== "" ? options.servername : net.isIP(host.replace(/^\[|\]$/g, "")) ? undefined : host;
        // `host` names the target, so its certificate is checked against the target (also for an IP address).
        callback(null, tls.connect({ ...(tlsSettings ?? {}), socket: toProxy, host: host.replace(/^\[|\]$/g, ""), servername }));
      };
      toProxy.on("data", onData);
      return undefined;
    }
  }
  const agent = new TunnelAgent({ keepAlive: true });
  cache.set(id, agent);
  for (const [oldest, retired] of cache) {
    if (cache.size <= TUNNEL_AGENT_LIMIT) {
      break;
    }
    cache.delete(oldest);
    retire(retired);
  }
  return agent;
}
