// ---------------------------------------------------------------------------
// The parts of one gateway request, as pure functions: URL, headers (the
// 7-level merge), retry delay, connection errors, error bodies and the
// structured-output check. Moved from @agentcc/client 1.0.1 base-client.ts
// unchanged, so that module stays under 400 lines.
// ---------------------------------------------------------------------------

import { VERSION } from "./constants.js";
import { AgentCCError, APIConnectionError, APITimeoutError } from "./errors.js";
import type { GatewayConfig } from "./gateway-config.js";
import { gatewayConfigToHeaders } from "./gateway-config.js";
import type { TraceContextManager } from "./trace-context.js";
import { validateJsonResponse } from "./validate-response.js";
import type { RequestOptions } from "./client-options.js";
import { assignHeaders, setMetadataHeader } from "./metadata-header.js";
import { parseGatewayEvidence } from "./gateway-evidence.js";
import { UNCONFIRMED_DISPATCH_REMEDY } from "./refusal-policy.js";
import { failedBeforeSend } from "./transport-dispatch.js";
import { abortError, throwIfAborted } from "./request-cancellation.js";

/** What a client contributes to every request's headers. */
export interface HeaderSources {
  /** In a browser page the two SDK headers are left out. */
  inBrowser: boolean;
  apiKey: string;
  defaultHeaders: Record<string, string>;
  sessionId: string | undefined;
  metadata: Record<string, unknown> | undefined;
  traceManager: TraceContextManager | undefined;
  config: GatewayConfig | undefined;
}

/** The request URL: base URL, path, then the client's and the request's query. */
export function buildUrl(baseUrl: string, defaultQuery: Record<string, string>, path: string, query?: Record<string, string>): string {
  const merged = { ...defaultQuery, ...query };
  const qs = Object.keys(merged).length ? "?" + new URLSearchParams(merged).toString() : "";
  return `${baseUrl}${path}${qs}`;
}

/**
 * The metadata a request sends: each layer in order (the client's
 * `metadata`, then the session's, then the request's `request_metadata`),
 * merged key by key with the later layer winning. The merge is shallow: a
 * nested object in a later layer replaces the earlier one whole. Returns
 * undefined when no layer is set; an empty object is sent as `{}`, as before.
 */
export function mergeMetadata(...layers: Array<Record<string, unknown> | undefined>): Record<string, unknown> | undefined {
  const set = layers.filter((layer): layer is Record<string, unknown> => layer != null);
  if (set.length === 0) return undefined;
  return Object.assign({}, ...set) as Record<string, unknown>;
}

/**
 * Header building — 7-level priority merge. Each level is merged with
 * `assignHeaders`: x-agentcc-metadata in any spelling is one header, and a
 * later level's value replaces it (every other name merges as before).
 */
export function buildHeaders(src: HeaderSources, options: RequestOptions): Record<string, string> {
  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {};

  // 1. SDK auto-headers (in a browser the two SDK headers are left out:
  // the gateway's CORS allowlist names neither)
  if (!src.inBrowser) headers["User-Agent"] = `futureagi-typescript/${VERSION}`;
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }
  if (!src.inBrowser) headers["x-agentcc-sdk-version"] = VERSION;
  headers["Accept"] = "application/json";

  // 2. Auth
  if (src.apiKey) {
    headers["Authorization"] = `Bearer ${src.apiKey}`;
  }

  // 3. Client-level default headers
  assignHeaders(headers, src.defaultHeaders);

  // 4. Client-level defaults (session, metadata). The metadata is the one
  // merge of the client's, the session's (already in a session client's
  // metadata) and this request's, later keys winning. It replaces a level-3
  // x-agentcc-metadata in any spelling.
  if (src.sessionId) {
    headers["x-agentcc-session-id"] = src.sessionId;
  }
  const metadata = mergeMetadata(src.metadata, options.metadata);
  if (metadata) {
    setMetadataHeader(headers, JSON.stringify(metadata));
  }

  // 4b. Trace context headers
  if (src.traceManager) {
    assignHeaders(headers, src.traceManager.getHeaders());
  }

  // 5. Config headers
  if (src.config) {
    assignHeaders(headers, gatewayConfigToHeaders(src.config));
  }

  // 6 & 7. Per-request headers (highest priority). A raw x-agentcc-metadata
  // here, in any spelling, replaces the merged one.
  assignHeaders(headers, options.headers);

  return headers;
}

/** The delay before retry `attempt`: Retry-After (capped at 60 s), else exponential backoff with jitter (capped at 8 s). */
export function retryDelay(attempt: number, headers?: Headers): number {
  // Respect Retry-After header
  if (headers) {
    const retryAfter = headers.get("retry-after");
    if (retryAfter) {
      const seconds = parseFloat(retryAfter);
      if (!Number.isNaN(seconds) && seconds > 0) {
        return Math.min(seconds * 1000, 60_000);
      }
    }
  }
  // Exponential backoff with jitter
  const base = 0.5 * Math.pow(2, attempt);
  const jitter = base * 0.25 * (Math.random() * 2 - 1);
  return Math.min((base + jitter) * 1000, 8_000);
}

export function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  throwIfAborted(signal);
  return new Promise((resolve, reject) => {
    const finish = () => { signal?.removeEventListener("abort", abort); resolve(); };
    const timer = setTimeout(finish, ms);
    const abort = () => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", abort);
      reject(abortError());
    };
    signal?.addEventListener("abort", abort, { once: true });
  });
}

/** Preserve public error classes without retaining credential-bearing transport
 * objects, error prose or URLs. Unknown outcomes are terminal under every policy.
 */
export function connectionError(err: unknown, _path: string, _url: string): APIConnectionError {
  const beforeSend = failedBeforeSend(err);
  const evidence = parseGatewayEvidence(beforeSend ? [["x-agentcc-dispatched", "false"]] : undefined);
  let timeout = false;
  try {
    timeout = (err instanceof DOMException && err.name === "TimeoutError")
      || (err instanceof TypeError && err.message.includes("abort"));
  } catch { /* Untrusted transport properties do not escape the error boundary. */ }
  const message = (timeout ? "Request timed out." : "Request connection failed.")
    + (beforeSend ? " The request was not sent." : ` ${UNCONFIRMED_DISPATCH_REMEDY}`);
  return timeout ? new APITimeoutError(message, evidence) : new APIConnectionError(message, undefined, evidence);
}

/** An error response's body: its JSON, else `{ message: <text> }`. */
export async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return { message: await response.text().catch(() => "Unknown error") };
  }
}

/**
 * Validate a structured-output answer against the request's JSON Schema
 * (enableJsonSchemaValidation): raise AgentCCError when it fails.
 */
export function checkStructuredOutput(body: RequestOptions["body"], json: unknown): void {
  if (!body || body instanceof FormData) return;
  const rf = (body as Record<string, unknown>).response_format as Record<string, unknown> | undefined;
  if (!rf || rf.type !== "json_schema" || !rf.json_schema) return;
  const schema = (rf.json_schema as Record<string, unknown>).schema as Record<string, unknown> | undefined;
  if (!schema) return;
  const choices = (json as Record<string, unknown>).choices as Array<Record<string, unknown>> | undefined;
  const content = (choices?.[0]?.message as Record<string, unknown> | undefined)?.content as string | undefined;
  if (!content) return;
  const validation = validateJsonResponse(content, schema);
  if (!validation.valid) {
    throw new AgentCCError(`Structured output validation failed: ${validation.errors.join("; ")}`);
  }
}
