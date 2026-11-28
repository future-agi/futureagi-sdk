// Against a real Agent Command Center gateway with a real provider, no mocks. Skipped unless
// FI_GATEWAY_URL and FI_GATEWAY_API_KEY (an sk-agentcc-* key) are set; FI_GATEWAY_TEST_MODEL
// picks the chat model (default gpt-4o-mini). The Python suite (python/tests/gateway/
// test_gateway_live.py) covers the gateway's features; this one proves the TypeScript transport
// on the paths that differ by surface: JSON, SSE, sessions, callbacks and typed errors.

import { AuthenticationError, Gateway, MetricsCallback } from "../index";

const configured = Boolean(process.env.FI_GATEWAY_URL && process.env.FI_GATEWAY_API_KEY);
const live = configured ? describe : describe.skip;
const MODEL = process.env.FI_GATEWAY_TEST_MODEL || "gpt-4o-mini";
const ASK = { model: MODEL, messages: [{ role: "user" as const, content: "Reply with the single word: pong" }], max_tokens: 16 };

live("gateway (live)", () => {
  jest.setTimeout(60_000);

  test("health, models and a chat completion with gateway metadata", async () => {
    const gw = new Gateway();
    expect(await gw.healthCheck()).toBe(true);
    expect((await gw.models.list()).data.length).toBeGreaterThan(0);
    const reply = await gw.chat.completions.create(ASK);
    expect(reply.choices[0].message.content).toBeTruthy();
    expect(reply.agentcc?.requestId).not.toBe("unknown");
    expect(reply.usage?.total_tokens).toBeGreaterThan(0);
  });

  test("a stream yields text, a final completion, and reaches the callbacks and the session", async () => {
    const metrics = new MetricsCallback();
    const scoped = new Gateway({ callbacks: [metrics] }).session({ name: "sdk-ts-live" });
    const stream = await scoped.client.chat.completions.stream(ASK);
    let text = "";
    for await (const piece of stream.textStream()) text += piece;
    expect(text.length).toBeGreaterThan(0);
    expect(stream.getFinalCompletion().choices[0].message.content).toBe(text);
    expect(scoped.session.requestCount).toBe(1);
    expect(metrics.getMetrics().requestCount).toBe(1);
  });

  test("a rejected key is an AuthenticationError carrying the gateway's message", async () => {
    const gw = new Gateway({ apiKey: "sk-agentcc-not-a-real-key", maxRetries: 0 });
    const error = await gw.chat.completions.create(ASK).catch((e) => e);
    expect(error).toBeInstanceOf(AuthenticationError);
    expect(error.message).not.toMatch(/^Request failed with status/);
  });
});
