import { AgentCC } from "../client";

describe("dryRun", () => {
  it("returns url, method, headers, and body", () => {
    const client = new AgentCC({ apiKey: "sk-test", baseUrl: "http://gw:8090" });
    const result = client.chat.completions.dryRun({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hello" }],
    });

    expect(result.method).toBe("POST");
    expect(result.url).toBe("http://gw:8090/v1/chat/completions");
    expect(result.headers["Authorization"]).toBe("Bearer sk-test");
    expect(result.body).toBeDefined();
    expect((result.body as any).model).toBe("gpt-4o");
    expect((result.body as any).messages).toHaveLength(1);
  });

  it("does not make a network call", () => {
    const mockFetch = jest.fn();
    const client = new AgentCC({
      apiKey: "sk-test",
      fetch: mockFetch as any,
    });

    client.chat.completions.dryRun({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hello" }],
    });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("applies modifyParams", () => {
    const client = new AgentCC({
      apiKey: "sk-test",
      modifyParams: (params) => ({ ...params, temperature: 0 }),
    });

    const result = client.chat.completions.dryRun({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hello" }],
    });

    expect((result.body as any).temperature).toBe(0);
  });

  it("extracts agentcc-specific params to headers", () => {
    const client = new AgentCC({ apiKey: "sk-test" });
    const result = client.chat.completions.dryRun({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hello" }],
      session_id: "sess-abc",
    } as any);

    // session_id should be extracted to a header
    expect(result.headers["x-agentcc-session-id"]).toBe("sess-abc");
    // And removed from body
    expect((result.body as any).session_id).toBeUndefined();
  });

  it("includes gateway config headers", () => {
    const client = new AgentCC({
      apiKey: "sk-test",
      config: { cache: { enabled: true, ttl: 300 } },
    });

    const result = client.chat.completions.dryRun({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hello" }],
    });

    // Should have cache headers from gateway config
    expect(result.headers).toBeDefined();
  });

  it("includes extra_headers in output", () => {
    const client = new AgentCC({ apiKey: "sk-test" });
    const result = client.chat.completions.dryRun({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hello" }],
      extra_headers: { "X-Custom": "value" },
    });

    expect(result.headers["X-Custom"]).toBe("value");
  });
});
