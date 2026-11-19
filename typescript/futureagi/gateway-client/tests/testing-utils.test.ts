import { describe, it, expect } from "@jest/globals";
import {
  MockAgentCC,
  mockCompletion,
  mockAgentCCMetadata,
  mockUsage,
  assertCompletionValid,
  assertCompletionHasContent,
  assertUsageValid,
  assertAgentCCMetadata,
  assertCostTracked,
} from "../src/testing.js";

describe("MockAgentCC", () => {
  it("returns queued responses", async () => {
    const mock = new MockAgentCC();
    mock.chat.completions.respondWith(mockCompletion("Hello!"));
    const result = await mock.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "hi" }],
    });
    expect(result.choices[0].message.content).toBe("Hello!");
  });

  it("records all calls", async () => {
    const mock = new MockAgentCC();
    await mock.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "first" }],
    });
    await mock.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: "second" }],
    });
    expect(mock.chat.completions.calls).toHaveLength(2);
    expect(mock.chat.completions.calls[0].params.model).toBe("gpt-4o");
    expect(mock.chat.completions.calls[1].params.model).toBe("gpt-4o-mini");
  });

  it("returns default response when no queued", async () => {
    const mock = new MockAgentCC();
    const result = await mock.chat.completions.create({
      model: "gpt-4o",
      messages: [],
    });
    expect(result.choices[0].message.content).toBe("Mock response");
  });

  it("mock embeddings works", async () => {
    const mock = new MockAgentCC();
    const result = await mock.embeddings.create({
      model: "text-embedding-3-small",
      input: "test",
    });
    expect(result.data).toHaveLength(1);
    expect(mock.embeddings.calls).toHaveLength(1);
  });
});

describe("factory functions", () => {
  it("mockCompletion creates valid completion", () => {
    const c = mockCompletion("test content", { model: "gpt-4o-mini", cost: 0.001 });
    expect(c.choices[0].message.content).toBe("test content");
    expect(c.model).toBe("gpt-4o-mini");
    expect(c.agentcc?.cost).toBe(0.001);
  });

  it("mockAgentCCMetadata creates valid metadata", () => {
    const m = mockAgentCCMetadata({ provider: "anthropic", latencyMs: 200 });
    expect(m.provider).toBe("anthropic");
    expect(m.latencyMs).toBe(200);
    expect(m.requestId).toBe("req-mock");
  });

  it("mockUsage creates valid usage", () => {
    const u = mockUsage(100, 50);
    expect(u.prompt_tokens).toBe(100);
    expect(u.completion_tokens).toBe(50);
    expect(u.total_tokens).toBe(150);
  });
});

describe("assertion helpers", () => {
  it("assertCompletionValid passes for valid completion", () => {
    expect(() => assertCompletionValid(mockCompletion("hi"))).not.toThrow();
  });

  it("assertCompletionValid fails for missing id", () => {
    const c = mockCompletion("hi");
    (c as any).id = "";
    expect(() => assertCompletionValid(c)).toThrow("missing id");
  });

  it("assertCompletionHasContent checks content", () => {
    expect(() => assertCompletionHasContent(mockCompletion("hello"), "hello")).not.toThrow();
    expect(() => assertCompletionHasContent(mockCompletion("hello"), "goodbye")).toThrow();
  });

  it("assertUsageValid passes for valid usage", () => {
    expect(() => assertUsageValid(mockUsage(10, 5))).not.toThrow();
  });

  it("assertAgentCCMetadata checks provider", () => {
    const m = mockAgentCCMetadata({ provider: "openai" });
    expect(() => assertAgentCCMetadata(m, { provider: "openai" })).not.toThrow();
    expect(() => assertAgentCCMetadata(m, { provider: "anthropic" })).toThrow();
  });

  it("assertCostTracked checks cost", () => {
    expect(() => assertCostTracked({ currentCost: 0.005 }, 0.005)).not.toThrow();
    expect(() => assertCostTracked({ currentCost: 0.005 }, 0.010)).toThrow();
  });
});
