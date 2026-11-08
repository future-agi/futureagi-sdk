/**
 * Raw responses: every platform call returns an {@link APIPromise}. Awaiting it gives the
 * wire-shaped data; `.withResponse()` gives `{ data, meta }`, where `meta` says what the final response
 * said about the call (request id, idempotency key, rate-limit headers, replay flag, redacted headers).
 * The twin of Python's `with_raw_response` (`fi._core.raw`).
 */

import { redactHeaders } from "./redact";

/** What one platform call's final response said, besides its data. */
export interface CallMeta {
  /** HTTP status of the final response. */
  readonly statusCode: number;
  /** Canonical SDK operation name from the generated contract. */
  readonly operation: string;
  /** Server request identifier, when returned. */
  readonly requestId?: string;
  /** Upstream request identifier, when returned. */
  readonly upstreamRequestId?: string;
  /** Server receipt identifier, when returned. */
  readonly receiptId?: string;
  /** The `Idempotency-Key` the call sent (minted, or yours). */
  readonly idempotencyKey?: string;
  /** True when the server replayed an earlier response for the same key. */
  readonly idempotentReplay: boolean;
  /** True for a not-found-means-applied call whose retry answered 404 (the first attempt applied). */
  readonly alreadyApplied: boolean;
  /** HTTP attempts made (1 when nothing was retried), including "in progress" resends. */
  readonly attempts: number;
  /** The response headers, with secret values redacted. */
  readonly headers: Readonly<Record<string, string>>;
  /** The rate-limit headers (`x-ratelimit-*`, `ratelimit-*`, `retry-after`). */
  readonly rateLimit: Readonly<Record<string, string>>;
}

/** `{ data, meta }` from `.withResponse()`. */
export interface RawResponse<T> {
  /** Parsed data returned by the operation. */
  readonly data: T;
  /** Final response metadata and attempt count. */
  readonly meta: CallMeta;
  /** Convenience alias for `meta.requestId`. */
  readonly requestId?: string;
  /** Convenience alias for `meta.idempotencyKey`. */
  readonly idempotencyKey?: string;
}

const RATE_LIMIT = /^(x-ratelimit-|ratelimit-|retry-after$)/u;

export function metaFrom(
  response: Response,
  operation: string,
  extra: { idempotencyKey?: string; attempts: number; replay: boolean; applied?: boolean },
): CallMeta {
  const pairs: [string, string][] = [];
  response.headers.forEach((value, key) => pairs.push([key, value]));
  const headers = redactHeaders(pairs);
  const rateLimit: Record<string, string> = {};
  for (const [key, value] of Object.entries(headers)) if (RATE_LIMIT.test(key)) rateLimit[key] = value;
  const h = response.headers;
  return {
    statusCode: response.status,
    operation,
    ...(h.get("x-request-id") !== null ? { requestId: h.get("x-request-id") as string } : {}),
    ...(h.get("x-upstream-request-id") !== null ? { upstreamRequestId: h.get("x-upstream-request-id") as string } : {}),
    ...(h.get("x-omega-receipt-id") !== null ? { receiptId: h.get("x-omega-receipt-id") as string } : {}),
    ...(extra.idempotencyKey !== undefined ? { idempotencyKey: extra.idempotencyKey } : {}),
    idempotentReplay: extra.replay,
    alreadyApplied: extra.applied ?? false,
    attempts: Math.max(1, extra.attempts),
    headers,
    rateLimit,
  };
}

/** A call in flight: await it for the data, or call `.withResponse()` for `{ data, meta }`. */
export class APIPromise<T> implements PromiseLike<T> {
  private readonly result: Promise<{ data: T; meta: CallMeta }>;

  constructor(run: () => Promise<{ data: T; meta: CallMeta }>) {
    this.result = run();
    this.result.catch(() => undefined); // the rejection reaches whichever of then/withResponse is used
  }

  /** The data plus the final response's metadata. */
  withResponse(): Promise<RawResponse<T>> {
    return this.result.then(({ data, meta }) => ({
      data,
      meta,
      ...(meta.requestId !== undefined ? { requestId: meta.requestId } : {}),
      ...(meta.idempotencyKey !== undefined ? { idempotencyKey: meta.idempotencyKey } : {}),
    }));
  }

  /** Map the data (handles wrap their resource this way); the metadata is kept. */
  map<U>(fn: (data: T) => U): APIPromise<U> {
    return new APIPromise(async () => {
      const { data, meta } = await this.result;
      return { data: fn(data), meta };
    });
  }

  then<R1 = T, R2 = never>(
    onFulfilled?: ((value: T) => R1 | PromiseLike<R1>) | null,
    onRejected?: ((reason: unknown) => R2 | PromiseLike<R2>) | null,
  ): Promise<R1 | R2> {
    return this.result.then(({ data }) => data).then(onFulfilled, onRejected);
  }

  /** Handle a rejected call without changing its request or metadata. */
  catch<R = never>(onRejected?: ((reason: unknown) => R | PromiseLike<R>) | null): Promise<T | R> {
    return this.then(undefined, onRejected);
  }

  /** Run cleanup after settlement and preserve the call's data or rejection. */
  finally(onFinally?: (() => void) | null): Promise<T> {
    return this.then().finally(onFinally);
  }
}
