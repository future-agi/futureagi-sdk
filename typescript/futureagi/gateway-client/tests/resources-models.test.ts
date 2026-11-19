import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../src/client.js";

function mockJsonResponse(data: Record<string, unknown>, status = 200) {
  return jest.fn<any>().mockResolvedValue(
    new Response(JSON.stringify(data), {
      status,
      headers: { "content-type": "application/json" },
    }),
  );
}

describe("models resource", () => {
  it("list() sends GET to /v1/models", async () => {
    const mockFetch = mockJsonResponse({
      object: "list",
      data: [
        { id: "gpt-4o", object: "model", created: 1700000000, owned_by: "openai" },
        { id: "gpt-3.5-turbo", object: "model", created: 1700000000, owned_by: "openai" },
      ],
    });
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.models.list();

    expect(result.data).toHaveLength(2);
    expect(result.data[0].id).toBe("gpt-4o");
    expect(result.agentcc).toBeDefined();
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/models");
    expect(init.method).toBe("GET");
  });

  it("retrieve() sends GET to /v1/models/:id", async () => {
    const mockFetch = mockJsonResponse({
      id: "gpt-4o",
      object: "model",
      created: 1700000000,
      owned_by: "openai",
    });
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.models.retrieve("gpt-4o");

    expect(result.id).toBe("gpt-4o");
    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/models/gpt-4o");
  });

  it("retrieve() encodes model ID", async () => {
    const mockFetch = mockJsonResponse({ id: "ft:gpt-4o:my-org", object: "model" });
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    await client.models.retrieve("ft:gpt-4o:my-org");

    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain(encodeURIComponent("ft:gpt-4o:my-org"));
  });
});
