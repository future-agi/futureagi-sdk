/**
 * One request from an operation and its arguments (ported from the Omega runtime's `request-build`);
 * the twin of Python's `fi._core.request` and `fi._core.idempotency`. The path from the
 * generated template with every parameter encoded, only the query keys the contract declares, the body
 * with its size limit checked before anything is sent, and the idempotency key.
 */

import { v4 as uuidv4 } from "uuid";

import { ConfigurationError, PayloadTooLargeError } from "./errors";
import type { OperationSpec } from "./policy";

/** Body limits checked before any network call (the gateway's body classes). */
export const BODY_LIMITS = { json: 1024 * 1024, bundle: 64 * 1024 * 1024 } as const;
export const IDEMPOTENCY_HEADER = "Idempotency-Key";
export const REPLAYED_HEADER = "x-omega-idempotent-replayed";
/** The wait for `idempotency_key_in_progress` when the server names none. */
export const IN_PROGRESS_DEFAULT_S = 1;
/** A longer `Retry-After` than this is not waited out: the error is thrown with it set. */
export const IN_PROGRESS_MAX_WAIT_S = 60;

export type QueryValue = string | number | boolean | undefined | null | readonly (string | number | boolean)[];

/** The arguments of one call. */
export interface OperationParams {
  readonly path?: Readonly<Record<string, string | number>>;
  readonly query?: Readonly<Record<string, QueryValue>>;
  /** JSON for `json` operations; JSON, a string, bytes or a Blob for `bundle` operations. */
  readonly body?: unknown;
}

function segment(value: string, name: string, op: OperationSpec): string {
  if (value === "" || value === "." || value === "..") {
    throw new ConfigurationError(`${op.name}: path parameter ${name} must not be empty, "." or ".."`, "invalid_path_param", op.name);
  }
  return encodeURIComponent(value);
}

/** The request path with every parameter percent-encoded; a value can never climb out of its segment. */
export function buildPath(op: OperationSpec, params: OperationParams["path"] = {}): string {
  const multi = new Set(op.multiSegment ?? []);
  const declared = new Set(op.pathParams ?? []);
  for (const key of Object.keys(params)) {
    if (!declared.has(key)) throw new ConfigurationError(`${op.name} has no path parameter ${key}`, "unknown_path_param", op.name);
  }
  return op.path.replace(/\{([^}]+)\}/gu, (_match, key: string) => {
    const raw = params[key];
    if (raw === undefined || raw === null) {
      throw new ConfigurationError(`${op.name}: missing path parameter ${key}`, "missing_path_param", op.name);
    }
    const value = String(raw);
    if (!multi.has(key)) return segment(value, key, op);
    return value
      .replace(/^\/+/u, "")
      .split("/")
      .map((part) => segment(part, key, op))
      .join("/");
  });
}

/** The query string (with `?`), or "". Undeclared keys are refused: they are never sent. */
export function buildQuery(op: OperationSpec, query: OperationParams["query"] = {}): string {
  const declared = new Set(op.query ?? []);
  const search = new URLSearchParams();
  for (const key of Object.keys(query).sort()) {
    const value = query[key];
    if (value === undefined || value === null) continue;
    if (!declared.has(key)) {
      throw new ConfigurationError(`${op.name} does not declare the query key ${key}, so it is not sent`, "undeclared_query_key", op.name);
    }
    const values = Array.isArray(value) ? value : [value];
    for (const item of values) search.append(key, typeof item === "boolean" ? (item ? "true" : "false") : String(item));
  }
  const text = search.toString();
  return text === "" ? "" : `?${text}`;
}

/** The encoded body and its media type, after the size check. */
export interface EncodedBody {
  readonly body?: string | Uint8Array | Blob;
  readonly contentType?: string;
  readonly size: number;
}

export function buildBody(op: OperationSpec, body: unknown): EncodedBody {
  if (body === undefined) return { size: 0 };
  const kind = op.body ?? "none";
  if (kind === "none") throw new ConfigurationError(`${op.name} takes no request body`, "unexpected_body", op.name);
  const limit = BODY_LIMITS[kind];
  let out: EncodedBody;
  if (body instanceof Uint8Array) out = { body, contentType: op.contentType ?? "application/octet-stream", size: body.byteLength };
  else if (typeof Blob !== "undefined" && body instanceof Blob)
    out = { body, contentType: op.contentType ?? (body.type || "application/octet-stream"), size: body.size };
  else if (kind === "bundle" && typeof body === "string")
    out = { body, contentType: op.contentType ?? "application/octet-stream", size: new TextEncoder().encode(body).byteLength };
  else {
    let text: string;
    try {
      text = JSON.stringify(body);
    } catch (error) {
      throw new ConfigurationError(`${op.name}: the request body is not JSON (${(error as Error).name})`, "invalid_body", op.name);
    }
    out = { body: text, contentType: "application/json", size: new TextEncoder().encode(text).byteLength };
  }
  if (out.size > limit) {
    throw new PayloadTooLargeError(413, undefined, {
      local: true,
      limitBytes: limit,
      code: "payload_too_large",
      operation: op.name,
      message: `${op.name}: the request body is ${out.size} bytes; the limit is ${limit} bytes (nothing was sent)`,
    });
  }
  return out;
}

const KEY = /^[\x21-\x7e]{1,255}$/u;

/** The caller's key (validated), else a new UUID4, else none for an operation that takes none. */
export function resolveIdempotencyKey(op: OperationSpec, supplied?: string): string | undefined {
  if (supplied !== undefined) {
    if (op.idempotent !== true) {
      throw new ConfigurationError(
        `${op.name} does not accept an idempotency key, so a repeat could apply twice`,
        "idempotency_not_supported",
        op.name,
      );
    }
    if (!KEY.test(supplied)) {
      throw new ConfigurationError(
        "idempotencyKey must be 1 to 255 visible ASCII characters with no spaces",
        "invalid_idempotency_key",
        op.name,
      );
    }
    return supplied;
  }
  return op.idempotent === true ? uuidv4() : undefined;
}

/** Seconds to wait before resending a keyed call the server reports as still running, else undefined. */
export function inProgressWait(
  op: OperationSpec,
  status: number,
  code: string | undefined,
  retryAfter: number | undefined,
): number | undefined {
  if (op.idempotent !== true || status !== 409 || code !== "idempotency_key_in_progress") return undefined;
  const seconds = retryAfter ?? IN_PROGRESS_DEFAULT_S;
  return seconds > IN_PROGRESS_MAX_WAIT_S ? undefined : seconds;
}
