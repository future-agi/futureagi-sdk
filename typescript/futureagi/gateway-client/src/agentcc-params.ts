import { HEADER_METADATA, isNotGiven } from "./constants.js";
import { assignHeaders, hasMetadataHeader } from "./metadata-header.js";

/** Keys that are AgentCC-specific and should be extracted from the body to headers. */
const AGENTCC_PARAM_TO_HEADER: Record<string, string> = {
  session_id: "x-agentcc-session-id",
  trace_id: "x-agentcc-trace-id",
  request_metadata: "x-agentcc-metadata",
  request_timeout: "x-agentcc-request-timeout",
  cache_ttl: "x-agentcc-cache-ttl",
  cache_namespace: "x-agentcc-cache-namespace",
  cache_force_refresh: "x-agentcc-cache-force-refresh",
  cache_control: "Cache-Control",
  guardrail_policy: "X-Guardrail-Policy",
};

const AGENTCC_PARAM_KEYS = new Set(Object.keys(AGENTCC_PARAM_TO_HEADER));

/**
 * Extract AgentCC-specific params from a body object.
 *
 * Returns `{ headers, cleanBody }` where:
 * - `headers` contains the extracted params as HTTP headers
 * - `cleanBody` is the original body with AgentCC params removed
 */
export function extractAgentCCParams(
  body: Record<string, unknown>,
): { headers: Record<string, string>; cleanBody: Record<string, unknown> } {
  const headers: Record<string, string> = {};
  const cleanBody: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(body)) {
    if (AGENTCC_PARAM_KEYS.has(key)) {
      if (value == null || isNotGiven(value)) continue;
      const headerName = AGENTCC_PARAM_TO_HEADER[key];
      if (typeof value === "object") {
        headers[headerName] = JSON.stringify(value);
      } else if (typeof value === "boolean") {
        headers[headerName] = value ? "true" : "false";
      } else {
        headers[headerName] = String(value);
      }
    } else if (key === "extra_headers" || key === "extra_body") {
      // Handled separately
    } else {
      cleanBody[key] = value;
    }
  }

  return { headers, cleanBody };
}

/** What a resource method sends for its per-request parameters. */
export interface PerRequestParts {
  /** The AgentCC parameters as headers, with `extra_headers` on top. */
  headers: Record<string, string>;
  /** The body without the AgentCC parameters (extra_body is the caller's). */
  cleanBody: Record<string, unknown>;
  /**
   * `request_metadata` as an object. The client merges it key by key over its
   * own and the session's metadata (see `mergeMetadata` in request-parts.ts),
   * so it is not in `headers`.
   */
  metadata: Record<string, unknown> | undefined;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value) && !isNotGiven(value);
}

/**
 * Split a resource call's parameters into headers, body and per-request
 * metadata. An x-agentcc-metadata header in `extra_headers`, in any spelling,
 * is a raw header: it is the one x-agentcc-metadata the request sends (kept
 * under that lowercase name), its value as given, in place of the merged
 * metadata.
 */
export function perRequestParts(params: Record<string, unknown>): PerRequestParts {
  const { headers: agentcc, cleanBody } = extractAgentCCParams(params);
  const extra = params.extra_headers as Record<string, string> | null | undefined;
  const headers = assignHeaders({ ...agentcc }, extra);
  const requestMetadata = params.request_metadata;
  if (!isPlainObject(requestMetadata) || hasMetadataHeader(extra)) return { headers, cleanBody, metadata: undefined };
  delete headers[HEADER_METADATA];
  return { headers, cleanBody, metadata: requestMetadata };
}
