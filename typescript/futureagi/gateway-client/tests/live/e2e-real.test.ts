/**
 * E2E tests: @agentcc/client 1.0.1's tests/e2e-real.test.ts (the recorded revision), ported to
 * @future-agi/sdk/gateway against agentcc-gateway the recorded revision.
 *
 * 1.0.1 ran these against a hand-started gateway on localhost:8090 proxying to
 * OpenAI with a static key. Here the gateway is built at the pin, its upstream is
 * the local mock (python/tests/gateway/live/stack/mock_upstream.py), and the key
 * is minted for the run. A real model's answers ("YES", "alice", a JSON color)
 * become the mock's [[mock:say:...]] / [[mock:color-json]] scenarios, and each
 * test also checks what the gateway forwarded upstream, which 1.0.1 could not.
 * Test names are 1.0.1's; tests/live/manifest.json maps all 31 (24 here, 7 to
 * the 2.0 shim: middleware, pre-call rules, token utilities, BudgetManager).
 */
import { expect, it } from "@jest/globals";
import {
  AgentCC,
  LoggingCallback,
  MetricsCallback,
  validateJsonResponse,
  toResponseFormat,
  checkValidKey,
  healthCheck,
} from "../../src/index.js";
import { describeLive, live, marker, mockRecords, MODEL, record, tapRecords, user } from "./_live.js";

function makeClient(opts: Record<string, unknown> = {}): AgentCC {
  return new AgentCC({ apiKey: live.key, baseUrl: live.base, maxRetries: 0, ...opts });
}

describeLive("E2E: Chat Completions", () => {
  it("creates a basic chat completion", async () => {
    const response = await makeClient().chat.completions.create({ model: MODEL, messages: user(`Say exactly: PONG ${marker()}`), max_tokens: 10 });
    expect(response.id).toBeTruthy();
    expect(response.choices).toHaveLength(1);
    expect(response.choices[0].message.role).toBe("assistant");
    expect(response.choices[0].message.content).toBe("PONG from mock");
    expect(response.choices[0].finish_reason).toBe("stop");
  });

  it("returns usage info", async () => {
    const response = await makeClient().chat.completions.create({ model: MODEL, messages: user(`Say hi ${marker()}`), max_tokens: 5 });
    const usage = (response as any).usage;
    expect(usage.prompt_tokens).toBeGreaterThan(0);
    expect(usage.completion_tokens).toBeGreaterThan(0);
    expect(usage.total_tokens).toBe(usage.prompt_tokens + usage.completion_tokens);
  });

  it("passes temperature and max_tokens", async () => {
    const m = marker();
    const response = await makeClient().chat.completions.create({ model: MODEL, messages: user(`[[mock:say:7]] Reply with a single digit ${m}`), temperature: 0, max_tokens: 3 });
    expect(response.choices[0].message.content).toBe("7");
    const [up] = await mockRecords(m);
    expect(up.body).toMatchObject({ temperature: 0, max_tokens: 3 });
  });

  it("handles system message", async () => {
    const m = marker();
    const messages = [
      { role: "system" as const, content: "Always respond with exactly 'YES'" },
      { role: "user" as const, content: `[[mock:say:YES]] Should I? ${m}` },
    ];
    const response = await makeClient().chat.completions.create({ model: MODEL, messages, max_tokens: 5, temperature: 0 });
    expect(response.choices[0].message.content?.toUpperCase()).toContain("YES");
    const [up] = await mockRecords(m);
    expect((up.body as any).messages).toEqual(messages);
  });

  it("handles multi-turn conversation", async () => {
    const m = marker();
    const messages = [
      { role: "user" as const, content: "My name is Alice." },
      { role: "assistant" as const, content: "Hello Alice!" },
      { role: "user" as const, content: `[[mock:say:alice]] What's my name? ${m}` },
    ];
    const response = await makeClient().chat.completions.create({ model: MODEL, messages, max_tokens: 20, temperature: 0 });
    expect(response.choices[0].message.content?.toLowerCase()).toContain("alice");
    const [up] = await mockRecords(m);
    expect((up.body as any).messages).toEqual(messages);
  });
});

describeLive("E2E: Streaming", () => {
  it("streams chat completion chunks", async () => {
    const stream = await makeClient().chat.completions.create({ model: MODEL, messages: user(`Count from 1 to 3 ${marker()}`), max_tokens: 30, stream: true });
    const chunks: string[] = [];
    for await (const chunk of stream) {
      const content = chunk.choices?.[0]?.delta?.content;
      if (content) chunks.push(content);
    }
    expect(chunks).toEqual(["Hello", " world"]);
  });

  it("StreamManager collects full text", async () => {
    const mgr = await makeClient().chat.completions.stream({ model: MODEL, messages: user(`Say 'hello world' ${marker()}`), max_tokens: 10 });
    const allChunks: string[] = [];
    for await (const chunk of mgr) {
      const c = chunk.choices?.[0]?.delta?.content;
      if (c) allChunks.push(c);
    }
    expect(allChunks.join("")).toBe("Hello world");
  });
});

describeLive("E2E: AgentCC Metadata", () => {
  it("auto-attaches agentcc metadata to response", async () => {
    const response = await makeClient().chat.completions.create({ model: MODEL, messages: user(`Hi ${marker()}`), max_tokens: 5 });
    const agentcc = response.agentcc!;
    record("e2e_metadata", agentcc);
    expect(agentcc.requestId).toBeTruthy();
    expect(agentcc.provider).toBe("mock-a");
    expect(agentcc.cost).toBeGreaterThan(0);
  });
});

describeLive("E2E: Session Management", () => {
  it("creates a session-scoped client", async () => {
    const m = marker();
    const tapped = new AgentCC({ apiKey: live.key, baseUrl: live.tap, maxRetries: 0 });
    const { client: sessClient, session } = tapped.session({ name: "e2e-test-session" });
    expect(session.sessionId).toBeTruthy();
    expect(session.name).toBe("e2e-test-session");
    const response = await sessClient.chat.completions.create({ model: MODEL, messages: user(`ping ${m}`), max_tokens: 5 });
    expect(response.choices[0].message.content).toBeTruthy();
    expect(session.requestCount).toBe(1);
    const [sent] = await tapRecords(m);
    expect(sent.headers["x-agentcc-session-id"]).toBe(session.sessionId);
    expect(sent.headers["x-agentcc-session-name"]).toBe("e2e-test-session");
  });

  it("tracks cost across session requests", async () => {
    const { client: sessClient, session } = makeClient().session();
    const a = await sessClient.chat.completions.create({ model: MODEL, messages: user(`1 ${marker()}`), max_tokens: 3 });
    const b = await sessClient.chat.completions.create({ model: MODEL, messages: user(`2 ${marker()}`), max_tokens: 3 });
    expect(session.requestCount).toBe(2);
    expect(session.totalCost).toBeCloseTo((a.agentcc!.cost ?? 0) + (b.agentcc!.cost ?? 0), 10);
  });
});

describeLive("E2E: Callbacks", () => {
  it("LoggingCallback fires on request", async () => {
    const logs: string[] = [];
    const origLog = console.log;
    console.log = (...args: any[]) => {
      logs.push(args.join(" "));
    };
    try {
      await makeClient({ callbacks: [new LoggingCallback()] }).chat.completions.create({ model: MODEL, messages: user(`test ${marker()}`), max_tokens: 5 });
    } finally {
      console.log = origLog;
    }
    expect(logs.length).toBeGreaterThan(0);
  });

  it("MetricsCallback tracks request count", async () => {
    const metricsCb = new MetricsCallback();
    await makeClient({ callbacks: [metricsCb] }).chat.completions.create({ model: MODEL, messages: user(`test ${marker()}`), max_tokens: 5 });
    const metrics = metricsCb.getMetrics();
    expect(metrics.requestCount).toBe(1);
    expect(metrics.avgLatencyMs).toBeGreaterThanOrEqual(0);
  });
});

describeLive("E2E: Trace Context", () => {
  it("sends traceparent header with request", async () => {
    const m = marker();
    const client = new AgentCC({ apiKey: live.key, baseUrl: live.tap, maxRetries: 0, traceContext: true });
    const traceId = (client as any)._traceManager.traceId;
    expect(traceId).toMatch(/^[0-9a-f]{32}$/);
    const response = await client.chat.completions.create({ model: MODEL, messages: user(`trace test ${m}`), max_tokens: 5 });
    expect(response).toBeDefined();
    const [sent] = await tapRecords(m);
    expect(sent.headers.traceparent).toMatch(new RegExp(`^00-${traceId}-[0-9a-f]{16}-0[01]$`));
  });
});

describeLive("E2E: Models", () => {
  it("lists available models", async () => {
    const models = await makeClient().models.list();
    const modelIds = models.data.map((m: any) => m.id);
    expect(modelIds).toContain("gpt-4o-mini");
    expect(modelIds).toContain("mock-b-only");
  });
});

describeLive("E2E: Cost Tracking", () => {
  it("tracks cumulative cost on client", async () => {
    const client = makeClient();
    expect(client.currentCost).toBe(0);
    const r = await client.chat.completions.create({ model: MODEL, messages: user(`cost test ${marker()}`), max_tokens: 5 });
    expect(client.currentCost).toBeCloseTo(r.agentcc!.cost as number, 10);
    expect(client.currentCost).toBeGreaterThan(0);
  });
});

describeLive("E2E: Dry Run", () => {
  it("inspects request without sending", () => {
    const result = makeClient().chat.completions.dryRun({ model: MODEL, messages: user("dry run test"), temperature: 0.7, max_tokens: 100 });
    expect(result.url).toBe(`${live.base}/v1/chat/completions`);
    expect(result.method).toBe("POST");
    expect(result.headers["Authorization"]).toContain("Bearer ");
    expect((result.body as any).model).toBe(MODEL);
    expect((result.body as any).temperature).toBe(0.7);
    expect((result.body as any).max_tokens).toBe(100);
  });
});

const colorSchema = {
  type: "object",
  properties: { color: { type: "string" }, hex: { type: "string" } },
  required: ["color", "hex"],
  additionalProperties: false,
};

describeLive("E2E: Validate Response", () => {
  it("validates real structured output against schema", async () => {
    const m = marker();
    const response = await makeClient().chat.completions.create({
      model: MODEL,
      messages: user(`[[mock:color-json]] Return a JSON object with "color" and "hex" for blue. ${m}`),
      response_format: { type: "json_schema", json_schema: { name: "color_info", strict: true, schema: colorSchema } } as any,
      max_tokens: 50,
      temperature: 0,
    });
    const content = response.choices[0].message.content!;
    const validation = validateJsonResponse(content, colorSchema as any);
    expect(validation.valid).toBe(true);
    expect(validation.errors).toHaveLength(0);
    expect(JSON.parse(content)).toEqual({ color: "blue", hex: "#0000ff" });
    const [up] = await mockRecords(m);
    expect((up.body as any).response_format.json_schema.name).toBe("color_info");
  });

  it("toResponseFormat creates correct format", () => {
    const rf = toResponseFormat({ type: "object", properties: { name: { type: "string" } } }, "person");
    expect((rf as any).type).toBe("json_schema");
    expect((rf as any).json_schema.name).toBe("person");
    expect((rf as any).json_schema.strict).toBe(true);
  });
});

describeLive("E2E: Auto JSON Schema Validation", () => {
  it("validates response automatically when flag is enabled", async () => {
    const response = await makeClient({ enableJsonSchemaValidation: true }).chat.completions.create({
      model: MODEL,
      messages: user(`[[mock:count-json]] Return JSON: {"count": 42} ${marker()}`),
      response_format: {
        type: "json_schema",
        json_schema: { name: "counter", strict: true, schema: { type: "object", properties: { count: { type: "number" } }, required: ["count"], additionalProperties: false } },
      } as any,
      max_tokens: 20,
      temperature: 0,
    });
    expect(JSON.parse(response.choices[0].message.content!).count).toBe(42);
  });
});

describeLive("E2E: Health Check Utilities", () => {
  it("checkValidKey returns valid for a good key", async () => {
    expect((await checkValidKey({ apiKey: live.key, baseUrl: live.base })).valid).toBe(true);
    expect((await checkValidKey({ apiKey: "not-a-minted-gateway-key", baseUrl: live.base })).valid).toBe(false);
  });

  it("healthCheck returns healthy", async () => {
    const result = await healthCheck({ model: MODEL, apiKey: live.key, baseUrl: live.base });
    record("e2e_health_check", result);
    expect(result.healthy).toBe(true);
    // 1.0.1 asserted > 0. healthCheck times with Date.now() (millisecond steps) and the mock
    // answers on loopback in under a millisecond, so 0 is a correct reading (one of three
    // repeated runs measured 0). The latency value itself is evidence, not a claim.
    expect(result.latencyMs).toBeGreaterThanOrEqual(0);
  });
});

describeLive("E2E: withOptions", () => {
  it("creates a derived client with different config", async () => {
    const m = marker();
    const tapped = new AgentCC({ apiKey: live.key, baseUrl: live.tap, maxRetries: 0 });
    const response = await tapped.withOptions({ defaultHeaders: { "X-Custom-E2E": "test" } }).chat.completions.create({ model: MODEL, messages: user(`derived test ${m}`), max_tokens: 5 });
    expect(response).toBeDefined();
    const [sent] = await tapRecords(m);
    expect(sent.headers["x-custom-e2e"]).toBe("test");
  });
});

describeLive("E2E: Client healthCheck", () => {
  it("client.healthCheck() returns true for running gateway", async () => {
    expect(await makeClient().healthCheck()).toBe(true);
  });
});

describeLive("E2E: Error Handling", () => {
  it("throws on invalid model", async () => {
    await expect(makeClient().chat.completions.create({ model: "nonexistent-model-xyz-123", messages: user("test"), max_tokens: 5 })).rejects.toThrow();
  });
});
