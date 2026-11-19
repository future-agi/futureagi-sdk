/**
 * The platform request executor; the twin of Python's `fi._core.platform_base`.
 *
 * Each call builds its own `Request` with `redirect: "manual"` (hey-api's client follows redirects, so
 * platform calls never go through it) and sends it through the shared `resilientFetch` (`transport.ts`) with
 * the operation's retry class. Under it sits a small recording fetch, made per call, that:
 * - logs each attempt's outcome, so a 404 on a retry of `sandboxes.kill` can count as applied;
 * - honours the caller's `signal` (resilientFetch gives each attempt its own timeout signal), and the
 *   backoff sleep rejects on abort, so an abort never turns into retries;
 * - removes the transport's key headers in Bearer mode (resilientFetch always adds them).
 *
 * The client's `FI_EXTRA_HEADERS` / `extraHeaders` go on a call whose URL is under its base URL, with the
 * core namespaces' rules (extra-headers.ts): read on each call, never over a header already set, a
 * malformed setting thrown before any fetch, the values scrubbed from a reflected error.
 *
 * On top of the transport: the idempotency key is minted once and sent on every attempt; a 409
 * `idempotency_key_in_progress` on a keyed call waits (`Retry-After`, else 1 s) and resends with the
 * same key; a 3xx throws `UnexpectedRedirectError` (the keys never reach another origin); every other
 * status maps through `apiError` (payload redacted, held secrets scrubbed); a failure with no response
 * is `APIConnectionError` / `APITimeoutError`.
 */

import type { ExtraHeaders } from "../extra-headers";
import { type RetryClass, resilientFetch } from "../transport";
import { apiError, connectionError, isPlatformError, isWrongRegionResponse } from "./error-map";
import { ConfigurationError, FutureAGIAPIError, PlatformNotConfiguredError, UnexpectedRedirectError } from "./errors";
import type { PlatformOrigin } from "./origins";
import { lookup, type OperationSpec, type OperationTable, retryClassOf } from "./policy";
import { APIPromise, type CallMeta, metaFrom } from "./raw";
import { redactValue, requestSecretValues, scrubText, scrubValue } from "./redact";
import {
  buildBody,
  buildPath,
  buildQuery,
  IDEMPOTENCY_HEADER,
  inProgressWait,
  type OperationParams,
  REPLAYED_HEADER,
  resolveIdempotencyKey,
} from "./request";

export const DEFAULT_TIMEOUT_MS = 30_000;
export const DEFAULT_STREAM_IDLE_MS = 45_000;
export const IN_PROGRESS_BUDGET_MS = 120_000;
const MAX_ERROR_BODY = 64 * 1024;
// x-omega-sdk families in the pinned Console contract and connector supplements.
const CONSOLE_FAMILIES = new Set(["deployments", "platform", "runs", "connectors"]);

/** Per-call options; every platform method accepts these. */
export interface CallOptions {
  /** Cancels this call, including its default retry sleep. */
  readonly signal?: AbortSignal;
  /** Per-attempt timeout in milliseconds, overriding the client default. */
  readonly timeoutMs?: number;
  /** Retry count for failures allowed by the operation's retry policy. */
  readonly retries?: number;
  /** Reuse this key for a contract-declared idempotent operation; otherwise one is minted. */
  readonly idempotencyKey?: string;
  /** Resume a resumable stream after this durable sequence. */
  readonly lastEventId?: string;
  /** Extra headers declared by this operation's contract; other names are refused. */
  readonly headers?: Readonly<Record<string, string>>;
}

/** What a client and its `withOptions` copies share. */
export interface PlatformShared {
  readonly resolveOrigin: () => PlatformOrigin;
  table?: OperationTable;
  readonly fetch?: typeof fetch;
  readonly retries?: number;
  readonly sleep?: (ms: number) => Promise<void>;
  readonly backoffBaseMs?: number;
  /** The client's `FI_EXTRA_HEADERS` / `extraHeaders`, read on each call; `{}` off its base URL. */
  readonly extraHeaders?: Pick<ExtraHeaders, "forUrl">;
  /** Namespace policy over decoded errors, before any value or field-name redaction. */
  readonly errorScrubber?: (value: unknown, secrets: readonly string[]) => unknown;
  origin?: PlatformOrigin;
}

/** What a `withOptions` copy may change. */
export interface Settings {
  readonly timeoutMs: number;
  readonly retries?: number;
  readonly streamIdleTimeoutMs: number;
}

// Interpret decoded data while the request's scrub set is local, never in public metadata.
type ResponseMapper = (value: unknown, secrets: readonly string[], meta: CallMeta) => unknown;

type Outcome = number | { error: unknown; preSend: boolean };
const PRE_SEND = new Set(["ECONNREFUSED", "ENOTFOUND", "EAI_AGAIN", "UND_ERR_CONNECT_TIMEOUT"]);

function isPreSend(error: unknown): boolean {
  let current: unknown = error;
  for (let depth = 0; depth < 4 && current !== null && typeof current === "object"; depth += 1) {
    const code = (current as { code?: unknown }).code;
    if (typeof code === "string" && PRE_SEND.has(code)) return true;
    current = (current as { cause?: unknown }).cause;
  }
  return false;
}

const mayHaveApplied = (o: Outcome): boolean => (typeof o === "number" ? o >= 500 : !o.preSend);

function abortableSleep(base: ((ms: number) => Promise<void>) | undefined, signal: AbortSignal | undefined) {
  return (ms: number): Promise<void> => {
    if (signal?.aborted === true) return Promise.reject(signal.reason);
    if (base !== undefined) return base(ms);
    return new Promise((resolve, reject) => {
      const timer = setTimeout(done, ms);
      function done(): void {
        signal?.removeEventListener("abort", onAbort);
        resolve();
      }
      function onAbort(): void {
        clearTimeout(timer);
        reject(signal?.reason);
      }
      signal?.addEventListener("abort", onAbort, { once: true });
    });
  };
}

function recordingFetch(base: typeof fetch, log: Outcome[], mode: PlatformOrigin["mode"], signal: AbortSignal | undefined): typeof fetch {
  return (async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    if (signal?.aborted === true) throw signal.reason;
    let request = new Request(input as RequestInfo, init);
    const headers = new Headers(request.headers);
    if (mode === "bearer") {
      headers.delete("X-Api-Key");
      headers.delete("X-Secret-Key");
    }
    const controller = new AbortController();
    const forward = (from: AbortSignal) => () => controller.abort(from.reason);
    const attemptSignal = request.signal;
    const offAttempt = forward(attemptSignal);
    attemptSignal.addEventListener("abort", offAttempt, { once: true });
    const offCaller = signal !== undefined ? forward(signal) : undefined;
    if (signal !== undefined && offCaller !== undefined) signal.addEventListener("abort", offCaller, { once: true });
    request = new Request(request, { headers, signal: controller.signal });
    try {
      const response = await base(request);
      log.push(response.status);
      return response;
    } catch (error) {
      log.push({ error, preSend: isPreSend(error) });
      throw error;
    } finally {
      attemptSignal.removeEventListener("abort", offAttempt);
      if (signal !== undefined && offCaller !== undefined) signal.removeEventListener("abort", offCaller);
    }
  }) as typeof fetch;
}

async function readCapped(response: Response): Promise<{ text: string; complete: boolean }> {
  if (response.body === null) return { text: "", complete: true };
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let text = "";
  let complete = false;
  try {
    while (text.length < MAX_ERROR_BODY) {
      const chunk = await reader.read();
      if (chunk.done) {
        complete = true;
        break;
      }
      text += decoder.decode(chunk.value, { stream: true });
    }
  } catch {
    // A capped or interrupted body cannot prove the absence of an EE envelope.
  } finally {
    reader.cancel().catch(() => undefined);
  }
  return { text, complete };
}

/** An opened stream: the live response (read its body) and its meta. */
export interface Opened {
  readonly response: Response;
  readonly meta: CallMeta;
}

export class PlatformCore {
  constructor(
    readonly shared: PlatformShared,
    readonly settings: Settings = { timeoutMs: DEFAULT_TIMEOUT_MS, streamIdleTimeoutMs: DEFAULT_STREAM_IDLE_MS },
  ) {}

  /** A copy with other defaults that shares the origin, the table and the fetch. */
  withSettings(options: { timeoutMs?: number; retries?: number }): PlatformCore {
    return new PlatformCore(this.shared, {
      ...this.settings,
      ...(options.timeoutMs !== undefined ? { timeoutMs: options.timeoutMs } : {}),
      ...(options.retries !== undefined ? { retries: options.retries } : {}),
    });
  }

  operation(name: string): OperationSpec {
    if (this.shared.table === undefined) {
      throw new PlatformNotConfiguredError(
        "this build of @future-agi/sdk has no platform operation table (src/generated/platform)",
        "no_contract",
      );
    }
    return lookup(this.shared.table, name);
  }

  origin(): PlatformOrigin {
    this.shared.origin ??= this.shared.resolveOrigin();
    return this.shared.origin;
  }

  /** Call a JSON operation; await it for the parsed body, or `.withResponse()` for `{ data, meta }`. */
  call<T = unknown>(name: string, params: OperationParams = {}, options: CallOptions = {}, mapResponse?: ResponseMapper): APIPromise<T> {
    return new APIPromise(async () => {
      const { data, meta } = await this.execute(name, params, options, false, mapResponse);
      return { data: data as T, meta };
    });
  }

  /** Open a streaming operation; read `response.body` (the resumable helpers do). */
  async openStream(name: string, params: OperationParams = {}, options: CallOptions = {}): Promise<Opened> {
    const { response, meta } = await this.execute(name, params, options, true);
    return { response: response as Response, meta };
  }

  private async execute(name: string, params: OperationParams, options: CallOptions, stream: boolean, mapResponse?: ResponseMapper) {
    const op = this.operation(name);
    if (op.humanOnly === true)
      throw new ConfigurationError(`${name} is a decision only a person makes, in the Future AGI app`, "human_only_verb", name);
    if (stream !== (op.stream !== undefined)) {
      throw new ConfigurationError(
        stream ? `${name} is not a streaming operation` : `${name} streams: open it with a stream method`,
        stream ? "not_a_stream" : "is_a_stream",
        name,
      );
    }
    const origin = this.origin();
    const url = `${origin.base}${buildPath(op, params.path)}${buildQuery(op, params.query)}`;
    const encoded = buildBody(op, params.body);
    const key = resolveIdempotencyKey(op, options.idempotencyKey);
    const headers: Record<string, string> = {
      Accept: stream ? "text/event-stream" : "application/json",
      "User-Agent": "futureagi-typescript",
      ...origin.headers,
    };
    const allowed = new Set([...(op.headers ?? []), ...(op.stream?.resume === "last-event-id" ? ["last-event-id"] : [])]);
    for (const [name_, value] of Object.entries(options.headers ?? {})) {
      if (!allowed.has(name_.toLowerCase()))
        throw new ConfigurationError(
          `${name} does not declare the header ${name_.toLowerCase()}, so it is not sent`,
          "undeclared_header",
          name,
        );
      headers[name_] = value;
    }
    if (options.lastEventId !== undefined && op.stream?.resume === "last-event-id") headers["Last-Event-ID"] = options.lastEventId;
    if (encoded.contentType !== undefined) headers["Content-Type"] = encoded.contentType;
    if (key !== undefined) headers[IDEMPOTENCY_HEADER] = key;
    // FI_EXTRA_HEADERS / extraHeaders, as on the core namespaces: read now (a malformed setting throws
    // before any fetch, never retried), only under the client's base URL, never over a header already set
    const extra = this.shared.extraHeaders?.forUrl(url) ?? {};
    const present = new Set(Object.keys(headers).map((header) => header.toLowerCase()));
    for (const [header, value] of Object.entries(extra)) {
      if (!present.has(header.toLowerCase())) headers[header] = value;
    }
    const retryClass: RetryClass = retryClassOf(op);
    const retries = stream ? 0 : (options.retries ?? this.settings.retries ?? this.shared.retries);
    const sleep = abortableSleep(this.shared.sleep, options.signal);
    // extra header values, and the token after an auth scheme, of 8 characters or more (as Python's)
    const extraSecrets = Object.values(extra).flatMap((value) => [value, value.slice(value.indexOf(" ") + 1).trim()]);
    const scrub = [...origin.secrets, ...extraSecrets.filter((value) => value.length >= 8), ...requestSecretValues(params.body, op.secretFields)];
    const deadline = Date.now() + IN_PROGRESS_BUDGET_MS;
    let earlier = 0;
    for (;;) {
      const log: Outcome[] = [];
      const send = resilientFetch({
        fetch: recordingFetch(this.shared.fetch ?? globalThis.fetch.bind(globalThis), log, origin.mode, options.signal),
        timeoutMs: options.timeoutMs ?? this.settings.timeoutMs,
        ...(retries !== undefined ? { retries } : {}),
        ...(this.shared.backoffBaseMs !== undefined ? { backoffBaseMs: this.shared.backoffBaseMs } : {}),
        sleep,
        resolveCredentials: () => ({ apiKey: origin.headers["X-Api-Key"] ?? "", secretKey: origin.headers["X-Secret-Key"] ?? "" }),
        retryPolicy: { class: retryClass },
      });
      const request = new Request(url, {
        method: op.method,
        headers,
        redirect: "manual",
        ...(encoded.body !== undefined ? { body: encoded.body as BodyInit } : {}),
      });
      let response: Response;
      try {
        response = await send(request);
      } catch (error) {
        if (options.signal?.aborted === true) throw options.signal.reason ?? error;
        throw connectionError(error, {
          operation: name,
          ...(key !== undefined ? { idempotencyKey: key } : {}),
          origin: origin.url.origin,
          possiblyApplied: log.some(mayHaveApplied),
        });
      }
      const attempts = earlier + log.length;
      const replay = response.headers.get(REPLAYED_HEADER)?.toLowerCase() === "true";
      const metaOf = (applied = false) =>
        metaFrom(response, name, { ...(key !== undefined ? { idempotencyKey: key } : {}), attempts, replay, applied });
      if (response.type === "opaqueredirect" || (response.status >= 300 && response.status < 400)) {
        await response.body?.cancel().catch(() => undefined);
        throw this.redirect(name, url, response);
      }
      if (response.ok) {
        if (stream) return { response, data: undefined, meta: metaOf() };
        const text = await response.text();
        let data: unknown;
        try {
          data = text.trim() === "" ? undefined : JSON.parse(text);
        } catch {
          throw new FutureAGIAPIError(response.status, undefined, {
            code: "invalid_json",
            operation: name,
            message: `${name}: the server's response was not JSON`,
          });
        }
        const meta = metaOf();
        if (mapResponse !== undefined) data = mapResponse(data, scrub, meta);
        return { response, data, meta };
      }
      const { text: raw, complete } = await readCapped(response);
      if (response.status === 404 && op.notFoundMeansApplied === true && log.slice(0, -1).some(mayHaveApplied)) {
        return { response, data: undefined, meta: metaOf(true) };
      }
      let body: unknown;
      let platformError = false;
      let wrongRegion = false;
      try {
        // Classify both raw envelopes before a privacy scrubber can rename keys or redact values.
        const decoded: unknown = raw.trim() === "" ? undefined : JSON.parse(raw);
        platformError = isPlatformError(decoded);
        wrongRegion = isWrongRegionResponse(response.status, decoded);
        body = wrongRegion ? { error: "wrong_region" } : (this.shared.errorScrubber ?? scrubValue)(decoded, scrub);
      } catch {
        body = undefined; // HTML (including FA's default Django 404) is never echoed
      }
      let consoleUnavailableMessage: string | undefined;
      let errorHeaders = response.headers;
      // Generated families identify Console calls; FA management has the gateway family.
      // Without EOF, a missing envelope may simply be a capped or interrupted EE body.
      if (response.status === 404 && CONSOLE_FAMILIES.has(op.family) && complete && !platformError) {
        const hint = origin.source === "derived"
          ? "for self-hosted Enterprise, set FI_PLATFORM_BASE_URL to your Console API origin."
          : "for self-hosted Enterprise, check your configured Console API URL (FI_PLATFORM_BASE_URL or platformBaseUrl).";
        consoleUnavailableMessage = scrubText(
          `The Console API is not available at ${origin.url.host}. ` +
          "Hosted Future AGI does not support Console access through the SDK in this release; " + hint,
          scrub,
        );
        // Scrub even short credentials for the new diagnostic; retain legacy request-ID behavior elsewhere.
        errorHeaders = new Headers();
        response.headers.forEach((value, key) => errorHeaders.set(key, scrubText(value, scrub, 1)));
      }
      const err = apiError(response.status, redactValue(body), errorHeaders, {
        operation: name,
        family: op.family,
        body, wrongRegion,
        ...(consoleUnavailableMessage !== undefined ? { consoleUnavailableMessage } : {}),
        ...(key !== undefined ? { idempotencyKey: key } : {}),
      });
      const wait = inProgressWait(op, response.status, err.code, err.retryAfter);
      if (wait === undefined || Date.now() + wait * 1000 > deadline) throw err;
      await sleep(wait * 1000);
      earlier += log.length;
    }
  }

  private redirect(name: string, url: string, response: Response): UnexpectedRedirectError {
    const location = response.headers.get("location");
    let host: string | undefined;
    try {
      host = location !== null ? new URL(location, url).host : undefined;
    } catch {
      host = undefined;
    }
    return new UnexpectedRedirectError(
      `${name}: the server answered ${response.status} and platform calls never follow a redirect (target host: ${host ?? "unknown"})`,
      response.status,
      host,
      response.headers.get("x-request-id") ?? undefined,
      name,
    );
  }
}
