/**
 * `FI_EXTRA_HEADERS`: extra HTTP headers on every request to the Future AGI platform, with the
 * same rules as the Python SDK (`fi._extra_headers`). A team environment behind a proxy that wants
 * its own header on each request (Google IAP's `Proxy-Authorization: Bearer <identity token>`)
 * sets it once.
 *
 * - Format: `Name=value` entries separated by newlines or `;`. Spaces around a name and its value
 *   are dropped; empty entries are skipped; only the first `=` splits an entry.
 * - Names must be HTTP tokens (no `:`, whitespace or control character; in a record, exactly a
 *   token); a name given twice is refused. Values must be visible ASCII or spaces, and not empty. A
 *   control character anywhere (CR, LF, NUL, tab or any other, before any trimming) is refused, so a
 *   value never starts a second header line. A value that is only an auth scheme (`Bearer`) is
 *   refused.
 * - `X-Api-Key`, `X-Secret-Key` and `Authorization` are refused: the SDK sends its own.
 * - `extraHeaders` (a record, or a string in the same format) is added to the setting and wins
 *   over it for the same name; a header set explicitly on the request wins over both.
 * - Sent only to URLs under the client's base URL (same scheme, host and port; a path under the
 *   base path). With extra headers in effect, a redirect is never followed to another host.
 * - Values are never logged or put in an error message, and `extraHeaders` values are never kept on
 *   an object that util.inspect, console.log or JSON.stringify can show. The environment is read
 *   when each request is sent.
 * - Browsers drop `Proxy-*` request headers; use Node.js for a proxy-authenticated environment.
 */

export const EXTRA_HEADERS_ENV = "FI_EXTRA_HEADERS";
const ARGUMENT = "extraHeaders";
const RESERVED = new Set(["x-api-key", "x-secret-key", "authorization"]);
const TOKEN = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;
const VALUE = /^[\x20-\x7e]+$/;
// eslint-disable-next-line no-control-regex
const CONTROL = /[\x00-\x1f\x7f]/;
const BARE_SCHEME = /^(bearer|basic|token)$/i;
/** Only U+0020 is trimmed: String.prototype.trim would silently drop CR, LF, tab and others. */
const trimSpaces = (text: string): string => text.replace(/^ +| +$/g, "");

export type ExtraHeadersInput = Record<string, string> | string | undefined;

/** `FI_EXTRA_HEADERS` (or `extraHeaders`) is malformed. The message names the setting and the entry,
 * never a header value. */
export class ExtraHeadersError extends Error {
  readonly code = "EXTRA_HEADERS_INVALID";

  constructor(message: string) {
    super(message);
    this.name = "ExtraHeadersError";
  }
}

/** `padded`: text form, where spaces (only U+0020) around the name are part of the format. */
function check(name: unknown, value: unknown, where: string, padded: boolean): [string, string] {
  if (typeof name !== "string" || !TOKEN.test(padded ? trimSpaces(name) : name)) {
    throw new ExtraHeadersError(
      `${where}: the name is not a valid HTTP header name (write Name=value; a name has no ':', whitespace or control character)`,
    );
  }
  const header = trimSpaces(name);
  if (RESERVED.has(header.toLowerCase())) {
    throw new ExtraHeadersError(
      `${where}: ${header} cannot be set here; the SDK sends its own X-Api-Key, X-Secret-Key and Authorization`,
    );
  }
  if (typeof value !== "string") throw new ExtraHeadersError(`${where} (${header}): the value must be a string`);
  if (CONTROL.test(value)) {
    // before any trimming: a CR, LF or NUL is refused, never dropped
    throw new ExtraHeadersError(
      `${where} (${header}): the value has a control character such as CR, LF, NUL or tab (not visible ASCII)`,
    );
  }
  const text = trimSpaces(value);
  if (!text) throw new ExtraHeadersError(`${where} (${header}): the value is empty`);
  if (!VALUE.test(text)) {
    throw new ExtraHeadersError(`${where} (${header}): the value has a character that is not visible ASCII`);
  }
  if (BARE_SCHEME.test(text)) {
    throw new ExtraHeadersError(
      `${where} (${header}): the value is only an auth scheme with no token (was the token variable empty?)`,
    );
  }
  return [header, text];
}

function add(out: Map<string, [string, string]>, name: string, value: string, where: string): void {
  if (out.has(name.toLowerCase())) throw new ExtraHeadersError(`${where}: ${name} is given twice`);
  out.set(name.toLowerCase(), [name, value]);
}

const toRecord = (out: Map<string, [string, string]>): Record<string, string> =>
  Object.fromEntries([...out.values()]);

/** `Name=value` entries (newlines or `;` between them) as a record; throws {@link ExtraHeadersError}. */
export function parseExtraHeaders(text: string, source: string = EXTRA_HEADERS_ENV): Record<string, string> {
  if (typeof text !== "string") throw new ExtraHeadersError(`${source} must be a string of Name=value entries`);
  const out = new Map<string, [string, string]>();
  let number = 0;
  for (const raw of text.split(/[;\r\n]/)) {
    if (!trimSpaces(raw)) continue; // spaces only: an entry of a tab or another control character is refused
    number += 1;
    const where = `${source} entry ${number}`;
    const at = raw.indexOf("=");
    if (at < 0) {
      throw new ExtraHeadersError(`${where} has no '=' (write Name=value; separate entries with ';' or newlines)`);
    }
    const [name, value] = check(raw.slice(0, at), raw.slice(at + 1), where, true);
    add(out, name, value, where);
  }
  return toRecord(out);
}

/** A client's `extraHeaders` option, checked by the same rules as the setting. */
export function validateExtraHeaders(headers: ExtraHeadersInput, source: string = ARGUMENT): Record<string, string> {
  if (headers === undefined || headers === null) return {};
  if (typeof headers === "string") return parseExtraHeaders(headers, source);
  if (typeof headers !== "object" || Array.isArray(headers)) {
    throw new ExtraHeadersError(`${source} must be a record of header names to values, or 'Name=value' text`);
  }
  const out = new Map<string, [string, string]>();
  Object.entries(headers).forEach(([name, value], index) => {
    const where = `${source} entry ${index + 1}`;
    const [header, text] = check(name, value, where, false);
    add(out, header, text, where);
  });
  return toRecord(out);
}

function readEnv(name: string): string | undefined {
  const maybeProcess = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process;
  return maybeProcess?.env?.[name];
}

/** The setting's headers (`{}` when unset or blank). */
export function readExtraHeadersEnv(): Record<string, string> {
  return parseExtraHeaders(readEnv(EXTRA_HEADERS_ENV) ?? "");
}

/** The setting, then the argument over it for the same name (names compare without case). */
export function mergeExtraHeaders(
  envHeaders: Record<string, string>,
  argument: Record<string, string>,
): Record<string, string> {
  const out = new Map<string, [string, string]>();
  for (const [name, value] of Object.entries(envHeaders)) out.set(name.toLowerCase(), [name, value]);
  for (const [name, value] of Object.entries(argument)) out.set(name.toLowerCase(), [name, value]);
  return toRecord(out);
}

function origin(url: string): [string, string, string, string] | undefined {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return undefined;
  }
  const scheme = parsed.protocol.toLowerCase();
  if ((scheme !== "http:" && scheme !== "https:") || !parsed.hostname) return undefined;
  const port = parsed.port || (scheme === "https:" ? "443" : "80");
  return [scheme, parsed.hostname.toLowerCase(), port, parsed.pathname || "/"];
}

/** Whether `url` is under `baseUrl`: same scheme, host and port, and a path under its path. */
export function isPlatformUrl(url: string, baseUrl: string): boolean {
  const target = origin(url);
  const base = origin(baseUrl);
  if (!target || !base || target[0] !== base[0] || target[1] !== base[1] || target[2] !== base[2]) return false;
  const prefix = base[3].replace(/\/+$/, "");
  return !prefix || target[3] === prefix || target[3].startsWith(`${prefix}/`);
}

/**
 * Each client's `extraHeaders` values, kept off the instance: util.inspect, console.log and
 * JSON.stringify of a client (HttpClient, APIKeyAuth, Dataset, Prompt …) or of its ExtraHeaders
 * show the base URL and the header names only, never a value.
 */
const ARGUMENTS = new WeakMap<ExtraHeaders, Readonly<Record<string, string>>>();
const INSPECT = Symbol.for("nodejs.util.inspect.custom");
const argumentOf = (extra: ExtraHeaders): Readonly<Record<string, string>> => ARGUMENTS.get(extra) ?? {};

/** One client's extra headers: its `extraHeaders` (checked when the client is built) over the setting
 * (read when each request is sent), for URLs under its base URL only. */
export class ExtraHeaders {
  constructor(
    readonly baseUrl: string,
    extraHeaders?: ExtraHeadersInput,
  ) {
    ARGUMENTS.set(this, Object.freeze(validateExtraHeaders(extraHeaders)));
  }

  resolve(): Record<string, string> {
    return mergeExtraHeaders(readExtraHeadersEnv(), argumentOf(this));
  }

  /** The headers for a request to `url`: `{}` off the base URL (the setting is not even read). */
  forUrl(url: string): Record<string, string> {
    return isPlatformUrl(url, this.baseUrl) ? this.resolve() : {};
  }

  /** The header names a platform request carries, for stripping on a redirect (`[]` if malformed). */
  names(): string[] {
    try {
      return Object.keys(this.resolve());
    } catch {
      return Object.keys(argumentOf(this));
    }
  }

  toJSON(): Record<string, unknown> {
    return { baseUrl: this.baseUrl, argumentNames: Object.keys(argumentOf(this)) };
  }
}

// util.inspect / console.log (Node): names only, as toJSON (util.inspect ignores toJSON)
Object.defineProperty(ExtraHeaders.prototype, INSPECT, {
  value(this: ExtraHeaders): Record<string, unknown> {
    return this.toJSON();
  },
});

function urlOf(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.href;
  return (input as Request).url;
}

/**
 * A fetch that adds the extra headers to requests under the base URL. When it adds any, the request
 * does not follow redirects (a 3xx comes back as the answer), so the headers never reach another host.
 */
export function withExtraHeaders(fetchImpl: typeof fetch, extra: ExtraHeaders): typeof fetch {
  const wrapped = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const headers = extra.forUrl(urlOf(input));
    if (Object.keys(headers).length === 0) return fetchImpl(input as RequestInfo, init);
    const request = new Request(new Request(input as RequestInfo, init), { redirect: "manual" });
    for (const [name, value] of Object.entries(headers)) {
      if (!request.headers.has(name)) request.headers.set(name, value);
    }
    return fetchImpl(request);
  };
  return wrapped as typeof fetch;
}
