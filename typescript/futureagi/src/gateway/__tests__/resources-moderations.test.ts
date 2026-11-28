import { AgentCC } from "../client";

describe("moderations resource", () => {
  it("create() sends POST to /v1/moderations", async () => {
    const mockFetch = jest.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "modr-abc",
          model: "text-moderation-latest",
          results: [
            {
              flagged: false,
              categories: { hate: false, sexual: false },
              category_scores: { hate: 0.001, sexual: 0.002 },
            },
          ],
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.moderations.create({
      model: "text-moderation-latest",
      input: "This is a test",
    });

    expect(result.results[0].flagged).toBe(false);
    expect(result.agentcc).toBeDefined();
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.input).toBe("This is a test");
  });
});
