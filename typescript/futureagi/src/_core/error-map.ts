/**
 * One status-to-class mapping for every namespace, core and platform; the twin of
 * Python's `fi._core.errors`. It reads the three platform error shapes, falling back to the status:
 *
 * - gateway: `{ error: "<code>", reason, requestId, retryAfterSeconds? }`
 * - EE:      `{ code, message, detail, request_id, error: { code, message, detail } }`
 * - Hub:     `{ error: { code, message, fix } }`
 *
 * A known `code` in its own status family picks a narrower class; an unknown code keeps its string
 * and the status picks the class. A string is read as a code only when it looks like one
 * (`snake_case`), so a Django `{ "error": "Some sentence" }` is never mistaken for a code.
 */

import {
  APIConnectionError,
  APITimeoutError,
  BadRequestError,
  ConflictError,
  ConsoleUnavailableError,
  FutureAGIAPIError,
  IdempotencyKeyInProgressError,
  IdempotencyKeyReusedError,
  NotFoundError,
  PaymentRequiredError,
  LicenseRequiredError,
  PayloadTooLargeError,
  PermissionDeniedError,
  ProductNotAvailableError,
  CoreRateLimitError,
  SandboxStateError,
  CoreServerError,
  UnprocessableEntityError,
  AuthenticationError,
  WrongRegionError,
} from "./errors";

type APIErrorClass = new (
  statusCode: number,
  payload: unknown,
  fields?: ConstructorParameters<typeof FutureAGIAPIError>[2],
) => FutureAGIAPIError;

const CODE = /^(?:[a-z][a-z0-9]*(?:[_.-][a-z0-9]+)*|[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+)$/u;
const MAX_MESSAGE = 500;
const STATUS_CLASSES: Record<number, APIErrorClass> = {
  400: BadRequestError,
  401: AuthenticationError,
  402: PaymentRequiredError,
  403: PermissionDeniedError,
  404: NotFoundError,
  409: ConflictError,
  413: PayloadTooLargeError,
  422: UnprocessableEntityError,
  429: CoreRateLimitError,
};
const CODE_CLASSES: Record<string, APIErrorClass> = {
  LICENSE_MISSING: LicenseRequiredError,
  product_not_admitted: ProductNotAvailableError,
  idempotency_key_in_progress: IdempotencyKeyInProgressError,
  idempotency_key_reused: IdempotencyKeyReusedError,
};

/** The class for a status and the server's code (a code wins only inside its own status family). */
export function errorClassFor(status: number, code?: string, family?: string): APIErrorClass {
  const base = STATUS_CLASSES[status] ?? (status >= 500 ? CoreServerError : FutureAGIAPIError);
  const byCode = code !== undefined ? CODE_CLASSES[code] : undefined;
  if (base !== FutureAGIAPIError && byCode !== undefined && byCode.prototype instanceof base) return byCode;
  if (status === 409 && family === "sandboxes" && base === ConflictError && (code === undefined || code === "conflict")) {
    return SandboxStateError;
  }
  return base;
}

/** `Retry-After` (seconds, or an HTTP date) in seconds; undefined when absent or unreadable. */
export function parseRetryAfter(value: unknown, now = Date.now()): number | undefined {
  if (typeof value === "number") return value >= 0 && Number.isFinite(value) ? value : undefined;
  if (typeof value !== "string" || value.trim() === "") return undefined;
  const seconds = Number(value);
  if (Number.isFinite(seconds)) return seconds >= 0 ? seconds : undefined;
  const at = Date.parse(value);
  return Number.isNaN(at) ? undefined : Math.max(0, (at - now) / 1000);
}

const asCode = (v: unknown): string | undefined => (typeof v === "string" && v.length <= 64 && CODE.test(v) ? v : undefined);
const asText = (v: unknown): string | undefined => {
  if (typeof v !== "string" || v.trim() === "") return undefined;
  const one = v.replace(/\s+/gu, " ").trim();
  return one.length > MAX_MESSAGE ? `${one.slice(0, MAX_MESSAGE)}...` : one;
};

/** What one of the three shapes says; `{}` for any other body. */
export interface ErrorShape {
  code?: string;
  message?: string;
  hint?: string;
  feature?: string;
  reason?: string;
  requestId?: string;
  upstreamRequestId?: string;
  retryAfter?: number;
}

export function readErrorShape(body: unknown): ErrorShape {
  if (body === null || typeof body !== "object" || Array.isArray(body)) return {};
  let b = body as Record<string, unknown>;
  if ("status" in b && b.result !== null && typeof b.result === "object" && !Array.isArray(b.result)) {
    b = { ...(b.result as Record<string, unknown>), ...b };
  }
  const nested = b.error !== null && typeof b.error === "object" ? (b.error as Record<string, unknown>) : {};
  const code = asCode(b.error_code) ?? asCode(b.code) ?? asCode(b.error) ?? asCode(nested.code);
  if (code === undefined) return {};
  const detail = b.detail ?? nested.detail;
  let retryAfter = parseRetryAfter(b.retryAfterSeconds);
  if (retryAfter === undefined && detail !== null && typeof detail === "object") {
    retryAfter = parseRetryAfter((detail as Record<string, unknown>).retryAfterSeconds);
  }
  const shape: ErrorShape = { code };
  // FA's top-level detail is a sentence; the feature lives in error.detail.
  const featureDetail = detail !== null && typeof detail === "object" && !Array.isArray(detail) ? detail : nested.detail;
  if (featureDetail !== null && typeof featureDetail === "object" && !Array.isArray(featureDetail)) {
    const feature = asText((featureDetail as Record<string, unknown>).feature);
    if (feature !== undefined) shape.feature = feature;
  }
  const message = asText(b.message) ?? asText(nested.message);
  const hint = asText(nested.fix) ?? asText(b.fix);
  const reason = asText(b.reason);
  if (message !== undefined) shape.message = message;
  if (hint !== undefined) shape.hint = hint;
  if (reason !== undefined) shape.reason = reason;
  if (typeof b.requestId === "string") shape.requestId = b.requestId;
  if (typeof b.request_id === "string") shape.upstreamRequestId = b.request_id;
  if (retryAfter !== undefined) shape.retryAfter = retryAfter;
  return shape;
}

/**
 * Does the decoded body carry a Console/EE, gateway or Hub error envelope?
 * The pinned OmegaEeError accepts any nonempty string code, or legacy error
 * (string or OmegaNestedError). Do not require today's regex or a known code.
 * Also preserve the legacy shapes readErrorShape already understands. Call before
 * scrubbing, since a credential can coincidentally equal a code or wire key.
 */
export function isPlatformError(body: unknown): boolean {
  if (readErrorShape(body).code !== undefined) return true;
  if (body === null || typeof body !== "object" || Array.isArray(body)) return false;
  const b = body as Record<string, unknown>;
  if ((typeof b.code === "string" && b.code.length > 0) || typeof b.error === "string") return true;
  if (b.error === null || typeof b.error !== "object" || Array.isArray(b.error)) return false;
  const error = b.error as Record<string, unknown>;
  return typeof error.code === "string" && error.code.length > 0 && typeof error.message === "string";
}

/** Options for {@link apiError}. */
export interface ApiErrorContext {
  /** The SDK operation (`runs.get`); words the message on platform calls. */
  readonly operation?: string;
  readonly family?: string;
  readonly idempotencyKey?: string;
  /** The unredacted body to read the shape from (the redactor treats a field named `code` as secret). */
  readonly body?: unknown;
  /** Exact envelope match before platform privacy normalization; false prevents shape promotion. */
  readonly wrongRegion?: boolean;
  /** Copy the body's own fields onto the error (core namespaces: `e.detail` keeps working). */
  readonly assignBody?: boolean;
  /** Only set by the Console executor after checking the raw response envelope. */
  readonly consoleUnavailableMessage?: string;
}

/** Only the frozen top-level string envelope at 403 is regional evidence. Never infer it from a
 * nested code, wrapper, status alone or response prose; check before any privacy transformation. */
export function isWrongRegionResponse(status: number, body: unknown): boolean {
  return status === 403 && body !== null && typeof body === "object" && !Array.isArray(body) &&
    Object.prototype.hasOwnProperty.call(body, "error") && (body as Record<string, unknown>).error === "wrong_region";
}

/** The `FutureAGIAPIError` subclass for a response, with every field read. */
export function apiError(status: number, payload: unknown, headers?: Headers, context: ApiErrorContext = {}): FutureAGIAPIError {
  if (status === 403 && (context.wrongRegion ?? isWrongRegionResponse(status, context.body ?? payload))) {
    return new WrongRegionError(status, undefined, {
      ...(context.operation !== undefined ? { operation: context.operation } : {}),
      ...(context.idempotencyKey !== undefined ? { idempotencyKey: context.idempotencyKey } : {}),
    });
  }
  const shape = readErrorShape(context.body ?? payload);
  const unavailable = status === 404 && context.consoleUnavailableMessage !== undefined;
  const cls = unavailable ? ConsoleUnavailableError : errorClassFor(status, shape.code, context.family);
  const retryAfter = parseRetryAfter(headers?.get("retry-after") ?? undefined) ?? shape.retryAfter;
  const requestId = shape.requestId ?? headers?.get("x-request-id") ?? undefined;
  let message: string | undefined;
  if (context.operation !== undefined) {
    const said = shape.message ?? shape.reason;
    message = `${context.operation} failed with status ${status} (${shape.code ?? `http_${status}`})${said !== undefined ? `: ${said}` : ""}`;
    if (shape.hint !== undefined) message += `. ${shape.hint}`;
  }
  if (cls === LicenseRequiredError) {
    const subject = shape.feature !== undefined ? `Feature '${shape.feature}'` : "This feature";
    message = (context.operation !== undefined ? `${context.operation} failed with status 402: ` : "") +
      `${subject} needs an Enterprise licence on this server (LICENSE_MISSING). ` +
      "Ask the server administrator to configure a licence that includes this feature.";
  }
  if (unavailable) message = context.consoleUnavailableMessage;
  const upstream = shape.upstreamRequestId ?? headers?.get("x-upstream-request-id") ?? undefined;
  const receipt = headers?.get("x-omega-receipt-id") ?? undefined;
  const err = new cls(status, payload, {
    ...(shape.code !== undefined ? { code: shape.code } : {}),
    ...(message !== undefined ? { message } : {}),
    ...(requestId !== undefined ? { requestId } : {}),
    ...(upstream !== undefined ? { upstreamRequestId: upstream } : {}),
    ...(receipt !== undefined ? { receiptId: receipt } : {}),
    ...(context.idempotencyKey !== undefined ? { idempotencyKey: context.idempotencyKey } : {}),
    ...(retryAfter !== undefined ? { retryAfter } : {}),
    ...(context.operation !== undefined ? { operation: context.operation } : {}),
  });
  if (context.assignBody === true && payload !== null && typeof payload === "object" && !Array.isArray(payload)) {
    for (const [key, value] of Object.entries(payload as Record<string, unknown>)) {
      if (!(key in err)) (err as unknown as Record<string, unknown>)[key] = value;
    }
  }
  return err;
}

const PRE_SEND_CODES = new Set(["ECONNREFUSED", "ENOTFOUND", "EAI_AGAIN", "UND_ERR_CONNECT_TIMEOUT"]);

function codeOf(error: unknown): string | undefined {
  let current: unknown = error;
  for (let depth = 0; depth < 4 && current !== null && typeof current === "object"; depth += 1) {
    const code = (current as { code?: unknown }).code;
    if (typeof code === "string") return code;
    current = (current as { cause?: unknown }).cause;
  }
  return undefined;
}

/** A fetch failure (after the transport's retries) as `APITimeoutError` or `APIConnectionError`. */
export function connectionError(
  error: unknown,
  context: { operation?: string; idempotencyKey?: string; origin?: string; timedOut?: boolean; possiblyApplied?: boolean } = {},
): APIConnectionError {
  const code = codeOf(error);
  const reason = error instanceof Error ? (error.cause instanceof Error ? error.cause.message : error.message) : String(error);
  const where = context.origin ?? "the server";
  const timedOut = context.timedOut === true || code === "UND_ERR_CONNECT_TIMEOUT" || /timed out/u.test(reason);
  const preSend = code !== undefined && PRE_SEND_CODES.has(code);
  const prefix = context.operation !== undefined ? `${context.operation}: ` : "";
  let err: APIConnectionError;
  if (timedOut) {
    err = new APITimeoutError(`${prefix}${where} did not answer in time (${reason}); the server may be busy, retry later`, error as Error);
  } else if (preSend) {
    err = new APIConnectionError(`${prefix}cannot reach ${where} (${reason}); check FI_PLATFORM_BASE_URL or FI_BASE_URL`, error as Error);
  } else {
    err = new APIConnectionError(`${prefix}the connection to ${where} broke before a response (${reason}); retry`, error as Error);
    err.kind = "connection";
  }
  if (timedOut) err.kind = "timeout";
  err.possiblyApplied = context.possiblyApplied ?? !preSend;
  if (context.idempotencyKey !== undefined) err.idempotencyKey = context.idempotencyKey;
  if (context.operation !== undefined) err.operation = context.operation;
  return err;
}
