/**
 * @jest-environment ./tests/jsdom-with-fetch.environment.cjs
 */
import { describe, it, expect } from "@jest/globals";
// Test the provider module exports and types without React DOM
// We verify the module structure and types are correct

describe("agentcc-react exports", () => {
  it("exports AgentCCProvider as a function", async () => {
    const mod = await import("../../src/react/index.js");
    expect(typeof mod.AgentCCProvider).toBe("function");
  });

  it("exports useAgentCCClient as a function", async () => {
    const mod = await import("../../src/react/index.js");
    expect(typeof mod.useAgentCCClient).toBe("function");
  });

  it("exports useAgentCCChat as a function", async () => {
    const mod = await import("../../src/react/index.js");
    expect(typeof mod.useAgentCCChat).toBe("function");
  });

  it("exports useAgentCCChatWithClient as a function", async () => {
    const mod = await import("../../src/react/index.js");
    expect(typeof mod.useAgentCCChatWithClient).toBe("function");
  });

  it("exports useAgentCCCompletion as a function", async () => {
    const mod = await import("../../src/react/index.js");
    expect(typeof mod.useAgentCCCompletion).toBe("function");
  });

  it("exports useAgentCCCompletionWithClient as a function", async () => {
    const mod = await import("../../src/react/index.js");
    expect(typeof mod.useAgentCCCompletionWithClient).toBe("function");
  });

  it("exports useAgentCCObject as a function", async () => {
    const mod = await import("../../src/react/index.js");
    expect(typeof mod.useAgentCCObject).toBe("function");
  });

  it("exports useAgentCCObjectWithClient as a function", async () => {
    const mod = await import("../../src/react/index.js");
    expect(typeof mod.useAgentCCObjectWithClient).toBe("function");
  });

  it("exports AgentCCContext", async () => {
    const mod = await import("../../src/react/index.js");
    expect(mod.AgentCCContext).toBeDefined();
    // React context has Provider and Consumer
    expect(mod.AgentCCContext.Provider).toBeDefined();
  });
});
