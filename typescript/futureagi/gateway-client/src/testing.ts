/**
 * Testing utilities for AgentCC SDK.
 *
 * @example
 * ```typescript
 * import { MockAgentCC, mockCompletion } from "@future-agi/sdk/gateway/testing";
 *
 * const mock = new MockAgentCC();
 * mock.chat.completions.respondWith(mockCompletion("Hello!"));
 * const result = await mock.chat.completions.create({ model: "gpt-4o", messages: [] });
 * expect(result.choices[0].message.content).toBe("Hello!");
 * expect(mock.chat.completions.calls).toHaveLength(1);
 * ```
 *
 * @module
 */

import type { ChatCompletion, ChatCompletionMessage } from "./types/chat/chat-completion.js";
import type { ChatCompletionCreateParams } from "./types/chat/completion-create-params.js";
import type { EmbeddingResponse } from "./types/embedding.js";
import type { Usage, AgentCCMetadata } from "./types/shared.js";

// ---------------------------------------------------------------------------
// MockAgentCC
// ---------------------------------------------------------------------------

export class MockChatCompletions {
  calls: Array<{ params: ChatCompletionCreateParams }> = [];
  private _responses: ChatCompletion[] = [];

  respondWith(response: ChatCompletion): void {
    this._responses.push(response);
  }

  async create(params: ChatCompletionCreateParams): Promise<ChatCompletion> {
    this.calls.push({ params });
    if (this._responses.length > 0) {
      return this._responses.shift()!;
    }
    return mockCompletion("Mock response");
  }
}

export class MockChat {
  completions = new MockChatCompletions();
}

export class MockEmbeddings {
  calls: Array<{ params: unknown }> = [];
  private _responses: EmbeddingResponse[] = [];

  respondWith(response: EmbeddingResponse): void {
    this._responses.push(response);
  }

  async create(params: unknown): Promise<EmbeddingResponse> {
    this.calls.push({ params });
    if (this._responses.length > 0) {
      return this._responses.shift()!;
    }
    return {
      object: "list",
      data: [{ object: "embedding", index: 0, embedding: [0.1, 0.2, 0.3] }],
      model: "text-embedding-3-small",
      usage: { prompt_tokens: 5, completion_tokens: 0, total_tokens: 5 },
    };
  }
}

export class MockAgentCC {
  chat = new MockChat();
  embeddings = new MockEmbeddings();
  currentCost = 0;
}

// ---------------------------------------------------------------------------
// Factory functions
// ---------------------------------------------------------------------------

export function mockCompletion(
  content?: string,
  opts: {
    model?: string;
    provider?: string;
    cost?: number;
    id?: string;
    finishReason?: string;
    usage?: Usage;
  } = {},
): ChatCompletion {
  const message: ChatCompletionMessage = {
    role: "assistant",
    content: content ?? null,
  };

  return {
    id: opts.id ?? "chatcmpl-mock",
    object: "chat.completion",
    created: Math.floor(Date.now() / 1000),
    model: opts.model ?? "gpt-4o",
    choices: [
      {
        index: 0,
        message,
        finish_reason: opts.finishReason ?? "stop",
      },
    ],
    usage: opts.usage ?? {
      prompt_tokens: 10,
      completion_tokens: 5,
      total_tokens: 15,
    },
    agentcc: mockAgentCCMetadata({
      provider: opts.provider,
      cost: opts.cost,
    }),
  };
}

export function mockAgentCCMetadata(
  opts: Partial<AgentCCMetadata> = {},
): AgentCCMetadata {
  return {
    requestId: opts.requestId ?? "req-mock",
    traceId: opts.traceId ?? "trace-mock",
    provider: opts.provider ?? "openai",
    latencyMs: opts.latencyMs ?? 100,
    cost: opts.cost ?? null,
    cacheStatus: opts.cacheStatus ?? null,
    modelUsed: opts.modelUsed ?? null,
    guardrailTriggered: opts.guardrailTriggered ?? false,
    guardrailName: opts.guardrailName ?? null,
    guardrailAction: opts.guardrailAction ?? null,
    guardrailConfidence: opts.guardrailConfidence ?? null,
    guardrailMessage: opts.guardrailMessage ?? null,
    fallbackUsed: opts.fallbackUsed ?? false,
    routingStrategy: opts.routingStrategy ?? null,
    timeoutMs: opts.timeoutMs ?? null,
    ratelimit: opts.ratelimit ?? null,
    configIgnored: opts.configIgnored ?? null,
    clientRequestId: opts.clientRequestId ?? null,
  };
}

export function mockUsage(
  promptTokens = 10,
  completionTokens = 5,
): Usage {
  return {
    prompt_tokens: promptTokens,
    completion_tokens: completionTokens,
    total_tokens: promptTokens + completionTokens,
  };
}

// ---------------------------------------------------------------------------
// Assertion helpers
// ---------------------------------------------------------------------------

export function assertCompletionValid(completion: ChatCompletion): void {
  if (!completion.id) throw new Error("Completion missing id");
  if (completion.object !== "chat.completion")
    throw new Error(`Expected object "chat.completion", got "${completion.object}"`);
  if (!Array.isArray(completion.choices) || completion.choices.length === 0)
    throw new Error("Completion has no choices");
  if (!completion.choices[0].message)
    throw new Error("First choice has no message");
}

export function assertCompletionHasContent(
  completion: ChatCompletion,
  expectedContent: string,
): void {
  assertCompletionValid(completion);
  const content = completion.choices[0].message.content;
  if (content !== expectedContent) {
    throw new Error(
      `Expected content "${expectedContent}", got "${content}"`,
    );
  }
}

export function assertUsageValid(usage: Usage): void {
  if (typeof usage.prompt_tokens !== "number" || usage.prompt_tokens < 0)
    throw new Error("Invalid prompt_tokens");
  if (typeof usage.completion_tokens !== "number" || usage.completion_tokens < 0)
    throw new Error("Invalid completion_tokens");
  if (typeof usage.total_tokens !== "number" || usage.total_tokens < 0)
    throw new Error("Invalid total_tokens");
}

export function assertAgentCCMetadata(
  metadata: AgentCCMetadata,
  opts: { provider?: string; costPresent?: boolean } = {},
): void {
  if (!metadata.requestId) throw new Error("AgentCCMetadata missing requestId");
  if (opts.provider && metadata.provider !== opts.provider) {
    throw new Error(
      `Expected provider "${opts.provider}", got "${metadata.provider}"`,
    );
  }
  if (opts.costPresent && metadata.cost == null) {
    throw new Error("Expected cost to be present");
  }
}

export function assertCostTracked(
  client: { currentCost: number },
  expectedCost: number,
  tolerance = 0.0001,
): void {
  const diff = Math.abs(client.currentCost - expectedCost);
  if (diff > tolerance) {
    throw new Error(
      `Expected cost ${expectedCost}, got ${client.currentCost} (diff: ${diff})`,
    );
  }
}
