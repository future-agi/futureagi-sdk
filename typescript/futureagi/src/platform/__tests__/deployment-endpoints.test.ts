import { Client } from "../client";
import { AuthenticationError, InternalServerError, NotFoundError } from "../errors";
import * as usage from "../resources/usage";
import { Prompt } from "../../prompt/client";
import { ModelConfig, PromptTemplate, UserMessage } from "../../prompt/types";
import { HttpMethod } from "../../api/types";

beforeEach(() => {
  jest.spyOn(globalThis, "fetch").mockImplementation(async () => {
    throw new Error("Offline tests must use their mock transport");
  });
});
afterEach(() => jest.restoreAllMocks());

test("saving a draft sends false without changing its other fields", async () => {
  const template = new PromptTemplate({
    id: "template-1", version: "v7", messages: [new UserMessage("Hello {{name}}")],
    model_configuration: new ModelConfig({ model_name: "test-model", max_tokens: 1000 }),
    variable_names: { name: ["Ada"] }, evaluation_configs: [{ name: "test-eval" }],
  });
  const prompt = new Prompt(template, {
    fiApiKey: "test-key", fiSecretKey: "test-secret", fiBaseUrl: "https://deployment.example.invalid",
  });
  jest.spyOn(prompt as any, "_currentVersionIsDraft").mockResolvedValue(true);
  const { messages, placeholders } = (prompt as any)._prepareMessagesAndPlaceholders();
  const request = jest.spyOn(prompt, "request").mockResolvedValue({});
  try {
    await expect(prompt.saveCurrentDraft()).resolves.toBe(true);
    expect(request).toHaveBeenCalledTimes(1);
    expect(request.mock.calls[0][0]).toEqual({
      method: HttpMethod.POST,
      url: expect.stringContaining("template-1"),
      timeout: 60000,
      json: {
        is_run: false, is_sdk: true, version: "v7",
        prompt_config: [{
          messages,
          configuration: {
            model: "test-model", temperature: 0.7, max_tokens: 1000,
            top_p: 1, frequency_penalty: 0, presence_penalty: 0,
          },
          placeholders: Object.keys(placeholders),
        }],
        variable_names: template.variable_names,
        evaluation_configs: template.evaluation_configs, placeholders,
      },
    });
    expect(request.mock.calls[0][0].json?.is_run).toBe(false);
  } finally {
    await prompt.close();
  }
});

test.each([
  [404, NotFoundError], [401, AuthenticationError], [500, InternalServerError],
] as const)("usage overview keeps compatible errors for status %s", async (status, oldType) => {
  const body = { detail: "unavailable", type: "test-type", code: "test-code" };
  const fetch = jest.fn(async (_url: string, _init: RequestInit) => new Response(JSON.stringify(body), {
    status, headers: { "x-request-id": "test-request" },
  }));
  const client = new Client({
    apiKey: "test-key", secretKey: "test-secret", baseUrl: "https://deployment.example.invalid",
    fetch, maxRetries: 0,
  });
  let error: unknown;
  try {
    await client.usage.overview(
      { period: "month", period_end: "2026-01-01", workspace_id: "workspace-1" },
      { headers: { "X-Test": "value" } },
    );
  } catch (caught) {
    error = caught;
  }
  expect(error).toBeInstanceOf(oldType);
  const typed = error as NotFoundError;
  expect(typed.status).toBe(status);
  expect(typed.body).toEqual(body);
  expect(typed.requestId).toBe("test-request");
  expect(fetch).toHaveBeenCalledTimes(1);
  const [url, init] = fetch.mock.calls[0];
  expect(new URL(url).pathname).toBe("/usage/v2/usage-overview/");
  expect(Object.fromEntries(new URL(url).searchParams)).toEqual({
    period: "month", period_end: "2026-01-01", workspace_id: "workspace-1",
  });
  expect(init.method).toBe("GET");
  expect(new Headers(init.headers).get("X-Test")).toBe("value");
  if (status === 404) {
    expect(typed.name).toBe("UsageOverviewUnavailableError");
    const errorType = (usage as unknown as Record<string, unknown>).UsageOverviewUnavailableError;
    expect(errorType).toBeDefined();
    expect(error).toBeInstanceOf(errorType as typeof NotFoundError);
    expect(typed.message.toLowerCase()).toContain("this deployment does not provide");
    expect(typed.message).toContain("GET /usage/v2/usage-overview/");
  } else {
    expect(typed.constructor).toBe(oldType);
  }
});
