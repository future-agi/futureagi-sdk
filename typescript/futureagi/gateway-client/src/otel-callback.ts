// ---------------------------------------------------------------------------
// OpenTelemetry Callback — GenAI semantic conventions instrumentation
// ---------------------------------------------------------------------------

import { CallbackHandler } from "./callbacks.js";
import type {
  CallbackRequest,
  CallbackResponse,
} from "./callbacks.js";

// ---------------------------------------------------------------------------
// Duck-typed OTel interfaces (no import of @opentelemetry/api)
// ---------------------------------------------------------------------------

export interface OTelTracer {
  startSpan(name: string, options?: Record<string, unknown>): OTelSpan;
}

export interface OTelSpan {
  setAttribute(key: string, value: string | number | boolean): void;
  setStatus(status: { code: number; message?: string }): void;
  recordException(error: Error): void;
  end(): void;
}

export interface OTelMeter {
  createCounter(
    name: string,
    options?: { description?: string; unit?: string },
  ): OTelCounter;
  createHistogram(
    name: string,
    options?: { description?: string; unit?: string },
  ): OTelHistogram;
}

export interface OTelCounter {
  add(value: number, attributes?: Record<string, string | number>): void;
}

export interface OTelHistogram {
  record(
    value: number,
    attributes?: Record<string, string | number>,
  ): void;
}

// ---------------------------------------------------------------------------
// No-op implementations (used when OTel is not available)
// ---------------------------------------------------------------------------

const noopSpan: OTelSpan = {
  setAttribute() {},
  setStatus() {},
  recordException() {},
  end() {},
};

const noopCounter: OTelCounter = { add() {} };
const noopHistogram: OTelHistogram = { record() {} };

const noopTracer: OTelTracer = {
  startSpan() {
    return noopSpan;
  },
};

const noopMeter: OTelMeter = {
  createCounter() {
    return noopCounter;
  },
  createHistogram() {
    return noopHistogram;
  },
};

// ---------------------------------------------------------------------------
// OTelCallback
// ---------------------------------------------------------------------------

export interface OTelCallbackOptions {
  tracer?: OTelTracer;
  meter?: OTelMeter;
  /** Span name prefix. Default: "agentcc" */
  spanPrefix?: string;
}

/**
 * OpenTelemetry callback for automatic instrumentation.
 * Creates spans and records metrics for every AgentCC request following
 * GenAI semantic conventions.
 *
 * @example
 * ```typescript
 * import { trace, metrics } from "@opentelemetry/api";
 *
 * const client = new AgentCC({
 *   callbacks: [new OTelCallback({
 *     tracer: trace.getTracer("my-app"),
 *     meter: metrics.getMeter("my-app"),
 *   })],
 * });
 * ```
 */
export class OTelCallback extends CallbackHandler {
  private _tracer: OTelTracer;
  private _spanPrefix: string;
  private _requestCounter: OTelCounter;
  private _errorCounter: OTelCounter;
  private _costCounter: OTelCounter;
  private _latencyHistogram: OTelHistogram;
  private _tokenHistogram: OTelHistogram;

  // Track active spans by request URL (simple correlation)
  private _spans = new Map<string, OTelSpan>();

  constructor(opts: OTelCallbackOptions = {}) {
    super();
    this._tracer = opts.tracer ?? noopTracer;
    this._spanPrefix = opts.spanPrefix ?? "agentcc";
    const meter = opts.meter ?? noopMeter;

    this._requestCounter = meter.createCounter("agentcc.request.count", {
      description: "Number of AgentCC requests",
    });
    this._errorCounter = meter.createCounter("agentcc.error.count", {
      description: "Number of AgentCC request errors",
    });
    this._costCounter = meter.createCounter("agentcc.request.cost", {
      description: "Cumulative cost of AgentCC requests",
      unit: "usd",
    });
    this._latencyHistogram = meter.createHistogram(
      "gen_ai.client.operation.duration",
      {
        description: "Duration of AgentCC operations",
        unit: "ms",
      },
    );
    this._tokenHistogram = meter.createHistogram(
      "gen_ai.client.token.usage",
      {
        description: "Token usage per request",
        unit: "token",
      },
    );
  }

  onRequestStart(request: CallbackRequest): void {
    const spanName = this._deriveSpanName(request.url);
    const span = this._tracer.startSpan(spanName);

    span.setAttribute("gen_ai.system", "agentcc");
    span.setAttribute("server.address", this._extractHost(request.url));

    const model = this._extractModel(request.body);
    if (model) {
      span.setAttribute("gen_ai.request.model", model);
    }

    this._spans.set(request.url, span);
    this._requestCounter.add(1, { model: model ?? "unknown" });
  }

  onRequestEnd(request: CallbackRequest, response: CallbackResponse): void {
    const span = this._spans.get(request.url);
    if (!span) return;

    const agentcc = response.agentcc;

    if (agentcc.modelUsed) {
      span.setAttribute("gen_ai.response.model", agentcc.modelUsed);
    }
    if (agentcc.provider) {
      span.setAttribute("agentcc.provider", agentcc.provider);
    }
    if (agentcc.requestId) {
      span.setAttribute("agentcc.request_id", agentcc.requestId);
    }
    if (agentcc.latencyMs !== undefined && agentcc.latencyMs !== null) {
      span.setAttribute("agentcc.latency_ms", agentcc.latencyMs);
      this._latencyHistogram.record(agentcc.latencyMs, {
        model: agentcc.modelUsed ?? "unknown",
      });
    }
    if (agentcc.cost !== undefined && agentcc.cost !== null) {
      span.setAttribute("agentcc.cost", agentcc.cost);
    }
    if (agentcc.cacheStatus) {
      span.setAttribute("agentcc.cache_status", agentcc.cacheStatus);
    }

    // Extract usage from response body
    const body = response.body as Record<string, unknown> | null;
    if (body) {
      const usage = body.usage as
        | { prompt_tokens?: number; completion_tokens?: number }
        | undefined;
      if (usage) {
        if (usage.prompt_tokens !== undefined) {
          span.setAttribute("gen_ai.usage.input_tokens", usage.prompt_tokens);
          this._tokenHistogram.record(usage.prompt_tokens, {
            type: "input",
          });
        }
        if (usage.completion_tokens !== undefined) {
          span.setAttribute(
            "gen_ai.usage.output_tokens",
            usage.completion_tokens,
          );
          this._tokenHistogram.record(usage.completion_tokens, {
            type: "output",
          });
        }
      }

      // Finish reasons
      const choices = body.choices as
        | Array<{ finish_reason?: string }>
        | undefined;
      if (choices && choices.length > 0) {
        const reasons = choices
          .map((c) => c.finish_reason)
          .filter(Boolean) as string[];
        if (reasons.length > 0) {
          span.setAttribute(
            "gen_ai.response.finish_reasons",
            reasons.join(","),
          );
        }
      }
    }

    span.setStatus({ code: 1 }); // OK
    span.end();
    this._spans.delete(request.url);
  }

  onError(request: CallbackRequest, error: Error): void {
    const span = this._spans.get(request.url);
    if (span) {
      span.setStatus({ code: 2, message: error.message }); // ERROR
      span.recordException(error);
      span.end();
      this._spans.delete(request.url);
    }
    this._errorCounter.add(1);
  }

  onCostUpdate(
    _request: CallbackRequest,
    cost: number,
    _cumulativeCost: number,
  ): void {
    this._costCounter.add(cost);
  }

  // -----------------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------------

  private _deriveSpanName(url: string): string {
    try {
      const path = new URL(url).pathname;
      // "/v1/chat/completions" → "agentcc.chat.completions"
      const clean = path
        .replace(/^\/v1\//, "")
        .replace(/\//g, ".");
      return `${this._spanPrefix}.${clean}`;
    } catch {
      return `${this._spanPrefix}.request`;
    }
  }

  private _extractHost(url: string): string {
    try {
      return new URL(url).hostname;
    } catch {
      return "unknown";
    }
  }

  private _extractModel(body: unknown): string | null {
    if (body && typeof body === "object" && "model" in body) {
      return (body as Record<string, unknown>).model as string;
    }
    return null;
  }
}
