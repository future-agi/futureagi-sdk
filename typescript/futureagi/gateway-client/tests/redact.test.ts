import { describe, it, expect } from "@jest/globals";
import { redactCallbackRequest } from "../src/redact.js";
import type { CallbackRequest } from "../src/callbacks.js";

describe("redactCallbackRequest", () => {
  it("redacts message content", () => {
    const req: CallbackRequest = {
      method: "POST",
      url: "http://localhost/v1/chat/completions",
      headers: {},
      body: {
        model: "gpt-4o",
        messages: [
          { role: "system", content: "You are helpful." },
          { role: "user", content: "What is my SSN?" },
        ],
      },
    };
    const redacted = redactCallbackRequest(req);
    const body = redacted.body as Record<string, unknown>;
    const msgs = body.messages as Array<Record<string, unknown>>;
    expect(msgs[0].content).toBe("[REDACTED]");
    expect(msgs[1].content).toBe("[REDACTED]");
    expect(msgs[0].role).toBe("system");
    expect(msgs[1].role).toBe("user");
  });

  it("preserves model and non-content fields", () => {
    const req: CallbackRequest = {
      method: "POST",
      url: "http://localhost/v1/chat/completions",
      headers: { Authorization: "Bearer sk-test" },
      body: {
        model: "gpt-4o",
        temperature: 0.7,
        messages: [{ role: "user", content: "hello" }],
      },
    };
    const redacted = redactCallbackRequest(req);
    const body = redacted.body as Record<string, unknown>;
    expect(body.model).toBe("gpt-4o");
    expect(body.temperature).toBe(0.7);
  });

  it("redacts legacy prompt", () => {
    const req: CallbackRequest = {
      method: "POST",
      url: "http://localhost/v1/completions",
      headers: {},
      body: { model: "gpt-3.5-turbo", prompt: "Say something secret" },
    };
    const redacted = redactCallbackRequest(req);
    expect((redacted.body as Record<string, unknown>).prompt).toBe("[REDACTED]");
  });

  it("redacts embedding input", () => {
    const req: CallbackRequest = {
      method: "POST",
      url: "http://localhost/v1/embeddings",
      headers: {},
      body: { model: "text-embedding-3-small", input: "secret text" },
    };
    const redacted = redactCallbackRequest(req);
    expect((redacted.body as Record<string, unknown>).input).toBe("[REDACTED]");
  });

  it("redacts array input", () => {
    const req: CallbackRequest = {
      method: "POST",
      url: "http://localhost/v1/embeddings",
      headers: {},
      body: { model: "text-embedding-3-small", input: ["text1", "text2"] },
    };
    const redacted = redactCallbackRequest(req);
    const input = (redacted.body as Record<string, unknown>).input as string[];
    expect(input).toEqual(["[REDACTED]", "[REDACTED]"]);
  });

  it("does not mutate original request", () => {
    const req: CallbackRequest = {
      method: "POST",
      url: "http://localhost/v1/chat/completions",
      headers: {},
      body: {
        model: "gpt-4o",
        messages: [{ role: "user", content: "original" }],
      },
    };
    redactCallbackRequest(req);
    const msgs = (req.body as Record<string, unknown>).messages as Array<Record<string, unknown>>;
    expect(msgs[0].content).toBe("original");
  });

  it("handles null body", () => {
    const req: CallbackRequest = {
      method: "GET",
      url: "http://localhost/healthz",
      headers: {},
      body: null,
    };
    const redacted = redactCallbackRequest(req);
    expect(redacted.body).toBeNull();
  });
});
