export const VERSION = "0.1.0";

// Defaults
export const DEFAULT_TIMEOUT = 600_000; // 600s in ms
export const DEFAULT_MAX_RETRIES = 2;
export const DEFAULT_BASE_URL = "http://localhost:8090";

// Request headers
export const HEADER_API_KEY = "Authorization";
export const HEADER_CONTENT_TYPE = "Content-Type";
export const HEADER_USER_AGENT = "User-Agent";
export const HEADER_SDK_VERSION = "x-agentcc-sdk-version";
export const HEADER_TRACE_ID = "x-agentcc-trace-id";
export const HEADER_SESSION_ID = "x-agentcc-session-id";
export const HEADER_SESSION_NAME = "x-agentcc-session-name";
export const HEADER_SESSION_PATH = "x-agentcc-session-path";
export const HEADER_METADATA = "x-agentcc-metadata";
export const HEADER_REQUEST_TIMEOUT = "x-agentcc-request-timeout";
export const HEADER_CACHE_TTL = "x-agentcc-cache-ttl";
export const HEADER_CACHE_NAMESPACE = "x-agentcc-cache-namespace";
export const HEADER_CACHE_FORCE_REFRESH = "x-agentcc-cache-force-refresh";
export const HEADER_CACHE_CONTROL = "Cache-Control";
export const HEADER_GUARDRAIL_POLICY = "X-Guardrail-Policy";
export const HEADER_CONFIG = "x-agentcc-config";

// Response headers
export const HEADER_RESPONSE_REQUEST_ID = "x-agentcc-request-id";
export const HEADER_RESPONSE_TRACE_ID = "x-agentcc-trace-id";
export const HEADER_RESPONSE_PROVIDER = "x-agentcc-provider";
export const HEADER_RESPONSE_LATENCY = "x-agentcc-latency-ms";
export const HEADER_RESPONSE_COST = "x-agentcc-cost";
export const HEADER_RESPONSE_CACHE = "x-agentcc-cache";
export const HEADER_RESPONSE_MODEL_USED = "x-agentcc-model-used";
export const HEADER_RESPONSE_GUARDRAIL_TRIGGERED = "x-agentcc-guardrail-triggered";
export const HEADER_RESPONSE_GUARDRAIL_NAME = "x-agentcc-guardrail-name";
export const HEADER_RESPONSE_GUARDRAIL_ACTION = "x-agentcc-guardrail-action";
export const HEADER_RESPONSE_GUARDRAIL_CONFIDENCE = "x-agentcc-guardrail-confidence";
export const HEADER_RESPONSE_GUARDRAIL_MESSAGE = "x-agentcc-guardrail-message";
export const HEADER_RESPONSE_FALLBACK_USED = "x-agentcc-fallback-used";
export const HEADER_RESPONSE_ROUTING_STRATEGY = "x-agentcc-routing-strategy";
export const HEADER_RESPONSE_TIMEOUT = "x-agentcc-timeout-ms";
export const HEADER_RATELIMIT_LIMIT = "x-ratelimit-limit-requests";
export const HEADER_RATELIMIT_REMAINING = "x-ratelimit-remaining-requests";
export const HEADER_RATELIMIT_RESET = "x-ratelimit-reset-requests";

export const RETRYABLE_STATUS_CODES = new Set([408, 429, 500, 502, 503, 504]);

/**
 * Default AgentCC Gateway URL.
 * Override via `AGENTCC_GATEWAY_URL` or `AGENTCC_BASE_URL` environment variable.
 */
export const AGENTCC_GATEWAY_URL: string =
  (typeof process !== "undefined" && process.env?.AGENTCC_GATEWAY_URL) ||
  (typeof process !== "undefined" && process.env?.AGENTCC_BASE_URL) ||
  "https://gateway.futureagi.com/v1";

/**
 * Sentinel value to distinguish "not provided" from explicit `undefined`/`null`.
 */
const NOT_GIVEN_SYMBOL = Symbol("NOT_GIVEN");

export type NotGiven = typeof NOT_GIVEN_SYMBOL;
export const NOT_GIVEN: NotGiven = NOT_GIVEN_SYMBOL;

export function isNotGiven(value: unknown): value is NotGiven {
  return value === NOT_GIVEN;
}
