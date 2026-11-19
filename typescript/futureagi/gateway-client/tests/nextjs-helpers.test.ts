import { describe, it, expect, beforeEach } from "@jest/globals";
import {
  createAgentCCClient,
  resetAgentCCClient,
  streamResponse,
} from "../src/nextjs.js";
import { AgentCC } from "../src/client.js";
import { StreamManager, Stream } from "../src/streaming.js";
import type { ChatCompletionChunk } from "../src/types/chat/chat-completion-chunk.js";

describe("createAgentCCClient", () => {
  beforeEach(() => {
    resetAgentCCClient();
  });

  it("returns a AgentCC instance", () => {
    const client = createAgentCCClient({ apiKey: "sk-test" });
    expect(client).toBeInstanceOf(AgentCC);
  });

  it("returns the same singleton", () => {
    const a = createAgentCCClient({ apiKey: "sk-test" });
    const b = createAgentCCClient({ apiKey: "sk-different" });
    expect(a).toBe(b);
  });

  it("reset allows new instance", () => {
    const a = createAgentCCClient({ apiKey: "sk-test" });
    resetAgentCCClient();
    const b = createAgentCCClient({ apiKey: "sk-test2" });
    expect(a).not.toBe(b);
  });
});

describe("streamResponse", () => {
  function makeChunk(content: string): ChatCompletionChunk {
    return {
      id: "chatcmpl-test",
      object: "chat.completion.chunk",
      created: 1700000000,
      model: "gpt-4o",
      choices: [{ index: 0, delta: { content }, finish_reason: null }],
    };
  }

  function makeDoneChunk(): ChatCompletionChunk {
    return {
      id: "chatcmpl-test",
      object: "chat.completion.chunk",
      created: 1700000000,
      model: "gpt-4o",
      choices: [{ index: 0, delta: {}, finish_reason: "stop" }],
    };
  }

  function mockStream(chunks: ChatCompletionChunk[]): Stream {
    const encoder = new TextEncoder();
    const sseData =
      chunks.map((c) => `data: ${JSON.stringify(c)}\n\n`).join("") +
      "data: [DONE]\n\n";

    const readable = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode(sseData));
        controller.close();
      },
    });

    const response = new Response(readable, {
      headers: { "content-type": "text/event-stream" },
    });
    return new Stream(response);
  }

  it("returns a Response with SSE content type", async () => {
    const stream = mockStream([makeChunk("Hello"), makeDoneChunk()]);
    const mgr = new StreamManager(stream);
    const res = streamResponse(mgr);

    expect(res).toBeInstanceOf(Response);
    expect(res.headers.get("Content-Type")).toBe("text/event-stream");
    expect(res.headers.get("Cache-Control")).toBe("no-cache");
  });

  it("produces SSE-formatted body", async () => {
    const stream = mockStream([makeChunk("Hi"), makeDoneChunk()]);
    const mgr = new StreamManager(stream);
    const res = streamResponse(mgr);

    const body = await res.text();
    expect(body).toContain("data: ");
    expect(body).toContain("[DONE]");
  });

  it("includes custom headers", async () => {
    const stream = mockStream([makeDoneChunk()]);
    const mgr = new StreamManager(stream);
    const res = streamResponse(mgr, {
      headers: { "X-Custom": "value" },
    });

    expect(res.headers.get("X-Custom")).toBe("value");
  });
});
