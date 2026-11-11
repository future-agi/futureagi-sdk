/**
 * Sandbox errors. `SandboxError` is the one base: `e instanceof SandboxError` is true for
 * every error the `Sandbox` handle throws for a refusal, a transport failure or a command stream.
 *
 * TypeScript has single inheritance, so each status class extends the shared class in `src/_core/errors` that the
 * platform executor would have thrown (`NotFoundError` here extends the root `NotFoundError`, and so on), so
 * existing handlers still catch them, and `SandboxError` recognises them by a brand (`Symbol.hasInstance`). Two
 * contract classes span several shared classes and are brands too: `ValidationError` (400, extending
 * `BadRequestError`) also matches the 422 `UnprocessableEntityError` and the 428 `PreconditionRequiredError`
 * here; `ConflictError` (409 and 412, extending the shared `ConflictError`) also matches `SandboxStateError` here
 * (a 409 the shared map calls `SandboxStateError`) and its `SandboxHibernatedError`. A status the contract does
 * not name, and a shared class more specific than its status (`WrongRegionError`, `ProductNotAvailableError`,
 * ...), keeps its shared class and gains the brand.
 *
 * `client.sandboxes.*` and the `Sandbox` handle throw these same classes (src/sandbox/wire.ts maps every call).
 *
 * Every class carries `status`, `code`, `message`, `detail`, `requestId` and `retryAfterSeconds` (from
 * `Retry-After` or `detail.retryAfterSeconds`). Messages and fields never contain a credential: the platform
 * executor scrubs the response, and nothing here adds a header or a key.
 */

import { errorClassFor } from "../_core/error-map";
import * as Core from "../_core/errors";
import { SDKException } from "../utils/errors";

const BRAND = Symbol.for("futureagi.sandbox.error");
const CONFLICT = Symbol.for("futureagi.sandbox.conflict");
const VALIDATION = Symbol.for("futureagi.sandbox.validation");

const branded = (value: unknown, brand: symbol): boolean =>
  typeof value === "object" && value !== null && (value as Record<symbol, unknown>)[brand] === true;

/** The fields every sandbox error has. */
export interface SandboxErrorFields {
  /** The HTTP status, when a response came back. */
  readonly status?: number;
  /** The server's machine code (`quota_exceeded`), or the SDK's (`command_incomplete`). */
  readonly code: string;
  /** The server's `detail` object, when it sent one. */
  readonly detail?: unknown;
  /** The server's request id, when it sent one. */
  readonly requestId?: string;
  /** The server's wait hint in seconds. */
  readonly retryAfterSeconds?: number;
  /** The SDK operation (`sandboxes.commands.run`). */
  readonly operation?: string;
}

/** The base of every sandbox error, including the status classes below (see the module comment). */
export class SandboxError extends SDKException implements SandboxErrorFields {
  readonly status?: number;
  readonly code: string;
  readonly detail?: unknown;
  readonly requestId?: string;
  readonly retryAfterSeconds?: number;
  readonly operation?: string;

  constructor(message: string, fields: SandboxErrorFields, cause?: Error) {
    super(message, cause);
    this.code = fields.code;
    if (fields.status !== undefined) this.status = fields.status;
    if (fields.detail !== undefined) this.detail = fields.detail;
    if (fields.requestId !== undefined) this.requestId = fields.requestId;
    if (fields.retryAfterSeconds !== undefined) this.retryAfterSeconds = fields.retryAfterSeconds;
    if (fields.operation !== undefined) this.operation = fields.operation;
  }

  /** `instanceof SandboxError` matches every branded error; a subclass matches by its prototype. */
  static [Symbol.hasInstance](value: unknown): boolean {
    if (this !== SandboxError) return Function.prototype[Symbol.hasInstance].call(this, value);
    return branded(value, BRAND);
  }

  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "SANDBOX_ERROR";
  }

  /** A JSON-safe record: never a payload or a credential. */
  toJSON(): Record<string, unknown> {
    const out: Record<string, unknown> = { name: this.name, errorCode: this.getErrorCode(), message: this.message, code: this.code };
    for (const key of ["status", "requestId", "retryAfterSeconds", "operation"] as const) {
      if (this[key] !== undefined) out[key] = this[key];
    }
    return out;
  }
}

/** The fields a status class adds to its shared class. */
interface StatusFields {
  /** The server's `detail` object, when it sent one. */
  readonly detail?: unknown;
  /** The server's wait hint in seconds (`retryAfter` on the shared class). */
  readonly retryAfterSeconds?: number;
}

/** 401: the credentials were refused. */
export class AuthenticationError extends Core.AuthenticationError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
}
/** 403: the credentials may not do this (or the wrong regional base). */
export class PermissionDeniedError extends Core.PermissionDeniedError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
}
/** 404: no such sandbox, file or snapshot in this workspace. */
export class NotFoundError extends Core.NotFoundError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
}
/** 409: the sandbox's state does not allow this, or a limit is reached. 412: a network policy update named a
 * stale revision (`network_policy_revision_mismatch`): read the policy again and decide; it is never retried.
 * `instanceof ConflictError` also matches this module's `SandboxStateError` and `SandboxHibernatedError`. */
export class ConflictError extends Core.ConflictError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
  static [Symbol.hasInstance](value: unknown): boolean {
    if (this !== ConflictError) return Function.prototype[Symbol.hasInstance].call(this, value);
    return branded(value, CONFLICT);
  }
}
/** 409 `conflict` (or no code): the sandbox's current state does not allow this verb. Also the shared
 * `SandboxStateError`, and a `ConflictError` here. */
export class SandboxStateError extends Core.SandboxStateError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
}
/** 409 with `detail.state` `hibernated`: a read, a sandbox created with autoResume off, or a resume refused at the
 * active cap (`detail.reason` `quota_exceeded`); call `resume()` and retry. Also the shared `SandboxStateError`. */
export class SandboxHibernatedError extends SandboxStateError {}
/** 409 `quota_exceeded`: the workspace's (or, with `detail.scope` `org`, the organization's) active-sandbox limit. */
export class QuotaExceededError extends ConflictError {}
/** 400: the request was refused as invalid. `instanceof ValidationError` also matches this module's
 * `UnprocessableEntityError` (422) and `PreconditionRequiredError` (428). */
export class ValidationError extends Core.BadRequestError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
  static [Symbol.hasInstance](value: unknown): boolean {
    if (this !== ValidationError) return Function.prototype[Symbol.hasInstance].call(this, value);
    return branded(value, VALIDATION);
  }
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "VALIDATION_ERROR";
  }
}
/** 422: the request was refused as invalid. Also the shared `UnprocessableEntityError`, and a `ValidationError`. */
export class UnprocessableEntityError extends Core.UnprocessableEntityError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "VALIDATION_ERROR";
  }
}
/** 428: a network policy update sent no `If-Match` (`network_policy_precondition_required`). A `ValidationError`. */
export class PreconditionRequiredError extends Core.FutureAGIAPIError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "VALIDATION_ERROR";
  }
}
/** 429: rate limited; `retryAfterSeconds` says when to try again. */
export class RateLimitError extends Core.CoreRateLimitError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
}
/** 502: the sandbox provider failed. */
export class ProviderError extends Core.CoreServerError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
}
/** 503: the sandbox service is unavailable. */
export class UnavailableError extends Core.CoreServerError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
}
/** 507: not enough disk (`insufficient_storage`, `disk_quota_exceeded`). */
export class InsufficientStorageError extends Core.CoreServerError implements StatusFields {
  declare readonly detail?: unknown;
  declare readonly retryAfterSeconds?: number;
}

/** No response came back. For a call that changes something, whether it completed is unknown. */
export class SandboxConnectionError extends Core.APIConnectionError implements SandboxErrorFields {
  /** Always `connection_error`. */
  readonly code = "connection_error";
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return this.kind === "timeout" ? "TIMEOUT" : super.getErrorCode();
  }
}

/** What a command stream had produced when it ended. */
export interface CommandOutput {
  /** The command's id from its `started` frame. */
  readonly execId?: string;
  /** Standard output read so far (`commands.run` only). */
  readonly stdout?: string;
  /** Standard error read so far (`commands.run` only). */
  readonly stderr?: string;
}

/** The output stream ended without an `exit` frame: the command may still be running, and whether it finished
 * is unknown. When the connection dropped or went idle after the stream opened, `cause` is that
 * `SandboxConnectionError`. Never retried. */
export class CommandIncompleteError extends SandboxError implements CommandOutput {
  readonly execId?: string;
  readonly stdout?: string;
  readonly stderr?: string;
  constructor(output: CommandOutput = {}, operation = "sandboxes.commands.run", cause?: Error) {
    super(
      "the command's output stream ended without an exit frame" +
        (output.execId !== undefined ? ` (exec ${output.execId})` : "") +
        (cause !== undefined ? ` because the connection failed (${cause.message})` : "") +
        "; whether it finished is unknown and it may still be running. It was not retried: cancel it with " +
        "commands.cancel or check its result in the sandbox",
      { code: "command_incomplete", operation },
      cause,
    );
    if (output.execId !== undefined) this.execId = output.execId;
    if (output.stdout !== undefined) this.stdout = output.stdout;
    if (output.stderr !== undefined) this.stderr = output.stderr;
  }
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "COMMAND_INCOMPLETE";
  }
}

/** The server failed after the command started (an `error` frame); the stream ended. */
export class CommandFailedError extends SandboxError implements CommandOutput {
  readonly execId?: string;
  readonly stdout?: string;
  readonly stderr?: string;
  constructor(serverMessage: string, output: CommandOutput = {}, operation = "sandboxes.commands.run") {
    super(`the command failed on the server: ${serverMessage}`, { code: "command_failed", operation });
    if (output.execId !== undefined) this.execId = output.execId;
    if (output.stdout !== undefined) this.stdout = output.stdout;
    if (output.stderr !== undefined) this.stderr = output.stderr;
  }
  /** The SDK error category, distinct from the server's machine-readable `code`. */
  getErrorCode(): string {
    return "COMMAND_FAILED";
  }
}

for (const cls of [
  AuthenticationError, PermissionDeniedError, NotFoundError, ConflictError, SandboxStateError, ValidationError,
  UnprocessableEntityError, PreconditionRequiredError, RateLimitError, ProviderError, UnavailableError,
  InsufficientStorageError, SandboxConnectionError,
]) {
  Object.defineProperty(cls.prototype, BRAND, { value: true });
}
Object.defineProperty(SandboxError.prototype, BRAND, { value: true });
for (const cls of [ConflictError, SandboxStateError]) Object.defineProperty(cls.prototype, CONFLICT, { value: true });
for (const cls of [ValidationError, UnprocessableEntityError, PreconditionRequiredError]) {
  Object.defineProperty(cls.prototype, VALIDATION, { value: true });
}

type StatusClass = new (statusCode: number, payload: unknown, fields?: Core.APIErrorFields) => Core.FutureAGIAPIError;

const BY_STATUS: Readonly<Record<number, StatusClass>> = {
  400: ValidationError,
  401: AuthenticationError,
  403: PermissionDeniedError,
  404: NotFoundError,
  409: ConflictError,
  412: ConflictError,
  422: UnprocessableEntityError,
  428: PreconditionRequiredError,
  429: RateLimitError,
  502: ProviderError,
  503: UnavailableError,
  507: InsufficientStorageError,
};

const record = (value: unknown): Record<string, unknown> | undefined =>
  value !== null && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : undefined;

/** The `detail` object of an error body (top level, or under `error`), with a lifted sandbox state put back. */
function detailOf(payload: unknown): Record<string, unknown> | undefined {
  const body = record(payload);
  const detail = record(body?.detail) ?? record(record(body?.error)?.detail);
  if (detail === undefined) return undefined;
  const { sandboxState, ...rest } = detail;
  return typeof sandboxState === "string" ? { ...rest, state: sandboxState } : detail;
}

/** The frozen contract's codes for the two If-Match refusals, when the body named none. */
const DEFAULT_CODES: Readonly<Record<number, string>> = {
  412: "network_policy_revision_mismatch",
  428: "network_policy_precondition_required",
};

/** The sandbox class for a refusal, or undefined to keep the shared one. A shared class more specific than its
 * status alone (`WrongRegionError`, `ProductNotAvailableError`, `IdempotencyKeyReusedError`, ...) is kept. */
function classFor(error: Core.FutureAGIAPIError, detail: Record<string, unknown> | undefined): StatusClass | undefined {
  const shared = error.constructor;
  const sandboxState = error.statusCode === 409 && shared === Core.SandboxStateError;
  if (shared !== errorClassFor(error.statusCode) && !sandboxState) return undefined;
  if (error.statusCode === 409) {
    if (error.code === "quota_exceeded") return QuotaExceededError;
    if (detail?.state === "hibernated") return SandboxHibernatedError;
    if (sandboxState) return SandboxStateError;
  }
  return BY_STATUS[error.statusCode];
}

/** The sandbox error for anything a sandbox call threw; an error that is not a refusal or a transport failure
 * (a configuration error, a redirect, an abort) is returned unchanged. Idempotent. */
export function toSandboxError(error: unknown): unknown {
  if (error instanceof SandboxError) return error;
  if (error instanceof Core.APIConnectionError) {
    const unknownOutcome = error.possiblyApplied
      ? " The request may have reached the server, so whether it completed is unknown: check before repeating a call that changes something."
      : "";
    const out = new SandboxConnectionError(`${error.message}${unknownOutcome}`, error.cause);
    out.kind = error.kind;
    out.possiblyApplied = error.possiblyApplied;
    if (error.operation !== undefined) out.operation = error.operation;
    if (error.idempotencyKey !== undefined) out.idempotencyKey = error.idempotencyKey;
    return out;
  }
  if (!(error instanceof Core.FutureAGIAPIError)) return error;
  if (error instanceof Core.WrongRegionError) {
    // The executor discarded the wrong-region response (only the fixed envelope is kept): nothing from it is
    // attached here, no `detail`, no sandbox state and no wait hint. It keeps its shared class and gains the brand.
    Object.defineProperty(error, BRAND, { value: true });
    return error;
  }
  const detail = detailOf(error.payload);
  const retryAfterSeconds = error.retryAfter;
  const requestId = error.requestId ?? error.upstreamRequestId;
  const cls = classFor(error, detail);
  const out =
    cls === undefined
      ? error
      : new cls(error.statusCode, error.payload, {
          code: error.code === `http_${error.statusCode}` ? DEFAULT_CODES[error.statusCode] ?? error.code : error.code,
          message: error.message,
          ...(requestId !== undefined ? { requestId } : {}),
          ...(error.upstreamRequestId !== undefined ? { upstreamRequestId: error.upstreamRequestId } : {}),
          ...(error.receiptId !== undefined ? { receiptId: error.receiptId } : {}),
          ...(error.idempotencyKey !== undefined ? { idempotencyKey: error.idempotencyKey } : {}),
          ...(retryAfterSeconds !== undefined ? { retryAfter: retryAfterSeconds } : {}),
          ...(error.operation !== undefined ? { operation: error.operation } : {}),
        });
  // As in the SandboxError constructor: a field the response did not carry is absent, not an own `undefined`.
  const fields: PropertyDescriptorMap = { [BRAND]: { value: true } };
  if (detail !== undefined) fields.detail = { value: detail, enumerable: true };
  if (retryAfterSeconds !== undefined) fields.retryAfterSeconds = { value: retryAfterSeconds, enumerable: true };
  Object.defineProperties(out, fields);
  return out;
}

/** Await a call, throwing its sandbox error. */
export async function mapped<T>(call: () => PromiseLike<T>): Promise<T> {
  try {
    return await call();
  } catch (error) {
    throw toSandboxError(error);
  }
}
