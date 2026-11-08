/**
 * D-10: AgentCCMetadata gains configIgnored (x-agentcc-config-ignored) and
 * clientRequestId (x-agentcc-client-request-id). @agentcc/client 1.0.1 dropped
 * both. fi.gateway (Python) reads them the same way: a list of names, null
 * when the header is absent.
 *
 * Every response metadata reader the gateway answers is
 * read on plain and streamed responses (the 1.0.1 readers stay as they were).
 */
import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../../src/index.js";
import { mockAgentCCMetadata } from "../../src/testing.js";
import { parseAgentCCMetadata } from "../../src/types/shared.js";

const COMPLETION = {
  id: "c1",
  object: "chat.completion",
  created: 1,
  model: "m",
  choices: [{ index: 0, message: { role: "assistant", content: "hi" }, finish_reason: "stop" }],
  usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
};

const GATEWAY_HEADERS: Record<string, string> = {
  "x-agentcc-request-id": "gw-req-1",
  "x-agentcc-trace-id": "trace-1",
  "x-agentcc-provider": "openai",
  "x-agentcc-model-used": "gpt-4o-mini",
  "x-agentcc-latency-ms": "42",
  "x-agentcc-cost": "0.00123",
  "x-agentcc-cache": "miss",
  "x-agentcc-fallback-used": "true",
  "x-agentcc-routing-strategy": "round-robin",
  "x-agentcc-guardrail-triggered": "true",
  "x-agentcc-guardrail-name": "pii",
  "x-agentcc-guardrail-action": "warn",
  "x-agentcc-guardrail-confidence": "0.91",
  "x-agentcc-guardrail-message": "PII found",
  "x-agentcc-timeout-ms": "30000",
  "x-ratelimit-limit-requests": "100",
  "x-ratelimit-remaining-requests": "99",
  "x-ratelimit-reset-requests": "60",
  "x-agentcc-config-ignored": "cache.strategy, fallback",
  "x-agentcc-client-request-id": "my-req-7",
};

function respond(body: string, contentType: string, extra: Record<string, string> = GATEWAY_HEADERS) {
  return jest.fn<typeof globalThis.fetch>(async () => new Response(body, { status: 200, headers: { "content-type": contentType, ...extra } }));
}

const EXPECTED = {
  requestId: null,
  gatewayEvidence: { dispatched: "unknown", gatewayRequestId: null, clientRequestId: "my-req-7" },
  traceId: "trace-1",
  provider: "openai",
  latencyMs: 42,
  cost: 0.00123,
  cacheStatus: "miss",
  modelUsed: "gpt-4o-mini",
  guardrailTriggered: true,
  guardrailName: "pii",
  guardrailAction: "warn",
  guardrailConfidence: 0.91,
  guardrailMessage: "PII found",
  fallbackUsed: true,
  routingStrategy: "round-robin",
  timeoutMs: 30000,
  ratelimit: { limit: 100, remaining: 99, reset: 60 },
  configIgnored: ["cache.strategy", "fallback"],
  clientRequestId: "my-req-7",
};

describe("D-10 response metadata", () => {
  it("a plain response carries every gateway reader, configIgnored as a list and clientRequestId", async () => {
    const fetch = respond(JSON.stringify(COMPLETION), "application/json");
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch });
    const result = await client.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }] });
    expect(result.agentcc).toEqual(EXPECTED);
  });

  it("a streamed response carries the same metadata", async () => {
    const chunk = { id: "c1", object: "chat.completion.chunk", created: 1, model: "m", choices: [{ index: 0, delta: { content: "hi" }, finish_reason: "stop" }] };
    const fetch = respond(`data: ${JSON.stringify(chunk)}\n\ndata: [DONE]\n\n`, "text/event-stream");
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch });
    const stream = await client.chat.completions.stream({ model: "m", messages: [{ role: "user", content: "hi" }] });
    for await (const _ of stream) {
      // drain
    }
    expect(stream.agentcc).toEqual(EXPECTED);
    expect(stream.getFinalCompletion().agentcc).toEqual(EXPECTED);
  });

  it("absent headers read as null; an empty config-ignored header is an empty list", () => {
    const none = parseAgentCCMetadata(new Headers());
    expect(none.configIgnored).toBeNull();
    expect(none.clientRequestId).toBeNull();
    expect(parseAgentCCMetadata(new Headers({ "x-agentcc-config-ignored": "" })).configIgnored).toEqual([]);
    expect(parseAgentCCMetadata(new Headers({ "x-agentcc-config-ignored": "fallback" })).configIgnored).toEqual(["fallback"]);
  });

  it("requestId stays the gateway's own id even when the client request id differs", () => {
    const meta = parseAgentCCMetadata(new Headers({ "x-agentcc-request-id": "gw", "x-agentcc-client-request-id": "mine" }));
    expect(meta.requestId).toBeNull();
    expect(meta.clientRequestId).toBe("mine");
  });

  it("mockAgentCCMetadata sets both fields (null by default, overridable)", () => {
    expect(mockAgentCCMetadata().configIgnored).toBeNull();
    expect(mockAgentCCMetadata().clientRequestId).toBeNull();
    expect(mockAgentCCMetadata({ configIgnored: ["fallback"], clientRequestId: "x" })).toMatchObject({ configIgnored: ["fallback"], clientRequestId: "x" });
  });
});
