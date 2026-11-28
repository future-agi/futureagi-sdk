import {
  VERSION,
  DEFAULT_TIMEOUT,
  DEFAULT_MAX_RETRIES,
  DEFAULT_BASE_URL,
  RETRYABLE_STATUS_CODES,
} from "./constants";
import {
  AgentCCError,
  APIConnectionError,
  APITimeoutError,
  APIStatusError,
  GuardrailBlockedError,
} from "./errors";
import type { GatewayConfig } from "./gateway-config";
import { gatewayConfigToHeaders } from "./gateway-config";
import type { AgentCCMetadata } from "./types/shared";
import { parseAgentCCMetadata } from "./types/shared";
import type { CallbackHandler, CallbackRequest, StreamInfo } from "./callbacks";
import { invokeCallbacks } from "./callbacks";
import { redactCallbackRequest } from "./redact";
import type { RetryPolicy } from "./retry-policy";
import { supportsFunctionCalling, supportsJsonMode } from "./models-info";
import { TraceContextManager } from "./trace-context";
import type { Middleware, MiddlewareContext, MiddlewareResult, NextFn } from "./middleware";
import { composeMiddlewares } from "./middleware";
import type { PreCallRule } from "./pre-call-rules";
import { evaluatePreCallRules } from "./pre-call-rules";
import { validateJsonResponse } from "./validate-response";
import type { DryRunResult } from "./dry-run";
import { cleanBaseUrl, envApiKey, envBaseUrl } from "./env";
import type { Session } from "./session";
import type { StreamHooks } from "./streaming";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface RequestOptions {
  method: string;
  path: string;
  body?: Record<string, unknown> | FormData | null;
  headers?: Record<string, string>;
  query?: Record<string, string>;
  timeout?: number;
  maxRetries?: number;
  /** If true, return the raw Response instead of parsing JSON. */
  raw?: boolean;
  /** If true, expect an SSE stream — do not consume body. */
  stream?: boolean;
}

export interface ClientOptions {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
  defaultHeaders?: Record<string, string>;
  defaultQuery?: Record<string, string>;
  sessionId?: string;
  metadata?: Record<string, unknown>;
  config?: GatewayConfig;
  fetch?: typeof globalThis.fetch;
  /** Callback handlers for request lifecycle hooks. */
  callbacks?: CallbackHandler[];
  /** Per-error-type retry configuration. Overrides `maxRetries` when set. */
  retryPolicy?: RetryPolicy;
  /** When true, removes params unsupported by the target model. */
  dropParams?: boolean;
  /** Transform request params before every request. */
  modifyParams?: (params: Record<string, unknown>) => Record<string, unknown>;
  /** When true, callbacks receive redacted message content. */
  redactMessages?: boolean;
  /** Enable W3C Trace Context auto-generation. */
  traceContext?: boolean;
  /** Propagate an upstream traceparent header. */
  traceparent?: string;
  /** Pre-call rules evaluated before every request. */
  preCallRules?: PreCallRule[];
  /** When true, auto-validate structured output responses against their JSON Schema. */
  enableJsonSchemaValidation?: boolean;
}

export interface WithResponseResult<T> {
  data: T;
  response: Response;
  agentcc: AgentCCMetadata;
}

// ---------------------------------------------------------------------------
// BaseClient
// ---------------------------------------------------------------------------

export class BaseClient {
  protected _apiKey: string;
  protected _baseUrl: string;
  protected _timeout: number;
  protected _maxRetries: number;
  protected _defaultHeaders: Record<string, string>;
  protected _defaultQuery: Record<string, string>;
  protected _sessionId: string | undefined;
  protected _metadata: Record<string, unknown> | undefined;
  protected _config: GatewayConfig | undefined;
  protected _fetch: typeof globalThis.fetch;
  protected _callbacks: CallbackHandler[];
  protected _retryPolicy: RetryPolicy | undefined;
  protected _dropParams: boolean;
  protected _modifyParams:
    | ((params: Record<string, unknown>) => Record<string, unknown>)
    | undefined;
  protected _redactMessages: boolean;
  protected _traceManager: TraceContextManager | undefined;
  protected _middlewares: Middleware[] = [];
  protected _preCallRules: PreCallRule[];
  protected _enableJsonSchemaValidation: boolean;
  /** The session of a client made by `session()`: its headers are read on every request, so `step()` takes effect. */
  protected _session: Session | undefined;
  private _totalCost = 0;

  constructor(opts: ClientOptions = {}) {
    this._apiKey = opts.apiKey || envApiKey();
    this._baseUrl = cleanBaseUrl(opts.baseUrl || envBaseUrl() || DEFAULT_BASE_URL);
    this._timeout = opts.timeout ?? DEFAULT_TIMEOUT;
    this._maxRetries = opts.maxRetries ?? DEFAULT_MAX_RETRIES;
    this._defaultHeaders = { ...opts.defaultHeaders };
    this._defaultQuery = { ...opts.defaultQuery };
    this._sessionId = opts.sessionId;
    this._metadata = opts.metadata;
    this._config = opts.config;
    this._fetch = opts.fetch ?? globalThis.fetch.bind(globalThis);
    this._callbacks = opts.callbacks ?? [];
    this._retryPolicy = opts.retryPolicy;
    this._dropParams = opts.dropParams ?? false;
    this._modifyParams = opts.modifyParams;
    this._redactMessages = opts.redactMessages ?? false;

    this._preCallRules = opts.preCallRules ?? [];
    this._enableJsonSchemaValidation = opts.enableJsonSchemaValidation ?? false;

    // Trace context
    if (opts.traceContext || opts.traceparent) {
      this._traceManager = new TraceContextManager({
        enabled: opts.traceContext ?? true,
        traceparent: opts.traceparent,
      });
    }
  }

  /** Cumulative cost of all requests made by this client. */
  get currentCost(): number {
    return this._totalCost;
  }

  resetCost(): void {
    this._totalCost = 0;
  }

  /** Add a middleware to the request chain. */
  use(middleware: Middleware): this {
    this._middlewares.push(middleware);
    return this;
  }

  /**
   * Build the full request (URL, headers, body) without actually sending it.
   * Useful for debugging / dry-run inspection.
   */
  buildRequest(options: RequestOptions): DryRunResult {
    let body = options.body ?? null;

    if (body && !(body instanceof FormData) && this._modifyParams) {
      body = this._modifyParams(body as Record<string, unknown>);
    }
    if (this._dropParams && body && !(body instanceof FormData)) {
      body = applyDropParams(body as Record<string, unknown>);
    }

    const effectiveOptions = body !== options.body ? { ...options, body } : options;

    const url = this._buildUrl(effectiveOptions.path, effectiveOptions.query);
    const headers = this._buildHeaders(effectiveOptions);

    return {
      url,
      method: effectiveOptions.method,
      headers,
      body: body instanceof FormData ? null : (body as Record<string, unknown> | null),
    };
  }

  // -----------------------------------------------------------------------
  // Request execution
  // -----------------------------------------------------------------------

  async request<T>(options: RequestOptions): Promise<T> {
    const { data } = await this._requestWithRetry<T>(options);
    return data;
  }

  async requestWithResponse<T>(
    options: RequestOptions,
  ): Promise<WithResponseResult<T>> {
    return this._requestWithRetry<T>(options);
  }

  async requestRaw(options: RequestOptions): Promise<Response> {
    const { data } = await this._requestWithRetry<Response>({
      ...options,
      raw: true,
    });
    return data;
  }

  async requestStream(options: RequestOptions): Promise<Response> {
    const { data } = await this._requestWithRetry<Response>({
      ...options,
      stream: true,
      raw: true,
    });
    return data;
  }

  // -----------------------------------------------------------------------
  // Retry loop
  // -----------------------------------------------------------------------

  private async _requestWithRetry<T>(
    options: RequestOptions,
  ): Promise<WithResponseResult<T>> {
    if (this._middlewares.length === 0) {
      return this._retryLoop<T>(options);
    }
    // Middlewares wrap the whole call (retries included): the first one added runs outermost.
    const isFormData = options.body instanceof FormData;
    const jsonBody = isFormData ? null : ((options.body as Record<string, unknown> | null | undefined) ?? null);
    const handler: NextFn = async (ctx: MiddlewareContext): Promise<MiddlewareResult> => {
      const started = Date.now();
      const result = await this._retryLoop<unknown>({
        ...options,
        method: ctx.method,
        path: ctx.path,
        body: isFormData ? options.body : ctx.body,
        headers: ctx.headers,
      });
      return {
        data: result.data,
        response: result.response,
        statusCode: result.response.status,
        latencyMs: Date.now() - started,
        agentcc: result.agentcc,
      };
    };
    const result = await composeMiddlewares(this._middlewares, handler)({
      method: options.method,
      path: options.path,
      body: jsonBody,
      headers: { ...options.headers },
      model: typeof jsonBody?.model === "string" ? jsonBody.model : undefined,
    });
    return { data: result.data as T, response: result.response, agentcc: result.agentcc };
  }

  private async _retryLoop<T>(
    options: RequestOptions,
  ): Promise<WithResponseResult<T>> {
    const flatMax = options.maxRetries ?? this._maxRetries;
    let lastError: unknown;

    // Determine max retries based on error type in each iteration
    let maxForAttempt = flatMax;

    for (let attempt = 0; attempt <= maxForAttempt; attempt++) {
      try {
        return await this._doRequest<T>(options);
      } catch (err) {
        lastError = err;

        // Non-retryable errors
        if (
          err instanceof APIStatusError &&
          !RETRYABLE_STATUS_CODES.has(err.statusCode)
        ) {
          throw err;
        }

        // Determine max retries for this error type
        if (this._retryPolicy) {
          if (err instanceof APITimeoutError) {
            maxForAttempt = this._retryPolicy.getRetriesForTimeout();
          } else if (err instanceof APIConnectionError) {
            maxForAttempt = this._retryPolicy.getRetriesForConnectionError();
          } else if (err instanceof APIStatusError) {
            maxForAttempt = this._retryPolicy.getRetriesForStatus(
              err.statusCode,
            );
          } else {
            throw err;
          }
        } else {
          // Without policy, use flat max for retryable errors
          if (
            err instanceof APITimeoutError ||
            err instanceof APIConnectionError
          ) {
            // retryable
          } else if (err instanceof APIStatusError) {
            // retryable status (already checked above)
          } else {
            throw err;
          }
        }

        if (attempt >= maxForAttempt) break;

        const delay = this._calculateDelay(
          attempt,
          err instanceof APIStatusError ? err.headers : undefined,
        );

        // Callback: onRetry
        if (this._callbacks.length > 0) {
          const cbReq = this._buildCallbackRequest(options);
          await invokeCallbacks(
            this._callbacks,
            "onRetry",
            cbReq,
            err,
            attempt,
            delay,
          );
        }

        await sleep(delay);
      }
    }

    throw lastError;
  }

  // -----------------------------------------------------------------------
  // Single request
  // -----------------------------------------------------------------------

  private async _doRequest<T>(
    options: RequestOptions,
  ): Promise<WithResponseResult<T>> {
    // 0. Pre-call rules
    if (this._preCallRules.length > 0) {
      const bodyObj = options.body instanceof FormData ? null : (options.body as Record<string, unknown> | null) ?? null;
      evaluatePreCallRules(this._preCallRules, {
        model: bodyObj?.model as string | undefined,
        path: options.path,
        body: bodyObj,
      });
    }

    // 1. Apply modifyParams
    let body = options.body;
    if (
      body &&
      !(body instanceof FormData) &&
      this._modifyParams
    ) {
      body = this._modifyParams(body as Record<string, unknown>);
    }

    // 2. Apply dropParams
    if (this._dropParams && body && !(body instanceof FormData)) {
      body = applyDropParams(body as Record<string, unknown>);
    }

    const effectiveOptions = body !== options.body ? { ...options, body } : options;

    // 3. Callback: onRequestStart
    if (this._callbacks.length > 0) {
      const cbReq = this._buildCallbackRequest(effectiveOptions);
      await invokeCallbacks(this._callbacks, "onRequestStart", cbReq);
    }

    const url = this._buildUrl(
      effectiveOptions.path,
      effectiveOptions.query,
    );
    const headers = this._buildHeaders(effectiveOptions);
    const isFormData = effectiveOptions.body instanceof FormData;

    const init: RequestInit = {
      method: effectiveOptions.method,
      headers,
      signal: AbortSignal.timeout(
        effectiveOptions.timeout ?? this._timeout,
      ),
    };

    if (effectiveOptions.body && effectiveOptions.method !== "GET") {
      if (isFormData) {
        init.body = effectiveOptions.body as FormData;
      } else {
        init.body = JSON.stringify(effectiveOptions.body);
      }
    }

    let response: Response;
    try {
      response = await this._fetch(url, init);
    } catch (err: unknown) {
      const connError =
        err instanceof DOMException && err.name === "TimeoutError"
          ? new APITimeoutError(
              `Request to ${effectiveOptions.path} timed out`,
            )
          : err instanceof TypeError &&
              (err as Error).message?.includes("abort")
            ? new APITimeoutError(
                `Request to ${effectiveOptions.path} timed out`,
              )
            : new APIConnectionError(
                `Failed to connect to ${url}: ${(err as Error).message}`,
                err,
              );

      // Callback: onError
      if (this._callbacks.length > 0) {
        const cbReq = this._buildCallbackRequest(effectiveOptions);
        await invokeCallbacks(this._callbacks, "onError", cbReq, connError);
      }

      throw connError;
    }

    // Track cost
    const costHeader = response.headers.get("x-agentcc-cost");
    let requestCost = 0;
    if (costHeader) {
      const cost = parseFloat(costHeader);
      if (!Number.isNaN(cost)) {
        this._totalCost += cost;
        requestCost = cost;
      }
    }

    // Parse agentcc metadata
    const agentcc = parseAgentCCMetadata(response.headers);

    // Stream / raw responses — return without consuming body
    if (effectiveOptions.stream || effectiveOptions.raw) {
      if (response.ok || response.status === 246) {
        // Fire callbacks for cost/cache/fallback
        if (this._callbacks.length > 0) {
          // A resource that parses the body itself (`requestRaw`) still owes the callbacks that
          // body (usage, model): read it from a clone. Streams and binary bodies are left alone.
          let callbackBody: unknown = null;
          const contentType = response.headers.get("content-type") || "";
          if (!effectiveOptions.stream && contentType.includes("application/json")) {
            callbackBody = await response.clone().json().catch(() => null);
          }
          await this._firePostRequestCallbacks(
            effectiveOptions,
            response,
            agentcc,
            requestCost,
            callbackBody,
          );
        }
        return {
          data: response as unknown as T,
          response,
          agentcc,
        };
      }
      const errBody = await safeJson(response);
      const statusError = APIStatusError.from(
        response.status,
        errBody,
        response.headers,
      );

      if (this._callbacks.length > 0) {
        const cbReq = this._buildCallbackRequest(effectiveOptions);
        if (statusError instanceof GuardrailBlockedError) {
          await invokeCallbacks(
            this._callbacks,
            "onGuardrailBlock",
            cbReq,
            statusError,
          );
        }
        await invokeCallbacks(this._callbacks, "onError", cbReq, statusError);
      }

      throw statusError;
    }

    // JSON responses
    if (!response.ok && response.status !== 246) {
      const errBody = await safeJson(response);
      const statusError = APIStatusError.from(
        response.status,
        errBody,
        response.headers,
      );

      if (this._callbacks.length > 0) {
        const cbReq = this._buildCallbackRequest(effectiveOptions);
        if (statusError instanceof GuardrailBlockedError) {
          await invokeCallbacks(
            this._callbacks,
            "onGuardrailBlock",
            cbReq,
            statusError,
          );
        }
        await invokeCallbacks(this._callbacks, "onError", cbReq, statusError);
      }

      throw statusError;
    }

    const json = await response.json();

    // Auto-attach agentcc metadata to response (8.1B.4)
    if (json && typeof json === "object") {
      (json as Record<string, unknown>).agentcc = agentcc;
    }

    // Auto-validate JSON Schema on structured output responses (8.1E.5)
    if (this._enableJsonSchemaValidation && effectiveOptions.body && !(effectiveOptions.body instanceof FormData)) {
      const reqBody = effectiveOptions.body as Record<string, unknown>;
      const rf = reqBody.response_format as Record<string, unknown> | undefined;
      if (rf && rf.type === "json_schema" && rf.json_schema) {
        const jsonSchemaObj = rf.json_schema as Record<string, unknown>;
        const schema = jsonSchemaObj.schema as Record<string, unknown> | undefined;
        if (schema) {
          const choices = (json as Record<string, unknown>).choices as Array<Record<string, unknown>> | undefined;
          const content = (choices?.[0]?.message as Record<string, unknown> | undefined)?.content as string | undefined;
          if (content) {
            const validation = validateJsonResponse(content, schema);
            if (!validation.valid) {
              throw new AgentCCError(
                `Structured output validation failed: ${validation.errors.join("; ")}`,
              );
            }
          }
        }
      }
    }

    // Fire post-request callbacks
    if (this._callbacks.length > 0) {
      await this._firePostRequestCallbacks(
        effectiveOptions,
        response,
        agentcc,
        requestCost,
        json,
      );
    }

    return { data: json as T, response, agentcc };
  }

  // -----------------------------------------------------------------------
  // Stream callbacks
  // -----------------------------------------------------------------------

  /**
   * Open an SSE request and return it with the hooks that report the stream to the callbacks
   * (`onStreamStart`, `onStreamChunk`, `onStreamEnd`, and `onError` if it breaks mid-way).
   */
  async openStream(
    options: RequestOptions,
  ): Promise<{ response: Response; hooks: StreamHooks | undefined }> {
    const response = await this.requestStream(options);
    if (this._callbacks.length === 0) {
      return { response, hooks: undefined };
    }
    const cbReq = this._buildCallbackRequest(options);
    const info = (chunkCount: number): StreamInfo => ({
      agentcc: parseAgentCCMetadata(response.headers),
      chunkCount,
    });
    return {
      response,
      hooks: {
        onStart: () => invokeCallbacks(this._callbacks, "onStreamStart", cbReq, info(0)),
        onChunk: (chunk) => invokeCallbacks(this._callbacks, "onStreamChunk", cbReq, chunk),
        onEnd: (completion, chunkCount) =>
          invokeCallbacks(this._callbacks, "onStreamEnd", cbReq, info(chunkCount), completion),
        onError: (error) => invokeCallbacks(this._callbacks, "onError", cbReq, error),
      },
    };
  }

  // -----------------------------------------------------------------------
  // Post-request callback firing
  // -----------------------------------------------------------------------

  private async _firePostRequestCallbacks(
    options: RequestOptions,
    response: Response,
    agentcc: AgentCCMetadata,
    requestCost: number,
    body: unknown,
  ): Promise<void> {
    const cbReq = this._buildCallbackRequest(options);
    const cbResp = this._buildCallbackResponse(response, agentcc, body);

    // Cost update
    if (requestCost > 0) {
      await invokeCallbacks(
        this._callbacks,
        "onCostUpdate",
        cbReq,
        requestCost,
        this._totalCost,
      );
    }

    // Cache hit
    if (agentcc.cacheStatus === "hit") {
      await invokeCallbacks(
        this._callbacks,
        "onCacheHit",
        cbReq,
        cbResp,
        agentcc.cacheStatus,
      );
    }

    // Fallback used
    if (agentcc.fallbackUsed && agentcc.modelUsed) {
      const originalModel =
        ((options.body as Record<string, unknown>)?.model as string) ??
        "unknown";
      await invokeCallbacks(
        this._callbacks,
        "onFallback",
        cbReq,
        originalModel,
        agentcc.modelUsed,
        "provider_fallback",
      );
    }

    // Guardrail warning (246)
    if (response.status === 246) {
      await invokeCallbacks(
        this._callbacks,
        "onGuardrailWarning",
        cbReq,
        cbResp,
      );
    }

    // Success
    await invokeCallbacks(this._callbacks, "onRequestEnd", cbReq, cbResp);
  }

  // -----------------------------------------------------------------------
  // Callback data builders
  // -----------------------------------------------------------------------

  private _buildCallbackRequest(options: RequestOptions): CallbackRequest {
    const url = this._buildUrl(options.path, options.query);
    let cbReq: CallbackRequest = {
      method: options.method,
      url,
      headers: options.headers ?? {},
      body: options.body ?? null,
    };
    if (this._redactMessages) {
      cbReq = redactCallbackRequest(cbReq);
    }
    return cbReq;
  }

  private _buildCallbackResponse(
    response: Response,
    agentcc: AgentCCMetadata,
    body: unknown,
  ): {
    statusCode: number;
    headers: Record<string, string>;
    agentcc: AgentCCMetadata;
    body: unknown;
  } {
    const headers: Record<string, string> = {};
    response.headers.forEach((v, k) => {
      headers[k] = v;
    });
    return { statusCode: response.status, headers, agentcc, body };
  }

  // -----------------------------------------------------------------------
  // Header building — 7-level priority merge
  // -----------------------------------------------------------------------

  private _buildHeaders(options: RequestOptions): Record<string, string> {
    const isFormData = options.body instanceof FormData;
    const headers: Record<string, string> = {};

    // 1. SDK auto-headers
    headers["User-Agent"] = `agentcc-typescript/${VERSION}`;
    if (!isFormData) {
      headers["Content-Type"] = "application/json";
    }
    headers["x-agentcc-sdk-version"] = VERSION;
    headers["Accept"] = "application/json";

    // 2. Auth
    if (this._apiKey) {
      headers["Authorization"] = `Bearer ${this._apiKey}`;
    }

    // 3. Client-level default headers
    Object.assign(headers, this._defaultHeaders);

    // 4. Client-level defaults (session, metadata)
    if (this._sessionId) {
      headers["x-agentcc-session-id"] = this._sessionId;
    }
    if (this._metadata) {
      headers["x-agentcc-metadata"] = JSON.stringify(this._metadata);
    }

    if (this._session) {
      Object.assign(headers, this._session.toHeaders());
    }

    // 4b. Trace context headers
    if (this._traceManager) {
      Object.assign(headers, this._traceManager.getHeaders());
    }

    // 5. Config headers
    if (this._config) {
      Object.assign(headers, gatewayConfigToHeaders(this._config));
    }

    // 6 & 7. Per-request headers (highest priority)
    if (options.headers) {
      Object.assign(headers, options.headers);
    }

    return headers;
  }

  // -----------------------------------------------------------------------
  // URL building
  // -----------------------------------------------------------------------

  private _buildUrl(
    path: string,
    query?: Record<string, string>,
  ): string {
    const base = this._baseUrl;
    const merged = { ...this._defaultQuery, ...query };
    const qs = Object.keys(merged).length
      ? "?" + new URLSearchParams(merged).toString()
      : "";
    return `${base}${path}${qs}`;
  }

  // -----------------------------------------------------------------------
  // Retry delay
  // -----------------------------------------------------------------------

  private _calculateDelay(attempt: number, headers?: Headers): number {
    // Respect Retry-After header
    if (headers) {
      const retryAfter = headers.get("retry-after");
      if (retryAfter) {
        const seconds = parseFloat(retryAfter);
        if (!Number.isNaN(seconds) && seconds > 0) {
          return Math.min(seconds * 1000, 60_000);
        }
      }
    }
    // Exponential backoff with jitter
    const base = 0.5 * Math.pow(2, attempt);
    const jitter = base * 0.25 * (Math.random() * 2 - 1);
    return Math.min((base + jitter) * 1000, 8_000);
  }
}

// ---------------------------------------------------------------------------
// dropParams — remove unsupported params based on model capabilities
// ---------------------------------------------------------------------------

function applyDropParams(
  body: Record<string, unknown>,
): Record<string, unknown> {
  const model = body.model as string | undefined;
  if (!model) return body;

  const result = { ...body };

  if (!supportsFunctionCalling(model)) {
    delete result.tools;
    delete result.tool_choice;
  }
  if (!supportsJsonMode(model)) {
    if (
      result.response_format &&
      typeof result.response_format === "object" &&
      (result.response_format as Record<string, unknown>).type !== "text"
    ) {
      delete result.response_format;
    }
  }

  return result;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// The body can be read once: take the text, then try JSON, so a non-JSON error (an HTML 502
// from a proxy) keeps its text as the message.
async function safeJson(response: Response): Promise<unknown> {
  const text = await response.text().catch(() => "");
  try {
    return JSON.parse(text);
  } catch {
    return { message: text || "Unknown error" };
  }
}
