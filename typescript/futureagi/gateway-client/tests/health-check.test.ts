import { describe, it, expect, jest } from "@jest/globals";
import { checkValidKey, healthCheck } from "../src/health-check.js";

// These tests use mocked fetch to avoid real network calls

describe("checkValidKey", () => {
  it("returns valid when models endpoint succeeds", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(JSON.stringify({ data: [] }), { status: 200 }),
    );
    // We can't directly inject fetch into checkValidKey, but we can
    // override globalThis.fetch for the test
    const originalFetch = globalThis.fetch;
    globalThis.fetch = mockFetch;

    try {
      const result = await checkValidKey({ apiKey: "sk-valid" });
      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("returns invalid on 401", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(JSON.stringify({ error: { message: "Authentication failed" } }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }),
    );
    const originalFetch = globalThis.fetch;
    globalThis.fetch = mockFetch;

    try {
      const result = await checkValidKey({ apiKey: "sk-invalid" });
      expect(result.valid).toBe(false);
      expect(result.error).toContain("Invalid or unauthorized");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("returns error on network failure", async () => {
    const mockFetch = jest.fn<any>().mockRejectedValue(new TypeError("fetch failed"));
    const originalFetch = globalThis.fetch;
    globalThis.fetch = mockFetch;

    try {
      const result = await checkValidKey({ apiKey: "sk-test" });
      expect(result.valid).toBe(false);
      expect(result.error).toBeDefined();
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

describe("healthCheck", () => {
  it("returns healthy on successful completion", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "chatcmpl-1",
          choices: [{ message: { content: "p" }, finish_reason: "stop" }],
          usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
        }),
        {
          status: 200,
          headers: {
            "content-type": "application/json",
            "x-agentcc-provider": "openai",
            "x-agentcc-model": "gpt-4o",
          },
        },
      ),
    );
    const originalFetch = globalThis.fetch;
    globalThis.fetch = mockFetch;

    try {
      const result = await healthCheck({ model: "gpt-4o", apiKey: "sk-test" });
      expect(result.healthy).toBe(true);
      expect(result.latencyMs).toBeGreaterThanOrEqual(0);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("returns unhealthy on failure", async () => {
    const mockFetch = jest.fn<any>().mockRejectedValue(new TypeError("connection refused"));
    const originalFetch = globalThis.fetch;
    globalThis.fetch = mockFetch;

    try {
      const result = await healthCheck({ model: "gpt-4o", apiKey: "sk-test" });
      expect(result.healthy).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.latencyMs).toBeGreaterThanOrEqual(0);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("measures latency", async () => {
    const mockFetch = jest.fn<any>().mockImplementation(async () => {
      await new Promise((r) => setTimeout(r, 20));
      return new Response(
        JSON.stringify({
          id: "chatcmpl-1",
          choices: [{ message: { content: "p" }, finish_reason: "stop" }],
          usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    });
    const originalFetch = globalThis.fetch;
    globalThis.fetch = mockFetch;

    try {
      const result = await healthCheck({ model: "gpt-4o", apiKey: "sk-test" });
      expect(result.healthy).toBe(true);
      expect(result.latencyMs).toBeGreaterThan(10);
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
