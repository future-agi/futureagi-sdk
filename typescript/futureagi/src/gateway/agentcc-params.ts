import { isNotGiven } from "./constants";

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
