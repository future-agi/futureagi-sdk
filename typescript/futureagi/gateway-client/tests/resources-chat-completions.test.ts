import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../src/client.js";

function mockJsonResponse(data: Record<string, unknown>, status = 200) {
  return jest.fn<any>().mockResolvedValue(
    new Response(JSON.stringify(data), {
      status,
      headers: { "content-type": "application/json" },
    }),
  );
}

function completionPayload(content = "Hello!") {
  return {
    id: "chatcmpl-abc",
    object: "chat.completion",
    created: 1700000000,
    model: "gpt-4o",
    choices: [
      {
        index: 0,
        message: { role: "assistant", content },
        finish_reason: "stop",
      },
    ],
    usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
  };
}

describe("chat.completions resource", () => {
  it("create() sends POST to /v1/chat/completions", async () => {
    const mockFetch = mockJsonResponse(completionPayload());
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hi" }],
    });

    expect(result.choices[0].message.content).toBe("Hello!");
    expect(result.agentcc).toBeDefined();
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/chat/completions");
    expect(init.method).toBe("POST");
  });

  it("create() passes model and messages in body", async () => {
    const mockFetch = mockJsonResponse(completionPayload());
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    await client.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: "You are helpful." },
        { role: "user", content: "Hello" },
      ],
      temperature: 0.5,
      max_tokens: 100,
    });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.model).toBe("gpt-4o-mini");
    expect(body.messages).toHaveLength(2);
    expect(body.temperature).toBe(0.5);
    expect(body.max_tokens).toBe(100);
  });

  it("create() extracts agentcc params to headers", async () => {
    const mockFetch = mockJsonResponse(completionPayload());
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hi" }],
      session_id: "sess-123",
    } as any);

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.session_id).toBeUndefined(); // extracted to header
    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers["x-agentcc-session-id"]).toBe("sess-123");
  });

  it("create() passes extra_headers", async () => {
    const mockFetch = mockJsonResponse(completionPayload());
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hi" }],
      extra_headers: { "X-Custom": "value" },
    });

    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers["X-Custom"]).toBe("value");
  });

  it("create() passes extra_body", async () => {
    const mockFetch = mockJsonResponse(completionPayload());
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hi" }],
      extra_body: { custom_param: "custom_value" },
    });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.custom_param).toBe("custom_value");
  });

  it("create() with stream returns a Stream", async () => {
    const sseData =
      `data: ${JSON.stringify({ choices: [{ delta: { content: "Hi" } }] })}\n\n` +
      "data: [DONE]\n\n";
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(sseData, {
        status: 200,
        headers: { "content-type": "text/event-stream" },
      }),
    );
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const stream = await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hi" }],
      stream: true,
    });

    expect(stream).toBeDefined();
    // Stream should be iterable
    expect(stream[Symbol.asyncIterator]).toBeDefined();
  });

  it("stream() returns a StreamManager", async () => {
    const sseData =
      `data: ${JSON.stringify({ choices: [{ delta: { content: "Hi" } }] })}\n\n` +
      "data: [DONE]\n\n";
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(sseData, {
        status: 200,
        headers: { "content-type": "text/event-stream" },
      }),
    );
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const mgr = await client.chat.completions.stream({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hi" }],
    });

    expect(mgr).toBeDefined();
    expect(mgr[Symbol.asyncIterator]).toBeDefined();
  });

  it("dryRun() returns request details without network call", () => {
    const mockFetch = jest.fn<any>();
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch as any });

    const result = client.chat.completions.dryRun({
      model: "gpt-4o",
      messages: [{ role: "user", content: "test" }],
    });

    expect(result.method).toBe("POST");
    expect(result.url).toContain("/v1/chat/completions");
    expect(result.headers).toBeDefined();
    expect(result.body).toBeDefined();
    expect(mockFetch).not.toHaveBeenCalled();
  });
});
