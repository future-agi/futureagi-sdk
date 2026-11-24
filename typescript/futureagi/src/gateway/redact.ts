/**
 * Message content redaction for callbacks.
 *
 * @module
 */

import type { CallbackRequest } from "./callbacks";

const REDACTED = "[REDACTED]";

/**
 * Deep-clone a CallbackRequest and replace message content with `[REDACTED]`.
 * Preserves roles, tool call metadata, and all non-content fields.
 */
export function redactCallbackRequest(request: CallbackRequest): CallbackRequest {
  const body = deepClone(request.body);

  if (body && typeof body === "object") {
    const b = body as Record<string, unknown>;

    // Chat completions: messages[].content
    if (Array.isArray(b.messages)) {
      b.messages = (b.messages as Record<string, unknown>[]).map((msg) => {
        const redacted = { ...msg };
        if (redacted.content != null) {
          redacted.content = REDACTED;
        }
        // Tool-call arguments are model-written content too.
        if (Array.isArray(redacted.tool_calls)) {
          redacted.tool_calls = (redacted.tool_calls as Record<string, unknown>[]).map((tc) =>
            tc && typeof tc.function === "object" && tc.function !== null
              ? { ...tc, function: { ...(tc.function as Record<string, unknown>), arguments: REDACTED } }
              : tc,
          );
        }
        if (redacted.function_call && typeof redacted.function_call === "object") {
          redacted.function_call = { ...(redacted.function_call as Record<string, unknown>), arguments: REDACTED };
        }
        return redacted;
      });
    }

    // Legacy completions: prompt
    if (typeof b.prompt === "string") {
      b.prompt = REDACTED;
    } else if (Array.isArray(b.prompt)) {
      b.prompt = b.prompt.map(() => REDACTED);
    }

    if (typeof b.instructions === "string") {
      b.instructions = REDACTED;
    }

    // Embeddings / moderations: input
    if (typeof b.input === "string") {
      b.input = REDACTED;
    } else if (Array.isArray(b.input)) {
      b.input = (b.input as unknown[]).map((item) =>
        typeof item === "string" ? REDACTED : item,
      );
    }
  }

  return {
    method: request.method,
    url: request.url,
    headers: { ...request.headers },
    body,
  };
}

function deepClone<T>(value: T): T {
  if (value === null || value === undefined) return value;
  return JSON.parse(JSON.stringify(value));
}
