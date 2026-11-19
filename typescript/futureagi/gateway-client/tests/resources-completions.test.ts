import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../src/client.js";

describe("completions resource (legacy)", () => {
  it("create() sends POST to /v1/completions", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "cmpl-abc",
          object: "text_completion",
          created: 1700000000,
          model: "gpt-3.5-turbo-instruct",
          choices: [{ text: "Hello there!", index: 0, finish_reason: "stop" }],
          usage: { prompt_tokens: 5, completion_tokens: 3, total_tokens: 8 },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.completions.create({
      model: "gpt-3.5-turbo-instruct",
      prompt: "Say hello",
      max_tokens: 10,
    });

    expect(result.choices[0].text).toBe("Hello there!");
    expect(result.agentcc).toBeDefined();
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/completions");
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body);
    expect(body.prompt).toBe("Say hello");
  });
});
