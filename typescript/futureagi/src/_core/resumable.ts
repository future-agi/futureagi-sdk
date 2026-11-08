/**
 * Resumable event streams: run events and deployment build logs; the twin of Python's
 * `fi._core.resumable` (its docstring has the rules).
 *
 * - Resume after the last durable sequence with `Last-Event-ID`, dropping repeats by sequence.
 * - Reconnect within bounds: `maxConsecutiveFailures` (10) reconnects in a row that deliver nothing new,
 *   `maxReconnects` (200) in all, an optional `maxStreamDurationMs`; then `StreamInterruptedError`
 *   with `lastSequence`. A 401, 403 or 404 on reconnect is terminal.
 * - `transport: "auto"` switches to long-poll after two SSE attempts that produced no byte.
 * - Live deltas are reconciled across reconnects (`message_reset` for a regenerated message).
 */

import { DeltaReconciler, type MessageResetEvent } from "./deltas";
import { FutureAGIAPIError, StreamInterruptedError } from "./errors";
import type { CallOptions, PlatformCore } from "./platform-base";
import type { OperationParams, QueryValue } from "./request";
import { decodeFrame, readSse } from "./sse";

/** Stream bounds and transport. */
export interface ResumableOptions {
  /** Cancels the active request, stream reader and default reconnect sleep. */
  readonly signal?: AbortSignal;
  /** Durable sequence to resume after, sent as `Last-Event-ID`. */
  readonly lastEventId?: string;
  /** Maximum silence in milliseconds; defaults to the client's stream idle timeout. */
  readonly idleTimeoutMs?: number;
  /** Total reconnect budget; defaults to 200. */
  readonly maxReconnects?: number;
  /** Consecutive attempts without new durable events before failing; defaults to 10. */
  readonly maxConsecutiveFailures?: number;
  /** Optional total duration budget in milliseconds, checked between attempts. */
  readonly maxStreamDurationMs?: number;
  /** Preferred transport; auto falls back to polling after two byte-free SSE attempts. */
  readonly transport?: "auto" | "sse" | "poll";
  /** Long-poll wait in milliseconds, capped by the contract; defaults to 25,000. */
  readonly pollWaitMs?: number;
  /** Reconcile replayed live text across connections; defaults to true. */
  readonly reconcileDeltas?: boolean;
  /** Test seam: the backoff sleep. */
  readonly sleep?: (ms: number) => Promise<void>;
  /** Jitter source returning a number in [0, 1); defaults to `Math.random`. */
  readonly random?: () => number;
}

export const STREAM_DEFAULTS = { maxReconnects: 200, maxConsecutiveFailures: 10, pollWaitMs: 25_000, sseAttemptsBeforePoll: 2 } as const;
const BASE_DELAY_MS = 500;
const MAX_DELAY_MS = 8_000;

function after(id: string, last: string | undefined): boolean {
  if (last === undefined) return true;
  if (/^\d+$/u.test(id.trim()) && /^\d+$/u.test(last.trim())) return Number(id) > Number(last);
  return id !== last;
}

const terminal = (error: unknown): boolean => error instanceof FutureAGIAPIError && [401, 403, 404].includes(error.statusCode);

function defaultSleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted === true) return reject(signal.reason);
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        reject(signal.reason);
      },
      { once: true },
    );
  });
}

/** Iterate a resumable stream's decoded events. `isEnd` says when the stream has reached its natural end. */
export async function* resumableEvents(
  core: PlatformCore,
  name: string,
  params: OperationParams,
  isEnd: (event: Record<string, unknown>) => boolean,
  options: ResumableOptions = {},
): AsyncGenerator<Record<string, unknown> | MessageResetEvent, void, undefined> {
  const spec = core.operation(name).stream;
  if (spec === undefined || spec.resume !== "last-event-id") {
    throw new FutureAGIAPIError(0, undefined, { code: "not_resumable", operation: name, message: `${name} is not a resumable stream` });
  }
  const limits = { ...STREAM_DEFAULTS, ...options };
  const idle = options.idleTimeoutMs ?? core.settings.streamIdleTimeoutMs;
  const pollWait = Math.min(limits.pollWaitMs, spec.pollMaxWaitMs ?? STREAM_DEFAULTS.pollWaitMs);
  const reconciler = options.reconcileDeltas === false ? undefined : new DeltaReconciler();
  const random = options.random ?? Math.random;
  const sleep = options.sleep ?? ((ms: number) => defaultSleep(ms, options.signal));
  const started = Date.now();
  let last = options.lastEventId;
  let mode: "sse" | "poll" = options.transport === "poll" && spec.pollParam !== undefined ? "poll" : "sse";
  let silentSse = 0;
  let failures = 0;
  let reconnects = 0;
  for (;;) {
    let newDurable = false;
    let sawByte = false;
    let attemptError: unknown;
    const attemptStarted = Date.now();
    reconciler?.newConnection();
    const query: Record<string, QueryValue> = { ...(params.query ?? {}) };
    if (mode === "poll" && spec.pollParam !== undefined) {
      query[spec.pollParam] = spec.pollValue;
      if (spec.pollWaitParam !== undefined) query[spec.pollWaitParam] = pollWait;
    }
    try {
      const callOptions: CallOptions = {
        ...(options.signal !== undefined ? { signal: options.signal } : {}),
        ...(last !== undefined ? { lastEventId: last } : {}),
      };
      const opened = await core.openStream(name, { ...params, query }, callOptions);
      const frames = readSse(opened.response.body ?? new ReadableStream(), {
        idleTimeoutMs: mode === "poll" ? idle + pollWait : idle,
        ...(options.signal !== undefined ? { signal: options.signal } : {}),
        onBytes: () => {
          sawByte = true;
        },
      });
      for await (const frame of frames) {
        if (frame.id !== undefined) {
          if (!after(frame.id, last)) continue;
          last = frame.id;
          newDurable = true;
        }
        const event = decodeFrame(frame, spec.knownEvents);
        for (const item of reconciler === undefined ? [event] : reconciler.push(event)) {
          yield item;
          if (item.type !== "unknown" && isEnd(item as Record<string, unknown>)) return;
        }
      }
    } catch (error) {
      if (options.signal?.aborted === true) throw options.signal.reason ?? error;
      if (terminal(error)) throw error;
      attemptError = error;
    }
    if (mode === "sse" && !sawByte) silentSse += 1;
    if (
      options.transport !== "sse" &&
      options.transport !== "poll" &&
      spec.pollParam !== undefined &&
      silentSse >= STREAM_DEFAULTS.sseAttemptsBeforePoll
    )
      mode = "poll";
    const quietPoll = mode === "poll" && attemptError === undefined && Date.now() - attemptStarted >= 1_000;
    failures = newDurable || quietPoll ? 0 : failures + 1;
    reconnects += 1;
    const overTime = options.maxStreamDurationMs !== undefined && Date.now() - started >= options.maxStreamDurationMs;
    if (failures >= limits.maxConsecutiveFailures || reconnects > limits.maxReconnects || overTime) {
      const why = overTime
        ? "its time cap"
        : failures >= limits.maxConsecutiveFailures
          ? `${failures} reconnects in a row that delivered nothing new`
          : `${limits.maxReconnects} reconnects`;
      throw new StreamInterruptedError(
        `${name} stopped after ${why}; resume from lastSequence`,
        last,
        name,
        attemptError instanceof Error ? attemptError : undefined,
      );
    }
    if (failures > 0) await sleep(random() * Math.min(MAX_DELAY_MS, BASE_DELAY_MS * 2 ** (failures - 1)));
  }
}
