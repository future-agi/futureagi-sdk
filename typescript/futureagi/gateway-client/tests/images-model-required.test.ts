import { describe, expect, it, jest } from "@jest/globals";
import { AgentCC } from "../src/client.js";
import { AgentCCError } from "../src/errors.js";
import type { ImageGenerateParams } from "../src/types/image.js";

const invalid = [
  {}, { model: undefined }, { model: null }, { model: "" }, { model: " \t" }, { model: 3 },
  { extra_body: { model: "" } }, { extra_body: { model: null } },
  { extra_body: { model: " \n" } }, { model: "test-model", extra_body: { model: "" } },
];
const valid = [
  { model: "test-model" },
  { extra_body: { model: "test-model" } },
  { model: "", extra_body: { model: "test-model" } },
  { model: "other-model", extra_body: { model: "test-model" } },
];

function setup() {
  const fetch = jest.fn<typeof globalThis.fetch>().mockImplementation(async () => new Response(
    JSON.stringify({ created: 1, data: [] }), { status: 200, headers: { "content-type": "application/json" } },
  ));
  const client = new AgentCC({ apiKey: "test-key", baseUrl: "https://deployment.example.invalid", fetch, maxRetries: 0 });
  return { client, fetch };
}

describe("image generation model validation", () => {
  it.each(invalid)("rejects an absent or empty effective model (%j)", async (arguments_) => {
    const { client, fetch } = setup();
    let error: unknown;
    try {
      await client.images.generate({ prompt: "A tree", ...arguments_ } as ImageGenerateParams);
    } catch (caught) {
      error = caught;
    }
    expect(fetch).not.toHaveBeenCalled();
    expect(error).toBeInstanceOf(AgentCCError);
    expect((error as Error).message).toMatch(/model/);
  });

  it.each(valid)("accepts the effective model and preserves other fields (%j)", async (arguments_) => {
    const { client, fetch } = setup();
    const params = { prompt: "A tree", n: 2, extra_headers: { "X-Test": "value" }, ...arguments_ };
    const original = JSON.stringify(params);
    await expect(client.images.generate(params)).resolves.toMatchObject({ data: [] });
    expect(JSON.stringify(params)).toBe(original);
    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, init] = fetch.mock.calls[0];
    expect(String(url)).toBe("https://deployment.example.invalid/v1/images/generations");
    expect(init?.method).toBe("POST");
    expect(new Headers(init?.headers).get("X-Test")).toBe("value");
    expect(JSON.parse(init?.body as string)).toEqual({ prompt: "A tree", n: 2, model: "test-model" });
  });
});
