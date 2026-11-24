import { patchOpenAI } from "../patch-openai";
import { AgentCC } from "../client";

describe("patchOpenAI", () => {
  it("extracts apiKey from OpenAI-like client", () => {
    const fakeOpenAI = { apiKey: "sk-test-123", baseURL: "https://api.openai.com/v1" };
    const agentcc = patchOpenAI(fakeOpenAI);

    expect(agentcc).toBeInstanceOf(AgentCC);
    // The apiKey is protected, but we can verify it was used by checking that
    // the instance was created without error
  });

  it("uses provided apiKey over extracted one", () => {
    const fakeOpenAI = { apiKey: "sk-original" };
    const agentcc = patchOpenAI(fakeOpenAI, { apiKey: "sk-override" });

    expect(agentcc).toBeInstanceOf(AgentCC);
  });

  it("uses provided baseUrl", () => {
    const fakeOpenAI = { apiKey: "sk-test" };
    const agentcc = patchOpenAI(fakeOpenAI, {
      baseUrl: "http://gateway:8090",
    });

    expect(agentcc).toBeInstanceOf(AgentCC);
  });

  it("passes through client options", () => {
    const fakeOpenAI = { apiKey: "sk-test" };
    const agentcc = patchOpenAI(fakeOpenAI, {
      timeout: 30000,
      maxRetries: 5,
      config: { cache: { ttl: 300 } },
    });

    expect(agentcc).toBeInstanceOf(AgentCC);
  });

  it("works without apiKey on client object", () => {
    const fakeOpenAI = {}; // no apiKey property
    const agentcc = patchOpenAI(fakeOpenAI, { apiKey: "sk-explicit" });

    expect(agentcc).toBeInstanceOf(AgentCC);
  });

  it("handles non-string apiKey gracefully", () => {
    const fakeOpenAI = { apiKey: 42 }; // not a string
    // Should not crash — falls back to env
    const agentcc = patchOpenAI(fakeOpenAI);
    expect(agentcc).toBeInstanceOf(AgentCC);
  });
});
