/**
 * Redaction (ported from the Omega runtime). Credentials, the Bearer token and every field
 * the contract marks secret are redacted in errors, raw-response views and cassettes. The twin of
 * Python's `fi._core.redact`.
 */

/** What a redacted value is replaced with. */
export const REDACTED = "[redacted]";

/** Header names whose values are never shown. */
export const SECRET_HEADERS: ReadonlySet<string> = new Set([
  "x-api-key",
  "x-secret-key",
  "authorization",
  "proxy-authorization",
  "cookie",
  "set-cookie",
  "sec-websocket-protocol",
]);

/** Field names that are treated as secret wherever they appear in a structured value. */
const SECRET_FIELD = /token|secret|password|passwd|api_?key|private_?key|credential|^code$|^state$|^env$|^envs$/iu;

const MAX_DEPTH = 8;

/** A copy of the headers with every secret value replaced. */
export function redactHeaders(headers: Iterable<[string, string]> | Record<string, string>): Record<string, string> {
  const entries =
    Symbol.iterator in Object(headers) ? [...(headers as Iterable<[string, string]>)] : Object.entries(headers as Record<string, string>);
  const out: Record<string, string> = {};
  for (const [name, value] of entries) {
    const key = name.toLowerCase();
    out[key] = SECRET_HEADERS.has(key) ? REDACTED : value;
  }
  return out;
}

/** A deep copy with every secret-named field replaced. Depth-limited; never throws. */
export function redactValue(value: unknown, depth = 0): unknown {
  if (depth > MAX_DEPTH) return REDACTED;
  if (Array.isArray(value)) return value.map((item) => redactValue(item, depth + 1));
  if (value !== null && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
      out[key] = SECRET_FIELD.test(key) ? REDACTED : redactValue(item, depth + 1);
    }
    return out;
  }
  return value;
}

/**
 * Redact the fields a contract marks secret. Paths are dot-separated; `*` matches every key or
 * array item at that level (for example `env.*` or `items.*.token`).
 */
export function redactPaths(value: unknown, paths: readonly string[]): unknown {
  let out = structuredCopy(value);
  for (const path of paths) out = redactPath(out, path.split("."));
  return out;
}

function structuredCopy(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(structuredCopy);
  if (value !== null && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) out[key] = structuredCopy(item);
    return out;
  }
  return value;
}

function redactPath(value: unknown, segments: readonly string[]): unknown {
  if (segments.length === 0) return REDACTED;
  if (value === null || typeof value !== "object") return value;
  const [head, ...rest] = segments as [string, ...string[]];
  if (Array.isArray(value)) {
    return head === "*" ? value.map((item) => redactPath(item, rest)) : value;
  }
  const record = value as Record<string, unknown>;
  for (const key of Object.keys(record)) {
    if (head === "*" || head === key) record[key] = redactPath(record[key], rest);
  }
  return record;
}

/** Replace secrets in one longest-first literal pass; minLength=1 also scrubs short credentials. */
export function scrubText(text: string, secrets: readonly (string | undefined)[], minLength = 4): string {
  const known = [...new Set(secrets.filter((s): s is string => typeof s === "string" && s.length > 0 && s.length >= minLength))]
    .sort((a, b) => b.length - a.length);
  if (known.length === 0) return text;
  const pattern = known.map(s => s.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&")).join("|");
  // A replacement is never scanned again, even if it contains another known secret.
  return text.replace(new RegExp(pattern, "gu"), () => REDACTED);
}

/**
 * A deep copy with secrets replaced in strings; scrubKeys=false preserves wire field names. A
 * secret a server reflected in JSON text with escapes (a quote, a backslash, `\uXXXX`) is only whole
 * once decoded, so `scrubText` on the raw text misses it. Depth-limited; never throws.
 */
export function scrubValue(value: unknown, secrets: readonly (string | undefined)[], depth = 0, minLength = 4, scrubKeys = true): unknown {
  if (depth > MAX_DEPTH) return REDACTED;
  if (typeof value === "string") return scrubText(value, secrets, minLength);
  if (Array.isArray(value)) return value.map((item) => scrubValue(item, secrets, depth + 1, minLength, scrubKeys));
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value as Record<string, unknown>).map(([key, item]) => [
      scrubKeys ? scrubText(key, secrets, minLength) : key,
      scrubValue(item, secrets, depth + 1, minLength, scrubKeys),
    ]));
  }
  return value;
}

/**
 * The string values a request carries in secret fields: those at the contract's marked paths
 * (`request.<path>`, `*` for any key) and any secret-named field. Used to scrub a server's reflected
 * error text, so a request secret never comes back through an error.
 */
export function requestSecretValues(body: unknown, markedPaths: readonly string[] = []): string[] {
  const out = new Set<string>();
  const collectAll = (value: unknown, depth = 0): void => {
    if (depth > MAX_DEPTH) return;
    if (typeof value === "string") out.add(value);
    else if (Array.isArray(value)) for (const item of value) collectAll(item, depth + 1);
    else if (value !== null && typeof value === "object") for (const item of Object.values(value)) collectAll(item, depth + 1);
  };
  const walkNamed = (value: unknown, depth = 0): void => {
    if (depth > MAX_DEPTH || value === null || typeof value !== "object") return;
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
      if (SECRET_FIELD.test(key)) collectAll(item);
      else walkNamed(item, depth + 1);
    }
  };
  const walkPath = (value: unknown, segments: readonly string[]): void => {
    if (segments.length === 0) return collectAll(value);
    if (value === null || typeof value !== "object") return;
    const [head, ...rest] = segments as [string, ...string[]];
    const entries = Array.isArray(value) ? value.map((v, i) => [String(i), v] as const) : Object.entries(value as Record<string, unknown>);
    for (const [key, item] of entries) if (head === "*" || head === key) walkPath(item, rest);
  };
  walkNamed(body);
  for (const path of markedPaths) {
    if (path.startsWith("request.")) walkPath(body, path.split(".").slice(1));
  }
  return [...out];
}
