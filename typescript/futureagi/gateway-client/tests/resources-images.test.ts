import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../src/client.js";

describe("images resource", () => {
  it("generate() sends POST to /v1/images/generations", async () => {
    const mockFetch = jest.fn<any>().mockResolvedValue(
      new Response(
        JSON.stringify({
          created: 1700000000,
          data: [{ url: "https://example.com/image.png" }],
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    const client = new AgentCC({ apiKey: "sk-test", fetch: mockFetch });

    const result = await client.images.generate({
      model: "dall-e-3",
      prompt: "A cat in space",
      n: 1,
      size: "1024x1024",
    });

    expect(result.data[0].url).toBe("https://example.com/image.png");
    expect(result.agentcc).toBeDefined();
    const [url, init] = mockFetch.mock.calls[0];
    expect(url).toContain("/v1/images/generations");
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body);
    expect(body.prompt).toBe("A cat in space");
    expect(body.model).toBe("dall-e-3");
  });
});
