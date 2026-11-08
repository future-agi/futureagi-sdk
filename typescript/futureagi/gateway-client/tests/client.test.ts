import { describe, it, expect } from "@jest/globals";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { AgentCC, VERSION } from "../src/index.js";

// D-03: the version is @future-agi/sdk's (1.0.1 compared it with @agentcc/client's).
const PACKAGE_VERSION = (
  JSON.parse(readFileSync(join(__dirname, "../../package.json"), "utf8")) as { version: string }
).version;

describe("AgentCC client", () => {
  it("constructs with defaults", () => {
    const client = new AgentCC({ apiKey: "test-key" });
    expect(client).toBeDefined();
    expect(client.chat).toBeDefined();
    expect(client.chat.completions).toBeDefined();
    expect(client.embeddings).toBeDefined();
    expect(client.images).toBeDefined();
    expect(client.audio).toBeDefined();
    expect(client.models).toBeDefined();
    expect(client.completions).toBeDefined();
    // D-21: the gateway serves no /v1/moderations or /v1/batches route.
    expect((client as unknown as Record<string, unknown>).moderations).toBeUndefined();
    expect((client as unknown as Record<string, unknown>).batches).toBeUndefined();
    expect(client.files).toBeDefined();
    expect(client.rerank).toBeDefined();
  });

  it("tracks cumulative cost", () => {
    const client = new AgentCC({ apiKey: "test" });
    expect(client.currentCost).toBe(0);
    client.resetCost();
    expect(client.currentCost).toBe(0);
  });

  it("withOptions creates a new client", () => {
    const client = new AgentCC({ apiKey: "key1", timeout: 5000 });
    const clone = client.withOptions({ apiKey: "key2" });
    expect(clone).toBeInstanceOf(AgentCC);
    expect(clone).not.toBe(client);
  });

  it("exports version", () => {
    // VERSION feeds the User-Agent and x-agentcc-sdk-version headers.
    expect(VERSION).toBe(PACKAGE_VERSION);
  });
});
