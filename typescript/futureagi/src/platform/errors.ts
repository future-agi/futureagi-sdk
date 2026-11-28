// One error hierarchy for every resource.

/** Base class for every error the platform client throws. */
export class FutureAGIError extends Error {
  constructor(message: string) {
    super(message);
    this.name = new.target.name;
  }
}

/** The request got no response (DNS, TLS, timeout, connection reset). */
export class APIConnectionError extends FutureAGIError {}

/**
 * The API answered with an error status. `type`, `code` and `detail` come from the backend's
 * error envelope (`{status: false, type, code, detail, ...}`) when it is present. A simulation
 * environment refusal (`{error, message, retryable}`) gives its `error` as `code`.
 */
export class APIError extends FutureAGIError {
  readonly status: number;
  readonly body: unknown;
  readonly type: string | null;
  readonly code: string | null;
  readonly detail: unknown;
  readonly requestId: string | null;

  constructor(message: string, status: number, body: unknown, requestId: string | null = null) {
    super(message);
    this.status = status;
    this.body = body;
    const envelope = isRecord(body) ? body : {};
    this.type = typeof envelope.type === "string" ? envelope.type : null;
    this.code =
      typeof envelope.code === "string" ? envelope.code : typeof envelope.error === "string" ? envelope.error : null;
    this.detail = envelope.detail;
    this.requestId = requestId;
  }
}

/** A successful response did not satisfy its checked public schema. Never includes body values. */
export class ResponseValidationError extends FutureAGIError {}

export class BadRequestError extends APIError {}
export class AuthenticationError extends APIError {}
/** Feature not on the organization's plan. */
export class PaymentRequiredError extends APIError {}
export class PermissionDeniedError extends APIError {}

/** The exact 403 `error: "wrong_region"` response; correction is manual, not automatic. */
export class WrongRegionError extends PermissionDeniedError {
  readonly code = "wrong_region";

  constructor() {
    super(
      "403 The selected regional base rejected this request (wrong_region). " +
        "Manually select the intended regional base: US https://api.futureagi.com or " +
        "EU https://api-eu.futureagi.com using baseUrl / FI_BASE_URL. " +
        "The SDK does not discover residency and does not probe, redirect or retry against another region.",
      403, { error: "wrong_region" },
    );
  }
}

/** Only the frozen top-level string envelope at 403 is regional evidence. Do not infer it from a
 * nested code, wrapper, status alone or response prose; check before any privacy transformation. */
function isWrongRegionResponse(status: number, body: unknown): boolean {
  return status === 403 && body !== null && typeof body === "object" && !Array.isArray(body) &&
    Object.prototype.hasOwnProperty.call(body, "error") && (body as Record<string, unknown>).error === "wrong_region";
}

export class NotFoundError extends APIError {}
export class ConflictError extends APIError {}
export class UnprocessableEntityError extends APIError {}
export class RateLimitError extends APIError {}
export class InternalServerError extends APIError {}

const BY_STATUS: Record<number, typeof APIError> = {
  400: BadRequestError,
  401: AuthenticationError,
  402: PaymentRequiredError,
  403: PermissionDeniedError,
  404: NotFoundError,
  409: ConflictError,
  422: UnprocessableEntityError,
  429: RateLimitError,
};

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Build the typed error for a non-2xx response whose body has already been read. */
export function errorFromResponse(status: number, text: string, requestId: string | null): APIError {
  let body: unknown = text;
  try {
    body = JSON.parse(text);
  } catch {
    // not JSON: keep the text
  }
  if (isWrongRegionResponse(status, body)) {
    return new WrongRegionError();
  }
  let message: string | null = null;
  if (isRecord(body)) {
    const candidate = body.message ?? body.error ?? body.detail;
    if (candidate !== undefined && candidate !== null) {
      message = typeof candidate === "string" ? candidate : JSON.stringify(candidate); // DRF field errors: {"field": ["..."]}
    }
  }
  const cls = BY_STATUS[status] ?? (status >= 500 ? InternalServerError : APIError);
  return new cls(`${status} ${message ?? `HTTP ${status}`}`, status, body, requestId);
}
