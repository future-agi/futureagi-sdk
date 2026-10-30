// One error hierarchy for every resource.

/** Base class for every error the platform client throws. */
export class FutureAGIError extends Error {
  constructor(message: string) {
    super(message);
    this.name = new.target.name;
  }
}

/** The request never got a response (DNS, TLS, timeout, connection reset). */
export class APIConnectionError extends FutureAGIError {}

/**
 * The API answered with an error status. `type`, `code` and `detail` come from the backend's
 * error envelope (`{status: false, type, code, detail, ...}`) when it is present.
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
    this.code = typeof envelope.code === "string" ? envelope.code : null;
    this.detail = envelope.detail;
    this.requestId = requestId;
  }
}

export class BadRequestError extends APIError {}
export class AuthenticationError extends APIError {}
/** Feature not on the organization's plan. */
export class PaymentRequiredError extends APIError {}
export class PermissionDeniedError extends APIError {}
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
