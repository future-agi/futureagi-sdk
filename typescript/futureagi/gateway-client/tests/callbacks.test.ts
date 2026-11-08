import { describe, it, expect, jest } from "@jest/globals";
import { CallbackHandler, invokeCallbacks } from "../src/callbacks.js";
import type { CallbackRequest, CallbackResponse } from "../src/callbacks.js";

class TestCallback extends CallbackHandler {
  events: string[] = [];

  override onRequestStart(request: CallbackRequest) {
    this.events.push(`start:${request.method}`);
  }

  override onRequestEnd(_request: CallbackRequest, response: CallbackResponse) {
    this.events.push(`end:${response.statusCode}`);
  }

  override onError(_request: CallbackRequest, error: Error) {
    this.events.push(`error:${error.message}`);
  }

  override onRetry(_request: CallbackRequest, _error: Error, attempt: number) {
    this.events.push(`retry:${attempt}`);
  }

  override onCostUpdate(_request: CallbackRequest, cost: number, cumulative: number) {
    this.events.push(`cost:${cost}:${cumulative}`);
  }

  override onCacheHit(_request: CallbackRequest, _response: CallbackResponse, cacheType: string) {
    this.events.push(`cache:${cacheType}`);
  }

  override onGuardrailWarning() {
    this.events.push("guardrail_warning");
  }

  override onGuardrailBlock() {
    this.events.push("guardrail_block");
  }

  override onFallback(_req: CallbackRequest, original: string, fallback: string) {
    this.events.push(`fallback:${original}->${fallback}`);
  }
}

const dummyReq: CallbackRequest = {
  method: "POST",
  url: "http://localhost/v1/chat/completions",
  headers: {},
  body: { model: "gpt-4o", messages: [] },
};

describe("CallbackHandler", () => {
  it("all hooks are no-op by default", () => {
    const cb = new (class extends CallbackHandler {})();
    // None of these should throw
    cb.onRequestStart(dummyReq);
    cb.onRequestEnd(dummyReq, { statusCode: 200, headers: {}, agentcc: {} as any, body: null });
    cb.onError(dummyReq, new Error("test"));
    cb.onRetry(dummyReq, new Error("test"), 0, 500);
  });

  it("concrete subclass receives events", () => {
    const cb = new TestCallback();
    cb.onRequestStart(dummyReq);
    cb.onRequestEnd(dummyReq, { statusCode: 200, headers: {}, agentcc: {} as any, body: null });
    expect(cb.events).toEqual(["start:POST", "end:200"]);
  });
});

describe("invokeCallbacks", () => {
  it("calls method on all callbacks", async () => {
    const cb1 = new TestCallback();
    const cb2 = new TestCallback();
    await invokeCallbacks([cb1, cb2], "onRequestStart", dummyReq);
    expect(cb1.events).toEqual(["start:POST"]);
    expect(cb2.events).toEqual(["start:POST"]);
  });

  it("swallows callback errors", async () => {
    class BrokenCallback extends CallbackHandler {
      override onRequestStart() {
        throw new Error("callback exploded");
      }
    }
    const broken = new BrokenCallback();
    const good = new TestCallback();

    // Should not throw
    await invokeCallbacks([broken, good], "onRequestStart", dummyReq);
    // Good callback still ran
    expect(good.events).toEqual(["start:POST"]);
  });

  it("handles async callbacks", async () => {
    class AsyncCallback extends CallbackHandler {
      called = false;
      override async onRequestStart() {
        await new Promise((r) => setTimeout(r, 1));
        this.called = true;
      }
    }
    const cb = new AsyncCallback();
    await invokeCallbacks([cb], "onRequestStart", dummyReq);
    expect(cb.called).toBe(true);
  });
});
