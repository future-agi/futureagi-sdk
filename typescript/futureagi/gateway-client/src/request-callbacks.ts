// ---------------------------------------------------------------------------
// The callback hooks a request fires, and the data they receive. Moved from
// @agentcc/client 1.0.1 base-client.ts unchanged, so that module stays under
// 400 lines.
// ---------------------------------------------------------------------------

import type { CallbackHandler, CallbackRequest, CallbackResponse } from "./callbacks.js";
import { invokeCallbacks } from "./callbacks.js";
import { GuardrailBlockedError } from "./errors.js";
import type { APIStatusError } from "./errors.js";
import { redactCallbackRequest, safeDiagnosticHeaders } from "./redact.js";
import type { AgentCCMetadata } from "./types/shared.js";
import type { RequestOptions } from "./client-options.js";
import { mergeMetadata } from "./request-parts.js";
import { assignHeaders, hasMetadataHeader } from "./metadata-header.js";
import { HEADER_METADATA } from "./constants.js";
import { getGatewayEvidence } from "./gateway-evidence.js";

/**
 * What a callback sees of the request (redacted when redactMessages is on):
 * the request's own headers, and for a request with request_metadata the
 * x-agentcc-metadata the wire gets: a raw x-agentcc-metadata of the request's
 * own (any spelling, kept once under the lowercase name), else the metadata
 * merged over `clientMetadata`.
 */
export function callbackRequest(
  options: RequestOptions,
  url: string,
  redact: boolean,
  clientMetadata?: Record<string, unknown>,
): CallbackRequest {
  const headers = options.metadata ? viewWithMetadata(options, clientMetadata) : options.headers ?? {};
  let cbReq: CallbackRequest = {
    method: options.method,
    url,
    headers: safeDiagnosticHeaders(Object.entries(headers)),
    body: options.body ?? null,
  };
  if (redact) {
    cbReq = redactCallbackRequest(cbReq);
  }
  return cbReq;
}

/** The request's own headers with the x-agentcc-metadata the wire gets. */
function viewWithMetadata(options: RequestOptions, clientMetadata?: Record<string, unknown>): Record<string, string> {
  const headers = assignHeaders({}, options.headers);
  if (!hasMetadataHeader(headers)) headers[HEADER_METADATA] = JSON.stringify(mergeMetadata(clientMetadata, options.metadata));
  return headers;
}

/** What a callback sees of the response. */
export function callbackResponse(response: Response, agentcc: AgentCCMetadata, body: unknown): CallbackResponse {
  const headers = safeDiagnosticHeaders(response.headers);
  return { statusCode: response.status, headers, agentcc, body, gatewayEvidence: getGatewayEvidence(response) };
}

/** onGuardrailBlock (for a 446), then onError, for an error status. */
export async function fireStatusErrorCallbacks(
  callbacks: CallbackHandler[],
  cbReq: CallbackRequest,
  statusError: APIStatusError,
): Promise<void> {
  if (statusError instanceof GuardrailBlockedError) {
    await invokeCallbacks(callbacks, "onGuardrailBlock", cbReq, statusError);
  }
  await invokeCallbacks(callbacks, "onError", cbReq, statusError);
}

/** The hooks a successful answer fires: cost, cache hit, fallback, guardrail warning, then onRequestEnd. */
export async function firePostRequestCallbacks(
  callbacks: CallbackHandler[],
  cbReq: CallbackRequest,
  options: RequestOptions,
  response: Response,
  agentcc: AgentCCMetadata,
  requestCost: number,
  totalCost: number,
  body: unknown,
): Promise<void> {
  const cbResp = callbackResponse(response, agentcc, body);

  // Cost update
  if (requestCost > 0) {
    await invokeCallbacks(callbacks, "onCostUpdate", cbReq, requestCost, totalCost);
  }

  // Cache hit
  if (agentcc.cacheStatus === "hit") {
    await invokeCallbacks(callbacks, "onCacheHit", cbReq, cbResp, agentcc.cacheStatus);
  }

  // Fallback used
  if (agentcc.fallbackUsed && agentcc.modelUsed) {
    const originalModel = ((options.body as Record<string, unknown>)?.model as string) ?? "unknown";
    await invokeCallbacks(callbacks, "onFallback", cbReq, originalModel, agentcc.modelUsed, "provider_fallback");
  }

  // Guardrail warning (246)
  if (response.status === 246) {
    await invokeCallbacks(callbacks, "onGuardrailWarning", cbReq, cbResp);
  }

  // Success
  await invokeCallbacks(callbacks, "onRequestEnd", cbReq, cbResp);
}
