// `Gateway`: the AgentCC client with Future AGI defaults.
//
// The gateway authenticates with its own virtual keys (`sk-agentcc-*`), not with the platform's
// FI_API_KEY / FI_SECRET_KEY pair, so it reads its own variables:
//
//     FI_GATEWAY_API_KEY   (fallback: AGENTCC_API_KEY)
//     FI_GATEWAY_URL       (fallback: AGENTCC_BASE_URL, then the hosted gateway)
//
// Managing gateways (keys, providers, logs, analytics) is a platform API and lives on
// `new Client().gateway` (the generated platform client); this module is the data plane only.

import type { ClientOptions } from "./base-client";
import { AgentCC } from "./client";
import { envBaseUrl } from "./env";

export const DEFAULT_GATEWAY_URL = "https://gateway.futureagi.com";

/**
 * OpenAI-compatible client for the Future AGI gateway (Agent Command Center).
 *
 * @example
 * ```typescript
 * import { Gateway } from "@future-agi/sdk/gateway";
 *
 * const gw = new Gateway();   // FI_GATEWAY_API_KEY, FI_GATEWAY_URL
 * const reply = await gw.chat.completions.create({
 *   model: "gpt-4o-mini",
 *   messages: [{ role: "user", content: "Hello" }],
 * });
 * ```
 */
export class Gateway extends AgentCC {
  constructor(opts: ClientOptions = {}) {
    super({ ...opts, baseUrl: opts.baseUrl || envBaseUrl() || DEFAULT_GATEWAY_URL });
  }
}
