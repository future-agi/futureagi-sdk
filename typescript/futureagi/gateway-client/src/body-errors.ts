import { AgentCCError } from "./error-base.js";
import type { ErrorBody } from "./errors.js";
import { parseGatewayEvidence } from "./gateway-evidence.js";
import type { GatewayEvidence } from "./gateway-evidence.js";
import { UNCONFIRMED_DISPATCH_REMEDY } from "./refusal-policy.js";

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
