/**
 * @jest-environment ./tests/jsdom-with-fetch.environment.cjs
 */
/**
 * React hooks tests using manual renderHook with React.createElement
 * (no @testing-library/react needed, just React + jsdom)
 */
import { describe, it, expect, jest, beforeEach } from "@jest/globals";
import React from "react";

// We can't use the hooks directly outside React components,
// so we test the underlying logic and exports.
// The hooks themselves are thin wrappers around useState/useCallback + AgentCC client.

import { AgentCC } from "../../src/index.js";

describe("useAgentCCChat logic", () => {
  function makeMockClient(content = "Hello!") {
    const mockFetch = jest.fn<any>().mockImplementation(async () => {
      // Simulate SSE stream response
      const encoder = new TextEncoder();
      const chunk = JSON.stringify({
        choices: [{ index: 0, delta: { content }, finish_reason: null }],
      });
      const done = JSON.stringify({
        choices: [{ index: 0, delta: {}, finish_reason: "stop" }],
      });
      const sseData = `data: ${chunk}\n\ndata: ${done}\n\ndata: [DONE]\n\n`;

      return new Response(encoder.encode(sseData), {
        status: 200,
        headers: { "content-type": "text/event-stream" },
      });
    });

    return new AgentCC({ apiKey: "sk-test", fetch: mockFetch, dangerouslyAllowBrowser: true });
  }

  it("client.chat.completions.stream can be called", async () => {
    const client = makeMockClient("Hi");
    const mgr = await client.chat.completions.stream({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hello" }],
    });

    const chunks: string[] = [];
    for await (const chunk of mgr) {
      if (chunk.choices?.[0]?.delta?.content) {
        chunks.push(chunk.choices[0].delta.content);
      }
    }
    expect(chunks).toContain("Hi");
  });

  it("client.chat.completions.create works for completion hook", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "chatcmpl-1",
          choices: [
            { message: { role: "assistant", content: "Completed!" }, finish_reason: "stop" },
          ],
          usage: { prompt_tokens: 5, completion_tokens: 2, total_tokens: 7 },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch, dangerouslyAllowBrowser: true });
    const result = await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "test" }],
    });

    expect(result.choices[0].message.content).toBe("Completed!");
  });

  it("client.chat.completions.create works for object hook with json_schema", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "chatcmpl-1",
          choices: [
            {
              message: {
                role: "assistant",
                content: '{"temp": 72, "condition": "sunny"}',
              },
              finish_reason: "stop",
            },
          ],
          usage: { prompt_tokens: 10, completion_tokens: 8, total_tokens: 18 },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );

    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch, dangerouslyAllowBrowser: true });
    const result = await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Weather?" }],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "weather",
          strict: true,
          schema: {
            type: "object",
            properties: { temp: { type: "number" }, condition: { type: "string" } },
          },
        },
      } as any,
    });

    const content = result.choices[0].message.content;
    expect(content).toBeDefined();
    const parsed = JSON.parse(content!);
    expect(parsed.temp).toBe(72);
    expect(parsed.condition).toBe("sunny");
  });
});

describe("React module exports", () => {
  it("AgentCCProvider is a React component function", async () => {
    const mod = await import("../../src/react/provider.js");
    expect(typeof mod.AgentCCProvider).toBe("function");
  });

  it("useAgentCCClient is a hook function", async () => {
    const mod = await import("../../src/react/provider.js");
    expect(typeof mod.useAgentCCClient).toBe("function");
  });

  it("useAgentCCChat is a hook function", async () => {
    const mod = await import("../../src/react/use-chat.js");
    expect(typeof mod.useAgentCCChat).toBe("function");
    expect(typeof mod.useAgentCCChatWithClient).toBe("function");
  });

  it("useAgentCCCompletion is a hook function", async () => {
    const mod = await import("../../src/react/use-completion.js");
    expect(typeof mod.useAgentCCCompletion).toBe("function");
    expect(typeof mod.useAgentCCCompletionWithClient).toBe("function");
  });

  it("useAgentCCObject is a hook function", async () => {
    const mod = await import("../../src/react/use-object.js");
    expect(typeof mod.useAgentCCObject).toBe("function");
    expect(typeof mod.useAgentCCObjectWithClient).toBe("function");
  });
});
