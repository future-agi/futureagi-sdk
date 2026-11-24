import {
  tokenCounter,
  getMaxTokens,
  getMaxOutputTokens,
  completionCost,
  completionCostFromResponse,
  trimMessages,
  getContextWindowFallback,
  getContentPolicyFallback,
  isPromptCachingValid,
} from "../tokens";
import type { ChatMessage } from "../tokens";

describe("tokenCounter", () => {
  it("returns 0 for no input", () => {
    expect(tokenCounter("gpt-4o")).toBe(0);
  });

  it("estimates tokens for raw text", () => {
    const count = tokenCounter("gpt-4o", { text: "Hello, world!" });
    expect(count).toBeGreaterThan(0);
  });

  it("estimates tokens for messages", () => {
    const messages: ChatMessage[] = [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: "What is 2 + 2?" },
    ];
    const count = tokenCounter("gpt-4o", { messages });
    expect(count).toBeGreaterThan(0);
    // Should include overhead (2 messages * 4 + 2 = 10 overhead)
    expect(count).toBeGreaterThanOrEqual(10);
  });

  it("handles multi-part content", () => {
    const messages: ChatMessage[] = [
      {
        role: "user",
        content: [
          { type: "text", text: "Describe this:" },
          { type: "image_url", image_url: { url: "http://example.com/img" } },
        ],
      },
    ];
    const count = tokenCounter("gpt-4o", { messages });
    expect(count).toBeGreaterThan(0);
  });

  it("handles messages with tool_calls", () => {
    const messages: ChatMessage[] = [
      {
        role: "assistant",
        tool_calls: [
          { id: "call_1", function: { name: "get_weather", arguments: '{"city":"NYC"}' } },
        ],
      },
    ];
    const count = tokenCounter("gpt-4o", { messages });
    expect(count).toBeGreaterThan(0);
  });
});

describe("getMaxTokens / getMaxOutputTokens", () => {
  it("returns context window for known models", () => {
    expect(getMaxTokens("gpt-4o")).toBe(128000);
    expect(getMaxTokens("gemini-2.0-flash")).toBe(1048576);
  });

  it("returns null for unknown models", () => {
    expect(getMaxTokens("unknown-model")).toBeNull();
  });

  it("returns max output tokens", () => {
    expect(getMaxOutputTokens("gpt-4o")).toBe(16384);
    expect(getMaxOutputTokens("claude-sonnet-4-20250514")).toBe(64000);
  });
});

describe("completionCost", () => {
  it("estimates cost for known model", () => {
    const cost = completionCost("gpt-4o", 1000, 500);
    expect(cost).not.toBeNull();
    // 1000 * 2.5e-6 + 500 * 10e-6 = 0.0025 + 0.005 = 0.0075
    expect(cost!).toBeCloseTo(0.0075, 6);
  });

  it("returns null for unknown model", () => {
    expect(completionCost("unknown-model", 100, 50)).toBeNull();
  });

  it("handles zero tokens", () => {
    expect(completionCost("gpt-4o", 0, 0)).toBe(0);
  });
});

describe("completionCostFromResponse", () => {
  it("uses gateway-reported cost if available", () => {
    const cost = completionCostFromResponse({
      model: "gpt-4o",
      usage: { prompt_tokens: 100, completion_tokens: 50 },
      agentcc: { cost: 0.0042 },
    });
    expect(cost).toBe(0.0042);
  });

  it("falls back to local estimation", () => {
    const cost = completionCostFromResponse({
      model: "gpt-4o",
      usage: { prompt_tokens: 1000, completion_tokens: 500 },
    });
    expect(cost).not.toBeNull();
    expect(cost!).toBeCloseTo(0.0075, 6);
  });

  it("returns null if no usage data", () => {
    expect(completionCostFromResponse({})).toBeNull();
  });
});

describe("trimMessages", () => {
  const makeLong = (n: number): string => "x".repeat(n);

  it("returns all messages if they fit", () => {
    const msgs: ChatMessage[] = [
      { role: "user", content: "short" },
    ];
    const trimmed = trimMessages(msgs, "gpt-4o");
    expect(trimmed).toHaveLength(1);
  });

  it("preserves system messages", () => {
    const msgs: ChatMessage[] = [
      { role: "system", content: "You are helpful." },
      { role: "user", content: makeLong(2000) },
      { role: "assistant", content: makeLong(2000) },
      { role: "user", content: "latest" },
    ];
    const trimmed = trimMessages(msgs, "gpt-4o", { maxTokens: 200 });
    expect(trimmed[0].role).toBe("system");
    // Should always include system message
    const roles = trimmed.map((m) => m.role);
    expect(roles).toContain("system");
  });

  it("removes oldest non-system messages first", () => {
    const msgs: ChatMessage[] = [
      { role: "user", content: makeLong(400) },
      { role: "assistant", content: makeLong(400) },
      { role: "user", content: "latest message" },
    ];
    const trimmed = trimMessages(msgs, "gpt-4o", { maxTokens: 100 });
    // The latest message should be kept if possible
    if (trimmed.length > 0) {
      expect(trimmed[trimmed.length - 1].content).toBe("latest message");
    }
  });

  it("throws for unknown model without maxTokens", () => {
    expect(() =>
      trimMessages([{ role: "user", content: "hi" }], "unknown-model-xyz"),
    ).toThrow("Unknown model");
  });

  it("works with explicit maxTokens", () => {
    const msgs: ChatMessage[] = [{ role: "user", content: "hello" }];
    const trimmed = trimMessages(msgs, "unknown-model-xyz", {
      maxTokens: 10000,
    });
    expect(trimmed).toHaveLength(1);
  });

  it("returns new array (no mutation)", () => {
    const msgs: ChatMessage[] = [{ role: "user", content: "hi" }];
    const trimmed = trimMessages(msgs, "gpt-4o");
    expect(trimmed).not.toBe(msgs);
  });
});

describe("fallbacks", () => {
  it("getContextWindowFallback returns larger model", () => {
    expect(getContextWindowFallback("gpt-4")).toBe("gpt-4-turbo");
    expect(getContextWindowFallback("gpt-4-turbo")).toBe("gpt-4o");
  });

  it("getContextWindowFallback returns null for unknown", () => {
    expect(getContextWindowFallback("gemini-2.0-flash")).toBeNull();
  });

  it("getContentPolicyFallback returns less restrictive model", () => {
    expect(getContentPolicyFallback("gpt-4o")).toBe("gpt-4-turbo");
  });

  it("getContentPolicyFallback returns null for unknown", () => {
    expect(getContentPolicyFallback("gpt-3.5-turbo")).toBeNull();
  });
});

describe("isPromptCachingValid", () => {
  it("detects Anthropic cache_control", () => {
    const msgs: ChatMessage[] = [
      { role: "user", content: "hi", cache_control: { type: "ephemeral" } },
    ];
    const [eligible, reason] = isPromptCachingValid(
      "claude-3-5-sonnet-20241022",
      msgs,
    );
    expect(eligible).toBe(true);
    expect(reason).toContain("Anthropic");
  });

  it("detects cache_control in content parts", () => {
    const msgs: ChatMessage[] = [
      {
        role: "user",
        content: [
          { type: "text", text: "hi", cache_control: { type: "ephemeral" } },
        ],
      },
    ];
    const [eligible] = isPromptCachingValid("claude-3-5-sonnet-20241022", msgs);
    expect(eligible).toBe(true);
  });

  it("detects long system prompts for OpenAI models", () => {
    const longSystem = "x".repeat(5000); // ~1250 tokens at 4 chars/token
    const msgs: ChatMessage[] = [{ role: "system", content: longSystem }];
    const [eligible, reason] = isPromptCachingValid("gpt-4o", msgs);
    expect(eligible).toBe(true);
    expect(reason).toContain("OpenAI");
  });

  it("returns false when no caching indicators", () => {
    const msgs: ChatMessage[] = [{ role: "user", content: "Hello" }];
    const [eligible] = isPromptCachingValid("gpt-4o", msgs);
    expect(eligible).toBe(false);
  });
});
