import { HEADER_CONFIG } from "./constants";

// ---------------------------------------------------------------------------
// Config sub-types
// ---------------------------------------------------------------------------

export interface FallbackTarget {
  model: string;
  provider?: string;
  override_params?: Record<string, unknown>;
}

export interface FallbackConfig {
  targets: FallbackTarget[];
  on_status_codes?: number[];
}

export interface LoadBalanceTarget {
  model: string;
  provider?: string;
  weight?: number;
  virtual_key?: string;
}

export interface LoadBalanceConfig {
  strategy?: "round_robin" | "weighted" | "least_latency" | "cost_optimized";
  targets?: LoadBalanceTarget[];
}

export interface CacheConfig {
  enabled?: boolean;
  strategy?: "exact" | "semantic";
  ttl?: number;
  namespace?: string;
  force_refresh?: boolean;
  semantic_threshold?: number;
  cache_by_model?: boolean;
  ignore_keys?: string[];
}

export interface GuardrailCheck {
  name: string;
  enabled?: boolean;
  action?: "block" | "warn" | "mask" | "log";
  confidence_threshold?: number;
  config?: Record<string, unknown>;
}

export interface GuardrailConfig {
  input_guardrails?: string[];
  output_guardrails?: string[];
  deny?: boolean;
  async_mode?: boolean;
  sequential?: boolean;
  checks?: GuardrailCheck[];
  pipeline_mode?: "parallel" | "sequential";
  fail_open?: boolean;
  timeout_ms?: number;
}

export interface RoutingCondition {
  field: string;
  operator: "$eq" | "$ne" | "$in" | "$nin" | "$regex" | "$gt" | "$gte" | "$lt" | "$lte";
  value: unknown;
  target: string;
}

export interface ConditionalRoutingConfig {
  conditions: RoutingCondition[];
  default_target?: string;
}

export interface TrafficMirrorConfig {
  enabled?: boolean;
  target_model?: string;
  target_provider?: string;
  sample_rate?: number;
}

export interface RetryConfig {
  max_retries?: number;
  on_status_codes?: number[];
  backoff_factor?: number;
  backoff_max?: number;
  backoff_jitter?: number;
  respect_retry_after?: boolean;
  max_retry_wait?: number;
}

export interface TimeoutConfig {
  connect?: number;
  read?: number;
  write?: number;
  pool?: number;
  total?: number;
}

// ---------------------------------------------------------------------------
// Top-level GatewayConfig
// ---------------------------------------------------------------------------

export interface GatewayConfig {
  fallback?: FallbackConfig;
  load_balance?: LoadBalanceConfig;
  cache?: CacheConfig;
  guardrails?: GuardrailConfig;
  routing?: ConditionalRoutingConfig;
  mirror?: TrafficMirrorConfig;
  retry?: RetryConfig;
  timeout?: TimeoutConfig;
}

/** Serialize a GatewayConfig to plain object (strips undefined values). */
export function gatewayConfigToDict(config: GatewayConfig): Record<string, unknown> {
  return JSON.parse(JSON.stringify(config));
}

/**
 * Convert a GatewayConfig to HTTP headers.
 * The main config goes into `x-agentcc-config` as JSON.
 * Backward-compat convenience headers are also set.
 */
export function gatewayConfigToHeaders(config: GatewayConfig): Record<string, string> {
  const headers: Record<string, string> = {};
  const dict = gatewayConfigToDict(config);
  if (Object.keys(dict).length > 0) {
    headers[HEADER_CONFIG] = JSON.stringify(dict);
  }

  // Backward-compat headers for common cases
  if (config.cache?.ttl != null) {
    headers["x-agentcc-cache-ttl"] = String(config.cache.ttl);
  }
  if (config.cache?.namespace) {
    headers["x-agentcc-cache-namespace"] = config.cache.namespace;
  }
  if (config.cache?.force_refresh) {
    headers["x-agentcc-cache-force-refresh"] = "true";
  }
  return headers;
}

// ---------------------------------------------------------------------------
// createHeaders() — standalone helper for use with other clients (e.g. openai)
// ---------------------------------------------------------------------------

export interface CreateHeadersOptions {
  apiKey?: string;
  config?: GatewayConfig;
  traceId?: string;
  sessionId?: string;
  sessionName?: string;
  sessionPath?: string;
  metadata?: Record<string, unknown>;
  userId?: string;
  requestId?: string;
  cacheTtl?: number;
  cacheNamespace?: string;
  cacheForceRefresh?: boolean;
  guardrailPolicy?: string;
  properties?: Record<string, string>;
}

/**
 * Build a headers dict suitable for passing to other HTTP clients
 * (e.g. `new OpenAI({ defaultHeaders: createHeaders({ ... }) })`).
 */
export function createHeaders(opts: CreateHeadersOptions): Record<string, string> {
  const h: Record<string, string> = {};

  if (opts.apiKey) {
    h["Authorization"] = `Bearer ${opts.apiKey}`;
  }
  if (opts.config) {
    Object.assign(h, gatewayConfigToHeaders(opts.config));
  }
  if (opts.traceId) h["x-agentcc-trace-id"] = opts.traceId;
  if (opts.sessionId) h["x-agentcc-session-id"] = opts.sessionId;
  if (opts.sessionName) h["x-agentcc-session-name"] = opts.sessionName;
  if (opts.sessionPath) h["x-agentcc-session-path"] = opts.sessionPath;
  if (opts.metadata) h["x-agentcc-metadata"] = JSON.stringify(opts.metadata);
  if (opts.userId) h["x-agentcc-user-id"] = opts.userId;
  if (opts.requestId) h["x-agentcc-request-id"] = opts.requestId;
  if (opts.cacheTtl != null) h["x-agentcc-cache-ttl"] = String(opts.cacheTtl);
  if (opts.cacheNamespace) h["x-agentcc-cache-namespace"] = opts.cacheNamespace;
  if (opts.cacheForceRefresh) h["x-agentcc-cache-force-refresh"] = "true";
  if (opts.guardrailPolicy) h["X-Guardrail-Policy"] = opts.guardrailPolicy;

  if (opts.properties) {
    for (const [k, v] of Object.entries(opts.properties)) {
      h[`x-agentcc-property-${k}`] = v;
    }
  }

  return h;
}
