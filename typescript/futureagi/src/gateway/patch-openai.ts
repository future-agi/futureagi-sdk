// ---------------------------------------------------------------------------
// patchOpenAI — Migrate an existing OpenAI client to AgentCC
// ---------------------------------------------------------------------------

import { AgentCC } from "./client";
import type { ClientOptions } from "./base-client";

/**
 * Create a AgentCC client from an existing OpenAI client instance.
 * Extracts the API key (if accessible) and creates a new AgentCC instance
 * pointed at the AgentCC gateway.
 *
 * @example
 * ```typescript
 * import OpenAI from "openai";
 * import { patchOpenAI } from "@future-agi/sdk/gateway";
 *
 * const openai = new OpenAI({ apiKey: "sk-..." });
 * const agentcc = patchOpenAI(openai, {
 *   config: { cache: { ttl: 300 } },
 * });
 * ```
 */
export function patchOpenAI(
  openaiClient: unknown,
  opts?: Partial<ClientOptions>,
): AgentCC {
  const client = openaiClient as Record<string, unknown>;

  // Try to extract apiKey from the OpenAI client (public in v4)
  const extractedApiKey =
    typeof client.apiKey === "string" ? client.apiKey : undefined;

  // Use provided apiKey, or extracted, or fall back to env
  const apiKey = opts?.apiKey ?? extractedApiKey;

  return new AgentCC({
    ...opts,
    apiKey,
  });
}
