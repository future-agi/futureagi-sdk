import { describe, it, expect } from "@jest/globals";
import { parseAgentCCMetadata } from "../src/types/shared.js";

describe("parseAgentCCMetadata", () => {
  it("parses all gateway headers", () => {
    const headers = new Headers({
      "x-agentcc-request-id": "req-123",
      "x-agentcc-trace-id": "trace-456",
      "x-agentcc-provider": "openai",
      "x-agentcc-latency-ms": "150",
      "x-agentcc-cost": "0.0035",
      "x-agentcc-cache": "hit",
      "x-agentcc-model-used": "gpt-4o-mini",
      "x-agentcc-guardrail-triggered": "true",
      "x-agentcc-guardrail-name": "pii-detection",
      "x-agentcc-guardrail-action": "warn",
      "x-agentcc-guardrail-confidence": "0.87",
      "x-agentcc-guardrail-message": "PII found",
      "x-agentcc-fallback-used": "true",
      "x-agentcc-routing-strategy": "round-robin",
      "x-agentcc-timeout-ms": "5000",
      "x-ratelimit-limit-requests": "100",
      "x-ratelimit-remaining-requests": "42",
      "x-ratelimit-reset-requests": "60",
    });

    const meta = parseAgentCCMetadata(headers);
    expect(meta.requestId).toBe("req-123");
    expect(meta.traceId).toBe("trace-456");
    expect(meta.provider).toBe("openai");
    expect(meta.latencyMs).toBe(150);
    expect(meta.cost).toBe(0.0035);
    expect(meta.cacheStatus).toBe("hit");
    expect(meta.modelUsed).toBe("gpt-4o-mini");
    expect(meta.guardrailTriggered).toBe(true);
    expect(meta.guardrailName).toBe("pii-detection");
    expect(meta.guardrailAction).toBe("warn");
    expect(meta.guardrailConfidence).toBe(0.87);
    expect(meta.guardrailMessage).toBe("PII found");
    expect(meta.fallbackUsed).toBe(true);
    expect(meta.routingStrategy).toBe("round-robin");
    expect(meta.timeoutMs).toBe(5000);
    expect(meta.ratelimit).toEqual({
      limit: 100,
      remaining: 42,
      reset: 60,
    });
  });

  it("uses defaults for missing headers", () => {
    const meta = parseAgentCCMetadata(new Headers());
    expect(meta.requestId).toBe("unknown");
    expect(meta.traceId).toBe("unknown");
    expect(meta.provider).toBe("unknown");
    expect(meta.latencyMs).toBe(0);
    expect(meta.cost).toBeNull();
    expect(meta.cacheStatus).toBeNull();
    expect(meta.guardrailTriggered).toBe(false);
    expect(meta.fallbackUsed).toBe(false);
    expect(meta.ratelimit).toBeNull();
  });
});
