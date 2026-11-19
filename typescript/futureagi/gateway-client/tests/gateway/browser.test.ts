/**
 * @jest-environment ./tests/jsdom-with-fetch.environment.cjs
 */
/**
 * D-18 in a browser page (jsdom: window, document and navigator exist).
 * Construction throws unless dangerouslyAllowBrowser is true; with it, the
 * client leaves out x-agentcc-sdk-version and User-Agent, which the gateway's
 * CORS allowlist does not name (middleware/cors.go at the recorded revision).
 */
import { describe, it, expect } from "@jest/globals";
import { AgentCC, AgentCCError } from "../../src/index.js";
import { isBrowser } from "../../src/browser.js";

const PARAMS = { model: "m", messages: [{ role: "user" as const, content: "hi" }] };

describe("D-18 in a browser page", () => {
  it("jsdom counts as a browser page", () => {
    expect(typeof (globalThis as { window?: unknown }).window).toBe("object");
    expect(isBrowser()).toBe(true);
  });

  it("construction throws AgentCCError pointing at the server route and the opt-in", () => {
    let caught: unknown;
    try {
      new AgentCC({ apiKey: "k", baseUrl: "https://gw.example.test" });
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(AgentCCError);
    const message = (caught as Error).message;
    expect(message).toContain("dangerouslyAllowBrowser: true");
    expect(message).toContain("@future-agi/sdk/gateway/nextjs");
    expect(message).not.toContain("k\"");
  });

  it("dangerouslyAllowBrowser: false still throws", () => {
    expect(() => new AgentCC({ apiKey: "k", dangerouslyAllowBrowser: false })).toThrow(AgentCCError);
  });

  it("with dangerouslyAllowBrowser: true the client is built and sends no x-agentcc-sdk-version or User-Agent", () => {
    const client = new AgentCC({ apiKey: "k", baseUrl: "https://gw.example.test", dangerouslyAllowBrowser: true });
    const { headers, url } = client.chat.completions.dryRun(PARAMS);
    const names = Object.keys(headers).map((h) => h.toLowerCase());
    expect(url).toBe("https://gw.example.test/v1/chat/completions");
    expect(names).not.toContain("x-agentcc-sdk-version");
    expect(names).not.toContain("user-agent");
    expect(headers.Authorization).toBe("Bearer k");
    expect(headers["Content-Type"]).toBe("application/json");
  });

  it("withOptions and session clients keep the opt-in", () => {
    const client = new AgentCC({ apiKey: "k", dangerouslyAllowBrowser: true });
    expect(() => client.withOptions({ timeout: 5 })).not.toThrow();
    expect(() => client.session({ name: "s" })).not.toThrow();
    expect(() => client.withOptions({ dangerouslyAllowBrowser: false })).toThrow(AgentCCError);
  });
});
