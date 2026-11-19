/**
 * D-18 outside a browser page: Node (this environment), a web worker (no
 * window) and a runtime with a window but no document (Deno 1.x) build the
 * client without the opt-in and send the SDK headers as before.
 */
import { describe, it, expect, afterEach } from "@jest/globals";
import { AgentCC, AgentCCError, VERSION } from "../../src/index.js";
import { isBrowser } from "../../src/browser.js";

const PARAMS = { model: "m", messages: [{ role: "user" as const, content: "hi" }] };
// Node 21+ has a navigator global of its own: restore what was there.
const saved = new Map<string, PropertyDescriptor | undefined>();
function setGlobal(name: string, value: unknown) {
  if (!saved.has(name)) saved.set(name, Object.getOwnPropertyDescriptor(globalThis, name));
  Object.defineProperty(globalThis, name, { value, configurable: true, writable: true });
}
afterEach(() => {
  for (const [name, descriptor] of saved) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else delete (globalThis as Record<string, unknown>)[name];
  }
  saved.clear();
});

describe("D-18 outside a browser page", () => {
  it("Node is not a browser page; the SDK headers are sent", () => {
    expect(isBrowser()).toBe(false);
    const { headers } = new AgentCC({ apiKey: "k" }).chat.completions.dryRun(PARAMS);
    expect(headers["User-Agent"]).toBe(`futureagi-typescript/${VERSION}`);
    expect(headers["x-agentcc-sdk-version"]).toBe(VERSION);
  });

  it("a window without a document (Deno 1.x) is not a browser page", () => {
    setGlobal("window", {});
    expect(isBrowser()).toBe(false);
    expect(() => new AgentCC({ apiKey: "k" })).not.toThrow();
  });

  it("a worker (navigator, no window) is not a browser page", () => {
    setGlobal("navigator", { userAgent: "worker" });
    expect(isBrowser()).toBe(false);
  });

  it("window, document and navigator together are a browser page", () => {
    setGlobal("window", { document: {} });
    setGlobal("navigator", { userAgent: "x" });
    expect(isBrowser()).toBe(true);
    expect(() => new AgentCC({ apiKey: "k" })).toThrow(AgentCCError);
    expect(() => new AgentCC({ apiKey: "k", dangerouslyAllowBrowser: true })).not.toThrow();
  });
});
