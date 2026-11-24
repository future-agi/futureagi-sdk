import { AgentCC, VERSION } from "../index";

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
    expect(client.moderations).toBeDefined();
    expect(client.completions).toBeDefined();
    expect(client.batches).toBeDefined();
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
    expect(VERSION).toBe("0.1.0");
  });
});
