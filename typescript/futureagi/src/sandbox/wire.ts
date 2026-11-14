// The sandbox rules on top of the shared platform executor, used by `client.sandboxes`
// (src/platform/resources/sandboxes.ts): no default host, the HTTPS guard, the self-hosted origin opt-in
// (`allowCustomBaseUrl`: a Bearer token goes only to loopback without it), the error scrubber that keeps a
// sandbox state, the sandbox error classes (./errors.ts) on every call, redirect privacy, send-once calls, the
// download size limit, and the exec stream, whose server error text is scrubbed and capped as an HTTP error
// body's message is.

import type * as T from "../generated/platform/types.gen";
import { connectionError, readErrorShape } from "../_core/error-map";
import { ConfigurationError, HostNotAllowedError, PlatformNotConfiguredError, UnexpectedRedirectError } from "../_core/errors";
import { isInsecureHttp, isLoopback } from "../_core/http-security";
import { type CallOptions, type Opened, PlatformCore } from "../_core/platform-base";
import { APIPromise } from "../_core/raw";
import { scrubValue } from "../_core/redact";
import { BODY_LIMITS, type OperationParams } from "../_core/request";
import { readSse, type SseFrame } from "../_core/sse";
import { SDKException } from "../utils/errors";
import { toSandboxError } from "./errors";

/** A client: anything with the platform executor. */
export type Host = { readonly _platform: PlatformCore };

/** What every sandbox resource is bound to: the client, the client's constructor-only origin opt-in, and whether
 * the client was given a base URL (`baseUrl` or `FI_BASE_URL`; a `platformBaseUrl` shows in the origin itself). */
export interface Bound {
  readonly host: Host;
  readonly allowCustomBaseUrl: boolean;
  readonly baseUrlGiven: boolean;
}

/** Per-call options of every sandbox method. Sandbox operations take no idempotency key. */
export type SandboxCallOptions = Omit<CallOptions, "idempotencyKey">;

/** `files.download` options: the call options plus the largest file to accept. */
export type DownloadOptions = SandboxCallOptions & {
  /** The largest file to accept, in bytes; default `BODY_LIMITS.bundle` (64 MiB, the upload limit). A larger file
   * throws `PayloadTooLargeError` (code `download_too_large`) and nothing is kept. */
  readonly maxBytes?: number;
};

/** Raw file content for `files.upload`: bytes, a Blob (a file from `fs.openAsBlob`), or text. */
export type UploadBody = Uint8Array | ArrayBuffer | Blob | string;

/** An exec event this SDK does not know yet; a newer server never breaks an older SDK. */
export interface UnknownExecFrame {
  readonly event: "unknown";
  /** The event name the server sent. */
  readonly eventType: string;
  readonly id?: string;
  /** Parsed JSON, or the text when the frame was not JSON. */
  readonly raw: unknown;
}

/** One frame of a command's output: `started`, `stdout`, `stderr`, then `exit` (or `error`). */
export type ExecFrame = T.OmegaExecFrame | UnknownExecFrame;

const SANDBOX_STATES = new Set(["active", "hibernated", "recovery_required", "destroyed"]);

/** Copy a sandbox state in an error's `detail` to `detail.sandboxState`: the shared redactor hides every
 * field named `state`, and the Sandbox handle needs it to tell a hibernated sandbox. Only the four state
 * names are copied. */
function liftSandboxState(value: unknown): unknown {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return value;
  const body = value as Record<string, unknown>;
  const lift = (detail: unknown): unknown => {
    if (detail === null || typeof detail !== "object" || Array.isArray(detail)) return detail;
    const state = (detail as Record<string, unknown>).state;
    return typeof state === "string" && SANDBOX_STATES.has(state) ? { ...(detail as Record<string, unknown>), sandboxState: state } : detail;
  };
  const out: Record<string, unknown> = { ...body };
  if ("detail" in body) out.detail = lift(body.detail);
  if (body.error !== null && typeof body.error === "object" && !Array.isArray(body.error)) {
    const nested = body.error as Record<string, unknown>;
    if ("detail" in nested) out.error = { ...nested, detail: lift(nested.detail) };
  }
  return out;
}

/** The client's executor with the sandbox rules: no default host, the HTTPS guard, the self-hosted origin opt-in,
 * and the error scrubber that keeps a state. Throws before anything is sent. */
export function sandboxCore(bound: Bound, operation: string): PlatformCore {
  const core = bound.host._platform;
  const origin = core.origin(); // resolved once and kept on the client's shared state
  if (origin.source === "derived" && !bound.baseUrlGiven) {
    // The client's own default host is not a sandbox host (OpenAPI servers[0]).
    throw new PlatformNotConfiguredError(
      `${operation}: no sandbox API host. Pass baseUrl (hosted: https://<gateway-host>) or platformBaseUrl ` +
        "(hosted: https://<gateway-host>/omega/api; self-hosted EE: its origin with the port) to FutureAGIClient, " +
        "or set FI_BASE_URL or FI_PLATFORM_BASE_URL. There is no default host. " +
        "(Sandbox.create, connect, list and settings read OMEGA_BASE_URL.)",
      "missing_base_url",
      operation,
    );
  }
  if (isInsecureHttp(origin.url)) {
    throw new ConfigurationError(
      `${operation}: sandbox calls need HTTPS (plain HTTP only to loopback); refusing to send credentials to ${origin.url.host}. ` +
        "allowInsecureHttp and FI_ALLOW_INSECURE_HTTP do not apply to sandboxes",
      "insecure_sandbox_origin",
      operation,
    );
  }
  // A Bearer token is the self-hosted credential (OpenAPI servers[1], securitySchemes.OmegaBearer): loopback only,
  // unless the client was built with allowCustomBaseUrl. No hosted host name admits it.
  if (origin.mode === "bearer" && !bound.allowCustomBaseUrl && !isLoopback(origin.url)) {
    throw new HostNotAllowedError(
      `${operation}: refusing to send a self-hosted Bearer token to ${origin.url.host}, which is not loopback. ` +
        "If this is your Omega EE, pass allowCustomBaseUrl: true to the FutureAGIClient constructor " +
        "(FI_ALLOW_CUSTOM_PLATFORM_URL and allowCustomPlatformUrl do not apply to a Bearer token)",
      "host_not_allowed",
      operation,
    );
  }
  const scrub = core.shared.errorScrubber ?? scrubValue;
  // the origin is handed over by resolveOrigin, so the per-call state keeps it off its enumerable fields too
  return new PlatformCore(
    { ...core.shared, resolveOrigin: () => origin, errorScrubber: (value, secrets) => liftSandboxState(scrub(value, secrets)) },
    core.settings,
  );
}

/** The byte limit of one download: `maxBytes`, else `BODY_LIMITS.bundle`. */
function downloadLimit(maxBytes: number | undefined, operation: string): number {
  if (maxBytes === undefined) return BODY_LIMITS.bundle;
  if (typeof maxBytes !== "number" || !Number.isSafeInteger(maxBytes) || maxBytes < 0) {
    throw new ConfigurationError(`${operation}: maxBytes must be a whole number of bytes, 0 or more`, "invalid_max_bytes", operation);
  }
  return maxBytes;
}

/** Server-supplied error text from the exec stream, treated as an HTTP error body's message is: every secret the
 * request carried replaced, whitespace collapsed and the length capped the same way. */
function errorText(text: string, scrub: (value: unknown) => unknown): string {
  const scrubbed = scrub(text);
  if (typeof scrubbed !== "string") return "";
  return readErrorShape({ code: "exec_error", message: scrubbed }).message ?? scrubbed.trim();
}

/** A redirect on a sandbox call never names where it pointed. */
export function privateRedirect(error: unknown): unknown {
  if (!(error instanceof UnexpectedRedirectError)) return error;
  const operation = error.operation ?? "sandbox call";
  return new UnexpectedRedirectError(
    `${operation}: the server answered ${error.statusCode} and sandbox calls never follow a redirect`,
    error.statusCode,
    undefined,
    error.requestId,
    error.operation,
  );
}

/** A sandbox call's failure as the caller sees it: the sandbox error class, and a redirect that names no target. */
export function failure(error: unknown): unknown {
  return toSandboxError(privateRedirect(error));
}

/** Call a JSON operation under the sandbox rules; `once` sends it a single time (no retry, not even on a 429 or a
 * failure before sending). */
export function call<R>(bound: Bound, name: string, params: OperationParams, options: SandboxCallOptions, once = false): APIPromise<R> {
  return new APIPromise(async () => {
    const core = sandboxCore(bound, name);
    try {
      const { data, meta } = await core.call<R>(name, params, once ? { ...options, retries: 0 } : options).withResponse();
      return { data, meta };
    } catch (error) {
      throw failure(error);
    }
  });
}

/** Call an operation whose success body is a file, under the sandbox rules, up to `maxBytes` (default
 * `BODY_LIMITS.bundle`). */
export function bytes(bound: Bound, name: string, params: OperationParams, options: DownloadOptions): APIPromise<Uint8Array> {
  return new APIPromise(async () => {
    const { maxBytes, ...rest } = options;
    const core = sandboxCore(bound, name);
    const limit = downloadLimit(maxBytes, name);
    try {
      const { data, meta } = await core.call<Uint8Array>(name, params, rest, undefined, limit).withResponse();
      return { data, meta };
    } catch (error) {
      throw failure(error);
    }
  });
}

/** A known frame's data with its server error text (`error.message`, `exit.error`) passed through `errorText`;
 * output and every other field are left as sent. */
function scrubbedData(event: string, data: Record<string, unknown>, scrub: (value: unknown) => unknown): Record<string, unknown> {
  if (event === "error" && typeof data.message === "string") return { ...data, message: errorText(data.message, scrub) };
  if (event === "exit" && typeof data.error === "string") return { ...data, error: errorText(data.error, scrub) };
  return data;
}

function decodeFrame(frame: SseFrame, known: readonly string[], scrub: (value: unknown) => unknown): ExecFrame {
  let raw: unknown;
  try {
    raw = JSON.parse(frame.data);
  } catch {
    raw = frame.data;
  }
  const id = frame.id ?? (frame.lastEventId !== "" ? frame.lastEventId : undefined);
  if (known.includes(frame.event) && raw !== null && typeof raw === "object" && !Array.isArray(raw)) {
    return { event: frame.event, id: id ?? "", data: scrubbedData(frame.event, raw as Record<string, unknown>, scrub) } as T.OmegaExecFrame;
  }
  return { event: "unknown", eventType: frame.event, ...(id !== undefined ? { id } : {}), raw };
}

/**
 * A command's output stream, for `for await`. It ends after the `exit` (or `error`) frame; if the
 * connection ends first it simply ends, and the caller decides (the `Sandbox` handle throws
 * `CommandIncompleteError`). `return()` (a `break` out of the loop) closes the connection, which cancels the
 * command. Never retried: a reconnect would run the command again. The server's error text in an `error` frame
 * (`message`) and an `exit` frame (`error`) has every secret the request carried replaced and is capped as an
 * HTTP error body's message is; output frames are passed as sent.
 */
export class ExecStream implements AsyncIterableIterator<ExecFrame> {
  /** Request id of the response that opened the stream, when the server sent one. */
  readonly requestId?: string;
  readonly #frames: AsyncGenerator<ExecFrame, void, undefined>;
  readonly #controller: AbortController;
  readonly #release: () => void;
  readonly #body: ReadableStream<Uint8Array>;
  readonly #scrub: (value: unknown) => unknown;
  #closed = false;
  #execId?: string;

  /** @internal Built by `client.sandboxes.commands.run`. */
  constructor(opened: Opened, core: PlatformCore, operation: string, controller: AbortController, release: () => void) {
    if (opened.meta.requestId !== undefined) this.requestId = opened.meta.requestId;
    this.#controller = controller;
    this.#release = release;
    this.#body = opened.response.body ?? new ReadableStream<Uint8Array>();
    this.#scrub = opened.scrubError ?? ((value: unknown) => (core.shared.errorScrubber ?? scrubValue)(value, core.origin().secrets));
    this.#frames = this.#read(core, operation);
  }

  /** The command's id from its `started` frame (pass it to `commands.cancel`), once that frame was read. */
  get execId(): string | undefined {
    return this.#execId;
  }

  next(): Promise<IteratorResult<ExecFrame, void>> {
    return this.#frames.next();
  }

  /** Stop reading and close the connection; the server cancels a command that is still running. */
  async return(): Promise<IteratorResult<ExecFrame, void>> {
    this.#closed = true;
    this.#controller.abort(new Error("the exec stream was closed"));
    this.#release();
    // a stream never read holds no reader: cancel its body here (a read one is cancelled by the reader)
    if (!this.#body.locked) await this.#body.cancel().catch(() => undefined);
    return this.#frames.return(undefined);
  }

  /** The same as `return()`. */
  async close(): Promise<void> {
    await this.return();
  }

  [Symbol.asyncIterator](): this {
    return this;
  }

  async *#read(core: PlatformCore, operation: string): AsyncGenerator<ExecFrame, void, undefined> {
    const known = core.operation(operation).stream?.knownEvents ?? [];
    try {
      const frames = readSse(this.#body, { idleTimeoutMs: core.settings.streamIdleTimeoutMs, signal: this.#controller.signal });
      for await (const frame of frames) {
        const decoded = decodeFrame(frame, known, this.#scrub);
        if (decoded.event === "started") this.#execId = decoded.data.execId;
        yield decoded;
        if (decoded.event === "exit" || decoded.event === "error") return;
      }
    } catch (error) {
      if (this.#closed) return;
      if (this.#controller.signal.aborted) throw this.#controller.signal.reason ?? error; // the caller's signal
      if (error instanceof SDKException) throw toSandboxError(error);
      throw toSandboxError(connectionError(error, { operation, origin: core.origin().url.origin, possiblyApplied: true }));
    } finally {
      this.#release();
      if (!this.#controller.signal.aborted) this.#controller.abort(new Error("the exec stream ended"));
    }
  }
}
