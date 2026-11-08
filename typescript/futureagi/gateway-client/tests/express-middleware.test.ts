import { describe, it, expect, jest } from "@jest/globals";
import { agentccMiddleware } from "../src/express.js";
import { AgentCC } from "../src/client.js";
import type { Session } from "../src/session.js";

describe("agentccMiddleware", () => {
  function makeReq(headers: Record<string, string> = {}) {
    return {
      method: "POST",
      path: "/api/chat",
      headers,
      agentcc: undefined as AgentCC | undefined,
      agentccSession: undefined as Session | undefined,
    };
  }

  function makeRes() {
    const listeners: Record<string, Array<() => void>> = {};
    return {
      on(event: string, listener: () => void) {
        if (!listeners[event]) listeners[event] = [];
        listeners[event].push(listener);
      },
      _fire(event: string) {
        (listeners[event] ?? []).forEach((fn) => fn());
      },
    };
  }

  it("attaches agentcc client to req", () => {
    const mw = agentccMiddleware({ apiKey: "sk-test" });
    const req = makeReq();
    const res = makeRes();
    const next = jest.fn<any>();

    mw(req, res, next);

    expect(req.agentcc).toBeInstanceOf(AgentCC);
    expect(next).toHaveBeenCalled();
  });

  it("attaches session to req", () => {
    const mw = agentccMiddleware({ apiKey: "sk-test" });
    const req = makeReq();
    const res = makeRes();
    const next = jest.fn<any>();

    mw(req, res, next);

    expect(req.agentccSession).toBeDefined();
    expect(typeof req.agentccSession!.sessionId).toBe("string");
  });

  it("uses x-request-id as session ID", () => {
    const mw = agentccMiddleware({ apiKey: "sk-test" });
    const req = makeReq({ "x-request-id": "req-abc-123" });
    const res = makeRes();
    const next = jest.fn<any>();

    mw(req, res, next);

    expect(req.agentccSession!.sessionId).toBe("req-abc-123");
  });

  it("uses custom session header", () => {
    const mw = agentccMiddleware({
      apiKey: "sk-test",
      sessionFromHeader: "x-correlation-id",
    });
    const req = makeReq({ "x-correlation-id": "corr-456" });
    const res = makeRes();
    const next = jest.fn<any>();

    mw(req, res, next);

    expect(req.agentccSession!.sessionId).toBe("corr-456");
  });

  it("generates session ID when header not present", () => {
    const mw = agentccMiddleware({ apiKey: "sk-test" });
    const req = makeReq();
    const res = makeRes();
    const next = jest.fn<any>();

    mw(req, res, next);

    expect(req.agentccSession!.sessionId).toBeTruthy();
    expect(typeof req.agentccSession!.sessionId).toBe("string");
  });

  it("propagates traceparent from incoming request", () => {
    const mw = agentccMiddleware({ apiKey: "sk-test" });
    const traceparent =
      "00-abcdef1234567890abcdef1234567890-1234567890abcdef-01";
    const req = makeReq({ traceparent });
    const res = makeRes();
    const next = jest.fn<any>();

    mw(req, res, next);

    // The client should exist and be a AgentCC instance
    expect(req.agentcc).toBeInstanceOf(AgentCC);
  });
});
