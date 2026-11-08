import { describe, it, expect } from "@jest/globals";
import { Session } from "../src/session.js";

describe("Session", () => {
  it("generates a session ID if not provided", () => {
    const s = new Session();
    expect(s.sessionId).toBeTruthy();
    expect(typeof s.sessionId).toBe("string");
  });

  it("uses provided session ID", () => {
    const s = new Session({ sessionId: "sess-123" });
    expect(s.sessionId).toBe("sess-123");
  });

  it("tracks steps in path", () => {
    const s = new Session();
    expect(s.path).toBe("/");
    s.step("research");
    expect(s.path).toBe("/research");
    s.step("summarize");
    expect(s.path).toBe("/research/summarize");
  });

  it("resetPath returns to root", () => {
    const s = new Session();
    s.step("a");
    s.step("b");
    expect(s.path).toBe("/a/b");
    s.resetPath();
    expect(s.path).toBe("/");
  });

  it("tracks request metrics", () => {
    const s = new Session();
    expect(s.totalCost).toBe(0);
    expect(s.requestCount).toBe(0);
    expect(s.totalTokens).toBe(0);

    s.trackRequest(0.005, 150);
    s.trackRequest(0.003, 100);

    expect(s.totalCost).toBeCloseTo(0.008);
    expect(s.requestCount).toBe(2);
    expect(s.totalTokens).toBe(250);
  });

  it("toHeaders includes session-id", () => {
    const s = new Session({ sessionId: "sess-abc", name: "research" });
    const h = s.toHeaders();
    expect(h["x-agentcc-session-id"]).toBe("sess-abc");
    expect(h["x-agentcc-session-name"]).toBe("research");
  });

  it("toHeaders includes path when not root", () => {
    const s = new Session({ sessionId: "s1" });
    expect(s.toHeaders()["x-agentcc-session-path"]).toBeUndefined();
    s.step("analyze");
    expect(s.toHeaders()["x-agentcc-session-path"]).toBe("/analyze");
  });

  it("toHeaders includes metadata as JSON", () => {
    const s = new Session({
      sessionId: "s1",
      metadata: { env: "prod", tier: "premium" },
    });
    const h = s.toHeaders();
    expect(JSON.parse(h["x-agentcc-metadata"])).toEqual({
      env: "prod",
      tier: "premium",
    });
  });

  it("toHeaders omits empty name and metadata", () => {
    const s = new Session({ sessionId: "s1" });
    const h = s.toHeaders();
    expect(h["x-agentcc-session-name"]).toBeUndefined();
    expect(h["x-agentcc-metadata"]).toBeUndefined();
  });
});
