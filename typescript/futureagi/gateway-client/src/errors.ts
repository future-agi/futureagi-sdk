import { classifyRefusal, CREDITS_OFF_REMEDY, hasUnconfirmedDispatch, numberField, refusalDetails, refusalMetadata, stringField, suggestionsField, UNCONFIRMED_DISPATCH_REMEDY, withRefusalDetails } from "./refusal-policy.js";
import type { RefusalCategory } from "./refusal-policy.js";
import { evidenceFromHeaders, parseGatewayEvidence } from "./gateway-evidence.js";
import type { GatewayEvidence } from "./gateway-evidence.js";
import { ambiguousMetadata, unpricedMetadata } from "./refusal-metadata.js";
import { safeDiagnosticHeaders } from "./redact.js";

/**
 * Full exception hierarchy mirroring the Python SDK.
 *
 * AgentCCError (base)
 * ├── APIConnectionError
 * │   └── APITimeoutError
 * ├── ResponseBodyError
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

/**
 * The gateway's error object, `{"message", "type", "param", "code"}`.
 * The gateway sends `param` as `null` when it is not set, and
 * OpenAI-compatible error bodies send `code` as `null` the same way.
 */
export interface ErrorBody {
  type?: string | null;
  code?: string | null;
  message?: string;
  param?: string | null;
  /** Machine-readable detail; the gateway omits it when there is none. */
  metadata?: unknown;
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
  readonly gatewayEvidence: GatewayEvidence;
  get dispatched() { return this.gatewayEvidence.dispatched; }
  get remedy(): string | null {
    return this.dispatched === "unknown" ? UNCONFIRMED_DISPATCH_REMEDY : null;
  }
  constructor(message: string, public readonly cause?: unknown, gatewayEvidence: GatewayEvidence = parseGatewayEvidence()) {
    super(message);
    this.name = "APIConnectionError";
    this.gatewayEvidence = gatewayEvidence;
  }
}

export class APITimeoutError extends APIConnectionError {
  constructor(message = "Request timed out", gatewayEvidence?: GatewayEvidence) {
    super(message, undefined, gatewayEvidence);
    this.name = "APITimeoutError";
  }
}

/**
 * A final response arrived, but its successful JSON body could not be read or
 * decoded. Never retried automatically: the request may already have executed.
 * Only the allowlisted header snapshot is retained, not the transport exception
 * (which may hold credential-bearing request/response objects).
 */
export class ResponseBodyError extends AgentCCError {
  readonly gatewayEvidence: GatewayEvidence;
  get requestId() { return this.gatewayEvidence.gatewayRequestId; }
  get gatewayRequestId() { return this.gatewayEvidence.gatewayRequestId; }
  get dispatched() { return this.gatewayEvidence.dispatched; }
  get clientRequestId() { return this.gatewayEvidence.clientRequestId; }

  get remedy(): string | null {
    return this.dispatched === "unknown" ? UNCONFIRMED_DISPATCH_REMEDY : null;
  }

  constructor(gatewayEvidence: GatewayEvidence) {
    super(bodyFailureGuidance("Failed to read response body", gatewayEvidence).message);
    this.name = "ResponseBodyError";
    this.gatewayEvidence = gatewayEvidence;
  }
}

// ---------------------------------------------------------------------------
// Status errors
// ---------------------------------------------------------------------------

export class APIStatusError extends AgentCCError {
  public readonly statusCode: number;
  public readonly body: ErrorBody | unknown;
  public readonly requestId: string | null;
  public readonly gatewayEvidence: GatewayEvidence;
  get dispatched() { return this.gatewayEvidence.dispatched; }
  get gatewayRequestId() { return this.gatewayEvidence.gatewayRequestId; }
  get clientRequestId() { return this.gatewayEvidence.clientRequestId; }
  public readonly headers: Headers;

  constructor(
    statusCode: number,
    body: unknown,
    headers: Headers,
    message?: string,
  ) {
    const msg =
      message ||
      gatewayMessage(body) ||
      `Request failed with status ${statusCode}`;
    super(msg);
    this.name = "APIStatusError";
    this.statusCode = statusCode;
    this.body = body;
    this.headers = new Headers(safeDiagnosticHeaders(headers));
    this.gatewayEvidence = evidenceFromHeaders(headers);
    this.requestId = this.gatewayEvidence.gatewayRequestId;
  }

  /** Canonical category; unknown/mismatched codes keep their class but are generic. */
  get category(): RefusalCategory {
    return refusalDetails(this.statusCode, this.body)?.category ?? "generic";
  }

  /** Corrective action text, or null when no corrective action is specified. */
  get remedy(): string | null {
    return refusalDetails(this.statusCode, this.body)?.remedy
      ?? (hasUnconfirmedDispatch(this.statusCode, this.body, this.headers, this.gatewayEvidence) ? UNCONFIRMED_DISPATCH_REMEDY : null);
  }

  /** Optional wire metadata, shared by every status class without adding stored state. */
  get metadata(): Record<string, unknown> | null { return refusalMetadata(this.body); }
  get requiredUsd(): number | null { return numberField(this.metadata, "required_usd"); }
  get availableUsd(): number | null { return numberField(this.metadata, "available_usd"); }
  get limitSource(): string | null { return stringField(this.metadata, "limit_source"); }
  get remedyHint(): string | null { return stringField(this.metadata, "remedy_hint"); }
  get scope(): string | null { return stringField(this.metadata, "scope"); }
  get resetsAt(): string | null { return stringField(this.metadata, "resets_at"); }
  get reason(): string | null { return stringField(this.metadata, "reason"); }
  get capScope(): string | null { return stringField(this.metadata, "cap_scope"); }
  get capRef(): string | null { return stringField(this.metadata, "cap_ref"); }
  get capKind(): string | null { return stringField(this.metadata, "cap_kind"); }
  get policyRevision(): number | null { return numberField(this.metadata, "policy_revision"); }
  get suggestions(): string[] | null { return suggestionsField(this.metadata); }
  get modelAliasRequested(): string | null { return stringField(this.metadata, "model_alias_requested"); }
  get model(): string | null { return stringField(this.metadata, "model"); }
  get unpricedMetadata() { return unpricedMetadata(this.metadata); }
  get ambiguousMetadata() { return ambiguousMetadata(this.metadata); }
  get candidates(): string[] | null {
    const value = this.metadata?.candidates;
    return Array.isArray(value) && value.every((item) => typeof item === "string") ? [...value] : null;
  }

  /** Factory: classify billing refusals by status and code, otherwise by status. */
  static from(
    statusCode: number,
    body: unknown,
    headers: Headers,
  ): APIStatusError {
    switch (classifyRefusal(statusCode, body)?.name) {
      case "InsufficientCreditsError": return new InsufficientCreditsError(body, headers);
      case "AgentBudgetExhaustedError": return new AgentBudgetExhaustedError(body, headers);
      case "BudgetExceededError": return new BudgetExceededError(body, headers);
      case "FutureAGICreditsOffError": return new FutureAGICreditsOffError(body, headers);
    }
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

/** 403 — a Future AGI model was called while the organization's credits are off. Never retried. */
export class FutureAGICreditsOffError extends PermissionDeniedError {
  constructor(body: unknown, headers: Headers) {
    super(body, headers);
    this.name = "FutureAGICreditsOffError";
  }

  /** Two ways to enable requests; the gateway's message is unchanged. */
  get remedy(): string {
    return CREDITS_OFF_REMEDY;
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

/** 402 — managed credits cannot pay for the request. */
export class InsufficientCreditsError extends withRefusalDetails(APIStatusError) {
  constructor(body: unknown, headers: Headers) {
    super(402, body, headers);
    this.name = "InsufficientCreditsError";
  }
}

/** 402 — the agent's budget is exhausted. */
export class AgentBudgetExhaustedError extends withRefusalDetails(APIStatusError) {
  constructor(body: unknown, headers: Headers) {
    super(402, body, headers);
    this.name = "AgentBudgetExhaustedError";
  }
}

/** 429 — a budget refusal; still caught by existing RateLimitError handlers. */
export class BudgetExceededError extends withRefusalDetails(RateLimitError) {
  constructor(body: unknown, headers: Headers) {
    super(body, headers);
    this.name = "BudgetExceededError";
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

/** The gateway's error fields for a {@link StreamError}. */
export interface StreamErrorOptions {
  /** An SDK-owned body read or decode failed, rather than a gateway error frame. */
  bodyReadFailure?: boolean;
  /** Owning initial response evidence, never inferred from an event payload. */
  gatewayEvidence?: GatewayEvidence;
  /** The error's type, e.g. `"guardrail_error"` or `"gateway_timeout"`. */
  type?: string | null;
  /** The error's code, e.g. `"stream_blocked"` for a guardrail block. */
  code?: string | null;
  param?: string | null;
  /**
   * The `error` value of the gateway's SSE frame, as sent: its error object,
   * or a string. `null` for any other value.
   */
  body?: ErrorBody | string | null;
}

/**
 * Raised while iterating a stream: when the gateway ends the stream with an
 * error event (a guardrail block, an upstream timeout), or when the stream
 * itself is malformed. For a gateway error, `message` is the gateway's message
 * and `type`, `code`, `param` and `body` carry its error object; for an SDK
 * error they are `null`.
 */
export class StreamError extends AgentCCError {
  public readonly gatewayEvidence: GatewayEvidence;
  get dispatched() { return this.gatewayEvidence.dispatched; }
  get gatewayRequestId() { return this.gatewayEvidence.gatewayRequestId; }
  get clientRequestId() { return this.gatewayEvidence.clientRequestId; }
  public readonly type: string | null;
  public readonly code: string | null;
  public readonly param: string | null;
  public readonly body: ErrorBody | string | null;

  public readonly remedy: string | null;

  constructor(message: string, options: StreamErrorOptions = {}) {
    const evidence = options.gatewayEvidence ?? parseGatewayEvidence();
    // Keep the public construction option compatible, but it is NOT an origin
    // marker: a caller-created instance is still wrapped at the stream exit.
    const guidance = options.bodyReadFailure ? bodyFailureGuidance(message, evidence) : { message, remedy: null };
    super(guidance.message);
    this.name = "StreamError";
    this.remedy = guidance.remedy;
    this.gatewayEvidence = evidence;
    this.type = options.type ?? null;
    this.code = options.code ?? null;
    this.param = options.param ?? null;
    this.body = options.body ?? null;
  }
}

// Only these internal factories establish origin. Public constructors, class
// membership, bodyReadFailure and evidence identity cannot populate these sets.
const sdkBodyFailures = new WeakSet<ResponseBodyError | StreamError>();
const sdkStreamFrames = new WeakSet<StreamError>();

/** @internal Construct a terminal failure of an SDK-owned successful body read. */
export function responseBodyError(evidence: GatewayEvidence): ResponseBodyError {
  const error = new ResponseBodyError(evidence);
  sdkBodyFailures.add(error);
  return error;
}

/** @internal Construct a body/read/decode failure, not a gateway error frame. */
export function streamBodyError(message: string, evidence: GatewayEvidence): StreamError {
  const error = new StreamError(message, { gatewayEvidence: evidence });
  sdkBodyFailures.add(error);
  return error;
}

/** @internal Only decoded gateway frames use this factory. */
export function streamFrameError(message: string, options: StreamErrorOptions = {}): StreamError {
  const error = new StreamError(message, options);
  sdkStreamFrames.add(error);
  return error;
}

/** @internal The common outgoing-error boundary for requests and SDK readers.
 * Stream callers supply the captured initial evidence. A reader's public error
 * class (even with matching evidence) cannot masquerade as one of our frames.
 */
export function errorAtExit<T>(error: T): T;
export function errorAtExit(error: unknown, streamEvidence: GatewayEvidence, retainReaderCause?: boolean): unknown;
export function errorAtExit(error: unknown, streamEvidence?: GatewayEvidence, retainReaderCause = false): unknown {
  if (streamEvidence && !sdkBodyFailures.has(error as StreamError) && !sdkStreamFrames.has(error as StreamError)) {
    const wrapped = streamBodyError("Failed to read stream body", streamEvidence);
    // Preserve normalized reader errors after the transport has scrubbed its
    // sent headers. Generic reader failures keep the existing cause-free shape.
    if (retainReaderCause && error instanceof StreamError) Object.defineProperty(wrapped, "cause", { value: error, configurable: true });
    error = wrapped;
  }
  if (sdkBodyFailures.has(error as StreamError)) {
    const failure = error as ResponseBodyError | StreamError;
    const guidance = bodyFailureGuidance(failure.message, failure.gatewayEvidence);
    failure.message = guidance.message;
    if (failure instanceof StreamError) Object.defineProperty(failure, "remedy", { value: guidance.remedy });
  }
  return error;
}

// This is also used by the public constructors for backward compatibility;
// calling it does not grant trusted origin. Applying the exit twice is harmless.
function bodyFailureGuidance(message: string, evidence: GatewayEvidence): { message: string; remedy: string | null } {
  if (evidence.dispatched !== "unknown") return { message, remedy: null };
  const parts = message.split(UNCONFIRMED_DISPATCH_REMEDY);
  if (parts.length === 2) return { message, remedy: UNCONFIRMED_DISPATCH_REMEDY };
  const text = parts.length === 1 ? message : parts.join("").trim().replace(/[.\s]+$/, "");
  return { message: `${text}. ${UNCONFIRMED_DISPATCH_REMEDY}`, remedy: UNCONFIRMED_DISPATCH_REMEDY };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * The message of an error response body: the gateway's envelope
 * `{"error": {"message": ...}}` first, then a top-level `message` (the only
 * place @agentcc/client 1.x looked, so every gateway error read "Request
 * failed with status N"). `body` itself is unchanged.
 */
function gatewayMessage(body: unknown): string | undefined {
  if (!body || typeof body !== "object" || Array.isArray(body)) return undefined;
  const envelope = (body as { error?: unknown }).error;
  if (envelope && typeof envelope === "object" && !Array.isArray(envelope)) {
    const inner = (envelope as ErrorBody).message;
    if (typeof inner === "string" && inner) return inner;
  }
  return (body as ErrorBody).message || undefined;
}

function parseIntHeader(headers: Headers, name: string): number | null {
  const v = headers.get(name);
  if (!v) return null;
  const n = parseInt(v, 10);
  return Number.isNaN(n) ? null : n;
}
