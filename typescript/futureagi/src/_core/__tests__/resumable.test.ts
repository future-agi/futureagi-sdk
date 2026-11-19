/**
 * Resumable streams: resume with no loss or duplication (durable ids and live deltas),
 * the idle timeout, the reconnect bound, the long-poll fallback, terminal statuses, abort.
 */
import { CoreServerError, dropped, json, makeCore, Script, sse } from "../__fixtures__/platform";
import { DeltaReconciler } from "../deltas";
import { AuthenticationError, NotFoundError, PermissionDeniedError, StreamInterruptedError } from "../errors";
import { resumableEvents, type ResumableOptions } from "../resumable";

const DONE: [undefined, string, unknown] = [undefined, "done", { type: "done" }];
const status = (seq: number, value: string): [string, string, unknown] => [String(seq), "status", { seq, status: value }];
const frameText = (frames: [string | undefined, string, unknown][]): string =>
  frames.map(([id, event, data]) => `${id !== undefined ? `id: ${id}\n` : ""}event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join("");
const fresh = (frames: [string | undefined, string, unknown][]) => () => sse(frames);
const drop = (frames: [string | undefined, string, unknown][]) => () => dropped(frameText(frames));

async function collect(script: Script, options: ResumableOptions = {}): Promise<Record<string, unknown>[]> {
  const out: Record<string, unknown>[] = [];
  const core = makeCore(script);
  const sleeps: number[] = [];
  for await (const e of resumableEvents(core, "runs.events", { path: { id: "c1" } }, (e) => e.type === "done", {
    sleep: async (ms) => void sleeps.push(ms),
    random: () => 0.5,
    ...options,
  })) {
    out.push(e as Record<string, unknown>);
  }
  return out;
}

describe("resumable streams", () => {
  it("resume after a drop loses nothing and repeats nothing", async () => {
    const script = new Script([drop([status(1, "a"), status(2, "b")]), fresh([status(2, "b"), status(3, "c"), DONE])]);
    const events = await collect(script);
    expect(events.map((e) => e.seq)).toEqual([1, 2, 3, undefined]);
    expect(script.requests[0]!.headers.get("last-event-id")).toBeNull();
    expect(script.requests[1]!.headers.get("last-event-id")).toBe("2");
    expect(script.requests.every((r) => r.headers.get("accept") === "text/event-stream")).toBe(true);
  });

  it("starts after the caller's lastEventId", async () => {
    const script = new Script([fresh([status(8, "x"), DONE])]);
    await collect(script, { lastEventId: "7" });
    expect(script.requests[0]!.headers.get("last-event-id")).toBe("7");
  });

  it("reconciles live deltas across a reconnect", async () => {
    const script = new Script([
      drop([[undefined, "message_delta", { messageId: "m1", delta: "Hel" }]]),
      fresh([
        [undefined, "message_delta", { messageId: "m1", delta: "Hello" }],
        [undefined, "message_delta", { messageId: "m1", delta: " world" }],
        DONE,
      ]),
    ]);
    const events = await collect(script);
    expect(
      events
        .filter((e) => e.type === "message_delta")
        .map((e) => e.delta)
        .join(""),
    ).toBe("Hello world");
  });

  it("a regenerated message is a message_reset; a rolling tail skips its overlap", () => {
    const r = new DeltaReconciler();
    r.push({ type: "message_delta", messageId: "m", delta: "draft" });
    r.newConnection();
    expect(r.push({ type: "message_delta", messageId: "m", delta: "final" })).toEqual([
      { type: "message_reset", messageId: "m", text: "final" },
    ]);
    r.push({ type: "activity_output", stepId: "s", stream: "stdout", chunk: "abcdef" });
    r.newConnection();
    expect(r.push({ type: "activity_output", stepId: "s", stream: "stdout", chunk: "defgh" })[0]).toMatchObject({ chunk: "gh" });
  });

  it("a stalled stream times out on its idle timeout and reconnects", async () => {
    let calls = 0;
    const script = new Script([
      () => {
        calls += 1;
        return new Response(
          new ReadableStream({
            start(c) {
              c.enqueue(new TextEncoder().encode(frameText([status(1, "a")])));
            },
          }),
          { status: 200 },
        );
      },
      fresh([status(2, "b"), DONE]),
    ]);
    const events = await collect(script, { idleTimeoutMs: 30, transport: "sse" });
    expect(calls).toBe(1);
    expect(events.map((e) => e.seq)).toEqual([1, 2, undefined]);
    expect(script.requests[1]!.headers.get("last-event-id")).toBe("1");
  });

  it("the reconnect bound throws StreamInterruptedError with the last sequence", async () => {
    const script = new Script([drop([status(4, "a")]), drop([]), drop([]), drop([])]);
    const err = await collect(script, { maxConsecutiveFailures: 3, transport: "sse" }).then(undefined, (e: unknown) => e);
    expect(err).toBeInstanceOf(StreamInterruptedError);
    expect((err as StreamInterruptedError).lastSequence).toBe("4");
    expect(script.requests).toHaveLength(4);
    const many = new Script(Array.from({ length: 20 }, (_, n) => drop([status(n + 1, "x")])));
    const total = await collect(many, { maxReconnects: 5, transport: "sse" }).then(undefined, (e: unknown) => e);
    expect((total as StreamInterruptedError).lastSequence).toBe("6");
  });

  it("auto switches to long-poll after two silent SSE attempts", async () => {
    const empty = () => new Response("", { status: 200, headers: { "content-type": "text/event-stream" } });
    const script = new Script([empty, empty, fresh([status(1, "a"), DONE])]);
    const events = await collect(script);
    expect(events.map((e) => e.seq)).toEqual([1, undefined]);
    expect(script.requests.map((r) => new URL(r.url).searchParams.get("transport"))).toEqual([null, null, "poll"]);
    expect(new URL(script.requests[2]!.url).searchParams.get("wait")).toBe("25000");
  });

  it.each([
    [401, AuthenticationError],
    [403, PermissionDeniedError],
    [404, NotFoundError],
  ] as const)("a %i on reconnect is terminal", async (code, cls) => {
    const script = new Script([drop([status(1, "a")]), json(code, { code: "nope" })]);
    await expect(collect(script)).rejects.toBeInstanceOf(cls);
    expect(script.requests).toHaveLength(2);
  });

  it("yields unknown events and never retries a stream in the transport", async () => {
    const events = await collect(new Script([fresh([["1", "hologram", { a: 1 }], DONE])]));
    expect(events[0]).toEqual({ type: "unknown", eventType: "hologram", raw: { a: 1 } });
    const script = new Script([json(503)]);
    await expect(makeCore(script).openStream("runs.events", { path: { id: "c1" } })).rejects.toBeInstanceOf(CoreServerError);
    expect(script.requests).toHaveLength(1);
  });

  it("an abort ends the iteration with the signal's reason", async () => {
    const controller = new AbortController();
    const hang = () => new Response(new ReadableStream({ start() {} }), { status: 200 });
    setTimeout(() => controller.abort(new Error("stop now")), 20);
    await expect(collect(new Script([hang]), { signal: controller.signal })).rejects.toThrow("stop now");
  });
});
