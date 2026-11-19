import type { BaseClient } from "../../base-client.js";
import type { ChatCompletionCreateParams } from "../../types/chat/completion-create-params.js";
import type { ChatCompletion } from "../../types/chat/chat-completion.js";
import { Stream, StreamManager } from "../../streaming.js";
import { perRequestParts } from "../../agentcc-params.js";
import { RunToolsRunner } from "../../run-tools.js";
import type {
  RunToolsParams,
  RunToolsResult,
  ToolWithExecute,
} from "../../run-tools.js";
import { isZodSchema, zodToJsonSchema } from "../../structured-output.js";
import { AgentCCError } from "../../errors.js";
import type { DryRunResult } from "../../dry-run.js";

export class ChatCompletions {
  constructor(private _client: BaseClient) {}

  /**
   * Create a chat completion.
   *
   * When `stream: true`, returns a `Stream` async iterable of `ChatCompletionChunk`.
   * Otherwise returns a `ChatCompletion`.
   */
  async create(params: ChatCompletionCreateParams & { stream: true }): Promise<Stream>;
  async create(params: ChatCompletionCreateParams & { stream?: false | null }): Promise<ChatCompletion>;
  async create(params: ChatCompletionCreateParams): Promise<ChatCompletion | Stream>;
  async create(params: ChatCompletionCreateParams): Promise<ChatCompletion | Stream> {
    const { headers: mergedHeaders, cleanBody, metadata } = perRequestParts(params as unknown as Record<string, unknown>);
    const extraBody = params.extra_body ?? {};
    const body = { ...cleanBody, ...extraBody };

    if (params.stream) {
      const response = await (this._client as any).requestStream({
        method: "POST",
        path: "/v1/chat/completions",
        body,
        headers: mergedHeaders,
        metadata,
      });
      return new Stream(response);
    }

    return this._client.request<ChatCompletion>({
      method: "POST",
      path: "/v1/chat/completions",
      body,
      headers: mergedHeaders,
      metadata,
    });
  }

  /**
   * Create a streaming chat completion and return a StreamManager
   * with convenience helpers (textStream, getFinalCompletion, etc.).
   */
  async stream(
    params: Omit<ChatCompletionCreateParams, "stream">,
  ): Promise<StreamManager> {
    const streamObj = await this.create({ ...params, stream: true } as ChatCompletionCreateParams & { stream: true });
    return new StreamManager(streamObj);
  }

  /**
   * Autonomous tool-calling loop. Sends the initial request, executes any
   * tool calls via the provided `execute` functions, feeds results back to
   * the model, and repeats until the model stops calling tools or `maxSteps`
   * is reached.
   *
   * @example
   * ```typescript
   * const result = await client.chat.completions.runTools({
   *   model: "gpt-4o",
   *   messages: [{ role: "user", content: "What's the weather?" }],
   *   tools: [{
   *     type: "function",
   *     function: {
   *       name: "get_weather",
   *       parameters: { type: "object", properties: { city: { type: "string" } } },
   *       execute: async (args) => ({ temp: 72 }),
   *     },
   *   }],
   *   maxSteps: 5,
   * });
   * ```
   */
  async runTools(params: RunToolsParams): Promise<RunToolsResult> {
    // We pass an object that satisfies the runner's client interface
    // Use the non-stream overload explicitly
    const self = this;
    const clientRef = {
      chat: {
        completions: {
          create: (p: ChatCompletionCreateParams) =>
            self.create({ ...p, stream: false } as ChatCompletionCreateParams & { stream: false }),
        },
      },
    };
    const runner = new RunToolsRunner(clientRef, params);
    return runner.run();
  }

  /**
   * Create a chat completion with structured output validated by a Zod schema.
   * Automatically sets `response_format` with the schema converted to JSON Schema,
   * and parses/validates the response.
   *
   * @example
   * ```typescript
   * import { z } from "zod";
   * const Weather = z.object({ temp: z.number(), condition: z.string() });
   *
   * const result = await client.chat.completions.createParsed({
   *   model: "gpt-4o",
   *   messages: [{ role: "user", content: "Weather in NYC?" }],
   *   responseSchema: Weather,
   * });
   * console.log(result.parsed.temp); // typed as number
   * ```
   */
  async createParsed<T = unknown>(
    params: ChatCompletionCreateParams & {
      responseSchema: unknown;
      schemaName?: string;
      strict?: boolean;
    },
  ): Promise<ChatCompletion & { parsed: T }> {
    const { responseSchema, schemaName, strict, ...restParams } = params;

    if (!isZodSchema(responseSchema)) {
      throw new AgentCCError(
        "createParsed: responseSchema must be a Zod schema. " +
          "Install zod and pass a z.object({...}) schema.",
      );
    }

    const jsonSchema = zodToJsonSchema(responseSchema);

    const completion = await this.create({
      ...restParams,
      stream: false,
      response_format: {
        type: "json_schema",
        json_schema: {
          name: schemaName ?? "response",
          schema: jsonSchema,
          strict: strict ?? true,
        },
      },
    } as ChatCompletionCreateParams & { stream: false }) as ChatCompletion;

    const content = completion.choices[0]?.message?.content;
    if (!content) {
      throw new AgentCCError("createParsed: no content in response");
    }

    let json: unknown;
    try {
      json = JSON.parse(content);
    } catch {
      throw new AgentCCError(
        `createParsed: response is not valid JSON: ${content.slice(0, 200)}`,
      );
    }

    // Validate with Zod
    const parsed = (responseSchema as { parse: (v: unknown) => T }).parse(
      json,
    );

    return Object.assign(completion, { parsed });
  }

  /**
   * Inspect the exact request that would be sent without making a network call.
   * Useful for debugging header construction, AgentCC param extraction, and
   * config serialization.
   *
   * @example
   * ```typescript
   * const req = client.chat.completions.dryRun({
   *   model: "gpt-4o",
   *   messages: [{ role: "user", content: "Hello" }],
   * });
   * console.log(req.url, req.headers, req.body);
   * ```
   */
  dryRun(params: ChatCompletionCreateParams): DryRunResult {
    const { headers: mergedHeaders, cleanBody, metadata } = perRequestParts(params as unknown as Record<string, unknown>);
    const extraBody = params.extra_body ?? {};
    const body = { ...cleanBody, ...extraBody };

    return (this._client as any).buildRequest({
      method: "POST",
      path: "/v1/chat/completions",
      body,
      headers: mergedHeaders,
      metadata,
    });
  }
}
