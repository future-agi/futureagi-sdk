/**
 * openaiOptions() and aiSdkProviderSettings() (D-08): plain options for the stock OpenAI SDK (and LangChain / LlamaIndex,
 * which take its options) and for the Vercel AI SDK's createOpenAI. They
 * always carry an explicit key; the Vercel settings have no default URL.
 * The vercel cases mirror the integration.vercel.* goldens of
 * @agentcc/vercel 1.0.0.
 */
import { describe, it, expect, beforeEach, afterEach } from "@jest/globals";
import { AgentCCError, aiSdkProviderSettings, openaiOptions } from "../../src/index.js";

let saved: NodeJS.ProcessEnv;
beforeEach(() => {
  saved = { ...process.env };
  for (const k of Object.keys(process.env)) if (/^(AGENTCC_|FI_|OPENAI_)/.test(k)) delete process.env[k];
});
afterEach(() => {
  process.env = saved;
});

describe("openaiOptions()", () => {
  it("returns an explicit key, the gateway origin plus /v1, and x-agentcc-* headers", () => {
    const opts = openaiOptions({ apiKey: "gw-key", baseUrl: "https://gw.example.test/v1/", sessionId: "s1", traceId: "t1", guardrailPolicy: "strict", properties: { team: "a" } });
    expect(opts).toEqual({
      apiKey: "gw-key",
      baseURL: "https://gw.example.test/v1",
      defaultHeaders: {
        "x-agentcc-session-id": "s1",
        "x-agentcc-trace-id": "t1",
        "X-Guardrail-Policy": "strict",
        "x-agentcc-property-team": "a",
        "OpenAI-Organization": null,
        "OpenAI-Project": null,
      },
    });
  });

  it("never puts the key in the headers (the OpenAI SDK sends it as Authorization itself)", () => {
    const opts = openaiOptions({ apiKey: "gw-key", baseUrl: "http://gw.test" });
    expect(Object.keys(opts.defaultHeaders).map((h) => h.toLowerCase())).not.toContain("authorization");
  });

  it("resolves key and URL from FI_GATEWAY_* then AGENTCC_*, with the client's loopback default", () => {
    process.env.AGENTCC_API_KEY = "agentcc-key";
    expect(openaiOptions()).toMatchObject({ apiKey: "agentcc-key", baseURL: "http://localhost:8090/v1" });
    process.env.FI_GATEWAY_API_KEY = "fi-key";
    process.env.FI_GATEWAY_BASE_URL = "http://fi-gw.test/v1";
    expect(openaiOptions()).toMatchObject({ apiKey: "fi-key", baseURL: "http://fi-gw.test/v1" });
  });

  it("throws AgentCCError when no key resolves, so OPENAI_API_KEY can never reach the gateway", () => {
    process.env.OPENAI_API_KEY = "sk-openai-must-not-leak";
    let caught: unknown;
    try {
      openaiOptions({ baseUrl: "http://gw.test" });
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(AgentCCError);
    expect((caught as Error).message).toContain("FI_GATEWAY_API_KEY");
    expect((caught as Error).message).toContain("OPENAI_API_KEY");
    expect((caught as Error).message).not.toContain("sk-openai-must-not-leak");
  });

  it("refuses the Future AGI key pair as the gateway key", () => {
    process.env.FI_API_KEY = "pair";
    expect(() => openaiOptions({ apiKey: "pair" })).toThrow(AgentCCError);
  });

  it("OPENAI_ORG_ID and OPENAI_PROJECT_ID are not forwarded: both headers are null (openai-node drops null headers)", () => {
    process.env.OPENAI_ORG_ID = "org-x";
    process.env.OPENAI_PROJECT_ID = "proj-x";
    const { defaultHeaders } = openaiOptions({ apiKey: "k" });
    expect(defaultHeaders["OpenAI-Organization"]).toBeNull();
    expect(defaultHeaders["OpenAI-Project"]).toBeNull();
    expect(JSON.stringify(defaultHeaders)).not.toMatch(/org-x|proj-x/);
  });

  it("a cache-only GatewayConfig is sent as x-agentcc-config; another section is a TypeError", () => {
    const opts = openaiOptions({ apiKey: "k", config: { cache: { ttl: 60 } } });
    expect(JSON.parse(String(opts.defaultHeaders["x-agentcc-config"]))).toEqual({ cache: { ttl: 60 } });
    expect(() => openaiOptions({ apiKey: "k", config: { retry: { attempts: 2 } } as never })).toThrow(TypeError);
  });
});

describe("aiSdkProviderSettings() (D-08)", () => {
  it("integration.vercel.defaults: nothing set throws (1.0 sent to https://api.agentcc.ai/v1)", () => {
    expect(() => aiSdkProviderSettings()).toThrow(AgentCCError);
  });

  it("integration.vercel.key_env_only: a key without a URL throws naming FI_GATEWAY_BASE_URL, never falling back to a host", () => {
    process.env.AGENTCC_API_KEY = "key-from-env";
    let caught: unknown;
    try {
      aiSdkProviderSettings();
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(AgentCCError);
    expect((caught as Error).message).toContain("FI_GATEWAY_BASE_URL");
    expect((caught as Error).message).not.toContain("agentcc.ai");
  });

  it("integration.vercel.env: AGENTCC_API_KEY and AGENTCC_BASE_URL resolve as in 1.0", () => {
    process.env.AGENTCC_API_KEY = "key-from-env";
    process.env.AGENTCC_BASE_URL = "https://agentcc-env.example.test/v1";
    expect(aiSdkProviderSettings()).toEqual({ apiKey: "key-from-env", baseURL: "https://agentcc-env.example.test/v1", headers: {}, compatibility: "compatible" });
  });

  it("FI_GATEWAY_* come first", () => {
    process.env.AGENTCC_API_KEY = "a";
    process.env.AGENTCC_BASE_URL = "https://a.test";
    process.env.FI_GATEWAY_API_KEY = "fi";
    process.env.FI_GATEWAY_BASE_URL = "https://fi.test/";
    expect(aiSdkProviderSettings()).toMatchObject({ apiKey: "fi", baseURL: "https://fi.test/v1" });
  });

  it("integration.vercel.explicit: the 1.0 headers except the two D-08 changes", () => {
    const settings = aiSdkProviderSettings({
      apiKey: "parity-gateway-key",
      baseURL: "https://gateway.example.test/v1",
      guardrailPolicy: "strict",
      sessionId: "s",
      traceId: "t",
      metadata: { k: "v" },
    });
    expect(settings).toEqual({
      apiKey: "parity-gateway-key",
      baseURL: "https://gateway.example.test/v1",
      headers: {
        "X-Guardrail-Policy": "strict",
        "x-agentcc-metadata": "{\"k\":\"v\"}",
        "x-agentcc-session-id": "s",
        "x-agentcc-trace-id": "t",
      },
      compatibility: "compatible",
    });
  });

  it("cacheEnabled sends only the TTL (no reader-less x-agentcc-cache: true); cacheTtl alone sends nothing, as 1.0", () => {
    expect(aiSdkProviderSettings({ apiKey: "k", baseURL: "http://gw.test", cacheEnabled: true, cacheTtl: "5m" }).headers).toEqual({ "x-agentcc-cache-ttl": "5m" });
    expect(aiSdkProviderSettings({ apiKey: "k", baseURL: "http://gw.test", cacheTtl: "5m" }).headers).toEqual({});
    expect(aiSdkProviderSettings({ apiKey: "k", baseURL: "http://gw.test", cacheEnabled: true }).headers).toEqual({});
  });

  it("userId, properties and extra headers are kept; extra headers merge last", () => {
    const { headers } = aiSdkProviderSettings({ apiKey: "k", baseURL: "http://gw.test", userId: "u", properties: { team: "a" }, headers: { "x-agentcc-trace-id": "override", "x-extra": "1" }, traceId: "t" });
    expect(headers).toEqual({ "x-agentcc-user-id": "u", "x-agentcc-property-team": "a", "x-agentcc-trace-id": "override", "x-extra": "1" });
  });

  it("throws without a key even when a URL is set (createOpenAI would read OPENAI_API_KEY)", () => {
    process.env.OPENAI_API_KEY = "sk-openai";
    expect(() => aiSdkProviderSettings({ baseURL: "http://gw.test" })).toThrow(AgentCCError);
  });

  it("refuses the Future AGI key pair", () => {
    process.env.FI_SECRET_KEY = "pair";
    expect(() => aiSdkProviderSettings({ apiKey: "pair", baseURL: "http://gw.test" })).toThrow(AgentCCError);
  });
});
