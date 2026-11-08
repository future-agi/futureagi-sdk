/**
 * Message content redaction for callbacks.
 *
 * @module
 */

import type { CallbackRequest } from "./callbacks.js";

const REDACTED = "[REDACTED]";
const SENSITIVE_HEADERS = new Set([
  "authorization", "proxy-authorization", "cookie", "set-cookie", "x-api-key", "api-key",
  "x-goog-api-key", "x-agentcc-config", "x-auth-token", "x-access-token", "x-api-token", "x-agentcc-api-key",
  "x-agentcc-session-id", "x-agentcc-session-name", "x-agentcc-session-path",
]);

/** Scrub only the SDK's fresh per-attempt headers, after fetch settles. Keeping
 * the same object removes credentials from any retained RequestInit reference;
 * the next attempt rebuilds from the untouched caller/client header sources.
 */
export function scrubCredentialHeaders(headers: Record<string, string>): void {
  for (const name of Object.keys(headers)) {
    if (SENSITIVE_HEADERS.has(name.toLowerCase())) headers[name] = REDACTED;
  }
}

// A standalone Stream may wrap a caller's Response that never crossed our
// transport. Do not retain arbitrary reader causes without a scrub guarantee.
const scrubbedResponses = new WeakSet<Response>();
export function markScrubbedResponse(response: Response): void { scrubbedResponses.add(response); }
export function hasScrubbedResponse(response: Response): boolean { return scrubbedResponses.has(response); }

/** Credential-bearing headers never belong to SDK errors or callback arguments,
 * regardless of the optional message-content redaction setting.
 */
export function safeDiagnosticHeaders(entries: Iterable<readonly [string, string]>): Record<string, string> {
  return Object.fromEntries([...entries].filter(([name]) => !SENSITIVE_HEADERS.has(name.toLowerCase())));
}

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
