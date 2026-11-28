/**
 * Full exception hierarchy mirroring the Python SDK.
 *
 * AgentCCError (base)
 * ├── APIConnectionError
 * │   └── APITimeoutError
 * ├── APIStatusError
 * │   ├── BadRequestError          (400)
 * │   ├── AuthenticationError      (401)
 * │   ├── PermissionDeniedError    (403)
 * │   ├── NotFoundError            (404)
 * │   ├── UnprocessableEntityError (422)
 * │   ├── RateLimitError           (429)
 * │   ├── InternalServerError      (500)
 * │   ├── BadGatewayError          (502)
 * │   ├── ServiceUnavailableError  (503)
 * │   ├── GatewayTimeoutError      (504)
 * │   ├── GuardrailBlockedError    (446)
 * │   └── GuardrailWarning         (246)
 * └── StreamError
 */

export interface ErrorBody {
  type?: string;
  code?: string;
  message?: string;
  param?: string;
}

// ---------------------------------------------------------------------------
// Base
// ---------------------------------------------------------------------------

export class AgentCCError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AgentCCError";
  }
}

// ---------------------------------------------------------------------------
// Connection errors
// ---------------------------------------------------------------------------

export class APIConnectionError extends AgentCCError {
  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = "APIConnectionError";
  }
}

export class APITimeoutError extends APIConnectionError {
  constructor(message = "Request timed out") {
    super(message);
    this.name = "APITimeoutError";
  }
}

// ---------------------------------------------------------------------------
// Status errors
// ---------------------------------------------------------------------------

export class APIStatusError extends AgentCCError {
  public readonly statusCode: number;
  public readonly body: ErrorBody | unknown;
  public readonly requestId: string | null;
  public readonly headers: Headers;

  constructor(
    statusCode: number,
    body: unknown,
    headers: Headers,
    message?: string,
  ) {
    const msg =
      message ||
      errorMessage(body) ||
      `Request failed with status ${statusCode}`;
    super(msg);
    this.name = "APIStatusError";
    this.statusCode = statusCode;
    this.body = body;
    this.headers = headers;
    this.requestId =
      headers.get("x-agentcc-request-id") ||
      headers.get("x-request-id") ||
      null;
  }

  /** Factory: return the most specific error subclass for a status code. */
  static from(
    statusCode: number,
    body: unknown,
    headers: Headers,
  ): APIStatusError {
    switch (statusCode) {
      case 246:
        return new GuardrailWarning(body, headers);
      case 400:
        return new BadRequestError(body, headers);
      case 401:
        return new AuthenticationError(body, headers);
      case 403:
        return new PermissionDeniedError(body, headers);
      case 404:
        return new NotFoundError(body, headers);
      case 422:
        return new UnprocessableEntityError(body, headers);
      case 429:
        return new RateLimitError(body, headers);
      case 446:
        return new GuardrailBlockedError(body, headers);
      case 500:
        return new InternalServerError(body, headers);
      case 502:
        return new BadGatewayError(body, headers);
      case 503:
        return new ServiceUnavailableError(body, headers);
      case 504:
        return new GatewayTimeoutError(body, headers);
      default:
        return new APIStatusError(statusCode, body, headers);
    }
  }
}

// --- Concrete status errors ---

export class BadRequestError extends APIStatusError {
  constructor(body: unknown, headers: Headers) {
    super(400, body, headers);
    this.name = "BadRequestError";
  }
}

export class AuthenticationError extends APIStatusError {
  constructor(body: unknown, headers: Headers) {
    super(401, body, headers);
    this.name = "AuthenticationError";
  }
}

export class PermissionDeniedError extends APIStatusError {
  constructor(body: unknown, headers: Headers) {
    super(403, body, headers);
    this.name = "PermissionDeniedError";
  }
}

export class NotFoundError extends APIStatusError {
  constructor(body: unknown, headers: Headers) {
    super(404, body, headers);
    this.name = "NotFoundError";
  }
}

export class UnprocessableEntityError extends APIStatusError {
  constructor(body: unknown, headers: Headers) {
    super(422, body, headers);
    this.name = "UnprocessableEntityError";
  }
}

export class RateLimitError extends APIStatusError {
  public readonly ratelimitLimit: number | null;
  public readonly ratelimitRemaining: number | null;
  public readonly ratelimitReset: number | null;

  constructor(body: unknown, headers: Headers) {
    super(429, body, headers);
    this.name = "RateLimitError";
    this.ratelimitLimit = parseIntHeader(headers, "x-ratelimit-limit-requests");
    this.ratelimitRemaining = parseIntHeader(
      headers,
      "x-ratelimit-remaining-requests",
    );
    this.ratelimitReset = parseIntHeader(
      headers,
      "x-ratelimit-reset-requests",
    );
  }
}

export class InternalServerError extends APIStatusError {
  constructor(body: unknown, headers: Headers) {
    super(500, body, headers);
    this.name = "InternalServerError";
  }
}

export class BadGatewayError extends APIStatusError {
  constructor(body: unknown, headers: Headers) {
    super(502, body, headers);
    this.name = "BadGatewayError";
  }
}

export class ServiceUnavailableError extends APIStatusError {
  constructor(body: unknown, headers: Headers) {
    super(503, body, headers);
    this.name = "ServiceUnavailableError";
  }
}

export class GatewayTimeoutError extends APIStatusError {
  constructor(body: unknown, headers: Headers) {
    super(504, body, headers);
    this.name = "GatewayTimeoutError";
  }
}

// --- Guardrail errors ---

function parseGuardrailHeader(headers: Headers, suffix: string): string | null {
  return headers.get(`x-agentcc-guardrail-${suffix}`) || null;
}

export class GuardrailBlockedError extends APIStatusError {
  public readonly guardrailName: string | null;
  public readonly guardrailAction: string | null;
  public readonly guardrailConfidence: number | null;
  public readonly guardrailMessage: string | null;

  constructor(body: unknown, headers: Headers) {
    super(446, body, headers, "Request blocked by guardrail");
    this.name = "GuardrailBlockedError";
    this.guardrailName = parseGuardrailHeader(headers, "name");
    this.guardrailAction = parseGuardrailHeader(headers, "action");
    this.guardrailMessage = parseGuardrailHeader(headers, "message");
    const conf = parseGuardrailHeader(headers, "confidence");
    this.guardrailConfidence = conf ? parseFloat(conf) : null;
  }
}

export class GuardrailWarning extends APIStatusError {
  public readonly guardrailName: string | null;
  public readonly guardrailAction: string | null;
  public readonly guardrailConfidence: number | null;
  public readonly guardrailMessage: string | null;
  public readonly completion: unknown;

  constructor(body: unknown, headers: Headers) {
    super(246, body, headers, "Request completed with guardrail warning");
    this.name = "GuardrailWarning";
    this.guardrailName = parseGuardrailHeader(headers, "name");
    this.guardrailAction = parseGuardrailHeader(headers, "action");
    this.guardrailMessage = parseGuardrailHeader(headers, "message");
    const conf = parseGuardrailHeader(headers, "confidence");
    this.guardrailConfidence = conf ? parseFloat(conf) : null;
    this.completion = body;
  }
}

// ---------------------------------------------------------------------------
// Stream error
// ---------------------------------------------------------------------------

export class StreamError extends AgentCCError {
  constructor(message: string) {
    super(message);
    this.name = "StreamError";
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// The gateway answers OpenAI-style (`{error: {message}}`); proxies and older routes answer
// `{error: "text"}`, `{message}` or `{detail}`.
function errorMessage(body: unknown): string | undefined {
  if (!body || typeof body !== "object") return undefined;
  const b = body as Record<string, unknown>;
  const candidates = [
    b.error && typeof b.error === "object" ? (b.error as Record<string, unknown>).message : b.error,
    b.message,
    b.detail,
  ];
  return candidates.find((c): c is string => typeof c === "string" && c.length > 0);
}

function parseIntHeader(headers: Headers, name: string): number | null {
  const v = headers.get(name);
  if (!v) return null;
  const n = parseInt(v, 10);
  return Number.isNaN(n) ? null : n;
}
