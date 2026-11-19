import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../src/client.js";

describe("rerank resource", () => {
  it("rank() sends POST to /v1/rerank", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(
        JSON.stringify({
          results: [
            { index: 0, relevance_score: 0.95 },
            { index: 1, relevance_score: 0.42 },
          ],
          model: "rerank-english-v3.0",
          usage: { total_tokens: 20 },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.rerank.rank({
      model: "rerank-english-v3.0",
      query: "What is machine learning?",
      documents: ["ML is a branch of AI", "Cooking recipes"],
      top_n: 2,
    });

    expect(result.results).toHaveLength(2);
    expect(result.results[0].relevance_score).toBe(0.95);
    expect(result.agentcc).toBeDefined();
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.query).toBe("What is machine learning?");
    expect(body.documents).toHaveLength(2);
    expect(body.top_n).toBe(2);
  });
});
