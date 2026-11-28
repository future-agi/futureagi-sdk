/** Which requests are keyed: the decision from the final request headers, shared by every sender that may carry a Future AGI key. */

import { ConfigurationError } from "./errors";

type Env = Record<string, string | undefined>;

function processEnv(): Env {
  return (globalThis as { process?: { env?: Env } }).process?.env ?? {};
}

/** The header names that carry a Future AGI credential. */
const KEY_HEADER_NAMES = new Set(["x-api-key", "x-secret-key", "authorization"]);

/** A key value shorter than this is not looked for inside other header values: a short string would match unrelated text. */
const MIN_KEY_VALUE_LENGTH = 8;

/** Where a request's headers can be held: a `Headers`, a list of name and value pairs, or a record. */
export type HeaderSource = Headers | Iterable<readonly [string, string]> | Record<string, unknown> | null | undefined;

/** The layer names axios merges into the headers a request writes: `common`, and the one named for the request method. */
const AXIOS_LAYERS = new Set(["common", "delete", "get", "head", "options", "post", "put", "patch"]);

/** A property name a spread array gives one of its items. */
const LIST_POSITION = /^(?:0|[1-9]\d*)$/u;

type HeaderPair = [string, unknown];

function readPairs(source: HeaderSource | string, mode: "headers" | "routing" | "params"): HeaderPair[] {
  if (source === null || source === undefined) return [];
  if (typeof source !== "object") throw unreadable(typeof source === "string" ? "a string" : `a ${typeof source}`);
  const pairs: HeaderPair[] = [];
  try {
    if (typeof (source as { [Symbol.iterator]?: unknown })[Symbol.iterator] === "function") {
      for (const entry of source as Iterable<unknown>) {
        const pair = entry as { length?: unknown; 0?: unknown; 1?: unknown } | null;
        if (typeof entry !== "object" || pair === null || typeof (pair as unknown as Record<symbol, unknown>)[Symbol.iterator] !== "function" || pair.length !== 2) throw unreadable("an entry that is not a name and value pair");
        pairs.push([pairName(pair[0]), pair[1]]);
      }
      return pairs;
    }

    if (mode !== "params") {
      const methods = source as { forEach?: unknown; get?: unknown };
      const forEach = methods.forEach;
      const hasForEach = typeof forEach === "function";
      const hasGet = typeof methods.get === "function";
      if (hasForEach && hasGet) {
        (forEach as (callback: (value: unknown, name: unknown) => void) => void).call(source, (value: unknown, name: unknown) => { pairs.push([pairName(name), value]); });
        if (mode === "headers") return pairs;
        // The routing check can also see records that go directly to Request, which reads their own fields.
      } else if (hasForEach || hasGet) {
        // A container with one of the two methods is neither a header container nor a record of header values.
        throw unreadable(hasForEach ? "a container with a forEach method and no get method" : "a container with a get method and no forEach method");
      }
    }

    const fields = Object.entries(source);
    // A spread list starts at zero. Params use their own numeric-position check. In a record without a "0" field, a
    // numeric name is a header name and a list is its values.
    const arrayLike = mode === "params" || fields.some(([name]) => name === "0");
    for (const [name, value] of fields) {
      if (LIST_POSITION.test(name) && arrayLike) {
        if (!Array.isArray(value) || value.length !== 2) throw unreadable("a record whose names are list positions");
        pairs.push([pairName(value[0]), value[1]]);
        if (mode === "routing") pairs.push([name, value]);
      } else {
        pairs.push([name, value]);
      }
    }
    return pairs;
  } catch (error) {
    if (error instanceof ConfigurationError) throw error;
    throw unreadable("a container that throws when it is read");
  }
}

/**
 * The header fields of an `HttpClient` request as one record, read as Axios reads a list of pairs: the values given
 * more than once under the same name form a list, each sent as its own header line (repeated `Set-Cookie` values of a
 * `Headers` of any fetch implementation included), and each name is kept as written. Axios then merges names that differ
 * only in letter case in the order they first appear, so the value given last under the name seen last wins.
 */
export function normalizeHeaders(source: HeaderSource | string): Record<string, unknown> {
  const pairs = readPairs(source, "headers");
  refuseEmptyKeyRepeat(pairs);
  const out: Record<string, unknown> = Object.create(null) as Record<string, unknown>;
  for (const [name, value] of pairs) {
    const held = out[name];
    out[name] = Object.prototype.hasOwnProperty.call(out, name) ? (Array.isArray(held) ? [...held, value] : [held, value]) : value;
  }
  return out;
}

/**
 * A credential header given more than once, once with a value and once empty, is refused: which of the two a sender
 * keeps decides whether the request carries a key, and so its route.
 */
function refuseEmptyKeyRepeat(pairs: readonly HeaderPair[]): void {
  const seen = new Map<string, { empty: boolean; filled: boolean }>();
  for (const [name, value] of pairs) {
    const lower = name.trim().toLowerCase();
    if (!KEY_HEADER_NAMES.has(lower) || (typeof value === "object" && value !== null)) continue;
    const state = seen.get(lower) ?? { empty: false, filled: false };
    if (headerText(value).trim() === "") state.empty = true;
    else state.filled = true;
    if (state.empty && state.filled) {
      throw new ConfigurationError(
        `The request headers give ${name} more than once, once with a value and once empty. Pass one value for it.`,
        "unreadable_headers",
      );
    }
    seen.set(lower, state);
  }
}

/** The header name of a pair: a string, as it is written; a name of another type is not guessed at. */
function pairName(name: unknown): string {
  if (typeof name !== "string") throw unreadable("a pair whose name is not a string");
  return name;
}

function headerText(value: unknown): string {
  return value === undefined || value === null ? "" : String(value);
}

function lastHeaderPairs(pairs: readonly HeaderPair[]): IterableIterator<HeaderPair> {
  const byName = new Map<string, HeaderPair>();
  for (const [name, value] of pairs) byName.set(name.toLowerCase(), [name, value]);
  return byName.values();
}

/** The last value for each header name, compared without case. */
export function headerRecord(source: HeaderSource | string): Record<string, string> {
  const pairs = readPairs(source, "headers");
  refuseEmptyKeyRepeat(pairs);
  return Object.fromEntries(Array.from(lastHeaderPairs(pairs), ([name, value]) => [name, headerText(value)]));
}

function unreadable(what: string): ConfigurationError {
  return new ConfigurationError(
    `The request headers are held in ${what}, which the SDK cannot read as header names and values. Pass a plain object, a Headers, a Map or an array of [name, value] pairs.`,
    "unreadable_headers",
  );
}

function* headerEntries(source: HeaderSource, axiosMethod?: string): Generator<[string, string]> {
  for (const [name, value] of readPairs(source, "routing")) {
    // axios writes the `common` layer and the layer of the request's method into the request headers (and none of the
    // others): the headers in those layers are the ones the request carries.
    const layer = name.trim().toLowerCase();
    if (axiosMethod !== undefined && AXIOS_LAYERS.has(layer) && typeof value === "object" && value !== null) {
      if (layer === "common" || layer === axiosMethod.toLowerCase()) yield* headerEntries(value as HeaderSource, undefined);
      continue;
    }
    yield [name, headerText(value)];
    if (Array.isArray(value)) {
      for (const item of value) yield [name, headerText(item)];
    }
  }
}

/** The Future AGI keys of the environment (`FI_API_KEY`, `FI_SECRET_KEY`) and the ones a caller configured, long enough to look for in a header value. */
function knownKeys(configured: readonly (string | undefined)[], env: Env): string[] {
  const keys = [...configured, env.FI_API_KEY, env.FI_SECRET_KEY].filter((key): key is string => typeof key === "string" && key.length >= MIN_KEY_VALUE_LENGTH);
  return [...new Set(keys.flatMap(spellings))];
}

/**
 * The ways an encoder writes a key into another value: as it is, as the inside of a JSON string (quotes and backslashes
 * escaped, with and without every non-ASCII letter as a \u escape, with and without every slash escaped), percent-encoded
 * (by `encodeURIComponent` and by `encodeURI`, with upper- and lower-case hex) and form-encoded (a space as `+`). A key
 * that holds none of those characters has one spelling.
 */
export function spellings(key: string): string[] {
  const json = JSON.stringify(key).slice(1, -1);
  const ascii = json.replace(/[\u0080-\uffff]/gu, (c) => `\\u${c.charCodeAt(0).toString(16).padStart(4, "0")}`);
  const lowerHex = (text: string): string => text.replace(/%[0-9A-F]{2}/gu, (hex) => hex.toLowerCase());
  const percent = [encodeURIComponent(key), encodeURI(key), new URLSearchParams([["", key]]).toString().slice(1)];
  return [...new Set([key, json, ascii, json.replace(/\//gu, "\\/"), ascii.replace(/\//gu, "\\/"), ...percent, ...percent.map(lowerHex)])];
}

/**
 * Whether the final headers of a request (every layer, after the defaults and the per-call headers are merged, in any
 * letter case) carry a Future AGI key: `X-Api-Key`, `X-Secret-Key` or `Authorization` with a value, or any header whose
 * value holds a configured key (`configured`) or `FI_API_KEY` / `FI_SECRET_KEY` from the environment. A request that
 * carries one is a keyed request, whether or not the client resolved a key of its own: the plain-http rule, the proxy
 * rule and the redirect refusal of a keyed send apply to it.
 * `skipAuthorization`: the `Authorization` header is the SDK's own Bearer token of a platform origin, which has its own
 * origin rule. `emptyCounts`: a credential header with an empty value marks the request as keyed too. `axiosMethod`: the
 * sources are axios header sets of a request with that method: a `common` layer and the layer named for the method are
 * part of the headers the request writes, the other method layers are not.
 */
export function headersCarryKey(
  sources: readonly HeaderSource[],
  options: { configured?: readonly (string | undefined)[]; skipAuthorization?: boolean; emptyCounts?: boolean; env?: Env; axiosMethod?: string } = {},
): boolean {
  const keys = knownKeys(options.configured ?? [], options.env ?? processEnv());
  for (const source of sources) {
    try {
      for (const [name, value] of headerEntries(source, options.axiosMethod)) {
        const lower = name.trim().toLowerCase();
        if (KEY_HEADER_NAMES.has(lower) && !(lower === "authorization" && options.skipAuthorization === true) && (options.emptyCounts === true || value.trim() !== "")) return true;
        if (keys.some((key) => value.includes(key))) return true;
      }
    } catch (error) {
      // headers that cannot be read cannot be shown to carry no key: the request counts as keyed
      if (error instanceof ConfigurationError) return true;
      throw error;
    }
  }
  return false;
}

/**
 * Query and param names that carry a key, compared without case, hyphens, underscores and spaces (`api_key`, `X-Api-Key`,
 * `apikey`, `fi_api_key`, `FI_SECRET_KEY`, `access_token`): the one list the keyed decision of every query reads.
 */
const KEY_QUERY_NAMES = new Set(["apikey", "xapikey", "secretkey", "xsecretkey", "authorization", "fiapikey", "fisecretkey", "accesstoken"]);

/** How many rounds of percent-decoding a query name or value is read through: a name encoded twice names the same key. */
const MAX_DECODE_ROUNDS = 3;

/** `text` with each run of `%XX` escapes decoded where it is valid UTF-8; a `%` that starts no escape is kept. */
function decodeEscapes(text: string): string {
  return text.replace(/(?:%[0-9A-Fa-f]{2})+/gu, (run) => { try { return decodeURIComponent(run); } catch { return run; } });
}

/** `text` and what each round of percent-decoding makes of it, up to `MAX_DECODE_ROUNDS` rounds. */
function decodedForms(text: string): string[] {
  const forms = [text];
  for (let round = 0, at = text; round < MAX_DECODE_ROUNDS; round += 1) {
    const next = decodeEscapes(at);
    if (next === at) break;
    forms.push(next);
    at = next;
  }
  return forms;
}

/**
 * Whether the query of `url` (items separated by `&` or `;`) and the `params` of a request (a record, a `URLSearchParams`,
 * a `Map` or a list of pairs, followed into nested objects and arrays) carry a Future AGI key: a param named like a
 * credential header (`api_key`, `X-Api-Key`, `secret-key`, `authorization`), alone or as a part of a bracketed or dotted
 * name (`auth[api_key]`, `auth.api_key`), with a value, or any param whose name or value holds a configured key or `FI_API_KEY` / `FI_SECRET_KEY`, in any of the
 * spellings an encoder gives it. Params that cannot be read count as keyed.
 */
export function queryCarriesKey(url: string, params: unknown, options: { configured?: readonly (string | undefined)[]; env?: Env } = {}): boolean {
  const keys = knownKeys(options.configured ?? [], options.env ?? processEnv());
  const items: Array<[string, string]> = [];
  const at = url.indexOf("?");
  if (at >= 0) {
    const query = url.slice(at + 1).split("#", 1)[0] ?? "";
    for (const part of query.split(/[&;]/u)) {
      if (part === "") continue;
      const eq = part.indexOf("=");
      let name = eq < 0 ? part : part.slice(0, eq);
      let value = eq < 0 ? "" : part.slice(eq + 1);
      try { name = decodeURIComponent(name.replace(/\+/gu, " ")); value = decodeURIComponent(value.replace(/\+/gu, " ")); } catch { /* kept as written */ }
      items.push([name, value]);
    }
    if (keys.some((key) => query.includes(key))) return true;
  }
  if (params !== undefined && params !== null) {
    try {
      const source = typeof URLSearchParams !== "undefined" && params instanceof URLSearchParams
        ? params.entries()
        : Object.entries(Object.fromEntries(readPairs(params as HeaderSource, "params")));
      for (const [name, value] of source) paramItems(name, value, items, 0);
    } catch (error) {
      if (error instanceof ConfigurationError) return true;
      throw error;
    }
  }
  return items.some(([name, value]) => (keyParamName(name) && value.trim() !== "")
    || keys.some((key) => decodedForms(name).some((form) => form.includes(key)) || decodedForms(value).some((form) => form.includes(key))));
}

/** Whether a param name, or any part of a bracketed or dotted one (`auth[api_key]`, `api_key[]`, `auth.api_key`), names a key. */
function keyParamName(name: string): boolean {
  return decodedForms(name).some((form) => form.split(/[\[\].]+/u).some((part) => KEY_QUERY_NAMES.has(part.toLowerCase().replace(/[-_\s]/gu, ""))));
}

/** How deep nested params are followed; params nested deeper than this cannot be shown to carry no key. */
const MAX_PARAM_DEPTH = 8;

/**
 * The name and value items a param gives, as an encoder writes nested params: a plain object or an array is followed into
 * `name[child]` items, any other value is one item with its JSON text. Params too deep to follow are refused as unreadable.
 */
function paramItems(name: string, value: unknown, items: Array<[string, string]>, depth: number): void {
  if (typeof value === "string") { items.push([name, value]); return; }
  if (value === undefined || value === null) { items.push([name, ""]); return; }
  const prototype = typeof value === "object" ? Object.getPrototypeOf(value) as unknown : undefined;
  if (Array.isArray(value) || (typeof value === "object" && (prototype === Object.prototype || prototype === null))) {
    if (depth >= MAX_PARAM_DEPTH) throw unreadable("params nested deeper than the SDK reads");
    for (const [child, item] of Object.entries(value as Record<string, unknown>)) paramItems(`${name}[${child}]`, item, items, depth + 1);
    return;
  }
  let text: string;
  try { text = JSON.stringify(value) ?? String(value); } catch { text = String(value); }
  items.push([name, text]);
}
