import {
  DEFAULT_TIMEOUT,
  DEFAULT_MAX_RETRIES,
  RETRYABLE_STATUS_CODES,
} from "./constants.js";
import {
  AgentCCError,
  APIConnectionError,
  APITimeoutError,
  APIStatusError,
  responseBodyError,
  errorAtExit,
} from "./errors.js";
import type { GatewayConfig } from "./gateway-config.js";
import { assertGatewayConfig } from "./gateway-config.js";
import type { AgentCCMetadata } from "./types/shared.js";
import { parseAgentCCMetadata } from "./types/shared.js";
import type { CallbackHandler, CallbackRequest } from "./callbacks.js";
import { invokeCallbacks } from "./callbacks.js";
import type { RetryPolicy } from "./retry-policy.js";
import { positiveRetryAfter, refusalDetails, refusalRetry } from "./refusal-policy.js";
import { TraceContextManager } from "./trace-context.js";
import { captureGatewayEvidence } from "./gateway-evidence.js";
import { assertNoShimOnlyOptions } from "./shim-only.js";
import { resolveApiKey, resolveBaseUrl } from "./env.js";
import { BROWSER_REFUSED, isBrowser } from "./browser.js";
import type { DryRunResult } from "./dry-run.js";
import { buildHeaders, buildUrl, checkStructuredOutput, connectionError, retryDelay, safeJson, sleep } from "./request-parts.js";
import { callbackRequest, firePostRequestCallbacks, fireStatusErrorCallbacks } from "./request-callbacks.js";
import { markScrubbedResponse, scrubCredentialHeaders } from "./redact.js";

export type { RequestOptions, ClientOptions, WithResponseResult } from "./client-options.js";
import type { RequestOptions, ClientOptions, WithResponseResult } from "./client-options.js";

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
  protected _redactMessages: boolean;
  protected _traceManager: TraceContextManager | undefined;
  protected _enableJsonSchemaValidation: boolean;
  protected _dangerouslyAllowBrowser: boolean;
  /** Whether this client runs in a browser page (then the SDK headers are left out). */
  protected _inBrowser: boolean;
  private _totalCost = 0;
  protected readonly _evidenceOptions: ClientOptions["gatewayEvidenceOptions"];

  constructor(opts: ClientOptions = {}) {
    this._inBrowser = isBrowser();
    this._dangerouslyAllowBrowser = opts.dangerouslyAllowBrowser === true;
    if (this._inBrowser && !this._dangerouslyAllowBrowser) throw new AgentCCError(BROWSER_REFUSED);
    assertNoShimOnlyOptions(opts);
    assertGatewayConfig(opts.config);
    this._apiKey = resolveApiKey(opts.apiKey, (message) => new AgentCCError(message));
    this._baseUrl = resolveBaseUrl(opts.baseUrl);
    this._timeout = opts.timeout ?? DEFAULT_TIMEOUT;
    this._maxRetries = opts.maxRetries ?? DEFAULT_MAX_RETRIES;
    this._defaultHeaders = { ...opts.defaultHeaders };
    this._defaultQuery = { ...opts.defaultQuery };
    this._sessionId = opts.sessionId;
    this._metadata = opts.metadata;
    this._config = opts.config;
    this._fetch = opts.fetch ?? globalThis.fetch.bind(globalThis);
    this._evidenceOptions = { ...opts.gatewayEvidenceOptions };
    this._callbacks = opts.callbacks ?? [];
    this._retryPolicy = opts.retryPolicy;
    this._redactMessages = opts.redactMessages ?? false;

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

  /**
   * Build the full request (URL, headers, body) without actually sending it.
   * Useful for debugging / dry-run inspection.
   */
  buildRequest(options: RequestOptions): DryRunResult {
    options = this.prepareRequest(options, "build");
    const body = options.body ?? null;
    return {
      url: this._buildUrl(options.path, options.query),
      method: options.method,
      headers: this._buildHeaders(options),
      body: body instanceof FormData ? null : (body as Record<string, unknown> | null),
    };
  }

  /** Public extension point, called once per attempt before callbacks and transport.
   * `build` prepares a dry-run only. The default implementation is an identity.
   */
  prepareRequest(options: RequestOptions, _mode: "send" | "build" = "send"): RequestOptions {
    return options;
  }

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
    const flatMax = options.maxRetries ?? this._maxRetries;
    let lastError: unknown;

    // Determine max retries based on error type in each iteration
    let maxForAttempt = flatMax;
    let refusalMax = Infinity;

    for (let attempt = 0; attempt <= maxForAttempt; attempt++) {
      try {
        return await this._doRequest<T>(options);
      } catch (caught) {
        const err = errorAtExit(caught);
        lastError = err;
        // A missing response is not proof of a pre-send failure. This safety
        // boundary precedes both flat limits and all per-error retry overrides.
        if (err instanceof APIConnectionError && err.gatewayEvidence.dispatched !== false) throw err;

        const refusal = err instanceof APIStatusError ? refusalRetry(err.statusCode, err.body, err.headers, err.gatewayEvidence) : null;
        // Header-only contract rows also admit 409; a code-less 409 stays terminal.
        if (err instanceof APIStatusError && (refusal === "never"
          || (refusal !== "once" && refusal !== "after" && !RETRYABLE_STATUS_CODES.has(err.statusCode)))) throw err;

        // Determine max retries for this error type
        if (this._retryPolicy) {
          if (err instanceof APITimeoutError) {
            maxForAttempt = this._retryPolicy.getRetriesForTimeout();
          } else if (err instanceof APIConnectionError) {
            maxForAttempt = this._retryPolicy.getRetriesForConnectionError();
          } else if (err instanceof APIStatusError) {
            // Conditional 402 and idempotency-in-progress use the 429-equivalent limit.
            maxForAttempt = this._retryPolicy.getRetriesForStatus(refusal === "once" || err.statusCode === 409 ? 429 : err.statusCode);
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

        // Keep the two-attempt ceiling even if a later attempt fails differently.
        if (refusal === "once") refusalMax = 1;
        maxForAttempt = Math.min(maxForAttempt, refusalMax);
        if (attempt >= maxForAttempt) break;

        // Required Retry-After waits must not be shortened by the ordinary 60s cap.
        const requiredDelay = err instanceof APIStatusError && refusalDetails(err.statusCode, err.body) !== null
          ? positiveRetryAfter(err.headers) : null;
        const delay = requiredDelay ?? retryDelay(attempt, err instanceof APIStatusError ? err.headers : undefined);

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

  private async _doRequest<T>(
    options: RequestOptions,
  ): Promise<WithResponseResult<T>> {
    const effectiveOptions = this.prepareRequest(options, "send");

    // Callback: onRequestStart
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
      try {
        response = await this._fetch(url, init);
      } finally {
        // Scrub before parsing bodies, delivering callbacks or exposing errors.
        // These headers belong to this attempt, never to the caller's options.
        scrubCredentialHeaders(headers);
      }
    } catch (err: unknown) {
      const connError = errorAtExit(connectionError(err, effectiveOptions.path, url));

      // Callback: onError
      if (this._callbacks.length > 0) {
        const cbReq = this._buildCallbackRequest(effectiveOptions);
        await invokeCallbacks(this._callbacks, "onError", cbReq, connError);
      }

      throw connError;
    }

    markScrubbedResponse(response);
    const gatewayEvidence = captureGatewayEvidence(response, this._evidenceOptions);
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
          await this._firePostRequestCallbacks(
            effectiveOptions,
            response,
            agentcc,
            requestCost,
            null,
          );
        }
        return {
          data: response as unknown as T,
          response,
          agentcc,
          gatewayEvidence,
        };
      }
      throw await this._statusError(response, effectiveOptions);
    }

    // JSON responses
    if (!response.ok && response.status !== 246) {
      throw await this._statusError(response, effectiveOptions);
    }

    let json: unknown;
    try {
      json = await response.json();
    } catch {
      const error = errorAtExit(responseBodyError(gatewayEvidence));
      if (this._callbacks.length > 0) {
        await invokeCallbacks(this._callbacks, "onError", this._buildCallbackRequest(effectiveOptions), error);
      }
      throw error;
    }

    // Auto-attach agentcc metadata to response
    if (json && typeof json === "object") {
      (json as Record<string, unknown>).agentcc = agentcc;
    }

    // Auto-validate JSON Schema on structured output responses
    if (this._enableJsonSchemaValidation) checkStructuredOutput(effectiveOptions.body, json);

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

    return { data: json as T, response, agentcc, gatewayEvidence };
  }

  // -----------------------------------------------------------------------
  // Post-request callbacks, request parts (src/request-callbacks.ts,
  // src/request-parts.ts)
  // -----------------------------------------------------------------------

  private async _firePostRequestCallbacks(
    options: RequestOptions,
    response: Response,
    agentcc: AgentCCMetadata,
    requestCost: number,
    body: unknown,
  ): Promise<void> {
    await firePostRequestCallbacks(
      this._callbacks,
      this._buildCallbackRequest(options),
      options,
      response,
      agentcc,
      requestCost,
      this._totalCost,
      body,
    );
  }

  /** The APIStatusError for an error answer, after its callbacks fire. */
  private async _statusError(response: Response, options: RequestOptions): Promise<APIStatusError> {
    const statusError = errorAtExit(APIStatusError.from(response.status, await safeJson(response), response.headers));
    if (this._callbacks.length > 0) {
      await fireStatusErrorCallbacks(this._callbacks, this._buildCallbackRequest(options), statusError);
    }
    return statusError;
  }

  private _buildCallbackRequest(options: RequestOptions): CallbackRequest {
    return callbackRequest(options, this._buildUrl(options.path, options.query), this._redactMessages, this._metadata);
  }

  private _buildHeaders(options: RequestOptions): Record<string, string> {
    return buildHeaders(
      {
        inBrowser: this._inBrowser,
        apiKey: this._apiKey,
        defaultHeaders: this._defaultHeaders,
        sessionId: this._sessionId,
        metadata: this._metadata,
        traceManager: this._traceManager,
        config: this._config,
      },
      options,
    );
  }

  private _buildUrl(path: string, query?: Record<string, string>): string {
    return buildUrl(this._baseUrl, this._defaultQuery, path, query);
  }
}
