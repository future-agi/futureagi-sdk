import { describe, it, expect } from "@jest/globals";
import { ChunkAccumulator, StreamManager, Stream } from "../src/streaming.js";
import type { ChatCompletionChunk } from "../src/types/chat/chat-completion-chunk.js";
import type { StreamEvent } from "../src/stream-events.js";

function makeContentChunk(content: string): ChatCompletionChunk {
  return {
    id: "chatcmpl-test",
    object: "chat.completion.chunk",
    created: 1700000000,
    model: "gpt-4o",
    choices: [{ index: 0, delta: { content }, finish_reason: null }],
  };
}

function makeToolCallChunk(index: number, id?: string, name?: string, args?: string): ChatCompletionChunk {
  return {
    id: "chatcmpl-test",
    object: "chat.completion.chunk",
    created: 1700000000,
    model: "gpt-4o",
    choices: [{
      index: 0,
      delta: {
        tool_calls: [{
          index,
          id,
          type: id ? "function" : undefined,
          function: { name, arguments: args },
        }],
      },
      finish_reason: null,
    }],
  };
}

function makeDoneChunk(finishReason = "stop"): ChatCompletionChunk {
  return {
    id: "chatcmpl-test",
    object: "chat.completion.chunk",
    created: 1700000000,
    model: "gpt-4o",
    choices: [{ index: 0, delta: {}, finish_reason: finishReason }],
  };
}

// Helper: create a mock Stream from chunks
function mockStream(chunks: ChatCompletionChunk[]): Stream {
  // Create a ReadableStream that yields SSE events
  const encoder = new TextEncoder();
  const sseData = chunks
    .map((c) => `data: ${JSON.stringify(c)}\n\n`)
    .join("") + "data: [DONE]\n\n";

  const readable = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(sseData));
      controller.close();
    },
  });

  // Create a mock Response
  const response = new Response(readable, {
    headers: { "content-type": "text/event-stream" },
  });
  return new Stream(response);
}

describe("StreamManager.events()", () => {
  it("yields content events", async () => {
    const stream = mockStream([
      makeContentChunk("Hello"),
      makeContentChunk(", world!"),
      makeDoneChunk(),
    ]);
    const mgr = new StreamManager(stream);
    const events: StreamEvent[] = [];
    for await (const event of mgr.events()) {
      events.push(event);
    }

    const contentEvents = events.filter((e) => e.type === "content");
    expect(contentEvents).toHaveLength(2);
    expect((contentEvents[0] as { type: "content"; text: string }).text).toBe("Hello");
    expect((contentEvents[1] as { type: "content"; text: string }).text).toBe(", world!");
  });

  it("yields done event with completion", async () => {
    const stream = mockStream([
      makeContentChunk("Hi"),
      makeDoneChunk(),
    ]);
    const mgr = new StreamManager(stream);
    const events: StreamEvent[] = [];
    for await (const event of mgr.events()) {
      events.push(event);
    }

    const doneEvents = events.filter((e) => e.type === "done");
    expect(doneEvents).toHaveLength(1);
    const done = doneEvents[0] as { type: "done"; completion: any };
    expect(done.completion.choices[0].message.content).toBe("Hi");
  });

  it("yields tool_call events", async () => {
    const stream = mockStream([
      makeToolCallChunk(0, "call_1", "get_weather", '{"ci'),
      makeToolCallChunk(0, undefined, undefined, 'ty":"NYC"}'),
      makeDoneChunk("tool_calls"),
    ]);
    const mgr = new StreamManager(stream);
    const events: StreamEvent[] = [];
    for await (const event of mgr.events()) {
      events.push(event);
    }

    const tcEvents = events.filter((e) => e.type === "tool_call");
    expect(tcEvents).toHaveLength(2);
    expect((tcEvents[0] as any).id).toBe("call_1");
    expect((tcEvents[0] as any).name).toBe("get_weather");
  });
});
