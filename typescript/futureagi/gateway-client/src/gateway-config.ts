import { HEADER_CONFIG } from "./constants.js";
import { AgentCCError } from "./errors.js";
import { guardFiKeyPair } from "./env.js";

// ---------------------------------------------------------------------------
// GatewayConfig: what the gateway applies from x-agentcc-config
// ---------------------------------------------------------------------------
//
// The gateway (agentcc-gateway at the recorded revision, middleware/agentcc_config_header.go)
// applies only the cache section's ttl, namespace and force_refresh from
// x-agentcc-config. Every other GatewayConfig section of @agentcc/client 1.x
// (fallback, load_balance, guardrails, routing, mirror, retry, timeout) and
// every other cache field it names in X-Agentcc-Config-Ignored and does not
// apply. So this client takes only those three fields and raises a TypeError
// for anything else, instead of sending what the gateway drops.

/** The cache fields the gateway reads from x-agentcc-config. */
export interface CacheConfig {
  /** Cache entry lifetime in seconds (x-agentcc-cache-ttl). */
  ttl?: number;
  /** Cache key namespace (x-agentcc-cache-namespace). */
  namespace?: string;
  /** Skip the cached answer and refresh it (x-agentcc-cache-force-refresh). */
  force_refresh?: boolean;
}

export interface GatewayConfig {
  cache?: CacheConfig;
}

const CACHE_FIELDS = new Set(["ttl", "namespace", "force_refresh"]);
const UNAPPLIED_SECTIONS = new Set(["fallback", "load_balance", "loadBalance", "guardrails", "routing", "mirror", "retry", "timeout"]);

/**
 * Raise a TypeError for a GatewayConfig section or cache field the gateway
 * does not apply. null and undefined mean "not set", as they do to the gateway.
 */
export function assertGatewayConfig(config: unknown): void {
  if (config === undefined || config === null) return;
  if (typeof config !== "object" || Array.isArray(config)) {
    throw new TypeError("GatewayConfig must be an object such as { cache: { ttl: 300 } }");
  }
  for (const [section, value] of Object.entries(config)) {
    if (value === undefined || value === null) continue;
    if (section !== "cache") {
      throw new TypeError(
        UNAPPLIED_SECTIONS.has(section)
          ? `GatewayConfig section "${section}" is not applied by the gateway (it names it in X-Agentcc-Config-Ignored); the only section is cache (ttl, namespace, force_refresh)`
          : `"${section}" is not a GatewayConfig section; the only section is cache (ttl, namespace, force_refresh)`,
      );
    }
    if (typeof value !== "object" || Array.isArray(value)) {
      throw new TypeError("GatewayConfig cache must be an object such as { ttl: 300 }");
    }
    for (const [field, v] of Object.entries(value)) {
      if (v === undefined || v === null || CACHE_FIELDS.has(field)) continue;
      throw new TypeError(
        `GatewayConfig cache.${field} is not read by the gateway (it names it in X-Agentcc-Config-Ignored); cache takes ttl, namespace and force_refresh`,
      );
    }
  }
}

/** Serialize a GatewayConfig to plain object (strips undefined values). */
export function gatewayConfigToDict(config: GatewayConfig): Record<string, unknown> {
  return JSON.parse(JSON.stringify(config));
}

/**
 * Convert a GatewayConfig to HTTP headers. The caller checks it first
 * (assertGatewayConfig: the client constructor, createHeaders).
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
 *
 * An `apiKey` equal to FI_API_KEY or FI_SECRET_KEY from the environment
 * raises AgentCCError, as every other entry point does: the gateway takes a
 * virtual key, never the Future AGI key pair.
 */
export function createHeaders(opts: CreateHeadersOptions): Record<string, string> {
  const h: Record<string, string> = {};

  if (opts.apiKey) {
    guardFiKeyPair(opts.apiKey, (message) => new AgentCCError(message));
    h["Authorization"] = `Bearer ${opts.apiKey}`;
  }
  if (opts.config) {
    assertGatewayConfig(opts.config);
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
