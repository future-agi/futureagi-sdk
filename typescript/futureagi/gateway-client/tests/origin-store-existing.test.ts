import { it, expect, jest } from "@jest/globals";
import type { GatewayEvidence } from "../src/gateway-evidence.js";

// A store that is already there is used when it has the right shape and is
// otherwise left alone: the SDK never replaces it.
const KEY = Symbol.for("futureagi.gateway.sdk-origin.v1");
const host = globalThis as unknown as Record<symbol, unknown>;
const evidence: GatewayEvidence = Object.freeze({ dispatched: "unknown", gatewayRequestId: null, clientRequestId: null });
type Errors = typeof import("../src/errors.js");

function seed(value: unknown) { Object.defineProperty(host, KEY, { value, configurable: true, writable: true, enumerable: false }); }
function load(): Errors {
  let loaded: Errors | undefined;
  jest.isolateModules(() => { loaded = require("../src/errors.js"); });
  return loaded as Errors;
}

it("an existing store of the right shape is the one the SDK records in", () => {
  const store = { bodyFailures: new WeakSet<object>(), streamFrames: new WeakSet<object>(), adapterResponses: new WeakSet<object>() };
  seed(store);
  try {
    const errors = load();
    const failure = errors.streamBodyError("synthetic body failure", evidence);
    const frame = errors.streamFrameError("synthetic gateway frame");
    expect(store.bodyFailures.has(failure)).toBe(true);
    expect(store.streamFrames.has(frame)).toBe(true);
    expect(store.bodyFailures.has(frame)).toBe(false);
    expect(host[KEY]).toBe(store);
  } finally { delete host[KEY]; }
});

for (const [name, bad] of [
  ["an object without the registries", {}],
  ["registries that are not weak sets", { bodyFailures: new Set(), streamFrames: new Set(), adapterResponses: new Set() }],
  ["registries that only look like weak sets", { bodyFailures: { has: () => true, add: () => undefined }, streamFrames: { has: () => true, add: () => undefined }, adapterResponses: { has: () => true, add: () => undefined } }],
  ["a primitive", "not a store"],
] as const) {
  it(`${name} is left in place and the SDK keeps working without it`, () => {
    seed(bad);
    try {
      const errors = load();
      const failure = errors.streamBodyError("synthetic body failure", evidence);
      expect(errors.sdkBodyFailureEvidence(failure)).toBe(evidence);
      expect(errors.sdkBodyFailureEvidence(errors.streamFrameError("synthetic gateway frame"))).toBeNull();
      expect(errors.sdkBodyFailureEvidence(new errors.StreamError("synthetic forged", { bodyReadFailure: true }))).toBeNull();
      expect(host[KEY]).toBe(bad);
    } finally { delete host[KEY]; }
  });
}
