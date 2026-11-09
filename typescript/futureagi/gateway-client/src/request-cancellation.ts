/** Internal cancellation ownership; no transport objects or caller reasons escape. */
export function abortError(): DOMException {
  return new DOMException("Request aborted.", "AbortError");
}

export function throwIfAborted(signal?: AbortSignal): void {
  if (signal?.aborted) throw abortError();
}

/** Native composition when available; Node 18 needs removable listeners. */
function combineSignals(signals: AbortSignal[]): { signal: AbortSignal; dispose: () => void } {
  if (typeof AbortSignal.any === "function") {
    return { signal: AbortSignal.any(signals), dispose: () => {} };
  }
  const controller = new AbortController();
  const listeners = new Map<AbortSignal, () => void>();
  const dispose = () => {
    for (const [signal, listener] of listeners) signal.removeEventListener("abort", listener);
    listeners.clear();
  };
  for (const signal of signals) {
    const abort = () => { controller.abort(signal.reason); dispose(); };
    if (signal.aborted) { abort(); break; }
    listeners.set(signal, abort);
    signal.addEventListener("abort", abort, { once: true });
  }
  return { signal: controller.signal, dispose };
}

export class RequestCancellation {
  private readonly controller = new AbortController();
  readonly signal: AbortSignal;
  readonly dispose: () => void;

  constructor(timeout: number, private readonly caller?: AbortSignal) {
    const combined = combineSignals([
      ...(caller ? [caller] : []), AbortSignal.timeout(timeout), this.controller.signal,
    ]);
    this.signal = combined.signal;
    this.dispose = combined.dispose;
  }

  /** Timeout-only failures keep their existing error classification. */
  get explicitlyAborted(): boolean {
    return this.controller.signal.aborted || this.caller?.aborted === true;
  }

  throwIfAborted(): void {
    if (this.explicitlyAborted) throw abortError();
  }

  abort(): void {
    this.controller.abort(abortError());
  }
}

// A raw Response stays caller-owned. SDK Stream readers take over this attempt
// until iteration ends; otherwise the caller's abort or timeout releases the
// fallback listeners. Never detach at headers: the body is still in flight.
const STORE_KEY = Symbol.for("futureagi.gateway.request-cancellation.v1");
const weakGet = WeakMap.prototype.get;
const weakSet = WeakMap.prototype.set;

function resolveCancellations(): WeakMap<Response, RequestCancellation> {
  const host = globalThis as unknown as Record<symbol, unknown>;
  if (STORE_KEY in host) {
    const existing = host[STORE_KEY];
    try {
      // Intrinsic access accepts real maps from other realms, not look-alikes
      // or patched instance methods. Never replace an occupied global slot.
      weakGet.call(existing as WeakMap<Response, RequestCancellation>, {});
      return existing as WeakMap<Response, RequestCancellation>;
    } catch {
      return new WeakMap<Response, RequestCancellation>();
    }
  }
  const created = new WeakMap<Response, RequestCancellation>();
  try {
    Object.defineProperty(host, STORE_KEY, { value: created });
  } catch {
    // A sealed global object: keep a private registry, as with origin stores.
  }
  return created;
}

// CJS, ESM and duplicate installs must all reach the originating attempt.
const responseCancellations = resolveCancellations();
export function setResponseCancellation(response: Response, cancellation: RequestCancellation): void {
  weakSet.call(responseCancellations, response, cancellation);
}
export function getResponseCancellation(response: Response): RequestCancellation | undefined {
  return weakGet.call(responseCancellations, response);
}
