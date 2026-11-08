/**
 * D-14b: createHeaders({ apiKey }) refuses the Future AGI key pair like every
 * other entry point (the client, withOptions, express, nextjs, openaiOptions,
 * aiSdkProviderSettings). The gateway takes a virtual key; an apiKey equal
 * to FI_API_KEY or FI_SECRET_KEY from the environment raises AgentCCError
 * instead of becoming "Authorization: Bearer <the FI key>". @agentcc/client
 * 1.0.1 had no guard at all.
 */
import { describe, it, expect, beforeEach, afterEach } from "@jest/globals";
import { AgentCCError, createHeaders, openaiOptions } from "../../src/index.js";

let saved: NodeJS.ProcessEnv;
beforeEach(() => {
  saved = { ...process.env };
  for (const k of Object.keys(process.env)) if (/^(AGENTCC_|FI_|OPENAI_)/.test(k)) delete process.env[k];
});
afterEach(() => {
  process.env = saved;
});

describe("D-14b createHeaders FI key-pair guard", () => {
  it("an apiKey equal to FI_API_KEY raises AgentCCError and names the variable, never the value", () => {
    process.env.FI_API_KEY = "fi-api-3";
    let caught: unknown;
    try {
      createHeaders({ apiKey: "fi-api-3" });
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(AgentCCError);
    expect((caught as Error).message).toContain("FI_API_KEY");
    expect((caught as Error).message).not.toContain("fi-api-3");
  });

  it("an apiKey equal to FI_SECRET_KEY raises AgentCCError", () => {
    process.env.FI_SECRET_KEY = "fi-secret-3";
    expect(() => createHeaders({ apiKey: "fi-secret-3", sessionId: "s" })).toThrow(AgentCCError);
  });

  it("a gateway key that differs from the key pair is sent as before", () => {
    process.env.FI_API_KEY = "fi-api-3";
    process.env.FI_SECRET_KEY = "fi-secret-3";
    expect(createHeaders({ apiKey: "sk-gw-1", sessionId: "s" })).toEqual({ Authorization: "Bearer sk-gw-1", "x-agentcc-session-id": "s" });
  });

  it("no apiKey: no Authorization header and no guard, with the key pair set", () => {
    process.env.FI_API_KEY = "fi-api-3";
    expect(createHeaders({ traceId: "t" })).toEqual({ "x-agentcc-trace-id": "t" });
  });

  it("an empty FI_API_KEY never matches", () => {
    process.env.FI_API_KEY = "";
    expect(createHeaders({ apiKey: "k" }).Authorization).toBe("Bearer k");
  });

  it("openaiOptions still refuses the key pair (it resolves the key before createHeaders)", () => {
    process.env.FI_API_KEY = "fi-api-3";
    expect(() => openaiOptions({ apiKey: "fi-api-3", baseUrl: "http://gw.test" })).toThrow(AgentCCError);
  });
});
