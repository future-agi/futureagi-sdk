import { describe, it, expect } from "@jest/globals";
import { extractAgentCCParams } from "../src/agentcc-params.js";

describe("extractAgentCCParams", () => {
  it("extracts agentcc params to headers and removes from body", () => {
    const { headers, cleanBody } = extractAgentCCParams({
      model: "gpt-4o",
      messages: [{ role: "user", content: "hi" }],
      session_id: "sess-123",
      trace_id: "trace-abc",
      cache_ttl: 300,
    });

    expect(headers["x-agentcc-session-id"]).toBe("sess-123");
    expect(headers["x-agentcc-trace-id"]).toBe("trace-abc");
    expect(headers["x-agentcc-cache-ttl"]).toBe("300");
    expect(cleanBody).toEqual({
      model: "gpt-4o",
      messages: [{ role: "user", content: "hi" }],
    });
    expect(cleanBody).not.toHaveProperty("session_id");
    expect(cleanBody).not.toHaveProperty("trace_id");
    expect(cleanBody).not.toHaveProperty("cache_ttl");
  });

  it("serializes metadata as JSON", () => {
    const { headers } = extractAgentCCParams({
      model: "gpt-4o",
      messages: [],
      request_metadata: { user: "test", env: "dev" },
    });
    expect(JSON.parse(headers["x-agentcc-metadata"])).toEqual({
      user: "test",
      env: "dev",
    });
  });

  it("serializes booleans", () => {
    const { headers } = extractAgentCCParams({
      model: "gpt-4o",
      messages: [],
      cache_force_refresh: true,
    });
    expect(headers["x-agentcc-cache-force-refresh"]).toBe("true");
  });

  it("skips null/undefined agentcc params", () => {
    const { headers } = extractAgentCCParams({
      model: "gpt-4o",
      messages: [],
      session_id: null,
      trace_id: undefined,
    });
    expect(headers).not.toHaveProperty("x-agentcc-session-id");
    expect(headers).not.toHaveProperty("x-agentcc-trace-id");
  });

  it("excludes extra_headers and extra_body from cleanBody", () => {
    const { cleanBody } = extractAgentCCParams({
      model: "gpt-4o",
      messages: [],
      extra_headers: { "x-custom": "value" },
      extra_body: { custom_field: true },
    });
    expect(cleanBody).not.toHaveProperty("extra_headers");
    expect(cleanBody).not.toHaveProperty("extra_body");
  });
});
