/**
 * Message content redaction for callbacks.
 *
 * @module
 */

import type { CallbackRequest } from "./callbacks.js";

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
        return redacted;
      });
    }

    // Legacy completions: prompt
    if (typeof b.prompt === "string") {
      b.prompt = REDACTED;
    } else if (Array.isArray(b.prompt)) {
      b.prompt = b.prompt.map(() => REDACTED);
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
