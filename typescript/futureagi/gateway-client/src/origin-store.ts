// ---------------------------------------------------------------------------
// The registries of trusted origins, shared by every copy of this package.
//
// The SDK decides what an error is (its own failed body read, or a genuine
// gateway error frame) from a record it makes when it raises the error, never
// from a class, a flag or a wire field a caller could set. That record has to
// be one per process: a CommonJS and an ES module build of the package, or two
// installed copies of it, each evaluate their own modules, and a registry
// private to a module would not know what another copy raised.
//
// The store lives in a slot of the global object under a registered symbol. The
// first copy creates it; later copies use it as it is. An existing slot is
// never replaced: one that is not a store of weak sets is left alone and this
// copy keeps private registries.
// ---------------------------------------------------------------------------

/** The registries, each holding objects by identity only. */
export interface OriginStore {
  /** Errors the SDK raised for a failed read or decode of a successful body. */
  readonly bodyFailures: WeakSet<object>;
  /** Errors the SDK decoded from a genuine gateway error frame. */
  readonly streamFrames: WeakSet<object>;
  /** Responses that opted in to the SDK stream-adapter framing. */
  readonly adapterResponses: WeakSet<object>;
}

const STORE_KEY = Symbol.for("futureagi.gateway.sdk-origin.v1");
const NAMES = ["bodyFailures", "streamFrames", "adapterResponses"] as const;

// The intrinsic methods, taken once: a registry is only ever read or written
// through these, so a patched `has` or `add` on a set cannot change an answer.
const weakHas = WeakSet.prototype.has;
const weakAdd = WeakSet.prototype.add;

/** True for a real weak set, whichever realm made it; look-alikes throw. */
function isWeakSet(value: unknown): value is WeakSet<object> {
  try {
    weakHas.call(value as WeakSet<object>, {});
    return true;
  } catch {
    return false;
  }
}

function isStore(value: unknown): value is OriginStore {
  if (typeof value !== "object" || value === null) return false;
  return NAMES.every((name) => isWeakSet((value as Record<string, unknown>)[name]));
}

function createStore(): OriginStore {
  return Object.freeze({ bodyFailures: new WeakSet<object>(), streamFrames: new WeakSet<object>(), adapterResponses: new WeakSet<object>() });
}

function resolveStore(): OriginStore {
  const host = globalThis as unknown as Record<symbol, unknown>;
  const existing = host[STORE_KEY];
  if (existing !== undefined) return isStore(existing) ? existing : createStore();
  const created = createStore();
  try {
    // Not writable, not configurable, not enumerable: no copy can swap it out.
    Object.defineProperty(host, STORE_KEY, { value: created });
  } catch {
    // A sealed global object: this copy keeps its own registries.
  }
  return created;
}

/** The process-wide store, or this copy's own when the global slot cannot be used. */
export const originStore: OriginStore = resolveStore();

/** Whether `value` is recorded in `registry`; false for any non-object. */
export function hasOrigin(registry: WeakSet<object>, value: unknown): boolean {
  return (typeof value === "object" || typeof value === "function") && value !== null && weakHas.call(registry, value);
}

/** Record `value` (an object) in `registry`. */
export function markOrigin<T extends object>(registry: WeakSet<object>, value: T): T {
  weakAdd.call(registry, value);
  return value;
}
