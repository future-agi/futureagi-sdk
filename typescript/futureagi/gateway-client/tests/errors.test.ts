import { describe, it, expect } from "@jest/globals";
import {
  AgentCCError,
  APIStatusError,
  BadRequestError,
  AuthenticationError,
  RateLimitError,
  GuardrailBlockedError,
  GuardrailWarning,
  APIConnectionError,
  APITimeoutError,
  StreamError,
} from "../src/errors.js";

function makeHeaders(init: Record<string, string> = {}): Headers {
  return new Headers(init);
}

describe("Error hierarchy", () => {
  it("AgentCCError is base", () => {
    const err = new AgentCCError("test");
    expect(err).toBeInstanceOf(Error);
    expect(err.name).toBe("AgentCCError");
    expect(err.message).toBe("test");
  });

  it("APIConnectionError extends AgentCCError", () => {
    const err = new APIConnectionError("conn fail");
    expect(err).toBeInstanceOf(AgentCCError);
    expect(err.name).toBe("APIConnectionError");
  });

  it("APITimeoutError extends APIConnectionError", () => {
    const err = new APITimeoutError();
    expect(err).toBeInstanceOf(APIConnectionError);
    expect(err).toBeInstanceOf(AgentCCError);
    expect(err.name).toBe("APITimeoutError");
  });

  it("StreamError extends AgentCCError", () => {
    const err = new StreamError("stream broken");
    expect(err).toBeInstanceOf(AgentCCError);
    expect(err.name).toBe("StreamError");
  });

  it("APIStatusError.from returns specific subclass", () => {
    expect(APIStatusError.from(400, {}, makeHeaders())).toBeInstanceOf(BadRequestError);
    expect(APIStatusError.from(401, {}, makeHeaders())).toBeInstanceOf(AuthenticationError);
    expect(APIStatusError.from(429, {}, makeHeaders())).toBeInstanceOf(RateLimitError);
    expect(APIStatusError.from(446, {}, makeHeaders())).toBeInstanceOf(GuardrailBlockedError);
    expect(APIStatusError.from(246, {}, makeHeaders())).toBeInstanceOf(GuardrailWarning);
    expect(APIStatusError.from(418, {}, makeHeaders())).toBeInstanceOf(APIStatusError);
  });

  it("RateLimitError parses rate-limit headers", () => {
    const headers = makeHeaders({
      "x-ratelimit-limit-requests": "100",
      "x-ratelimit-remaining-requests": "5",
      "x-ratelimit-reset-requests": "30",
    });
    const err = new RateLimitError({}, headers);
    expect(err.ratelimitLimit).toBe(100);
    expect(err.ratelimitRemaining).toBe(5);
    expect(err.ratelimitReset).toBe(30);
  });

  it("GuardrailBlockedError parses guardrail headers", () => {
    const headers = makeHeaders({
      "x-agentcc-guardrail-name": "pii-detection",
      "x-agentcc-guardrail-action": "block",
      "x-agentcc-guardrail-confidence": "0.95",
      "x-agentcc-guardrail-message": "PII detected",
    });
    const err = new GuardrailBlockedError({}, headers);
    expect(err.guardrailName).toBe("pii-detection");
    expect(err.guardrailAction).toBe("block");
    expect(err.guardrailConfidence).toBe(0.95);
    expect(err.guardrailMessage).toBe("PII detected");
    expect(err.statusCode).toBe(446);
  });

  it("GuardrailWarning stores completion body", () => {
    const body = { id: "chatcmpl-123", choices: [] };
    const err = new GuardrailWarning(body, makeHeaders());
    expect(err.completion).toBe(body);
    expect(err.statusCode).toBe(246);
  });

  it("APIStatusError parses request-id header", () => {
    const headers = makeHeaders({
      "x-agentcc-request-id": "req-abc-123",
    });
    const err = new APIStatusError(500, {}, headers);
    expect(err.requestId).toBe("req-abc-123");
  });
});
