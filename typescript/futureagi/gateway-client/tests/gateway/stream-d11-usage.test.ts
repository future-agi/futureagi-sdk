/**
 * D-11: the final usage is the last usage the stream carried (1.0.1 read the
 * last chunk's, so a chunk after the usage chunk erased it). Also kept from
 * 1.0.1: usage comes from the finish chunk with no stream_options ever sent.
 */
import { describe, it, expect } from "@jest/globals";
import { ChunkAccumulator } from "../../src/index.js";
import type { StreamEvent } from "../../src/index.js";
import { chunk, clientFor, drain, PARAMS } from "./_stream-cases.js";
import type { Reply } from "./_stream-cases.js";

describe("D-11 final usage from the last chunk that carries it", () => {
  it("a chunk after the usage chunk no longer erases it", () => {
    const acc = new ChunkAccumulator();
    acc.add(JSON.parse(chunk({ choices: [{ index: 0, delta: { content: "Hi" }, finish_reason: null }] })));
    acc.add(JSON.parse(chunk({ choices: [], usage: { prompt_tokens: 3, completion_tokens: 1, total_tokens: 4 } })));
    acc.add(JSON.parse(chunk({ choices: [{ index: 0, delta: {}, finish_reason: "stop" }] })));
    expect(acc.getFinalCompletion().usage).toEqual({ prompt_tokens: 3, completion_tokens: 1, total_tokens: 4 });
  });

  it("the latest usage wins when several chunks carry one", () => {
    const acc = new ChunkAccumulator();
    acc.add(JSON.parse(chunk({ usage: { prompt_tokens: 1, completion_tokens: 0, total_tokens: 1 } })));
    acc.add(JSON.parse(chunk({ usage: { prompt_tokens: 1, completion_tokens: 2, total_tokens: 3 } })));
    expect(acc.getFinalCompletion().usage?.total_tokens).toBe(3);
  });

  it("no usage anywhere: usage is undefined, as before", () => {
    const acc = new ChunkAccumulator();
    acc.add(JSON.parse(chunk({ choices: [{ index: 0, delta: { content: "Hi" }, finish_reason: "stop" }] })));
    expect(acc.getFinalCompletion().usage).toBeUndefined();
  });

  it("usage comes from the finish chunk the gateway sends, and no stream_options is ever added", async () => {
    const usage = { prompt_tokens: 5, completion_tokens: 2, total_tokens: 7 };
    const frames = [
      chunk({ choices: [{ index: 0, delta: { role: "assistant", content: "Hi" }, finish_reason: null }] }),
      chunk({ choices: [{ index: 0, delta: {}, finish_reason: "stop" }], usage }),
      "[DONE]",
    ];
    const reply: Reply = { status: 200, headers: { "content-type": "text/event-stream" }, sse: frames };
    const { client, sent } = clientFor(reply);
    const manager = await client.chat.completions.stream(PARAMS);
    const events = (await drain<StreamEvent>(manager.events())).items;
    expect(events.filter((e) => e.type === "usage")).toEqual([{ type: "usage", usage }]);
    expect(manager.getFinalCompletion().usage).toEqual(usage);
    const c2 = clientFor(reply);
    await drain(await c2.client.chat.completions.create({ ...PARAMS, stream: true }));
    for (const request of [...sent, ...c2.sent]) {
      expect(request).not.toHaveProperty("stream_options");
      expect(request.stream).toBe(true);
    }
  });
});
