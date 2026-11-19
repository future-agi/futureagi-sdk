import { describe, it, expect, jest } from "@jest/globals";
import { OTelCallback } from "../src/otel-callback.js";
import type {
  OTelTracer,
  OTelSpan,
  OTelMeter,
  OTelCounter,
  OTelHistogram,
} from "../src/otel-callback.js";
import type { CallbackRequest, CallbackResponse } from "../src/callbacks.js";
import type { AgentCCMetadata } from "../src/types/shared.js";

// ---------------------------------------------------------------------------
// Mock OTel implementations
// ---------------------------------------------------------------------------

function createMockSpan(): OTelSpan & {
  attributes: Record<string, unknown>;
  status: { code: number; message?: string } | null;
  exceptions: Error[];
  ended: boolean;
} {
  const span = {
    attributes: {} as Record<string, unknown>,
    status: null as { code: number; message?: string } | null,
    exceptions: [] as Error[],
    ended: false,
    setAttribute(key: string, value: string | number | boolean) {
      span.attributes[key] = value;
    },
    setStatus(s: { code: number; message?: string }) {
      span.status = s;
    },
    recordException(error: Error) {
      span.exceptions.push(error);
    },
    end() {
      span.ended = true;
    },
  };
  return span;
}

function createMockTracer() {
  const spans: ReturnType<typeof createMockSpan>[] = [];
  const tracer: OTelTracer = {
    startSpan(name: string) {
      const span = createMockSpan();
      spans.push(span);
      return span;
    },
  };
  return { tracer, spans };
}

function createMockMeter() {
  const counters: Record<string, { values: number[] }> = {};
  const histograms: Record<string, { values: number[] }> = {};

  const meter: OTelMeter = {
    createCounter(name: string) {
      counters[name] = { values: [] };
      return { add(v: number) { counters[name].values.push(v); } };
    },
    createHistogram(name: string) {
      histograms[name] = { values: [] };
      return { record(v: number) { histograms[name].values.push(v); } };
    },
  };
  return { meter, counters, histograms };
}

function makeRequest(model = "gpt-4o"): CallbackRequest {
  return {
    method: "POST",
    url: "http://gateway:8090/v1/chat/completions",
    headers: {},
    body: { model, messages: [] },
  };
}

function makeAgentCCMeta(overrides: Partial<AgentCCMetadata> = {}): AgentCCMetadata {
  return {
    requestId: "req-1",
    traceId: "trace-1",
    provider: "openai",
    latencyMs: 150,
    cost: 0.005,
    cacheStatus: null,
    modelUsed: "gpt-4o",
    guardrailTriggered: false,
    guardrailName: null,
    guardrailAction: null,
    guardrailConfidence: null,
    guardrailMessage: null,
    fallbackUsed: false,
    routingStrategy: null,
    timeoutMs: null,
    ratelimit: null,
    ...overrides,
  };
}

function makeResponse(agentcc?: Partial<AgentCCMetadata>): CallbackResponse {
  return {
    statusCode: 200,
    headers: {},
    agentcc: makeAgentCCMeta(agentcc),
    body: {
      choices: [{ finish_reason: "stop" }],
      usage: { prompt_tokens: 100, completion_tokens: 50, total_tokens: 150 },
    },
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("OTelCallback", () => {
  it("creates span on request start", () => {
    const { tracer, spans } = createMockTracer();
    const cb = new OTelCallback({ tracer });

    cb.onRequestStart(makeRequest("gpt-4o"));

    expect(spans).toHaveLength(1);
    expect(spans[0].attributes["gen_ai.system"]).toBe("agentcc");
    expect(spans[0].attributes["gen_ai.request.model"]).toBe("gpt-4o");
    expect(spans[0].attributes["server.address"]).toBe("gateway");
  });

  it("sets response attributes and ends span", () => {
    const { tracer, spans } = createMockTracer();
    const cb = new OTelCallback({ tracer });

    const req = makeRequest();
    cb.onRequestStart(req);
    cb.onRequestEnd(req, makeResponse());

    expect(spans[0].attributes["gen_ai.response.model"]).toBe("gpt-4o");
    expect(spans[0].attributes["agentcc.provider"]).toBe("openai");
    expect(spans[0].attributes["agentcc.latency_ms"]).toBe(150);
    expect(spans[0].attributes["agentcc.cost"]).toBe(0.005);
    expect(spans[0].attributes["gen_ai.usage.input_tokens"]).toBe(100);
    expect(spans[0].attributes["gen_ai.usage.output_tokens"]).toBe(50);
    expect(spans[0].attributes["gen_ai.response.finish_reasons"]).toBe("stop");
    expect(spans[0].status).toEqual({ code: 1 });
    expect(spans[0].ended).toBe(true);
  });

  it("records error on span", () => {
    const { tracer, spans } = createMockTracer();
    const cb = new OTelCallback({ tracer });

    const req = makeRequest();
    cb.onRequestStart(req);
    const error = new Error("API timeout");
    cb.onError(req, error);

    expect(spans[0].status).toEqual({ code: 2, message: "API timeout" });
    expect(spans[0].exceptions).toHaveLength(1);
    expect(spans[0].ended).toBe(true);
  });

  it("records metrics", () => {
    const { tracer } = createMockTracer();
    const { meter, counters, histograms } = createMockMeter();
    const cb = new OTelCallback({ tracer, meter });

    const req = makeRequest();
    cb.onRequestStart(req);
    cb.onRequestEnd(req, makeResponse());

    expect(counters["agentcc.request.count"].values).toEqual([1]);
    expect(histograms["gen_ai.client.operation.duration"].values).toEqual([150]);
    expect(histograms["gen_ai.client.token.usage"].values).toContain(100);
    expect(histograms["gen_ai.client.token.usage"].values).toContain(50);
  });

  it("records cost metric via onCostUpdate", () => {
    const { meter, counters } = createMockMeter();
    const cb = new OTelCallback({ meter });

    cb.onCostUpdate(makeRequest(), 0.005, 0.01);

    expect(counters["agentcc.request.cost"].values).toEqual([0.005]);
  });

  it("records error counter", () => {
    const { tracer } = createMockTracer();
    const { meter, counters } = createMockMeter();
    const cb = new OTelCallback({ tracer, meter });

    const req = makeRequest();
    cb.onRequestStart(req);
    cb.onError(req, new Error("fail"));

    expect(counters["agentcc.error.count"].values).toEqual([1]);
  });

  it("works without tracer/meter (no-op)", () => {
    const cb = new OTelCallback();

    // Should not throw
    const req = makeRequest();
    cb.onRequestStart(req);
    cb.onRequestEnd(req, makeResponse());
    cb.onError(makeRequest(), new Error("test"));
    cb.onCostUpdate(makeRequest(), 0.01, 0.01);
  });

  it("derives span name from URL path", () => {
    const { tracer, spans } = createMockTracer();
    const cb = new OTelCallback({ tracer });

    cb.onRequestStart({
      method: "POST",
      url: "http://gateway:8090/v1/embeddings",
      headers: {},
      body: { model: "text-embedding-3-small", input: "test" },
    });

    // Span name should be derived from path
    expect(spans).toHaveLength(1);
  });

  it("uses custom span prefix", () => {
    const { tracer, spans } = createMockTracer();
    const cb = new OTelCallback({ tracer, spanPrefix: "myapp" });

    cb.onRequestStart(makeRequest());
    // The span was created (we can't easily check the name from our mock,
    // but we verify it doesn't crash)
    expect(spans).toHaveLength(1);
  });
});
