/**
 * The load-time fetch identity rule, shared by every sender of the SDK: the runtime's own `fetch` is `globalThis.fetch`
 * as it was when this module was evaluated. A `globalThis.fetch` that differs from it at the time of a send (a wrapper
 * an application or a library writes into the global after the SDK loads) is a fetch of the caller's own: a transport
 * the SDK cannot inspect, so keys or a Bearer token go through it only with `customFetchReceivesKeys: true`, as through
 * a `fetch` option. A replacement made before the SDK loads is captured as the runtime's fetch; the rule cannot see it.
 */

import { ConfigurationError } from "./errors";
import { CUSTOM_FETCH_CODE } from "./http-security";

const LOADED: typeof fetch | undefined = typeof globalThis.fetch === "function" ? globalThis.fetch : undefined;
let runtimeFetch = LOADED;
/** `Reflect.apply` as it was at load: a send applies the fetch that was checked, and reads no property of it (a `bind`
 * defined on that function, or a replaced `Function.prototype.bind`, could answer with another fetch). */
const apply = Reflect.apply;

/** A fetch that calls `checked` itself with `globalThis` as its receiver. */
function applying(checked: typeof fetch): typeof fetch {
  return ((...args: Parameters<typeof fetch>) => apply(checked, globalThis, args)) as typeof fetch;
}

/** Whether `candidate` is the runtime's own fetch, by identity with the fetch captured at load. */
export function isRuntimeFetch(candidate: unknown): boolean {
  return candidate !== undefined && candidate === runtimeFetch;
}

/** Test seam: treat `candidate` as the runtime's own fetch, so a test that replaces `globalThis.fetch` can run the
 * runtime-fetch rules. Without an argument the fetch captured at module load applies again. */
export function setRuntimeFetch(candidate?: typeof fetch): void {
  runtimeFetch = candidate ?? LOADED;
}

/** The fetch a send without a `fetch` option goes through: `globalThis.fetch` as it stands at the call, called itself
 * with the global as its receiver, and whether it is the runtime's own (`runtime: false` for a replacement, which the
 * senders treat as a caller's fetch). */
export function globalFetch(): { fetch: typeof fetch; runtime: boolean } {
  const current = globalThis.fetch;
  if (typeof current !== "function") throw new Error("no global fetch: pass `fetch` in the client options (Node >= 18 has one)");
  return { fetch: applying(current), runtime: isRuntimeFetch(current) };
}

/** The refusal of a keyed (or Bearer) send through a replaced `globalThis.fetch` without `customFetchReceivesKeys`:
 * the code of the fetch-option refusal, `custom_fetch_not_opted_in`, with a message that names the global. */
export function replacedGlobalRefusal(mode: "keys" | "bearer" = "keys"): ConfigurationError {
  const what = mode === "bearer" ? "a Bearer token" : "API keys";
  return new ConfigurationError(
    `Refusing to send ${what} through globalThis.fetch: it is not the fetch the SDK captured when it loaded, so it is a ` +
      `transport of the caller's own that cannot be inspected, and a proxy inside it would receive ${mode === "bearer" ? "the token" : "the keys"}. ` +
      "Restore the runtime's fetch, or set customFetchReceivesKeys: true if you own that transport (the proxy rules do not apply " +
      "to it; plain http to a host that is not loopback needs allowInsecureHttp).",
    CUSTOM_FETCH_CODE,
  );
}
