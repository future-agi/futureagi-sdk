// ---------------------------------------------------------------------------
// The client's options and a request's options (@agentcc/client 1.0.1
// base-client.ts types, plus dangerouslyAllowBrowser). base-client.ts
// re-exports them, so every import of them is unchanged.
// ---------------------------------------------------------------------------

import type { CallbackHandler } from "./callbacks.js";
import type { GatewayConfig } from "./gateway-config.js";
import type { RetryPolicy } from "./retry-policy.js";
import type { AgentCCMetadata } from "./types/shared.js";

export interface RequestOptions {
  method: string;
  path: string;
  body?: Record<string, unknown> | FormData | null;
  headers?: Record<string, string>;
  query?: Record<string, string>;
  /**
   * This request's metadata (`request_metadata`): merged key by key over the
   * client's `metadata` (a session client's includes the session's), the
   * request's keys winning, and sent as one `x-agentcc-metadata` JSON header.
   * An x-agentcc-metadata in `headers`, in any spelling, is sent in its place.
   */
  metadata?: Record<string, unknown>;
  timeout?: number;
  maxRetries?: number;
  /** If true, return the raw Response instead of parsing JSON. */
  raw?: boolean;
  /** If true, expect an SSE stream — do not consume body. */
  stream?: boolean;
}

export interface ClientOptions {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
  defaultHeaders?: Record<string, string>;
  defaultQuery?: Record<string, string>;
  sessionId?: string;
  metadata?: Record<string, unknown>;
  config?: GatewayConfig;
  fetch?: typeof globalThis.fetch;
  /** Callback handlers for request lifecycle hooks. */
  callbacks?: CallbackHandler[];
  /** Per-error-type retry configuration. Overrides `maxRetries` when set. */
  retryPolicy?: RetryPolicy;
  /** When true, callbacks receive redacted message content. */
  redactMessages?: boolean;
  /** Enable W3C Trace Context auto-generation. */
  traceContext?: boolean;
  /** Propagate an upstream traceparent header. */
  traceparent?: string;
  /** When true, auto-validate structured output responses against their JSON Schema. */
  enableJsonSchemaValidation?: boolean;
  /**
   * Allow construction in a browser page. Without it the client
   * throws there, because every visitor could read the gateway key; call the
   * gateway from your server instead (./gateway/nextjs, ./gateway/express,
   * ./gateway/react's default server route).
   */
  dangerouslyAllowBrowser?: boolean;
}

export interface WithResponseResult<T> {
  data: T;
  response: Response;
  agentcc: AgentCCMetadata;
}
