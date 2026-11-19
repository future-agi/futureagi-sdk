/** The SSE parser (ported from the Omega runtime tests, vitest to jest). */
import { isDeepStrictEqual } from "node:util";

import { readSse, type SseFrame, SseParser } from "../sse";

function parseAll(text: string): SseFrame[] {
  const p = new SseParser();
  return [...p.push(text), ...p.end()];
}

/** A stream that exercises every rule: CR, LF and CRLF ends, comments, ids, retry, multi-line data,
 * an id-less delta frame, multi-byte characters, and a field with no colon. */
const CORPUS =
  "﻿: keepalive\r\n" +
  'id: 1\nevent: status\ndata: {"status":"running"}\n\n' +
  'event: message_delta\r\ndata: {"delta":"héllo wörld 🚀"}\r\n\r\n' +
  "id: 2\revent: activity\rdata: line one\rdata: line two\r\r" +
  "retry: 1500\nid: 3\ndata\n\n" +
  ": ping\n\n" +
  "event: ignored-without-data\n\n" +
  "id: 4\ndata:  leading-space-kept-after-first\nevent: done\n\n";

const EXPECTED: SseFrame[] = [
  { event: "status", data: '{"status":"running"}', id: "1", lastEventId: "1" },
  { event: "message_delta", data: '{"delta":"héllo wörld 🚀"}', lastEventId: "1" },
  { event: "activity", data: "line one\nline two", id: "2", lastEventId: "2" },
  { event: "message", data: "", id: "3", lastEventId: "3", retry: 1500 },
  { event: "done", data: " leading-space-kept-after-first", id: "4", lastEventId: "4" },
];

describe("SSE parser", () => {
  it("parses every rule of the corpus", () => {
    expect(parseAll(CORPUS)).toEqual(EXPECTED);
  });

  it("an incomplete final block is discarded", () => {
    expect(parseAll("data: a\n\ndata: unterminated")).toEqual([{ event: "message", data: "a", lastEventId: "" }]);
  });

  it("an id with NUL is ignored; the last id persists across blocks", () => {
    const frames = parseAll("id: 5\ndata: a\n\nid: x\u0000y\ndata: b\n\n");
    expect(frames.map((f) => [f.id, f.lastEventId])).toEqual([
      ["5", "5"],
      [undefined, "5"],
    ]);
  });

  it("counts comments (keepalives)", () => {
    const p = new SseParser();
    p.push(": a\n: b\r\n");
    expect(p.comments).toBe(2);
  });

  it("yields identical events for 10,000 random chunk splits of the encoded bytes", async () => {
    const bytes = new TextEncoder().encode(CORPUS);
    let seed = 0x5eed;
    const random = (): number => {
      seed = (Math.imul(seed, 1103515245) + 12345) >>> 0;
      return seed / 2 ** 32;
    };
    for (let round = 0; round < 10_000; round += 1) {
      const cuts = new Set<number>();
      const count = 1 + Math.floor(random() * 12);
      for (let i = 0; i < count; i += 1) cuts.add(1 + Math.floor(random() * (bytes.length - 1)));
      const points = [0, ...[...cuts].sort((a, b) => a - b), bytes.length];
      const chunks: Uint8Array[] = [];
      for (let i = 0; i < points.length - 1; i += 1) chunks.push(bytes.slice(points[i], points[i + 1]));
      const body = new ReadableStream<Uint8Array>({
        start(controller) {
          for (const chunk of chunks) controller.enqueue(chunk);
          controller.close();
        },
      });
      const frames: SseFrame[] = [];
      for await (const frame of readSse(body)) frames.push(frame);
      if (!isDeepStrictEqual(frames, EXPECTED)) {
        throw new Error(`round ${round} with cuts ${points.join(",")} gave ${JSON.stringify(frames)}`);
      }
    }
  });

  it("an idle stream fails with an APITimeoutError after idleTimeoutMs", async () => {
    const body = new ReadableStream<Uint8Array>({ start() {} });
    const started = Date.now();
    await expect(async () => {
      for await (const _ of readSse(body, { idleTimeoutMs: 120 })) void _;
    }).rejects.toMatchObject({ name: "APITimeoutError", possiblyApplied: true });
    expect(Date.now() - started).toBeGreaterThanOrEqual(100);
  });

  it("an abort ends the read with the signal's reason", async () => {
    const body = new ReadableStream<Uint8Array>({ start() {} });
    const controller = new AbortController();
    setTimeout(() => controller.abort(new Error("stop now")), 30);
    await expect(async () => {
      for await (const _ of readSse(body, { signal: controller.signal })) void _;
    }).rejects.toThrow("stop now");
  });
});
