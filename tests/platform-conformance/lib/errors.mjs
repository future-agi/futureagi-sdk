/**
 * Error normalisation and classification: the language-neutral error names every runner reports.
 *
 * Three wire shapes arrive:
 *   gateway  {error: "<code>", reason, requestId, retryAfterSeconds?}
 *   EE       {error: {code, message, detail}, code, message, detail, request_id}
 *   Hub      {error: {code, message, fix}}
 * A body in none of them (an HTML 502, an empty 504) is classified by status alone: its code is
 * `http_<status>`, its text is dropped, and the request id comes from the `x-request-id` header.
 * The names are neutral: each SDK's conformance binding maps its own error classes onto them, so
 * every runner reports the same `errorClass`.
 */

const NOT_ENABLED = /(^|_)not_enabled$|^feature_disabled$|_disabled$/;

function str(value) {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

/** One normalised record from a status, a parsed body (or null) and a header getter. */
export function normalizeError(status, body, header = () => undefined) {
  const obj = body !== null && typeof body === "object" && !Array.isArray(body) ? body : null;
  const nested = obj && obj.error && typeof obj.error === "object" ? obj.error : null;
  const code = str(obj?.code) ?? str(nested?.code) ?? (typeof obj?.error === "string" ? obj.error : undefined);
  const known = code !== undefined;
  const retryHeader = Number(header("retry-after"));
  const retryBody = Number(obj?.retryAfterSeconds ?? nested?.retryAfterSeconds);
  const record = {
    status,
    code: known ? code : `http_${status}`,
    shape: !known ? "status-only" : nested ? (nested.fix !== undefined ? "hub" : "ee") : "gateway",
    reason: known ? str(obj?.reason) : undefined,
    message: known ? str(obj?.message) ?? str(nested?.message) : undefined,
    hint: known ? str(nested?.fix) : undefined,
    requestId: str(header("x-request-id")) ?? (known ? str(obj?.requestId) : undefined),
    upstreamRequestId: (known ? str(obj?.request_id) : undefined) ?? str(header("x-upstream-request-id")),
    retryAfterSeconds: Number.isFinite(retryBody) ? retryBody : Number.isFinite(retryHeader) ? retryHeader : undefined,
  };
  for (const key of Object.keys(record)) if (record[key] === undefined) delete record[key];
  return record;
}

/** The neutral error name for a status and code, or null for a 2xx. */
export function errorClassFor(status, code = "") {
  if (status >= 200 && status < 300) return null;
  if (status >= 300 && status < 400) return "UnexpectedRedirectError";
  switch (status) {
    case 400: return "BadRequestError";
    case 401: return "AuthenticationError";
    case 403: return "PermissionDeniedError";
    case 404: return code === "product_not_admitted" ? "ProductNotAvailableError" : "NotFoundError";
    case 409:
      if (code === "idempotency_key_in_progress") return "IdempotencyKeyInProgressError";
      if (/quota/.test(code)) return "QuotaExceededError";
      if (/state|not_running|hibernated|already_/.test(code)) return "SandboxStateError";
      return "ConflictError";
    case 413: return "PayloadTooLargeError";
    case 422: return code === "idempotency_key_reused" ? "IdempotencyKeyReusedError" : "UnprocessableEntityError";
    case 429: return "RateLimitError";
    case 500: return "InternalServerError";
    case 502: return "UpstreamError";
    case 503:
      if (code === "product_paused") return "ProductPausedError";
      if (code === "omega_rate_limit_unavailable") return "RateLimitUnavailableError";
      if (NOT_ENABLED.test(code)) return "FeatureNotEnabledError";
      return "ServiceUnavailableError";
    case 504: return "GatewayTimeoutError";
    case 507: return "InsufficientStorageError";
    default: return status >= 500 ? "InternalServerError" : "APIStatusError";
  }
}

/** Every class name above plus the client-side ones, for case validation. */
export const ERROR_CLASSES = Object.freeze([
  "SDKException", "HostNotAllowedError", "MixedCredentialsError", "PlatformNotConfiguredError",
  "CredentialsMissingError", "APIConnectionError", "APITimeoutError", "APIStatusError",
  "UnexpectedRedirectError", "BadRequestError", "AuthenticationError", "PermissionDeniedError",
  "NotFoundError", "ProductNotAvailableError", "ConflictError", "SandboxStateError", "QuotaExceededError",
  "IdempotencyKeyInProgressError", "PayloadTooLargeError", "UnprocessableEntityError",
  "IdempotencyKeyReusedError", "RateLimitError", "InternalServerError", "UpstreamError",
  "GatewayTimeoutError", "ServiceUnavailableError", "ProductPausedError", "RateLimitUnavailableError",
  "FeatureNotEnabledError", "InsufficientStorageError", "StreamError", "StreamInterruptedError",
  "CommandInterruptedError", "CommandExitError", "IncompatibleServerError", "EgressBlockedError",
]);
