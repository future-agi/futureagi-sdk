/** Token usage information. */
export interface Usage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  prompt_tokens_details?: Record<string, unknown>;
  completion_tokens_details?: Record<string, unknown>;
}

/** Rate-limit information parsed from response headers. */
export interface RateLimitInfo {
  limit: number | null;
  remaining: number | null;
  reset: number | null;
}

/**
 * AgentCC gateway metadata attached to every response.
 * Parsed from `x-agentcc-*` response headers.
 */
export interface AgentCCMetadata {
  requestId: string;
  traceId: string;
  provider: string;
  latencyMs: number;
  cost: number | null;
  cacheStatus: string | null;
  modelUsed: string | null;
  guardrailTriggered: boolean;
  guardrailName: string | null;
  guardrailAction: string | null;
  guardrailConfidence: number | null;
  guardrailMessage: string | null;
  fallbackUsed: boolean;
  routingStrategy: string | null;
  timeoutMs: number | null;
  ratelimit: RateLimitInfo | null;
}

/** Parse AgentCCMetadata from HTTP response headers. */
export function parseAgentCCMetadata(headers: Headers): AgentCCMetadata {
  const rl = parseRateLimit(headers);
  return {
    requestId: headers.get("x-agentcc-request-id") ?? "unknown",
    traceId: headers.get("x-agentcc-trace-id") ?? "unknown",
    provider: headers.get("x-agentcc-provider") ?? "unknown",
    latencyMs: intHeader(headers, "x-agentcc-latency-ms") ?? 0,
    cost: floatHeader(headers, "x-agentcc-cost"),
    cacheStatus: headers.get("x-agentcc-cache"),
    modelUsed: headers.get("x-agentcc-model-used"),
    guardrailTriggered: headers.get("x-agentcc-guardrail-triggered") === "true",
    guardrailName: headers.get("x-agentcc-guardrail-name"),
    guardrailAction: headers.get("x-agentcc-guardrail-action"),
    guardrailConfidence: floatHeader(headers, "x-agentcc-guardrail-confidence"),
    guardrailMessage: headers.get("x-agentcc-guardrail-message"),
    fallbackUsed: headers.get("x-agentcc-fallback-used") === "true",
    routingStrategy: headers.get("x-agentcc-routing-strategy"),
    timeoutMs: intHeader(headers, "x-agentcc-timeout-ms"),
    ratelimit: rl.limit !== null ? rl : null,
  };
}

function intHeader(h: Headers, name: string): number | null {
  const v = h.get(name);
  if (!v) return null;
  const n = parseInt(v, 10);
  return Number.isNaN(n) ? null : n;
}

function floatHeader(h: Headers, name: string): number | null {
  const v = h.get(name);
  if (!v) return null;
  const n = parseFloat(v);
  return Number.isNaN(n) ? null : n;
}

function parseRateLimit(h: Headers): RateLimitInfo {
  return {
    limit: intHeader(h, "x-ratelimit-limit-requests"),
    remaining: intHeader(h, "x-ratelimit-remaining-requests"),
    reset: intHeader(h, "x-ratelimit-reset-requests"),
  };
}
