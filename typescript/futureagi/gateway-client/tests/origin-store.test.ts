import { it, expect, jest } from "@jest/globals";
import type { GatewayEvidence } from "../src/gateway-evidence.js";

// Every copy of the package shares one process-wide store of trusted origins.
// This file loads no source module at the top, so the first copy creates it.
const KEY = Symbol.for("futureagi.gateway.sdk-origin.v1");
const slot = () => (globalThis as unknown as Record<symbol, unknown>)[KEY];
const evidence: GatewayEvidence = Object.freeze({ dispatched: "unknown", gatewayRequestId: null, clientRequestId: null });
const EVENT = "futureagi.sdk-error";
type Errors = typeof import("../src/errors.js");
type Adapter = typeof import("../src/stream-adapter.js");

function load<T>(path: string): T {
  let loaded: T | undefined;
  jest.isolateModules(() => { loaded = require(path); });
  return loaded as T;
}

it("no store exists before the first copy loads", () => {
  expect(slot()).toBeUndefined();
});

it("the first copy creates one store that later copies reuse and cannot replace", () => {
  load<Errors>("../src/errors.js");
  const store = slot();
  expect(store).toBeDefined();
  load<Errors>("../src/errors.js");
  load<Adapter>("../src/stream-adapter.js");
  expect(slot()).toBe(store);
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, KEY);
  expect(descriptor).toMatchObject({ writable: false, enumerable: false, configurable: false });
  expect(() => { (globalThis as unknown as Record<symbol, unknown>)[KEY] = {}; }).toThrow(TypeError);
  expect(slot()).toBe(store);
});

it("a copy recognises what another copy's SDK code raised, and nothing else", () => {
  const a = load<Errors>("../src/errors.js");
  const b = load<Errors>("../src/errors.js");
  expect(a.StreamError).not.toBe(b.StreamError);
  const bodyFailure = a.streamBodyError("synthetic body failure", evidence);
  expect(b.sdkBodyFailureEvidence(bodyFailure)).toBe(evidence);
  expect(b.sdkBodyFailureEvidence(a.responseBodyError(evidence))).toBe(evidence);
  const frame = a.streamFrameError("synthetic gateway frame", { type: "guardrail_error" });
  expect(b.sdkBodyFailureEvidence(frame)).toBeNull();
  expect(b.errorAtExit(frame, evidence)).toBe(frame);
  // Public construction, flags, evidence and look-alikes grant nothing.
  const forged = new a.StreamError("synthetic forged", { bodyReadFailure: true, gatewayEvidence: evidence });
  expect(b.sdkBodyFailureEvidence(forged)).toBeNull();
  expect(b.errorAtExit(forged, evidence)).not.toBe(forged);
  for (const value of ["text", 42, null, undefined, {}, { gatewayEvidence: evidence }, Object.create(bodyFailure)]) {
    expect(b.sdkBodyFailureEvidence(value)).toBeNull();
  }
});

it("a response opted in by one copy is an adapter response for another", () => {
  const a = load<Adapter>("../src/stream-adapter.js");
  const b = load<Adapter>("../src/stream-adapter.js");
  const frame = { sdk_error: { version: 1, evidence: { dispatched: true, gatewayRequestId: null, clientRequestId: null } } };
  const optedIn = a.acceptStreamAdapterResponse(new Response("", { headers: { [a.SDK_STREAM_FORMAT_HEADER]: a.SDK_STREAM_FORMAT } }));
  const decoded = b.streamAdapterErrorFromEvent(optedIn, EVENT, frame, evidence);
  expect(decoded).not.toBeNull();
  expect(decoded?.gatewayEvidence).toEqual({ dispatched: true, gatewayRequestId: null, clientRequestId: null });
  const stranger = new Response("", { headers: { [a.SDK_STREAM_FORMAT_HEADER]: a.SDK_STREAM_FORMAT } });
  expect(b.streamAdapterErrorFromEvent(stranger, EVENT, frame, evidence)).toBeNull();
});
