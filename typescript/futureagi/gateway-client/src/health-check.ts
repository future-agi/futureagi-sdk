// ---------------------------------------------------------------------------
// Health Check Utilities — standalone functions for connectivity validation
// ---------------------------------------------------------------------------

import { AgentCC } from "./client.js";
import type { AgentCCMetadata } from "./types/shared.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CheckValidKeyOptions {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

export interface CheckValidKeyResult {
  valid: boolean;
  error?: string;
}

export interface HealthCheckOptions {
  model: string;
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

export interface HealthCheckResult {
  healthy: boolean;
  latencyMs: number;
  provider?: string;
  model?: string;
  error?: string;
}

// ---------------------------------------------------------------------------
// checkValidKey
// ---------------------------------------------------------------------------

/**
 * Validate that an API key is accepted by the gateway.
 * Sends GET /v1/models and checks the response status.
 *
 * @example
 * ```typescript
 * const result = await checkValidKey({ apiKey: "sk-test-123" });
 * if (result.valid) console.log("Key is valid!");
 * ```
 */
export async function checkValidKey(
  opts: CheckValidKeyOptions,
): Promise<CheckValidKeyResult> {
  const client = new AgentCC({
    apiKey: opts.apiKey,
    baseUrl: opts.baseUrl,
    timeout: opts.timeout ?? 10_000,
    maxRetries: 0,
  });

  try {
    await client.models.list();
    return { valid: true };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);

    // Auth errors mean the key is invalid but the gateway is reachable
    if (
      message.includes("401") ||
      message.includes("403") ||
      message.includes("Authentication") ||
      message.includes("Permission")
    ) {
      return { valid: false, error: "Invalid or unauthorized API key" };
    }

    // Connection errors mean we can't reach the gateway
    return { valid: false, error: message };
  }
}

// ---------------------------------------------------------------------------
// healthCheck
// ---------------------------------------------------------------------------

/**
 * Send a minimal completion request to verify end-to-end connectivity
 * through the gateway to a specific model.
 *
 * @example
 * ```typescript
 * const result = await healthCheck({
 *   model: "gpt-4o",
 *   apiKey: "sk-test-123",
 * });
 * console.log(result.healthy, result.latencyMs);
 * ```
 */
export async function healthCheck(
  opts: HealthCheckOptions,
): Promise<HealthCheckResult> {
  const client = new AgentCC({
    apiKey: opts.apiKey,
    baseUrl: opts.baseUrl,
    timeout: opts.timeout ?? 30_000,
    maxRetries: 0,
  });

  const start = Date.now();

  try {
    const response = await client.chat.completions.create({
      model: opts.model,
      messages: [{ role: "user", content: "ping" }],
      max_tokens: 1,
    });

    const latencyMs = Date.now() - start;
    const agentcc = (response as { agentcc?: AgentCCMetadata }).agentcc;

    return {
      healthy: true,
      latencyMs,
      provider: agentcc?.provider ?? undefined,
      model: agentcc?.modelUsed ?? opts.model,
    };
  } catch (err: unknown) {
    const latencyMs = Date.now() - start;
    const message = err instanceof Error ? err.message : String(err);

    return {
      healthy: false,
      latencyMs,
      error: message,
    };
  }
}
