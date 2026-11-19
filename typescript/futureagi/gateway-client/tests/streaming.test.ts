import { describe, it, expect } from "@jest/globals";
import { ChunkAccumulator } from "../src/streaming.js";
import type { ChatCompletionChunk } from "../src/types/chat/chat-completion-chunk.js";

function makeChunk(
  content: string | null,
  finishReason: string | null = null,
): ChatCompletionChunk {
  return {
    id: "chatcmpl-test",
    object: "chat.completion.chunk",
    created: 1700000000,
    model: "gpt-4o",
    choices: [
      {
        index: 0,
        delta: { content },
        finish_reason: finishReason,
      },
    ],
  };
}

describe("ChunkAccumulator", () => {
  it("accumulates text from multiple chunks", () => {
    const acc = new ChunkAccumulator();
    acc.add(makeChunk("Hello"));
    acc.add(makeChunk(", "));
    acc.add(makeChunk("world!"));
    acc.add(makeChunk(null, "stop"));

    expect(acc.getText()).toBe("Hello, world!");
  });

  it("produces a valid ChatCompletion", () => {
    const acc = new ChunkAccumulator();
    acc.add(makeChunk("Hi"));
    acc.add(makeChunk(null, "stop"));

    const completion = acc.getFinalCompletion();
    expect(completion.id).toBe("chatcmpl-test");
    expect(completion.object).toBe("chat.completion");
    expect(completion.model).toBe("gpt-4o");
    expect(completion.choices).toHaveLength(1);
    expect(completion.choices[0].message.role).toBe("assistant");
    expect(completion.choices[0].message.content).toBe("Hi");
    expect(completion.choices[0].finish_reason).toBe("stop");
  });

  it("accumulates tool calls across chunks", () => {
    const acc = new ChunkAccumulator();
    acc.add({
      id: "chatcmpl-test",
      object: "chat.completion.chunk",
      created: 1700000000,
      model: "gpt-4o",
      choices: [{
        index: 0,
        delta: {
          tool_calls: [{
            index: 0,
            id: "call_abc",
            type: "function",
            function: { name: "get_weather", arguments: '{"lo' },
          }],
        },
        finish_reason: null,
      }],
    });
    acc.add({
      id: "chatcmpl-test",
      object: "chat.completion.chunk",
      created: 1700000000,
      model: "gpt-4o",
      choices: [{
        index: 0,
        delta: {
          tool_calls: [{
            index: 0,
            function: { arguments: 'cation":"NYC"}' },
          }],
        },
        finish_reason: null,
      }],
    });
    acc.add(makeChunk(null, "tool_calls"));

    const completion = acc.getFinalCompletion();
    expect(completion.choices[0].message.tool_calls).toHaveLength(1);
    const tc = completion.choices[0].message.tool_calls![0];
    expect(tc.id).toBe("call_abc");
    expect(tc.function.name).toBe("get_weather");
    expect(tc.function.arguments).toBe('{"location":"NYC"}');
  });
});
