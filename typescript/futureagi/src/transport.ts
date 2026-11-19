/**
 * HTTP defaults for FutureAGIClient, the TypeScript twin of python/fi/_http.py:
 * - a 30 s per-request timeout (AbortController; fetch has no separate connect timeout);
 * - retries with no retry class:
 *   - 429 (the server refused before doing anything): every method;
 *   - 502, 503 and 504: idempotent methods only (GET, HEAD, OPTIONS, PUT, DELETE). A 5xx on a POST
 *     or PATCH may mean the request ran, so it is never repeated: a create that documents "one
 *     attempt" (`datasets.versions.create`, `experimentRuns.create`) makes one attempt;
 *   - a pre-send network error (ECONNREFUSED, ENOTFOUND, EAI_AGAIN, UND_ERR_CONNECT_TIMEOUT: nothing
 *     left the machine): every method;
 *   - any other network error (the request may have been sent): idempotent methods only;
 *   - our own timeout (the AbortController fired): never.
 *   Backoff 0.5-1-2-4 s capped at 30 s; Retry-After honoured;
 * - lazy keys: X-Api-Key / X-Secret-Key are resolved on the first request, so constructing a
 *   client never throws for missing keys;
 * - a per-request retry policy, the twin of Python's request.extensions["fi.retry"]:
 *   the `retryPolicy` option is a class, `{ class?, retries? }` (Python's `{"class", "retries"}`), or a
 *   function of the Request that returns either (the platform resolves it from its generated policy
 *   table). Without one, the rules above apply.
 *   - "keyed" (a durable idempotency key) and "http-idempotent": 429, 502, 503, 504 and any network
 *     error, on any method;
 *   - "keyed-not-durable" (a restarted server forgets the key) and "unsafe" (a 5xx may mean the
 *     request ran): 429 and pre-send network errors only, never a 5xx.
 *   Our own timeout is never retried, in any class.
 */

import { checkHttpSecurity } from "./_core/http-security";

export const DEFAULT_TIMEOUT_MS = 30_000;
export const MAX_SLEEP_MS = 30_000;
const RETRY_ALWAYS = new Set([429]); // every method: the server refused before doing anything
const RETRY_IDEMPOTENT = new Set([502, 503, 504]); // idempotent methods only: the request may have run
const IDEMPOTENT = new Set(["GET", "HEAD", "OPTIONS", "PUT", "DELETE"]);
const PRE_SEND_CODES = new Set(["ECONNREFUSED", "ENOTFOUND", "EAI_AGAIN", "UND_ERR_CONNECT_TIMEOUT"]);

export type Credentials = { apiKey: string; secretKey: string };

export const RETRY_CLASSES = ["keyed", "keyed-not-durable", "http-idempotent", "unsafe"] as const;
export type RetryClass = (typeof RETRY_CLASSES)[number];
/** A class, or `{ class?, retries? }`: `retries` overrides the attempt count for this request only. */
export type RetryPolicyValue = RetryClass | { class?: RetryClass; retries?: number };
export type RetryPolicy = RetryPolicyValue | ((request: Request) => RetryPolicyValue | undefined);
const RETRY_5XX = new Set([502, 503, 504]);

export type TransportOptions = {
  fetch?: typeof fetch;
  timeoutMs?: number;
  retries?: number;
  backoffBaseMs?: number;
  sleep?: (ms: number) => Promise<void>;
  resolveCredentials: () => Credentials;
  retryPolicy?: RetryPolicy;
};

export function shouldRetry(method: string, status: number, retryClass?: RetryClass): boolean {
  if (retryClass === undefined) {
    return RETRY_ALWAYS.has(status) || (RETRY_IDEMPOTENT.has(status) && IDEMPOTENT.has(method.toUpperCase()));
  }
  if (retryClass === "keyed" || retryClass === "http-idempotent") return status === 429 || RETRY_5XX.has(status);
  return status === 429; // keyed-not-durable, unsafe: never a 5xx
}

/** The retry class and count for one request; throws on an unknown class or a bad count (a typo
 * must not retry silently). */
export function retryPolicyFor(
  policy: RetryPolicy | undefined,
  request: Request,
): { retryClass?: RetryClass; retries?: number } {
  const value = typeof policy === "function" ? policy(request) : policy;
  if (value === undefined) return {};
  const { class: retryClass, retries } =
    typeof value === "object" && value !== null ? value : { class: value, retries: undefined };
  if (retryClass !== undefined && !(RETRY_CLASSES as readonly string[]).includes(retryClass)) {
    throw new TypeError(`unknown retry class ${JSON.stringify(retryClass)}; one of ${RETRY_CLASSES.join(", ")}`);
  }
  if (retries !== undefined && !(Number.isInteger(retries) && retries >= 0)) {
    throw new TypeError(`retry policy retries must be a non-negative integer, not ${JSON.stringify(retries)}`);
  }
  return { retryClass, retries };
}

/** The retry class for one request; throws on an unknown class (a typo must not retry silently). */
export function retryClassFor(policy: RetryPolicy | undefined, request: Request): RetryClass | undefined {
  return retryPolicyFor(policy, request).retryClass;
}

/** True when a fetch error's code (on the error or its cause, as undici reports it) shows the
 * request never left: the connection was refused, the name did not resolve, or connect timed out. */
export function isPreSendError(error: unknown): boolean {
  let current: unknown = error;
  for (let depth = 0; depth < 4 && current && typeof current === "object"; depth++) {
    const code = (current as { code?: unknown }).code;
    if (typeof code === "string" && PRE_SEND_CODES.has(code)) return true;
    current = (current as { cause?: unknown }).cause;
  }
  return false;
}

export function shouldRetryNetworkError(method: string, error: unknown, retryClass?: RetryClass): boolean {
  if (retryClass === "keyed" || retryClass === "http-idempotent") return true;
  if (retryClass !== undefined) return isPreSendError(error);
  return IDEMPOTENT.has(method.toUpperCase()) || isPreSendError(error);
}

export function retryAfterMs(response: Response): number | undefined {
  const value = response.headers.get("Retry-After");
  if (!value) return undefined;
  const seconds = Number(value);
  if (Number.isFinite(seconds)) return Math.max(0, seconds * 1000);
  const when = Date.parse(value);
  return Number.isNaN(when) ? undefined : Math.max(0, when - Date.now());
}

const defaultSleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export function resilientFetch(options: TransportOptions): typeof fetch {
  const baseFetch = options.fetch ?? globalThis.fetch.bind(globalThis);
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const defaultRetries = options.retries ?? 3;
  const base = options.backoffBaseMs ?? 500;
  const sleep = options.sleep ?? defaultSleep;
  let creds: Credentials | undefined;

  const wrapped = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    creds ??= options.resolveCredentials();
    // Enforce at the last shared layer too: a caller cannot turn credential forwarding back on.
    const original = new Request(input as RequestInfo, { ...init, redirect: "manual" });
    // Bearer platform requests have already passed the origin guard; their key placeholders are empty.
    if (creds.apiKey || creds.secretKey) checkHttpSecurity(new URL(original.url), "keys");
    const policy = retryPolicyFor(options.retryPolicy, original);
    const retryClass = policy.retryClass;
    const retries = policy.retries ?? defaultRetries;
    if (!original.headers.has("X-Api-Key")) original.headers.set("X-Api-Key", creds.apiKey);
    if (!original.headers.has("X-Secret-Key")) original.headers.set("X-Secret-Key", creds.secretKey);
    for (let attempt = 0; ; attempt++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(new Error(`request timed out after ${timeoutMs} ms`)), timeoutMs);
      const request = new Request(original.clone(), { signal: controller.signal });
      let response: Response;
      try {
        response = await baseFetch(request);
      } catch (error) {
        clearTimeout(timer);
        const aborted = controller.signal.aborted;
        if (aborted || attempt >= retries || !shouldRetryNetworkError(original.method, error, retryClass)) throw error;
        await sleep(Math.min(base * 2 ** attempt, MAX_SLEEP_MS));
        continue;
      }
      clearTimeout(timer);
      if (attempt >= retries || !shouldRetry(original.method, response.status, retryClass)) return response;
      const delay = Math.min(retryAfterMs(response) ?? base * 2 ** attempt, MAX_SLEEP_MS);
      await response.body?.cancel().catch(() => undefined);
      await sleep(delay);
    }
  };
  return wrapped as typeof fetch;
}
