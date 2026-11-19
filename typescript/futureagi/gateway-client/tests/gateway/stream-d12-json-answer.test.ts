/**
 * D-12: a JSON answer to a stream request (a cache hit; chat_stream.go:211-214
 * at the recorded revision) is one real chat.completion.chunk whose delta is the cached
 * message. @agentcc/client 1.0.1 yielded the completion body itself, so
 * stream readers got no text. Stream case cache_hit_json_to_stream.
 */
import { describe, it, expect } from "@jest/globals";
import { ChunkAccumulator, StreamError, Stream } from "../../src/index.js";
import type { StreamEvent } from "../../src/index.js";
import { chunkFromCompletion } from "../../src/stream-frames.js";
import { CASE, chunk, clientFor, drain, PARAMS } from "./_stream-cases.js";

describe("D-12 a JSON answer to a stream request", () => {
  const reply = CASE("cache_hit_json_to_stream");

  it("create({stream: true}) yields one chat.completion.chunk whose delta is the cached message", async () => {
    const { client } = clientFor(reply);
    const { items, error } = await drain(await client.chat.completions.create({ ...PARAMS, stream: true }));
    expect(error).toBeNull();
    expect(items).toHaveLength(1);
    const [only] = items;
    expect(only.object).toBe("chat.completion.chunk");
    expect(only.id).toBe("chatcmpl-cache");
    expect(only.choices).toEqual([{ index: 0, delta: { role: "assistant", content: "Cached hello" }, finish_reason: "stop" }]);
    expect(only.usage).toEqual({ prompt_tokens: 4, completion_tokens: 2, total_tokens: 6 });
    expect(only.agentcc?.cacheStatus).toBe("hit");
    expect(only.agentcc?.requestId).toBeNull();
    expect(only).not.toHaveProperty("message");
  });

  it("StreamManager text, final completion and events read the cached answer", async () => {
    const a = clientFor(reply);
    const manager = await a.client.chat.completions.stream(PARAMS);
    expect((await drain(manager)).error).toBeNull();
    expect(manager.getFinalText()).toBe("Cached hello");
    const final = manager.getFinalCompletion();
    expect(final.choices[0].message.content).toBe("Cached hello");
    expect(final.choices[0].finish_reason).toBe("stop");
    expect(final.usage?.total_tokens).toBe(6);

    const b = clientFor(reply);
    expect((await drain((await b.client.chat.completions.stream(PARAMS)).textStream())).items.join("")).toBe("Cached hello");

    const c = clientFor(reply);
    const events = (await drain<StreamEvent>((await c.client.chat.completions.stream(PARAMS)).events())).items;
    expect(events.map((e) => e.type)).toEqual(["content", "usage", "done"]);
  });

  it("tool calls in the cached message become indexed tool-call deltas", () => {
    const out = chunkFromCompletion({
      id: "x",
      object: "chat.completion",
      created: 2,
      model: "m",
      choices: [
        {
          index: 0,
          message: { role: "assistant", content: null, tool_calls: [{ id: "call_1", type: "function", function: { name: "f", arguments: "{}" } }, { id: "call_2", type: "function", function: { name: "g", arguments: "{\"a\":1}" } }] },
          finish_reason: "tool_calls",
        },
      ],
      system_fingerprint: "fp",
    });
    expect(out).toEqual({
      id: "x",
      object: "chat.completion.chunk",
      created: 2,
      model: "m",
      choices: [
        {
          index: 0,
          delta: {
            role: "assistant",
            content: null,
            tool_calls: [
              { index: 0, id: "call_1", type: "function", function: { name: "f", arguments: "{}" } },
              { index: 1, id: "call_2", type: "function", function: { name: "g", arguments: "{\"a\":1}" } },
            ],
          },
          finish_reason: "tool_calls",
        },
      ],
      system_fingerprint: "fp",
    });
    const acc = new ChunkAccumulator();
    acc.add(out);
    expect(acc.getFinalCompletion().choices[0].message.tool_calls?.map((t) => t.function.name)).toEqual(["f", "g"]);
  });

  it("an error body on a JSON answer raises a typed StreamError; a body that is not JSON raises StreamError", async () => {
    const err = await drain(
      await clientFor({ status: 200, headers: { "content-type": "application/json" }, json: { error: { message: "blocked", type: "guardrail_error", code: "stream_blocked", param: null } } }).client.chat.completions.create({ ...PARAMS, stream: true }),
    );
    expect(err.error).toBeInstanceOf(StreamError);
    expect((err.error as StreamError).code).toBe("stream_blocked");
    expect((err.error as StreamError).message).toBe("blocked");

    const bad = new Stream(new Response("not json", { headers: { "content-type": "application/json" } }));
    const res = await drain(bad);
    expect(res.error).toBeInstanceOf(StreamError);
    expect(res.items).toHaveLength(0);
  });

  it("a JSON answer that already is a chunk is yielded as it is", async () => {
    const stream = new Stream(new Response(chunk({ choices: [{ index: 0, delta: { content: "x" }, finish_reason: "stop" }] }), { headers: { "content-type": "application/json" } }));
    const { items } = await drain(stream);
    expect(items[0].choices[0].delta.content).toBe("x");
  });
});
