/**
 * D-16b and D-11b: what the gateway's trailing usage chunk must not change.
 *
 * - One usage event per stream (D-16b). The Agent Command Center gateway at
 *   the recorded revision re-sends the usage on a second trailing chunk with empty
 *   choices; @agentcc/client 1.0.1 yielded a usage event for each, so a
 *   consumer adding them up counted the tokens twice. events() now yields
 *   the usage event once, at the first chunk that carries usage; the done
 *   event's completion carries the last usage the stream carried (D-11).
 * - The final finish_reason comes from the last chunk that has choices
 *   (D-11b). 1.0.1 read the last chunk, so the trailing usage chunk (empty
 *   choices) turned "tool_calls" or "length" into "stop".
 */
import { describe, it, expect } from "@jest/globals";
import { ChunkAccumulator } from "../../src/index.js";
import type { StreamEvent } from "../../src/index.js";
import { chunk, clientFor, drain, PARAMS } from "./_stream-cases.js";
import type { Reply } from "./_stream-cases.js";

// The frames of the "usage chunk with empty choices" stream as the gateway at
// the recorded revision sends them (mock upstream): the usage chunk comes twice.
const RECORDED: string[] = [
  '{"id":"chatcmpl-sdk101","object":"chat.completion.chunk","created":1761177600,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"role":"assistant","content":"Hello"},"finish_reason":null}]}',
  '{"id":"chatcmpl-sdk101","object":"chat.completion.chunk","created":1761177600,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}',
  '{"id":"chatcmpl-sdk101","object":"chat.completion.chunk","created":1761177600,"model":"gpt-4o-mini","choices":[],"usage":{"prompt_tokens":9,"completion_tokens":1,"total_tokens":10}}',
  '{"id":"chatcmpl-sdk101","object":"chat.completion.chunk","created":1761177600,"model":"gpt-4o-mini","choices":[],"usage":{"prompt_tokens":9,"completion_tokens":1,"total_tokens":10}}',
  "[DONE]",
];
const sse = (frames: string[]): Reply => ({ status: 200, headers: { "content-type": "text/event-stream" }, sse: frames });

describe("D-16b one usage event per stream", () => {
  it("the recorded gateway stream (usage sent twice) yields one usage event, then done", async () => {
    const { client } = clientFor(sse(RECORDED));
    const manager = await client.chat.completions.stream(PARAMS);
    const { items, error } = await drain<StreamEvent>(manager.events());
    expect(error).toBeNull();
    expect(items.map((e) => e.type)).toEqual(["content", "usage", "done"]);
    const usage = { prompt_tokens: 9, completion_tokens: 1, total_tokens: 10 };
    expect(items[1]).toEqual({ type: "usage", usage });
    const done = items[2] as Extract<StreamEvent, { type: "done" }>;
    expect(done.completion.usage).toEqual(usage);
    expect(done.completion.choices[0].finish_reason).toBe("stop");
  });

  it("adding up the usage events counts the tokens once", async () => {
    const { client } = clientFor(sse(RECORDED));
    let total = 0;
    for await (const event of (await client.chat.completions.stream(PARAMS)).events()) {
      if (event.type === "usage") total += event.usage.total_tokens;
    }
    expect(total).toBe(10);
  });

  it("when a later chunk carries a different usage: still one event (the first); done and getFinalCompletion carry the last", async () => {
    const frames = [
      chunk({ choices: [{ index: 0, delta: { content: "a" }, finish_reason: "stop" }], usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 } }),
      chunk({ choices: [], usage: { prompt_tokens: 9, completion_tokens: 2, total_tokens: 11 } }),
      "[DONE]",
    ];
    const { client } = clientFor(sse(frames));
    const manager = await client.chat.completions.stream(PARAMS);
    const { items } = await drain<StreamEvent>(manager.events());
    const usages = items.filter((e) => e.type === "usage");
    expect(usages).toEqual([{ type: "usage", usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 } }]);
    const done = items[items.length - 1] as Extract<StreamEvent, { type: "done" }>;
    expect(done.completion.usage?.total_tokens).toBe(11);
    expect(manager.getFinalCompletion().usage?.total_tokens).toBe(11);
  });

  it("a stream with no usage yields no usage event", async () => {
    const { client } = clientFor(sse([chunk({ choices: [{ index: 0, delta: { content: "a" }, finish_reason: "stop" }] }), "[DONE]"]));
    const { items } = await drain<StreamEvent>((await client.chat.completions.stream(PARAMS)).events());
    expect(items.map((e) => e.type)).toEqual(["content", "done"]);
  });

  it("each events() stream counts its own usage: a second stream on the same client yields its own event", async () => {
    const first = clientFor(sse(RECORDED));
    const second = clientFor(sse(RECORDED));
    for (const { client } of [first, second]) {
      const { items } = await drain<StreamEvent>((await client.chat.completions.stream(PARAMS)).events());
      expect(items.filter((e) => e.type === "usage")).toHaveLength(1);
    }
  });
});

describe("D-11b finish_reason from the last chunk that has choices", () => {
  const toolCallsThenUsage = [
    chunk({
      choices: [{ index: 0, delta: { tool_calls: [{ index: 0, id: "call_1", type: "function", function: { name: "f", arguments: "{}" } }] }, finish_reason: null }],
    }),
    chunk({ choices: [{ index: 0, delta: {}, finish_reason: "tool_calls" }], usage: { prompt_tokens: 1, completion_tokens: 1, total_tokens: 2 } }),
    chunk({ choices: [], usage: { prompt_tokens: 9, completion_tokens: 2, total_tokens: 11 } }),
    chunk({ choices: [] }),
    "[DONE]",
  ];

  it("tool_calls survives a trailing usage chunk and a trailing empty chunk", async () => {
    const { client } = clientFor(sse(toolCallsThenUsage));
    const manager = await client.chat.completions.stream(PARAMS);
    await drain(manager);
    const final = manager.getFinalCompletion();
    expect(final.choices[0].finish_reason).toBe("tool_calls");
    expect(final.usage?.total_tokens).toBe(11);
    expect(final.choices[0].message.tool_calls?.[0]).toMatchObject({ id: "call_1", function: { name: "f", arguments: "{}" } });
  });

  it("length survives the recorded trailing usage chunks", () => {
    const acc = new ChunkAccumulator();
    const frames = RECORDED.slice(0, -1).map((f) => JSON.parse(f));
    frames[1].choices[0].finish_reason = "length";
    for (const f of frames) acc.add(f);
    expect(acc.getFinalCompletion().choices[0].finish_reason).toBe("length");
  });

  it("the done event's completion has the same finish_reason", async () => {
    const { client } = clientFor(sse(toolCallsThenUsage));
    const { items } = await drain<StreamEvent>((await client.chat.completions.stream(PARAMS)).events());
    const done = items[items.length - 1] as Extract<StreamEvent, { type: "done" }>;
    expect(done.type).toBe("done");
    expect(done.completion.choices[0].finish_reason).toBe("tool_calls");
  });

  it("no chunk with choices, or a last choice with no finish_reason: stop, as before", () => {
    const empty = new ChunkAccumulator();
    empty.add(JSON.parse(chunk({ choices: [], usage: { prompt_tokens: 1, completion_tokens: 0, total_tokens: 1 } })));
    expect(empty.getFinalCompletion().choices[0].finish_reason).toBe("stop");
    const open = new ChunkAccumulator();
    open.add(JSON.parse(chunk({ choices: [{ index: 0, delta: { content: "cut" }, finish_reason: null }] })));
    expect(open.getFinalCompletion().choices[0].finish_reason).toBe("stop");
    expect(new ChunkAccumulator().getFinalCompletion().choices[0].finish_reason).toBe("stop");
  });
});
