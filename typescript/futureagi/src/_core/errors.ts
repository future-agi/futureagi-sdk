/**
 * Public error tree: `import { NotFoundError } from "@future-agi/sdk"`; the same shape as Python's `fi.errors`.
 * Every class extends `SDKException`; status classes extend `FutureAGIAPIError`.
 * Status mapping is shared, except a complete non-envelope Console 404 is `ConsoleUnavailableError`.
 * No response means `APIConnectionError` / `APITimeoutError`; `possiblyApplied` is false only before sending.
 * Core errors copy body fields, preserving access such as `e.detail`.
 *
 * The root exports these as `CoreRateLimitError` / `CoreServerError`; the released `RateLimitError` /
 * `ServerError` remain the `DatasetError` subclasses in `src/utils/errors.ts` (CHANGELOG "Unreleased").
 */

import { SDKException } from "../utils/errors";

/** The record a `FutureAGIAPIError` carries besides its status and body. */
export interface APIErrorFields {
  /** Server machine-readable code; defaults to `http_<status>`. */
  readonly code?: string;
  /** Display message, overriding the description derived from the body. */
  readonly message?: string;
  /** Server request identifier, when available. */
  readonly requestId?: string;
  /** Upstream request identifier, when available. */
  readonly upstreamRequestId?: string;
  /** Server receipt identifier, when available. */
  readonly receiptId?: string;
  /** Idempotency key sent with the request, if any. */
  readonly idempotencyKey?: string;
  /** Server retry hint in seconds. */
  readonly retryAfter?: number;
  /** SDK operation name associated with the failure, when available. */
  readonly operation?: string;
}

/** The server answered with an HTTP error status. `payload` is the parsed body (redacted on platform calls). */
export class FutureAGIAPIError extends SDKException {
  /** HTTP status returned by the server. */
  readonly statusCode: number;
  /** Parsed response body, redacted for platform calls. */
  readonly payload: unknown;
  /** The server's machine code (`idempotency_key_in_progress`), or `http_<status>`. */
  readonly code: string;
  /** Server request identifier, when available. */
  readonly requestId?: string;
  /** Upstream request identifier, when available. */
  readonly upstreamRequestId?: string;
  /** Server receipt identifier, when available. */
  readonly receiptId?: string;
  /** The `Idempotency-Key` the call sent, when it sent one. */
  readonly idempotencyKey?: string;
  /** The server's wait hint, in seconds. */
  readonly retryAfter?: number;
  /** SDK operation name associated with the failure, when available. */
  readonly operation?: string;

  constructor(statusCode: number, payload: unknown, fields: APIErrorFields = {}) {
    let text = fields.message ?? `Future AGI API request failed with status ${statusCode}: ${describe(payload)}`;
    if (fields.requestId !== undefined && !text.includes(fields.requestId)) text += ` (request id ${fields.requestId})`;
    super(text);
    this.statusCode = statusCode;
    this.payload = payload;
    this.code = fields.code ?? `http_${statusCode}`;
    if (fields.requestId !== undefined) this.requestId = fields.requestId;
    if (fields.upstreamRequestId !== undefined) this.upstreamRequestId = fields.upstreamRequestId;
    if (fields.receiptId !== undefined) this.receiptId = fields.receiptId;
    if (fields.idempotencyKey !== undefined) this.idempotencyKey = fields.idempotencyKey;
    if (fields.retryAfter !== undefined) this.retryAfter = fields.retryAfter;
    if (fields.operation !== undefined) this.operation = fields.operation;
  }

  /** The HTTP status (the same value as `statusCode`). */
  get status(): number {
    return this.statusCode;
  }

  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "FUTURE_AGI_API_ERROR";
  }

  /** A JSON-safe record: never the payload or a credential. */
  toJSON(): Record<string, unknown> {
    const out: Record<string, unknown> = { name: this.name, errorCode: this.getErrorCode(), message: this.message };
    for (const key of [
      "statusCode",
      "code",
      "requestId",
      "upstreamRequestId",
      "receiptId",
      "idempotencyKey",
      "retryAfter",
      "operation",
    ] as const) {
      if (this[key] !== undefined) out[key] = this[key];
    }
    return out;
  }
}

function describe(payload: unknown): string {
  if (typeof payload === "string") return payload.slice(0, 500);
  try {
    return JSON.stringify(payload)?.slice(0, 500) ?? String(payload);
  } catch {
    return String(payload);
  }
}

/** Missing or rejected credentials. */
export class AuthError extends SDKException {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "AUTH_ERROR";
  }
}
/** No API key / secret key could be resolved. */
export class CredentialsMissingError extends AuthError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "MISSING_AUTH";
  }
}
/** 400: the server refused the request as malformed. */
export class BadRequestError extends FutureAGIAPIError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "BAD_REQUEST";
  }
}

/** 401. Python's twin is also an `AuthError`; TypeScript has single inheritance, so use `isAuthError(e)`. */
export class AuthenticationError extends FutureAGIAPIError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "AUTHENTICATION_FAILED";
  }
}

/** 402: payment, entitlement or a licence is required; inspect `code` for the reason. */
export class PaymentRequiredError extends FutureAGIAPIError {
  /** Stable SDK category; distinct from the server's machine code. */
  getErrorCode(): string {
    return "PAYMENT_REQUIRED";
  }
}

/** 402 LICENSE_MISSING: ask this server's administrator to configure an Enterprise licence.
 * Mapped messages name the feature when the server supplies it.
 * Makes no claim about availability on hosted deployments.
 */
export class LicenseRequiredError extends PaymentRequiredError {
  /** Stable SDK category; distinct from the server's machine code. */
  getErrorCode(): string {
    return "LICENSE_REQUIRED";
  }
}

/** 403: the keys are valid but may not do this. */
export class PermissionDeniedError extends FutureAGIAPIError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "PERMISSION_DENIED";
  }
}

/** 403 with the exact top-level `error: "wrong_region"` envelope. Correction is explicit, never automatic. */
export class WrongRegionError extends PermissionDeniedError {
  constructor(statusCode: number, _payload: unknown, fields: APIErrorFields = {}) {
    // Do not retain server prose, payloads or diagnostic IDs: opaque exec/upload failures may echo
    // fragments of private input, and response-supplied destinations are never routing guidance.
    super(statusCode, { error: "wrong_region" }, {
      code: "wrong_region",
      message: "The selected regional base rejected this request (wrong_region). Manually select the intended regional base: " +
        "US https://api.futureagi.com or EU https://api-eu.futureagi.com using baseUrl / FI_BASE_URL, or explicitly " +
        "configure platformBaseUrl / FI_PLATFORM_BASE_URL with the required platform path. The SDK does not discover " +
        "residency and never probes, redirects or retries against another region.",
      ...(fields.operation !== undefined ? { operation: fields.operation } : {}),
      ...(fields.idempotencyKey !== undefined ? { idempotencyKey: fields.idempotencyKey } : {}),
    });
  }
  /** A permission-denied specialization, publicly catchable without parsing prose. */
  getErrorCode(): string {
    return "WRONG_REGION";
  }
}

/** 404. */
export class NotFoundError extends FutureAGIAPIError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "NOT_FOUND";
  }
}

/** A complete non-envelope Console 404; `instanceof NotFoundError` still matches.
 * Hosted Future AGI does not support Console SDK access in this release. For self-hosted Enterprise,
 * set FI_PLATFORM_BASE_URL to the Console API origin, or check that URL if already configured.
 * Capped/interrupted bodies, even HTML, cannot establish unavailability; no preflight is made.
 */
export class ConsoleUnavailableError extends NotFoundError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "CONSOLE_UNAVAILABLE";
  }
}

/** 404 `product_not_admitted`: the product is not enabled for this workspace. */
export class ProductNotAvailableError extends NotFoundError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "PRODUCT_NOT_AVAILABLE";
  }
}

/** 409. */
export class ConflictError extends FutureAGIAPIError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "CONFLICT";
  }
}

/** 409 `idempotency_key_in_progress`; the platform client waits and resends before throwing it. */
export class IdempotencyKeyInProgressError extends ConflictError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "IDEMPOTENCY_KEY_IN_PROGRESS";
  }
}

/** 409 for a verb the sandbox's current state does not allow. */
export class SandboxStateError extends ConflictError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "SANDBOX_STATE";
  }
}

/** 413, or a refusal before anything was sent (`local: true`, with `limitBytes`). */
export class PayloadTooLargeError extends FutureAGIAPIError {
  /** True if the SDK rejected the body before sending it. */
  readonly local: boolean;
  /** Locally enforced body limit in bytes, when known. */
  readonly limitBytes?: number;
  constructor(statusCode: number, payload: unknown, fields: APIErrorFields & { local?: boolean; limitBytes?: number } = {}) {
    super(statusCode, payload, fields);
    this.local = fields.local ?? false;
    if (fields.limitBytes !== undefined) this.limitBytes = fields.limitBytes;
  }
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "PAYLOAD_TOO_LARGE";
  }
}

/** 422. */
export class UnprocessableEntityError extends FutureAGIAPIError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "UNPROCESSABLE_ENTITY";
  }
}

/** 422 `idempotency_key_reused`: the same key was sent earlier with a different body. */
export class IdempotencyKeyReusedError extends UnprocessableEntityError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "IDEMPOTENCY_KEY_REUSED";
  }
}

/** 429 after the transport's own retries; `retryAfter` is the server's hint in seconds. */
export class CoreRateLimitError extends FutureAGIAPIError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "RATE_LIMITED";
  }
}

/** A 5xx status after the transport's own retries. */
export class CoreServerError extends FutureAGIAPIError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "SERVER_ERROR";
  }
}

/** True for an `AuthError`, a 401 or a 403 (Python's `isinstance(e, fi.errors.AuthError)`). */
export function isAuthError(error: unknown): boolean {
  return error instanceof AuthError || error instanceof AuthenticationError || error instanceof PermissionDeniedError;
}

/** No HTTP response came back. `kind` is `connect` (nothing was sent), `timeout` or `connection`. */
export class TransportError extends SDKException {
  /** Whether the failure occurred while connecting, waiting, or after sending. */
  kind: "connect" | "timeout" | "connection" = "connect";
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "SERVER_UNREACHABLE";
  }
}
/** The request got no response after the transport's own retries; `possiblyApplied` when it may have run. */
export class APIConnectionError extends TransportError {
  /** True when the request may have reached the server before the connection failed. */
  possiblyApplied = false;
  /** Idempotency key sent with the failed request, if any. */
  idempotencyKey?: string;
  /** SDK operation name associated with the failure, when known. */
  operation?: string;
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return this.kind === "connect" ? "SERVER_UNREACHABLE" : "CONNECTION_LOST";
  }
}
/** No answer in time: the request timeout, a stream's idle timeout, or a waiter's deadline. */
export class APITimeoutError extends APIConnectionError {
  /** Timeout classification used by transport-error handlers. */
  kind: "connect" | "timeout" | "connection" = "timeout";
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "TIMEOUT";
  }
}

/** The client refused before sending anything. `code` says which rule. */
export class ConfigurationError extends SDKException {
  /** Machine-readable identifier of the client-side validation rule. */
  readonly code: string;
  /** SDK operation name associated with the failure, when available. */
  readonly operation?: string;
  constructor(message: string, code = "invalid_option", operation?: string) {
    super(message);
    this.code = code;
    if (operation !== undefined) this.operation = operation;
  }
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "CONFIGURATION_ERROR";
  }
}
/** The keys would go to an origin outside the guard; pass `allowCustomPlatformUrl: true` to allow it. */
export class HostNotAllowedError extends ConfigurationError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "HOST_NOT_ALLOWED";
  }
}
/** A Bearer token together with an explicit key pair. */
export class MixedCredentialsError extends ConfigurationError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "MIXED_CREDENTIALS";
  }
}
/** The platform origin is unusable, or no such platform operation exists. */
export class PlatformNotConfiguredError extends ConfigurationError {
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "PLATFORM_NOT_CONFIGURED";
  }
}

/** A 3xx answer: platform calls never follow redirects. `targetHost` names the host only. */
export class UnexpectedRedirectError extends SDKException {
  constructor(
    message: string,
    /** Redirect status returned by the server. */
    readonly statusCode: number,
    /** Redirect target's host and port only, never its path or query. */
    readonly targetHost?: string,
    /** Server request identifier, when available. */
    readonly requestId?: string,
    /** SDK operation name associated with the redirect. */
    readonly operation?: string,
  ) {
    super(message);
  }
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "UNEXPECTED_REDIRECT";
  }
}

/** A resumable stream spent its reconnect budget; resume from `lastSequence`. */
export class StreamInterruptedError extends SDKException {
  constructor(
    message: string,
    /** Last durable event sequence; pass it when resuming the stream. */
    readonly lastSequence?: string,
    /** SDK streaming operation whose reconnect budget was exhausted. */
    readonly operation?: string,
    cause?: Error,
  ) {
    super(message, cause);
  }
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "STREAM_INTERRUPTED";
  }
}
