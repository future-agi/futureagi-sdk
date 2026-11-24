/**
 * Token counting, cost estimation, and prompt utilities.
 *
 * Token counting uses a character-based estimate (~4 chars per token for
 * English text).  This is intentionally dependency-free — if exact counts
 * are needed, pass the text through tiktoken separately.
 *
 * @module
 */

import { getModelInfo } from "./models-info";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ChatMessage {
  role?: string;
  content?: string | ContentPart[] | null;
  tool_calls?: unknown[];
  [key: string]: unknown;
}

interface ContentPart {
  type?: string;
  text?: string;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Token counting
// ---------------------------------------------------------------------------

/**
 * Estimate the number of tokens for text or messages.
 *
 * Uses a character-based heuristic (~4 English characters per token).
 * Add `tiktoken` or `gpt-tokenizer` in your project for exact counts.
 */
export function tokenCounter(
  model: string,
  opts: { text?: string; messages?: ChatMessage[] } = {},
): number {
  const { text, messages } = opts;
  if (text == null && messages == null) return 0;

  let content = "";
  let overhead = 0;

  if (text != null) {
    content = text;
  } else if (messages != null) {
    const parts: string[] = [];
    for (const msg of messages) {
      parts.push(msg.role ?? "");
      const c = msg.content;
      if (typeof c === "string") {
        parts.push(c);
      } else if (Array.isArray(c)) {
        for (const part of c) {
          if (part && typeof part === "object" && part.type === "text") {
            parts.push(part.text ?? "");
          }
        }
      }
      if (msg.tool_calls) {
        parts.push(JSON.stringify(msg.tool_calls));
      }
    }
    content = parts.join("\n");
    overhead = messages.length * 4 + 2; // ~4 tokens per message + 2 priming
  }

  // Character-based estimate: ~4 chars per token
  const count = Math.max(Math.ceil(content.length / 4), text != null || messages != null ? 1 : 0);
  return count + overhead;
}

// ---------------------------------------------------------------------------
// Context window queries
// ---------------------------------------------------------------------------

/** Return the context window size for a model, or `null` if unknown. */
export function getMaxTokens(model: string): number | null {
  return getModelInfo(model)?.maxTokens ?? null;
}

/** Return the max output tokens for a model, or `null` if unknown. */
export function getMaxOutputTokens(model: string): number | null {
  return getModelInfo(model)?.maxOutputTokens ?? null;
}

// ---------------------------------------------------------------------------
// Cost estimation
// ---------------------------------------------------------------------------

/**
 * Estimate the cost of a completion in USD.
 *
 * Returns `null` if the model is unknown.
 */
export function completionCost(
  model: string,
  promptTokens: number = 0,
  completionTokens: number = 0,
): number | null {
  const info = getModelInfo(model);
  if (!info) return null;
  return (
    promptTokens * info.inputCostPerToken +
    completionTokens * info.outputCostPerToken
  );
}

/**
 * Estimate cost from a ChatCompletion-like response object.
 *
 * Checks `response.agentcc.cost` (gateway-reported) first, then falls back
 * to local estimation from usage data.
 */
export function completionCostFromResponse(response: {
  model?: string;
  usage?: { prompt_tokens?: number; completion_tokens?: number };
  agentcc?: { cost?: number | null };
}): number | null {
  // Gateway-reported cost
  if (response.agentcc?.cost != null) {
    return response.agentcc.cost;
  }

  // Local estimation
  if (response.usage && response.model) {
    return completionCost(
      response.model,
      response.usage.prompt_tokens ?? 0,
      response.usage.completion_tokens ?? 0,
    );
  }
  return null;
}

// ---------------------------------------------------------------------------
// Message trimming
// ---------------------------------------------------------------------------

/**
 * Trim messages to fit within a model's context window.
 *
 * Always preserves system messages.  Removes oldest non-system messages
 * first until the total token estimate is within `trimRatio * maxTokens`.
 *
 * @throws {Error} If the model is unknown and `maxTokens` is not provided.
 */
export function trimMessages(
  messages: ChatMessage[],
  model: string,
  opts: { trimRatio?: number; maxTokens?: number } = {},
): ChatMessage[] {
  const { trimRatio = 0.75 } = opts;
  let { maxTokens } = opts;

  if (maxTokens == null) {
    const info = getModelInfo(model);
    if (!info) {
      throw new Error(
        `Unknown model "${model}". ` +
          "Provide maxTokens explicitly or register the model first.",
      );
    }
    maxTokens = info.maxTokens;
  }

  const budget = Math.floor(maxTokens * trimRatio);

  // Check if messages already fit
  const total = tokenCounter(model, { messages });
  if (total <= budget) return [...messages];

  // Separate system from non-system messages
  const systemMsgs: ChatMessage[] = [];
  const nonSystemMsgs: ChatMessage[] = [];
  for (const msg of messages) {
    if (msg.role === "system") {
      systemMsgs.push(msg);
    } else {
      nonSystemMsgs.push(msg);
    }
  }

  const systemTokens = systemMsgs.length
    ? tokenCounter(model, { messages: systemMsgs })
    : 0;
  const remainingBudget = budget - systemTokens;

  // Add non-system messages from newest to oldest until budget exhausted
  const kept: ChatMessage[] = [];
  let runningTokens = 0;
  for (let i = nonSystemMsgs.length - 1; i >= 0; i--) {
    const msgTokens = tokenCounter(model, { messages: [nonSystemMsgs[i]] });
    if (runningTokens + msgTokens <= remainingBudget) {
      kept.push(nonSystemMsgs[i]);
      runningTokens += msgTokens;
    } else {
      break;
    }
  }
  kept.reverse();

  return [...systemMsgs, ...kept];
}

// ---------------------------------------------------------------------------
// Context window & content policy fallbacks
// ---------------------------------------------------------------------------

const CONTEXT_WINDOW_FALLBACKS: Record<string, string> = {
  "gpt-4": "gpt-4-turbo",
  "gpt-4-turbo": "gpt-4o",
  "gpt-3.5-turbo": "gpt-4o-mini",
  "claude-3-haiku-20240307": "claude-3-5-haiku-20241022",
  "claude-3-opus-20240229": "claude-sonnet-4-20250514",
};

/** Return a model with a larger context window, or `null`. */
export function getContextWindowFallback(model: string): string | null {
  return CONTEXT_WINDOW_FALLBACKS[model] ?? null;
}

const CONTENT_POLICY_FALLBACKS: Record<string, string> = {
  "gpt-4o": "gpt-4-turbo",
  "gpt-4o-mini": "gpt-3.5-turbo",
};

/** Return a less restrictive model for content policy errors, or `null`. */
export function getContentPolicyFallback(model: string): string | null {
  return CONTENT_POLICY_FALLBACKS[model] ?? null;
}

// ---------------------------------------------------------------------------
// Prompt caching detection
// ---------------------------------------------------------------------------

/**
 * Check if a prompt qualifies for provider-side caching.
 *
 * Returns `[isEligible, reason]`.
 */
export function isPromptCachingValid(
  model: string,
  messages: ChatMessage[],
): [boolean, string] {
  // Anthropic models with cache_control
  if (model.toLowerCase().includes("claude")) {
    for (const msg of messages) {
      if ("cache_control" in msg) {
        return [true, "Anthropic cache_control detected"];
      }
      const content = msg.content;
      if (Array.isArray(content)) {
        for (const part of content) {
          if (part && typeof part === "object" && "cache_control" in part) {
            return [true, "Anthropic cache_control detected"];
          }
        }
      }
    }
  }

  // OpenAI models with long system prompts
  const lower = model.toLowerCase();
  if (["gpt-", "o1", "o3"].some((p) => lower.includes(p))) {
    for (const msg of messages) {
      if (msg.role === "system" && typeof msg.content === "string") {
        const systemTokens = tokenCounter(model, { text: msg.content });
        if (systemTokens >= 1024) {
          return [true, "System prompt eligible for OpenAI automatic caching"];
        }
      }
    }
  }

  return [false, "No caching indicators found"];
}
