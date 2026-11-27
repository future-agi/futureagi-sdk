// The one HTTP layer every resource uses: auth, retries, envelope unwrap, errors.
// Mirrors the Python `fi/platform/_transport.py`; the same catalog drives both.

import { APIConnectionError, APIError, errorFromResponse, isRecord } from "./errors";
import { getPath, Pager, Pagination } from "./pagination";
import { INSECURE_HTTP_CODE, ProxyEndpoint, carriesKey, flattenHeaders, insecureHttpError, isLoopbackUrl, plainHttpRoute, proxyFor, sendDirect, usesRuntimeFetch } from "../utils/plain-http";

/** What generated code passes in for each call (emitted from the catalog). */
export interface Operation {
  id: string;
  method: string;
  path: string;
  unwrap: string | null;
  pagination: Pagination | null;
  /** Body fields go as form data, file params as uploads. */
  multipart?: boolean;
  /** How the response body is read: JSON (default), text, or auto (JSON when the response says so, else text). */
  decode?: "json" | "text" | "auto";
  /** The contract leaves the `{status, result}` envelope out of many responses, so by default one is removed
   * whenever present even when `unwrap` names no key. `client.request(..., { unwrap: null })` turns that off. */
  autoUnwrap?: boolean;
}

/** A file parameter: a path (Node only), raw bytes, a Blob, or an explicit name + content. */
export type FileInput = string | Uint8Array | Blob | { name: string; data: Uint8Array | Blob | string };

/** Any JSON value, for the request fields the backend accepts as such (`x-json-value` in the contract):
 * a string or number is as valid there as an object. */
export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

/** Per-call overrides, accepted by every generated method as its last argument. */
export interface RequestOptions {
  /** Added to (and overriding) the client's headers. */
  headers?: Record<string, string>;
  /** Milliseconds. */
  timeout?: number;
  maxRetries?: number;
  /** Query fields the contract does not describe yet. */
  extraQuery?: Record<string, unknown>;
  /** Body fields the contract does not describe yet (JSON and form bodies). */
  extraBody?: Record<string, unknown>;
}

export interface RequestArgs {
  path?: Record<string, string>;
  query?: Record<string, unknown>;
  body?: unknown;
  files?: Record<string, FileInput | FileInput[] | undefined>;
}

export type FetchLike = (url: string, init: RequestInit) => Promise<Response>;

export interface ResolvedConfig {
  apiKey: string;
  secretKey: string;
  baseUrl: string;
  workspaceId?: string;
  /** Milliseconds. */
  timeout: number;
  maxRetries: number;
  defaultHeaders?: Record<string, string>;
  /** Send keyed requests over plain http to hosts that are not loopback (also FI_ALLOW_INSECURE_HTTP=1). */
  allowInsecureHttp?: boolean;
  fetch: FetchLike;
}

// 429 means the server did not process the request, so any method may retry it. A
// timeout, a 5xx or a dropped connection may have happened after a write was applied,
// so those are retried only for methods that are safe to repeat.
const RETRY_ANY_METHOD = new Set([429]);
const RETRY_IDEMPOTENT = new Set([408, 500, 502, 503, 504]);
const IDEMPOTENT_METHODS = new Set(["GET", "HEAD", "OPTIONS", "PUT", "DELETE"]);
const REDIRECT_STATUSES = new Set([301, 302, 303, 307, 308]);
const MAX_REDIRECTS = 5;

/** Later layers replace earlier ones whatever the letter case: `x-workspace-id` set per call replaces the
 * client's `X-Workspace-Id` instead of being sent next to it (header names are case-insensitive, and a
 * server given both may combine or reject them). */
function mergeHeaders(...layers: Array<Record<string, string> | undefined>): Record<string, string> {
  return flattenHeaders(layers); // a layer given as `Headers`, a `Map` or [name, value] pairs is read as headers too
}

const originOf = (url: string) => new URL(url).origin.toLowerCase();

/** Where to follow a redirect, when its target is on the client's own origin. The credentials travel in
 * custom headers (`X-Api-Key`, `X-Secret-Key`) that fetch does not strip on a cross-origin redirect the way
 * it strips `Authorization`, so a redirect that leaves the origin is refused instead of followed. */
function followRedirect(baseUrl: string, from: string, status: number, location: string, method: string): { url: string; method: string } {
  const target = new URL(location, from).toString();
  if (originOf(target) !== originOf(baseUrl)) {
    throw new APIConnectionError(`${status} redirect to ${target} was not followed: it leaves ${baseUrl} and the API keys would go with it`);
  }
  const asGet = status === 303 || ((status === 301 || status === 302) && method === "POST"); // the way browsers re-issue these
  return { url: target, method: asGet ? "GET" : method };
}

/** Release a response we will not read, so its connection is free for the next attempt. Not awaited:
 * cancelling one branch of a cloned body settles only when the other is done too, which would hang. */
function discard(response: Response): void {
  response.body?.cancel().catch(() => undefined);
}

function canRetry(op: Operation, status: number | null, attempt: number, maxRetries: number): boolean {
  if (attempt >= maxRetries) {
    return false;
  }
  if (status === null) {
    return IDEMPOTENT_METHODS.has(op.method); // transport error: the request may have reached the server
  }
  return RETRY_ANY_METHOD.has(status) || (RETRY_IDEMPOTENT.has(status) && IDEMPOTENT_METHODS.has(op.method));
}

function backoffMs(attempt: number, retryAfter: string | null): number {
  if (retryAfter) {
    const seconds = Number(retryAfter);
    if (!Number.isNaN(seconds)) {
      return Math.min(seconds, 30) * 1000;
    }
  }
  return Math.min(500 * 2 ** attempt, 8000) * (0.75 + Math.random() / 2);
}

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

/** An ad-hoc operation for an endpoint the catalog does not describe (`client.request`). */
export function rawOperation(method: string, path: string, unwrap: string | null = "result", multipart = false, decode: Operation["decode"] = "json"): Operation {
  if (!path.startsWith("/")) {
    throw new Error(`path must start with '/', got ${JSON.stringify(path)}`);
  }
  // unwrap: null is an explicit "give me the whole body"
  return { id: `raw:${method.toUpperCase()} ${path}`, method: method.toUpperCase(), path, unwrap, pagination: null, multipart, decode, autoUnwrap: unwrap !== null };
}

function buildUrl(config: ResolvedConfig, op: Operation, args: RequestArgs, options?: RequestOptions): string {
  let path = op.path;
  for (const [name, value] of Object.entries(args.path ?? {})) {
    path = path.replace(`{${name}}`, encodeURIComponent(String(value)));
  }
  const url = new URL(config.baseUrl + path);
  for (const [key, value] of Object.entries({ ...(args.query ?? {}), ...(options?.extraQuery ?? {}) })) {
    if (value === undefined || value === null) {
      continue;
    }
    for (const item of Array.isArray(value) ? value : [value]) {
      url.searchParams.append(key, formValue(item));
    }
  }
  return url.toString();
}

function formValue(value: unknown): string {
  if (typeof value === "boolean") {
    return value ? "true" : "false"; // the way DRF parses them
  }
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

function cleanBody(body: unknown, extra?: Record<string, unknown>): unknown {
  if (!isRecord(body)) {
    return body; // a non-object body (e.g. a list) is sent as is
  }
  const merged: Record<string, unknown> = { ...body, ...(extra ?? {}) };
  for (const key of Object.keys(merged)) {
    if (merged[key] === undefined) {
      delete merged[key]; // not passed; an explicit null is sent, that is how a nullable field is cleared
    }
  }
  return merged;
}

async function toBlob(file: FileInput): Promise<{ name: string; blob: Blob }> {
  if (typeof file === "string") {
    const { readFile } = await import("node:fs/promises");
    const { basename } = await import("node:path");
    return { name: basename(file), blob: new Blob([new Uint8Array(await readFile(file))]) };
  }
  if (file instanceof Uint8Array) {
    return { name: "upload", blob: new Blob([file]) };
  }
  if (file instanceof Blob) {
    return { name: (file as File).name ?? "upload", blob: file };
  }
  const data = file.data instanceof Blob ? file.data : new Blob([typeof file.data === "string" ? file.data : new Uint8Array(file.data)]);
  return { name: file.name, blob: data };
}

async function buildBody(op: Operation, args: RequestArgs, options?: RequestOptions): Promise<{ body?: RequestInit["body"]; headers: Record<string, string> }> {
  if (!op.multipart) {
    if (args.files && Object.values(args.files).some((v) => v !== undefined)) {
      throw new TypeError(`${op.id}: files are only accepted by multipart operations`);
    }
    if (args.body === undefined) {
      return { headers: {} };
    }
    return { body: JSON.stringify(cleanBody(args.body, options?.extraBody)), headers: { "Content-Type": "application/json" } };
  }
  const form = new FormData();
  const fields = cleanBody(args.body ?? {}, options?.extraBody);
  if (isRecord(fields)) {
    for (const [key, value] of Object.entries(fields)) {
      if (value !== null) {
        form.append(key, formValue(value)); // a form field cannot carry null
      }
    }
  }
  for (const [field, value] of Object.entries(args.files ?? {})) {
    if (value === undefined || value === null) {
      continue;
    }
    for (const item of Array.isArray(value) ? value : [value]) {
      const { name, blob } = await toBlob(item);
      form.append(field, blob, name);
    }
  }
  return { body: form, headers: {} }; // fetch sets the multipart boundary itself
}

function decode(op: Operation, status: number, headers: Headers, text: string): unknown {
  if (status === 204 || text.length === 0) {
    return null;
  }
  const contentType = headers.get("content-type") ?? "";
  if (op.decode === "text" || (op.decode === "auto" && !contentType.includes("json"))) {
    return text; // e.g. a CSV export: the body is the result
  }
  let data: unknown;
  try {
    data = JSON.parse(text);
  } catch {
    throw new APIError(`${status} non-JSON response (${contentType || "unknown"})`, status, text, headers.get("x-request-id"));
  }
  if (op.unwrap && isRecord(data) && op.unwrap in data) {
    return data[op.unwrap];
  }
  // The backend wraps most successes in {status, result}, but the contract often leaves
  // the envelope out, so unwrap it whenever it is exactly that shape.
  if (op.autoUnwrap !== false && isRecord(data) && Object.keys(data).length === 2 && data.status === true && "result" in data) {
    return data.result;
  }
  return data;
}

type Route = { kind: "fetch" } | { kind: "direct" } | { kind: "tunnel"; proxy: ProxyEndpoint };

/** How a request to `url` is sent: `fetch` (the configured fetch, as given), `direct` (straight to its host, with the
 * SDK's own Node agent: a keyed plain-http request of a client that uses the runtime's fetch) or `tunnel` (a keyed
 * https request of a client that uses the runtime's fetch, when the environment names a proxy for `url`: sent by the
 * SDK inside a CONNECT tunnel through that proxy, with TLS to its host inside the tunnel). Throws the
 * refusal for a keyed plain-http request that cannot be sent directly (a fetch supplied by the caller, to a host that
 * is not loopback) and for a keyed request whose proxy cannot carry a tunnel. */
function routing(config: ResolvedConfig, url: string, headers: Record<string, string>): Route {
  const keyed = carriesKey(headers);
  const plain = plainHttpRoute(url, keyed, config.allowInsecureHttp);
  if (usesRuntimeFetch(config) && keyed && plain === "unchanged" && /^https:/i.test(url)) {
    const proxy = proxyFor(url);
    if (proxy !== null) {
      return { kind: "tunnel", proxy };
    }
  }
  if (plain === "unchanged") {
    return { kind: "fetch" };
  }
  if (usesRuntimeFetch(config)) {
    return { kind: "direct" };
  }
  if (isLoopbackUrl(url)) {
    return { kind: "fetch" }; // the caller's fetch decides how to reach this machine
  }
  throw cannotSendDirectly(url);
}

function cannotSendDirectly(url: string): Error {
  return insecureHttpError(
    `The request to ${new URL(url).host} cannot be sent directly over plain http: the transport in use may route it through a proxy. ` +
      "Use an https:// base URL.",
  );
}

/** Send `init` to `url` by the route `routing` chose. */
async function send(config: ResolvedConfig, url: string, init: RequestInit & { method: string; headers: Record<string, string> }, route: Route): Promise<Response> {
  if (route.kind !== "fetch") {
    let proxy = route.kind === "tunnel" ? route.proxy : undefined;
    let headers = init.headers;
    // A Proxy-Authorization the caller set is for the proxy: it goes on the CONNECT (when the proxy has no user name and
    // password of its own), and not inside the tunnel to the host. On the direct route there is no proxy, and it is not sent.
    for (const proxyAuthName of Object.keys(headers).filter((name) => name.trim().toLowerCase() === "proxy-authorization")) {
      const { [proxyAuthName]: callerProxyAuth, ...rest } = headers;
      headers = rest;
      if (proxy !== undefined && proxy.auth === undefined && proxy.authorization === undefined && String(callerProxyAuth).trim() !== "") {
        proxy = { ...proxy, authorization: String(callerProxyAuth) };
      }
    }
    const response = await sendDirect(url, { method: init.method, headers, body: init.body, signal: init.signal ?? undefined, timeout: config.timeout }, proxy);
    if (response !== null) {
      return response;
    }
    if (proxy !== undefined) {
      throw insecureHttpError(`The request to ${new URL(url).host} cannot be sent through the proxy: this runtime has no Node http, https, net and tls modules.`);
    }
    if (!isLoopbackUrl(url)) {
      throw cannotSendDirectly(url); // a runtime without node:http
    }
    return config.fetch(url, { ...init, headers });
  }
  return config.fetch(url, init);
}

export class Transport {
  constructor(readonly config: ResolvedConfig) {}

  headers(options?: RequestOptions): Record<string, string> {
    const headers: Record<string, string> = {
      "X-Api-Key": this.config.apiKey,
      "X-Secret-Key": this.config.secretKey,
      "User-Agent": "futureagi-typescript",
    };
    if (this.config.workspaceId) {
      headers["X-Workspace-Id"] = this.config.workspaceId;
    }
    return mergeHeaders(headers, this.config.defaultHeaders, options?.headers);
  }

  /** One HTTP call for `op`: auth, retries, envelope unwrap, typed errors. Resolves to decoded JSON. */
  async request(op: Operation, args: RequestArgs = {}, options?: RequestOptions): Promise<unknown> {
    let url = buildUrl(this.config, op, args, options);
    let method = op.method;
    const timeout = options?.timeout ?? this.config.timeout;
    const maxRetries = options?.maxRetries ?? this.config.maxRetries;
    let attempt = 0;
    let redirects = 0;
    for (;;) {
      // Rebuilt per attempt (a FormData stream is single-use); a request re-issued as a GET after a redirect has no body.
      const { body, headers } = method === op.method ? await buildBody(op, args, options) : { body: undefined, headers: {} };
      let response: Response;
      let text: string;
      try {
        const sent = mergeHeaders(this.headers(options), headers);
        const route = routing(this.config, url, sent);
        response = await send(this.config, url, {
          method,
          headers: sent,
          body,
          signal: AbortSignal.timeout(timeout),
          redirect: "manual", // followed below, and only within the client's own origin
        }, route);
        const location = response.headers.get("location");
        if (REDIRECT_STATUSES.has(response.status) && location) {
          discard(response);
          if (++redirects > MAX_REDIRECTS) {
            throw new APIConnectionError(`${op.id}: more than ${MAX_REDIRECTS} redirects`);
          }
          ({ url, method } = followRedirect(this.config.baseUrl, url, response.status, location, method));
          continue;
        }
        if (canRetry(op, response.status, attempt, maxRetries)) {
          discard(response); // release the connection before waiting, not after
          await sleep(backoffMs(attempt, response.headers.get("retry-after")));
          attempt++;
          continue;
        }
        text = await response.text(); // the connection can still drop or time out mid-body: a transport error like any other
      } catch (error) {
        if (error instanceof APIConnectionError || (error as { code?: unknown } | null)?.code === INSECURE_HTTP_CODE) {
          throw error; // a refused redirect or address: a decision, not a transport failure
        }
        if (canRetry(op, null, attempt, maxRetries)) {
          await sleep(backoffMs(attempt, null));
          attempt++;
          continue;
        }
        throw new APIConnectionError(error instanceof Error ? error.message : String(error));
      }
      if (response.status >= 300) {
        // a redirect without a target is not a result
        throw errorFromResponse(response.status, text, response.headers.get("x-request-id"));
      }
      return decode(op, response.status, response.headers, text);
    }
  }

  /** Call an endpoint the catalog does not describe; the usual auth, retries and errors apply. */
  raw(method: string, path: string, args: RequestArgs & { unwrap?: string | null; multipart?: boolean; decode?: Operation["decode"] } = {}, options?: RequestOptions): Promise<unknown> {
    const { unwrap, multipart, decode: mode, ...rest } = args;
    return this.request(rawOperation(method, path, unwrap === undefined ? "result" : unwrap, multipart ?? false, mode ?? "json"), rest, options);
  }

  /** The typed form of `request`: the result is the contract's response type (no runtime validation). */
  call<T>(op: Operation, args: RequestArgs = {}, options?: RequestOptions): Promise<T> {
    return this.request(op, args, options) as Promise<T>;
  }

  paginate<T>(op: Operation, args: RequestArgs = {}, options?: RequestOptions): Pager<T> {
    const spec = op.pagination;
    if (!spec) {
      throw new Error(`${op.id} is not paginated`);
    }
    // The pager owns the page cursor: it is set after `extraQuery`, so a caller's page value cannot pin every fetch to one page.
    const { extraQuery, ...rest } = options ?? {};
    const perCall: RequestOptions | undefined = options ? rest : undefined;
    return new Pager<T>(async (page: number) => {
      const data = await this.request(op, { ...args, query: { ...(extraQuery ?? {}), ...(args.query ?? {}), [spec.page_param]: page } }, perCall);
      if (!Array.isArray(getPath(data, spec.items))) {
        // A page without its items list means the contract's page shape is wrong; never let that look like an empty result.
        throw new APIError(`${op.id}: page has no '${spec.items}' list`, 200, data);
      }
      return data;
    }, spec);
  }
}
