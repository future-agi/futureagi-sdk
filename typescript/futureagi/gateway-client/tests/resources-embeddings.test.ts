import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../src/client.js";

function mockJsonResponse(data: Record<string, unknown>) {
  return jest.fn<any>().mockResolvedValue(
    new Response(JSON.stringify(data), {
      status: 200,
      headers: { "content-type": "application/json" },
    }),
  );
}

describe("embeddings resource", () => {
  it("create() sends POST to /v1/embeddings", async () => {
    const mockFetch = mockJsonResponse({
      object: "list",
      data: [{ embedding: [0.1, 0.2, 0.3], index: 0 }],
      model: "text-embedding-3-small",
      usage: { prompt_tokens: 5, total_tokens: 5 },
    });
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.embeddings.create({
      model: "text-embedding-3-small",
      input: "Hello world",
    });

    expect(result.data[0].embedding).toEqual([0.1, 0.2, 0.3]);
    expect(result.agentcc).toBeDefined();
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/embeddings");
    expect(init.method).toBe("POST");
  });

  it("create() passes model and input in body", async () => {
    const mockFetch = mockJsonResponse({
      data: [{ embedding: [0.1], index: 0 }],
      usage: { prompt_tokens: 1, total_tokens: 1 },
    });
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    await client.embeddings.create({
      model: "text-embedding-3-large",
      input: ["text1", "text2"],
    });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.model).toBe("text-embedding-3-large");
    expect(body.input).toEqual(["text1", "text2"]);
  });
});
