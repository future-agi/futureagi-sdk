/**
 * Server-sent events (ported from the Omega runtime): an incremental parser that follows
 * the WHATWG `text/event-stream` rules, and a reader with an idle timeout. The twin of Python's
 * `fi._core.sse`.
 *
 * The parser yields the same frames whatever way the bytes are split (CR, LF and CRLF line ends, a CR
 * at the end of one chunk and its LF at the start of the next, multi-byte characters split across
 * chunks, a leading BOM). A frame's `id` is set only when its own block had an `id:` line, because
 * the live delta frames omit `id:` so that `Last-Event-ID` stays on the durable sequence.
 */

import { APITimeoutError } from "./errors";

/** One dispatched event. */
export interface SseFrame {
  /** The event type (`message` when the block named none). */
  readonly event: string;
  /** The data lines joined by `\n`. */
  readonly data: string;
  /** The `id:` of this block, when it had one. */
  readonly id?: string;
  /** The stream's last event id at dispatch (persists across blocks, per the spec). */
  readonly lastEventId: string;
  /** A `retry:` value in this block, in ms. */
  readonly retry?: number;
}

/** An incremental parser over decoded text. */
export class SseParser {
  private buffer = "";
  private pendingCr = false;
  private data: string[] = [];
  private hasData = false;
  private eventType = "";
  private blockId: string | undefined;
  private retry: number | undefined;
  private lastId = "";
  private sawBom = false;
  /** Comment lines seen (keepalives), counted for idle tracking. */
  comments = 0;

  /** Feed text; returns the frames completed by it. */
  push(text: string): SseFrame[] {
    if (text.length === 0) return [];
    let input = text;
    if (!this.sawBom && input.length > 0) {
      this.sawBom = true;
      if (input.charCodeAt(0) === 0xfeff) input = input.slice(1);
    }
    if (this.pendingCr && input.startsWith("\n")) input = input.slice(1);
    this.pendingCr = false;
    const frames: SseFrame[] = [];
    this.buffer += input;
    let start = 0;
    for (let i = 0; i < this.buffer.length; i += 1) {
      const ch = this.buffer.charCodeAt(i);
      if (ch !== 10 && ch !== 13) continue;
      const line = this.buffer.slice(start, i);
      if (ch === 13) {
        if (i + 1 < this.buffer.length) {
          if (this.buffer.charCodeAt(i + 1) === 10) i += 1;
        } else {
          this.pendingCr = true;
        }
      }
      start = i + 1;
      const frame = this.line(line);
      if (frame !== undefined) frames.push(frame);
    }
    this.buffer = this.buffer.slice(start);
    return frames;
  }

  /** End of stream: an incomplete final block is discarded, per the spec. */
  end(): SseFrame[] {
    this.buffer = "";
    this.resetBlock();
    return [];
  }

  private resetBlock(): void {
    this.data = [];
    this.hasData = false;
    this.eventType = "";
    this.blockId = undefined;
    this.retry = undefined;
  }

  private line(line: string): SseFrame | undefined {
    if (line === "") return this.dispatch();
    if (line.startsWith(":")) {
      this.comments += 1;
      return undefined;
    }
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "event") this.eventType = value;
    else if (field === "data") {
      this.data.push(value);
      this.hasData = true;
    } else if (field === "id") {
      if (!value.includes("\u0000")) {
        this.blockId = value;
        this.lastId = value;
      }
    } else if (field === "retry" && /^\d+$/u.test(value)) this.retry = Number(value);
    return undefined;
  }

  private dispatch(): SseFrame | undefined {
    if (!this.hasData) {
      this.resetBlock();
      return undefined;
    }
    const frame: SseFrame = {
      event: this.eventType === "" ? "message" : this.eventType,
      data: this.data.join("\n"),
      lastEventId: this.lastId,
      ...(this.blockId !== undefined ? { id: this.blockId } : {}),
      ...(this.retry !== undefined ? { retry: this.retry } : {}),
    };
    this.resetBlock();
    return frame;
  }
}

/** Options for {@link readSse}. */
export interface ReadSseOptions {
  /** Fail with {@link APITimeoutError} when no byte (data or keepalive) arrives for this long. */
  readonly idleTimeoutMs?: number;
  readonly signal?: AbortSignal;
  /** Called on each byte chunk (the first byte matters to transport switching). */
  readonly onBytes?: () => void;
}

/** Read frames from a response body. Cancels the body when the consumer stops early. */
export async function* readSse(body: ReadableStream<Uint8Array>, options: ReadSseOptions = {}): AsyncGenerator<SseFrame, void, undefined> {
  const reader = body.getReader();
  const decoder = new TextDecoder("utf-8");
  const parser = new SseParser();
  const idle = options.idleTimeoutMs;
  try {
    for (;;) {
      const chunk = await readWithIdle(reader, idle, options.signal);
      if (chunk.done) {
        const tail = decoder.decode();
        for (const frame of parser.push(tail)) yield frame;
        parser.end();
        return;
      }
      options.onBytes?.();
      for (const frame of parser.push(decoder.decode(chunk.value, { stream: true }))) yield frame;
    }
  } finally {
    reader.cancel().catch(() => undefined);
    try {
      reader.releaseLock();
    } catch {
      // a pending read may still hold the lock; cancel already ended it
    }
  }
}

async function readWithIdle(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  idleMs: number | undefined,
  signal: AbortSignal | undefined,
): Promise<ReadableStreamReadResult<Uint8Array>> {
  if (signal?.aborted === true) throw signal.reason;
  if (idleMs === undefined && signal === undefined) return reader.read();
  return new Promise((resolve, reject) => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const cleanup = (): void => {
      if (timer !== undefined) clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
    };
    const onAbort = (): void => {
      cleanup();
      reject(signal?.reason);
    };
    if (idleMs !== undefined) {
      timer = setTimeout(() => {
        cleanup();
        const err = new APITimeoutError(`no data within the stream's idle timeout (${idleMs} ms)`);
        err.possiblyApplied = true;
        reject(err);
      }, idleMs);
    }
    signal?.addEventListener("abort", onAbort, { once: true });
    reader.read().then(
      (result) => {
        cleanup();
        resolve(result);
      },
      (error: unknown) => {
        cleanup();
        reject(error);
      },
    );
  });
}

/** An event with an unknown type, as yielded: a newer server's event never breaks an older SDK. */
export interface UnknownStreamEvent {
  /** Discriminator for an event the SDK cannot decode as a known type. */
  readonly type: "unknown";
  /** Event name received from the server. */
  readonly eventType: string;
  /** Parsed JSON, or the original text when the frame was not JSON. */
  readonly raw: unknown;
}

/** Decode one frame: its JSON object with `type` set, or an unknown event. Never throws. */
export function decodeFrame(frame: SseFrame, known: readonly string[]): Record<string, unknown> {
  let raw: unknown;
  try {
    raw = JSON.parse(frame.data);
  } catch {
    raw = frame.data;
  }
  const isObject = raw !== null && typeof raw === "object" && !Array.isArray(raw);
  const type = frame.event === "message" && isObject ? String((raw as { type?: unknown }).type ?? "message") : frame.event;
  if (!known.includes(type) || !isObject) return { type: "unknown", eventType: type, raw };
  return { ...(raw as Record<string, unknown>), type };
}
