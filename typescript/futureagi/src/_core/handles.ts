/**
 * Handles: `Deployment`, `Sandbox` and `Run` share one base; the twin of Python's
 * `fi._core.handles`. A handle wraps one resource's wire-shaped object: `.data`, `.id`, `.status`,
 * `toJSON()` (a deep copy), `refresh()`, and **one waiter, `wait({ timeoutMs })`**, which polls
 * `refresh()` with backoff until `isDone()` and throws `APITimeoutError` when the time runs out.
 *
 * A resource namespace subclasses {@link Handle} with `fetchData()` (the read call) and `isDone()`; a handle that owns
 * a resource (a sandbox) overrides `dispose()`, which `await using` calls through `Symbol.asyncDispose`
 * where the runtime defines it. {@link pollUntil} is the shared loop for any other waiter.
 */

import { APITimeoutError } from "./errors";

/** `Symbol.asyncDispose` where the runtime has it, else the registered symbol TypeScript's helpers use. */
export const ASYNC_DISPOSE: symbol = (Symbol as unknown as { asyncDispose?: symbol }).asyncDispose ?? Symbol.for("Symbol.asyncDispose");

/** Bounds and scheduling for a resource waiter. */
export interface PollOptions {
  /** Maximum polling duration in milliseconds; defaults to five minutes. */
  readonly timeoutMs?: number;
  /** Initial polling delay in milliseconds; defaults to 500. */
  readonly intervalMs?: number;
  /** Backoff ceiling in milliseconds; defaults to 5,000. */
  readonly maxIntervalMs?: number;
  /** Cancels the default backoff sleep and requests made by a handle's waiter. */
  readonly signal?: AbortSignal;
  /** Description included in timeout errors. */
  readonly label?: string;
  /** Custom backoff sleep, receiving milliseconds. */
  readonly sleep?: (ms: number) => Promise<void>;
  /** Clock returning milliseconds; defaults to `Date.now`. */
  readonly now?: () => number;
}

const sleepFor = (ms: number, signal?: AbortSignal): Promise<void> =>
  new Promise((resolve, reject) => {
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

/** Await `check` until it returns something other than undefined, and return that. */
export async function pollUntil<T>(check: () => Promise<T | undefined>, options: PollOptions = {}): Promise<T> {
  const timeoutMs = options.timeoutMs ?? 300_000;
  const now = options.now ?? Date.now;
  const sleep = options.sleep ?? ((ms: number) => sleepFor(ms, options.signal));
  const deadline = now() + timeoutMs;
  let interval = options.intervalMs ?? 500;
  for (;;) {
    const value = await check();
    if (value !== undefined) return value;
    const remaining = deadline - now();
    if (remaining <= 0) {
      const err = new APITimeoutError(`${options.label ?? "the wait"} did not finish within ${timeoutMs / 1000} s`);
      err.possiblyApplied = true;
      throw err;
    }
    await sleep(Math.min(interval, remaining));
    interval = Math.min(interval * 2, options.maxIntervalMs ?? 5_000);
  }
}

function deepCopy<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

/** A resource snapshot with refresh, polling and optional lifecycle cleanup. */
export abstract class Handle<T extends object> {
  /** The resource's noun, for messages (`deployment`). */
  protected readonly noun: string = "resource";
  private current: T;

  constructor(data: T) {
    this.current = data;
  }

  /** The wire-shaped object (the same object until the next `refresh()`). */
  get data(): T {
    return this.current;
  }

  /** Resource identifier, when the wire object includes a string `id`. */
  get id(): string | undefined {
    const id = (this.current as Record<string, unknown>).id;
    return typeof id === "string" ? id : undefined;
  }

  /** Status value from the latest resource snapshot. */
  get status(): unknown {
    return (this.current as Record<string, unknown>).status;
  }

  /** A deep copy of the wire-shaped object. */
  toJSON(): T {
    return deepCopy(this.current);
  }

  protected abstract fetchData(options?: { signal?: AbortSignal }): Promise<T>;
  protected abstract isDone(): boolean;

  /** Re-read the resource from the server; resolves to this handle. */
  async refresh(options: { signal?: AbortSignal } = {}): Promise<this> {
    this.current = await this.fetchData(options);
    return this;
  }

  /** Poll until the resource reaches a final state; resolves to this handle. */
  async wait(options: PollOptions = {}): Promise<this> {
    if (this.isDone()) return this;
    return pollUntil(
      async () => ((await this.refresh(options.signal !== undefined ? { signal: options.signal } : {})).isDone() ? this : undefined),
      {
        label: `waiting for ${this.noun} ${this.id ?? ""}`.trim(),
        ...options,
      },
    );
  }

  /** Release what the handle owns (a sandbox kills itself); a no-op by default. */
  async dispose(): Promise<void> {
    return undefined;
  }

  [ASYNC_DISPOSE](): Promise<void> {
    return this.dispose();
  }
}
