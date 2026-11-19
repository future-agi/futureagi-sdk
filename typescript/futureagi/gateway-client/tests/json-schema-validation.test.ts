import { describe, it, expect, jest } from "@jest/globals";
import { AgentCC } from "../src/client.js";

describe("enableJsonSchemaValidation", () => {
  function makeMockFetch(responseContent: string) {
    return jest.fn<any>().mockResolvedValue(
      new Response(
        JSON.stringify({
          id: "chatcmpl-1",
          object: "chat.completion",
          created: 1700000000,
          model: "gpt-4o",
          choices: [
            {
              index: 0,
              message: { role: "assistant", content: responseContent },
              finish_reason: "stop",
            },
          ],
          usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
  }

  it("passes validation when response matches schema", async () => {
    const mockFetch = makeMockFetch('{"name":"Alice","age":30}');
    const client = new AgentCC({
      apiKey: "sk-test",
      enableJsonSchemaValidation: true,
      fetch: mockFetch,
    });

    const response = await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Give me a person" }],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "person",
          strict: true,
          schema: {
            type: "object",
            properties: {
              name: { type: "string" },
              age: { type: "number" },
            },
            required: ["name", "age"],
          },
        },
      },
    });

    expect(response.choices[0].message.content).toBe('{"name":"Alice","age":30}');
  });

  it("throws when response does not match schema", async () => {
    const mockFetch = makeMockFetch('{"name":"Alice","age":"thirty"}');
    const client = new AgentCC({
      apiKey: "sk-test",
      enableJsonSchemaValidation: true,
      fetch: mockFetch,
    });

    await expect(
      client.chat.completions.create({
        model: "gpt-4o",
        messages: [{ role: "user", content: "Give me a person" }],
        response_format: {
          type: "json_schema",
          json_schema: {
            name: "person",
            strict: true,
            schema: {
              type: "object",
              properties: {
                name: { type: "string" },
                age: { type: "number" },
              },
              required: ["name", "age"],
            },
          },
        },
      }),
    ).rejects.toThrow("Structured output validation failed");
  });

  it("skips validation when not using json_schema response_format", async () => {
    const mockFetch = makeMockFetch("Just a regular response");
    const client = new AgentCC({
      apiKey: "sk-test",
      enableJsonSchemaValidation: true,
      fetch: mockFetch,
    });

    // No response_format, should not throw
    const response = await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Hello" }],
    });

    expect(response.choices[0].message.content).toBe("Just a regular response");
  });

  it("skips validation when flag is false", async () => {
    const mockFetch = makeMockFetch('{"name":"Alice","age":"thirty"}');
    const client = new AgentCC({
      apiKey: "sk-test",
      enableJsonSchemaValidation: false,
      fetch: mockFetch,
    });

    // Should NOT throw even with invalid data
    const response = await client.chat.completions.create({
      model: "gpt-4o",
      messages: [{ role: "user", content: "Give me a person" }],
      response_format: {
        type: "json_schema",
        json_schema: {
          name: "person",
          strict: true,
          schema: {
            type: "object",
            properties: { age: { type: "number" } },
          },
        },
      },
    });

    expect(response).toBeDefined();
  });
});
