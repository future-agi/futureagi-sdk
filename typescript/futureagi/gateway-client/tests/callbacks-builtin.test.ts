import { describe, it, expect, jest } from "@jest/globals";
import { LoggingCallback, MetricsCallback, JSONLoggingCallback } from "../src/callbacks-builtin.js";
import type { CallbackRequest, CallbackResponse } from "../src/callbacks.js";
import type { AgentCCMetadata } from "../src/types/shared.js";

function makeReq(model = "gpt-4o"): CallbackRequest {
  return {
    method: "POST",
    url: "http://localhost/v1/chat/completions",
    headers: {},
    body: { model, messages: [] },
  };
}

function makeMeta(overrides: Partial<AgentCCMetadata> = {}): AgentCCMetadata {
  return {
    requestId: "req-1",
    traceId: "trace-1",
    provider: "openai",
    latencyMs: 150,
    cost: 0.005,
    cacheStatus: null,
    modelUsed: null,
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

function makeResp(overrides: Partial<AgentCCMetadata> = {}): CallbackResponse {
  return {
    statusCode: 200,
    headers: {},
    agentcc: makeMeta(overrides),
    body: null,
  };
}

describe("LoggingCallback", () => {
  it("logs request start and end", () => {
    const spy = jest.spyOn(console, "log").mockImplementation(() => {});
    const cb = new LoggingCallback();
    cb.onRequestStart(makeReq());
    cb.onRequestEnd(makeReq(), makeResp());
    expect(spy).toHaveBeenCalledTimes(2);
    expect(spy.mock.calls[0][0]).toContain("POST");
    expect(spy.mock.calls[1][0]).toContain("150ms");
    spy.mockRestore();
  });
});

describe("MetricsCallback", () => {
  it("tracks request count and cost", () => {
    const cb = new MetricsCallback();
    cb.onRequestEnd(makeReq(), makeResp({ cost: 0.01 }));
    cb.onRequestEnd(makeReq(), makeResp({ cost: 0.02 }));
    cb.onError(makeReq(), new Error("fail"));

    const m = cb.getMetrics();
    expect(m.requestCount).toBe(2);
    expect(m.totalCost).toBeCloseTo(0.03);
    expect(m.errorCount).toBe(1);
    expect(m.avgLatencyMs).toBe(150);
  });

  it("tracks cache hits and guardrails", () => {
    const cb = new MetricsCallback();
    cb.onCacheHit(makeReq(), makeResp(), "hit");
    cb.onCacheHit(makeReq(), makeResp(), "hit");
    cb.onGuardrailBlock(makeReq(), new Error("blocked"));
    cb.onGuardrailWarning(makeReq(), makeResp());

    const m = cb.getMetrics();
    expect(m.cacheHits).toBe(2);
    expect(m.guardrailBlocks).toBe(1);
    expect(m.guardrailWarnings).toBe(1);
  });

  it("reset clears all counters", () => {
    const cb = new MetricsCallback();
    cb.onRequestEnd(makeReq(), makeResp({ cost: 0.5 }));
    cb.onError(makeReq(), new Error("x"));
    cb.reset();
    const m = cb.getMetrics();
    expect(m.requestCount).toBe(0);
    expect(m.totalCost).toBe(0);
    expect(m.errorCount).toBe(0);
  });
});

describe("JSONLoggingCallback", () => {
  it("writes structured JSON per event", () => {
    const lines: string[] = [];
    const cb = new JSONLoggingCallback((line) => lines.push(line));
    cb.onRequestStart(makeReq("gpt-4o-mini"));
    cb.onRequestEnd(makeReq(), makeResp());

    expect(lines).toHaveLength(2);
    const start = JSON.parse(lines[0]);
    expect(start.event).toBe("request_start");
    expect(start.model).toBe("gpt-4o-mini");
    expect(start.timestamp).toBeDefined();

    const end = JSON.parse(lines[1]);
    expect(end.event).toBe("request_end");
    expect(end.latencyMs).toBe(150);
    expect(end.cost).toBe(0.005);
  });

  it("logs errors", () => {
    const lines: string[] = [];
    const cb = new JSONLoggingCallback((line) => lines.push(line));
    cb.onError(makeReq(), new Error("timeout"));
    const parsed = JSON.parse(lines[0]);
    expect(parsed.event).toBe("error");
    expect(parsed.errorMessage).toBe("timeout");
  });
});
