/**
 * Built-in callback implementations.
 *
 * @module
 */

import { CallbackHandler } from "./callbacks.js";
import type { CallbackRequest, CallbackResponse } from "./callbacks.js";
import type { Session } from "./session.js";

// ---------------------------------------------------------------------------
// LoggingCallback — console.log for each lifecycle event
// ---------------------------------------------------------------------------

export class LoggingCallback extends CallbackHandler {
  private _prefix: string;

  constructor(prefix = "[AgentCC]") {
    super();
    this._prefix = prefix;
  }

  override onRequestStart(request: CallbackRequest): void {
    const model = (request.body as Record<string, unknown>)?.model ?? "unknown";
    console.log(`${this._prefix} → ${request.method} ${request.url} model=${model}`);
  }

  override onRequestEnd(_request: CallbackRequest, response: CallbackResponse): void {
    console.log(
      `${this._prefix} ← ${response.statusCode} latency=${response.agentcc.latencyMs}ms` +
        (response.agentcc.cost != null ? ` cost=$${response.agentcc.cost}` : ""),
    );
  }

  override onError(request: CallbackRequest, error: Error): void {
    console.log(`${this._prefix} ✗ ${request.method} ${request.url}: ${error.name}: ${error.message}`);
  }

  override onRetry(_request: CallbackRequest, error: Error, attempt: number, delay: number): void {
    console.log(`${this._prefix} ↻ retry #${attempt + 1} in ${delay}ms (${error.name})`);
  }

  override onCacheHit(_request: CallbackRequest, _response: CallbackResponse, cacheType: string): void {
    console.log(`${this._prefix} ⚡ cache ${cacheType}`);
  }

  override onGuardrailWarning(_request: CallbackRequest, response: CallbackResponse): void {
    console.log(`${this._prefix} ⚠ guardrail warning: ${response.agentcc.guardrailName}`);
  }

  override onGuardrailBlock(_request: CallbackRequest, error: Error): void {
    console.log(`${this._prefix} ⛔ guardrail blocked: ${error.message}`);
  }
}

// ---------------------------------------------------------------------------
// MetricsCallback — in-memory counters
// ---------------------------------------------------------------------------

export class MetricsCallback extends CallbackHandler {
  requestCount = 0;
  errorCount = 0;
  totalLatencyMs = 0;
  totalCost = 0;
  totalTokens = 0;
  cacheHits = 0;
  guardrailBlocks = 0;
  guardrailWarnings = 0;
  retryCount = 0;

  override onRequestEnd(_request: CallbackRequest, response: CallbackResponse): void {
    this.requestCount++;
    this.totalLatencyMs += response.agentcc.latencyMs;
    if (response.agentcc.cost != null) this.totalCost += response.agentcc.cost;
  }

  override onError(): void {
    this.errorCount++;
  }

  override onRetry(): void {
    this.retryCount++;
  }

  override onCacheHit(): void {
    this.cacheHits++;
  }

  override onGuardrailBlock(): void {
    this.guardrailBlocks++;
  }

  override onGuardrailWarning(): void {
    this.guardrailWarnings++;
  }

  override onCostUpdate(_request: CallbackRequest, _cost: number, _cumulativeCost: number): void {
    // Cost already tracked in onRequestEnd via agentcc.cost
  }

  getMetrics() {
    return {
      requestCount: this.requestCount,
      errorCount: this.errorCount,
      avgLatencyMs: this.requestCount > 0 ? this.totalLatencyMs / this.requestCount : 0,
      totalCost: this.totalCost,
      totalTokens: this.totalTokens,
      cacheHits: this.cacheHits,
      guardrailBlocks: this.guardrailBlocks,
      guardrailWarnings: this.guardrailWarnings,
      retryCount: this.retryCount,
    };
  }

  reset(): void {
    this.requestCount = 0;
    this.errorCount = 0;
    this.totalLatencyMs = 0;
    this.totalCost = 0;
    this.totalTokens = 0;
    this.cacheHits = 0;
    this.guardrailBlocks = 0;
    this.guardrailWarnings = 0;
    this.retryCount = 0;
  }
}

// ---------------------------------------------------------------------------
// JSONLoggingCallback — structured JSON output per event
// ---------------------------------------------------------------------------

export class JSONLoggingCallback extends CallbackHandler {
  private _write: (line: string) => void;

  constructor(writer?: (line: string) => void) {
    super();
    this._write = writer ?? ((line: string) => console.log(line));
  }

  private _log(event: string, data: Record<string, unknown>): void {
    this._write(
      JSON.stringify({
        timestamp: new Date().toISOString(),
        event,
        ...data,
      }),
    );
  }

  override onRequestStart(request: CallbackRequest): void {
    const body = request.body as Record<string, unknown> | undefined;
    this._log("request_start", {
      method: request.method,
      url: request.url,
      model: body?.model,
    });
  }

  override onRequestEnd(request: CallbackRequest, response: CallbackResponse): void {
    this._log("request_end", {
      url: request.url,
      status: response.statusCode,
      latencyMs: response.agentcc.latencyMs,
      cost: response.agentcc.cost,
      provider: response.agentcc.provider,
      cacheStatus: response.agentcc.cacheStatus,
      traceId: response.agentcc.traceId,
      requestId: response.agentcc.requestId,
    });
  }

  override onError(request: CallbackRequest, error: Error): void {
    this._log("error", {
      url: request.url,
      errorName: error.name,
      errorMessage: error.message,
    });
  }

  override onRetry(request: CallbackRequest, error: Error, attempt: number, delay: number): void {
    this._log("retry", {
      url: request.url,
      attempt,
      delay,
      errorName: error.name,
    });
  }

  override onCostUpdate(_request: CallbackRequest, cost: number, cumulativeCost: number): void {
    this._log("cost_update", { cost, cumulativeCost });
  }

  override onGuardrailWarning(_request: CallbackRequest, response: CallbackResponse): void {
    this._log("guardrail_warning", {
      guardrailName: response.agentcc.guardrailName,
      guardrailAction: response.agentcc.guardrailAction,
      guardrailConfidence: response.agentcc.guardrailConfidence,
    });
  }

  override onGuardrailBlock(_request: CallbackRequest, error: Error): void {
    this._log("guardrail_block", { errorMessage: error.message });
  }

  override onSessionStart(session: Session): void {
    this._log("session_start", {
      sessionId: session.sessionId,
      sessionName: session.name,
    });
  }
}
