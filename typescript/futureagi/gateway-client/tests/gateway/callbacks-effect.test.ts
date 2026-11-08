/**
 * A callback symbol stays in @future-agi/sdk/gateway only
 * if a real request through the client shows its output. Each test sends
 * requests through AgentCC with a mocked fetch and reads what the callback
 * produced. The trimmed CallbackHandler declares only hooks the client calls,
 * and this file proves each one is called.
 */
import { describe, it, expect, jest, afterEach } from "@jest/globals";
import {
  AgentCC,
  CallbackHandler,
  JSONLoggingCallback,
  LoggingCallback,
  MetricsCallback,
  OTelCallback,
  RetryPolicy,
} from "../../src/index.js";
import type { CallbackRequest, CallbackResponse } from "../../src/index.js";

const PARAMS = { model: "gpt-4o", messages: [{ role: "user" as const, content: "secret question" }] };
const BODY = { id: "c1", object: "chat.completion", created: 1, model: "gpt-4o", choices: [{ index: 0, message: { role: "assistant", content: "hi" }, finish_reason: "stop" }] };

function respond(status: number, headers: Record<string, string> = {}, body: unknown = BODY) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...headers } });
}

class Recorder extends CallbackHandler {
  calls: Array<[string, unknown[]]> = [];
  override onRequestStart(...a: [CallbackRequest]) { this.calls.push(["onRequestStart", a]); }
  override onRequestEnd(...a: [CallbackRequest, CallbackResponse]) { this.calls.push(["onRequestEnd", a]); }
  override onError(...a: [CallbackRequest, Error]) { this.calls.push(["onError", a]); }
  override onRetry(...a: [CallbackRequest, Error, number, number]) { this.calls.push(["onRetry", a]); }
  override onGuardrailWarning(...a: [CallbackRequest, CallbackResponse]) { this.calls.push(["onGuardrailWarning", a]); }
  override onGuardrailBlock(...a: [CallbackRequest, Error]) { this.calls.push(["onGuardrailBlock", a]); }
  override onCacheHit(...a: [CallbackRequest, CallbackResponse, string]) { this.calls.push(["onCacheHit", a]); }
  override onCostUpdate(...a: [CallbackRequest, number, number]) { this.calls.push(["onCostUpdate", a]); }
  override onFallback(...a: [CallbackRequest, string, string, string]) { this.calls.push(["onFallback", a]); }
  override onSessionStart(...a: [unknown]) { this.calls.push(["onSessionStart", a]); }
  names() { return this.calls.map(([n]) => n); }
}

afterEach(() => {
  jest.restoreAllMocks();
});

describe("CallbackHandler hooks the client calls", () => {
  it("declares exactly the 10 hooks the client calls (1.x's 5 never-called hooks are gone)", () => {
    const hooks = Object.getOwnPropertyNames(CallbackHandler.prototype).filter((n) => n !== "constructor").sort();
    expect(hooks).toEqual(["onCacheHit", "onCostUpdate", "onError", "onFallback", "onGuardrailBlock", "onGuardrailWarning", "onRequestEnd", "onRequestStart", "onRetry", "onSessionStart"]);
  });

  it("a success with cost, cache hit and fallback calls start, cost, cache, fallback and end", async () => {
    const rec = new Recorder();
    const fetch = jest.fn<typeof globalThis.fetch>(async () =>
      respond(200, { "x-agentcc-cost": "0.25", "x-agentcc-cache": "hit", "x-agentcc-fallback-used": "true", "x-agentcc-model-used": "gpt-4o-mini" }),
    );
    const client = new AgentCC({ apiKey: "k", fetch, callbacks: [rec] });
    await client.chat.completions.create(PARAMS);
    expect(rec.names()).toEqual(["onRequestStart", "onCostUpdate", "onCacheHit", "onFallback", "onRequestEnd"]);
    expect(rec.calls[1][1].slice(1)).toEqual([0.25, 0.25]);
    expect(rec.calls[3][1].slice(1)).toEqual(["gpt-4o", "gpt-4o-mini", "provider_fallback"]);
  });

  it("a 246 guardrail warning calls onGuardrailWarning", async () => {
    const rec = new Recorder();
    const fetch = jest.fn<typeof globalThis.fetch>(async () => respond(246, { "x-agentcc-guardrail-name": "pii" }));
    const client = new AgentCC({ apiKey: "k", fetch, callbacks: [rec] });
    await client.chat.completions.create(PARAMS);
    expect(rec.names()).toContain("onGuardrailWarning");
  });

  it("a 446 guardrail block calls onGuardrailBlock then onError", async () => {
    const rec = new Recorder();
    const fetch = jest.fn<typeof globalThis.fetch>(async () => respond(446, {}, { error: { message: "blocked", type: "guardrail_error" } }));
    const client = new AgentCC({ apiKey: "k", fetch, callbacks: [rec], maxRetries: 0 });
    await expect(client.chat.completions.create(PARAMS)).rejects.toThrow();
    expect(rec.names()).toEqual(["onRequestStart", "onGuardrailBlock", "onError"]);
  });

  it("a retried 503 calls onRetry with the attempt and delay", async () => {
    const rec = new Recorder();
    let n = 0;
    const fetch = jest.fn<typeof globalThis.fetch>(async () => (n++ === 0 ? respond(503, { "retry-after": "0.001" }, { error: { message: "busy" } }) : respond(200)));
    const client = new AgentCC({ apiKey: "k", fetch, callbacks: [rec], retryPolicy: new RetryPolicy({ serviceUnavailableRetries: 1 }) });
    await client.chat.completions.create(PARAMS);
    const retry = rec.calls.find(([name]) => name === "onRetry")!;
    expect(retry[1].slice(2)).toEqual([0, 1]);
  });

  it("client.session() calls onSessionStart", () => {
    const rec = new Recorder();
    const client = new AgentCC({ apiKey: "k", callbacks: [rec] });
    client.session({ name: "checkout" });
    expect(rec.names()).toEqual(["onSessionStart"]);
  });
});

describe("built-in callbacks produce output on a real request", () => {
  it("LoggingCallback logs the request and the response", async () => {
    const log = jest.spyOn(console, "log").mockImplementation(() => {});
    const fetch = jest.fn<typeof globalThis.fetch>(async () => respond(200, { "x-agentcc-latency-ms": "12", "x-agentcc-cost": "0.5" }));
    await new AgentCC({ apiKey: "k", fetch, callbacks: [new LoggingCallback("[t]")] }).chat.completions.create(PARAMS);
    const lines = log.mock.calls.map((c) => String(c[0]));
    expect(lines[0]).toMatch(/^\[t\] → POST http:\/\/localhost:8090\/v1\/chat\/completions model=gpt-4o$/);
    expect(lines).toContain("[t] ← 200 latency=12ms cost=$0.5");
  });

  it("MetricsCallback counts requests, cost and cache hits", async () => {
    const metrics = new MetricsCallback();
    const fetch = jest.fn<typeof globalThis.fetch>(async () => respond(200, { "x-agentcc-cost": "0.5", "x-agentcc-cache": "hit" }));
    const client = new AgentCC({ apiKey: "k", fetch, callbacks: [metrics] });
    await client.chat.completions.create(PARAMS);
    await client.chat.completions.create(PARAMS);
    const m = metrics.getMetrics();
    expect(m.requestCount).toBe(2);
    expect(m.totalCost).toBeCloseTo(1.0);
    expect(m.cacheHits).toBe(2);
  });

  it("JSONLoggingCallback writes one JSON line per event", async () => {
    const lines: string[] = [];
    const fetch = jest.fn<typeof globalThis.fetch>(async () => respond(200, { "x-agentcc-cost": "0.1" }));
    await new AgentCC({ apiKey: "k", fetch, callbacks: [new JSONLoggingCallback((l: string) => lines.push(l))] }).chat.completions.create(PARAMS);
    const events = lines.map((l) => JSON.parse(l).event);
    expect(events).toEqual(["request_start", "cost_update", "request_end"]);
  });

  it("OTelCallback starts and ends a span and records metrics", async () => {
    const spans: Array<{ name: string; ended: boolean; attrs: Record<string, unknown> }> = [];
    const tracer = {
      startSpan(name: string) {
        const span = { name, ended: false, attrs: {} as Record<string, unknown> };
        spans.push(span);
        return {
          setAttribute(k: string, v: unknown) { span.attrs[k] = v; return this; },
          setStatus() { return this; },
          recordException() {},
          end() { span.ended = true; },
        };
      },
    };
    const fetch = jest.fn<typeof globalThis.fetch>(async () => respond(200, { "x-agentcc-provider": "openai" }));
    await new AgentCC({ apiKey: "k", fetch, callbacks: [new OTelCallback({ tracer } as never)] }).chat.completions.create(PARAMS);
    expect(spans).toHaveLength(1);
    expect(spans[0].ended).toBe(true);
    expect(spans[0].attrs["agentcc.provider"]).toBe("openai");
  });
});

describe("redactMessages (K: callbacks receive redacted content)", () => {
  it("callbacks see redacted message content while the request carries the real text", async () => {
    const rec = new Recorder();
    const fetch = jest.fn<typeof globalThis.fetch>(async () => respond(200));
    await new AgentCC({ apiKey: "k", fetch, callbacks: [rec], redactMessages: true }).chat.completions.create(PARAMS);
    const seen = (rec.calls[0][1][0] as CallbackRequest).body as { messages: Array<{ content: string }> };
    expect(seen.messages[0].content).toBe("[REDACTED]");
    const sent = JSON.parse((fetch.mock.calls[0][1] as RequestInit).body as string);
    expect(sent.messages[0].content).toBe("secret question");
  });

  it("without redactMessages callbacks see the real content", async () => {
    const rec = new Recorder();
    const fetch = jest.fn<typeof globalThis.fetch>(async () => respond(200));
    await new AgentCC({ apiKey: "k", fetch, callbacks: [rec] }).chat.completions.create(PARAMS);
    const seen = (rec.calls[0][1][0] as CallbackRequest).body as { messages: Array<{ content: string }> };
    expect(seen.messages[0].content).toBe("secret question");
  });
});
