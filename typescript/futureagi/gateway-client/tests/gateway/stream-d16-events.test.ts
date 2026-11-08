/**
 * D-16: StreamEvent has only the variants that fire, and `done` comes once,
 * after the body ends ([DONE] or its end), so a late error frame raises
 * before it. 1.0.1 yielded done at a "stop" / "tool_calls" chunk, so a
 * consumer that broke on done lost the gateway's late guardrail error, and a
 * stream ending on "length" yielded no done. The error is a typed
 * StreamError. Stream cases late_error_after_finish_reason and
 * guardrail_header_open (tests/fixtures/gateway/stream-cases-extra.json).
 */
import { describe, it, expect } from "@jest/globals";
import { StreamError } from "../../src/index.js";
import type { StreamEvent } from "../../src/index.js";
import { CASE, chunk, clientFor, drain, PARAMS } from "./_stream-cases.js";
import type { Reply } from "./_stream-cases.js";

describe("D-16 events: only what fires, and done after the body", () => {
  const late = CASE("late_error_after_finish_reason");

  it("late_error_after_finish_reason: events() yields content and usage, then throws StreamError before done", async () => {
    const { client } = clientFor(late);
    const { items, error } = await drain<StreamEvent>((await client.chat.completions.stream(PARAMS)).events());
    expect(items.map((e) => e.type)).toEqual(["content", "usage"]);
    expect(error).toBeInstanceOf(StreamError);
    expect((error as StreamError).code).toBe("stream_blocked");
    expect((error as StreamError).type).toBe("guardrail_error");
  });

  it("a consumer that breaks on done never misses the late error", async () => {
    const { client } = clientFor(late);
    const seen: string[] = [];
    let caught: unknown = null;
    try {
      for await (const event of (await client.chat.completions.stream(PARAMS)).events()) {
        seen.push(event.type);
        if (event.type === "done") break;
      }
    } catch (e) {
      caught = e;
    }
    expect(seen).not.toContain("done");
    expect(caught).toBeInstanceOf(StreamError);
  });

  it("done comes exactly once, last, after [DONE], with the final completion", async () => {
    const reply = CASE("guardrail_header_open");
    const { client } = clientFor(reply);
    const manager = await client.chat.completions.stream(PARAMS);
    const { items, error } = await drain<StreamEvent>(manager.events());
    expect(error).toBeNull();
    expect(items.map((e) => e.type)).toEqual(["content", "done"]);
    const done = items[1] as Extract<StreamEvent, { type: "done" }>;
    expect(done.completion.choices[0].message.content).toBe("Safe text");
    expect(manager.agentcc.guardrailTriggered).toBe(true);
    expect(manager.agentcc.guardrailName).toBe("pii");
  });

  it("a stream that ends on finish_reason length still yields done (1.0.1 yielded none)", async () => {
    const reply: Reply = {
      status: 200,
      headers: { "content-type": "text/event-stream" },
      sse: [chunk({ choices: [{ index: 0, delta: { content: "cut" }, finish_reason: "length" }] }), "[DONE]"],
    };
    const { client } = clientFor(reply);
    const { items } = await drain<StreamEvent>((await client.chat.completions.stream(PARAMS)).events());
    expect(items.map((e) => e.type)).toEqual(["content", "done"]);
  });

  it("a body that ends without [DONE] still ends with done", async () => {
    const reply: Reply = { status: 200, headers: { "content-type": "text/event-stream" }, sse: [chunk({ choices: [{ index: 0, delta: { content: "a" }, finish_reason: "stop" }] })] };
    const { client } = clientFor(reply);
    const { items } = await drain<StreamEvent>((await client.chat.completions.stream(PARAMS)).events());
    expect(items.map((e) => e.type)).toEqual(["content", "done"]);
  });

  it("StreamEvent has exactly the four types that fire", () => {
    const types: Array<StreamEvent["type"]> = ["content", "tool_call", "usage", "done"];
    // @ts-expect-error "error" was never emitted and is no longer a StreamEvent
    const gone: StreamEvent["type"] = "error";
    expect(types).toHaveLength(4);
    expect(gone).toBe("error");
  });
});
