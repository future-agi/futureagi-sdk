// Internal wire protocol for SDK-owned stream adapters, not gateway frames.
import { sdkBodyFailureEvidence, streamBodyError } from "./errors.js";
import type { StreamError } from "./errors.js";
import { parseGatewayEvidence } from "./gateway-evidence.js";
import type { GatewayEvidence } from "./gateway-evidence.js";
import { hasOrigin, markOrigin, originStore } from "./origin-store.js";

export const SDK_STREAM_FORMAT_HEADER = "x-futureagi-stream-format";
export const SDK_STREAM_FORMAT = "sdk-v1";
export const SDK_STREAM_ERROR_EVENT = "futureagi.sdk-error";
// Shared by every copy of the package, like the error origins (origin-store.ts).
const adapterResponses = originStore.adapterResponses;
const evidenceHeaders = ["x-agentcc-request-id", "x-agentcc-client-request-id", "x-agentcc-dispatched"] as const;

interface SDKStreamErrorFrame {
  sdk_error: { version: 1; evidence: GatewayEvidence };
}

/** Copy only validated owning evidence, never an error's headers, cause or body. */
function cleanEvidence(evidence: GatewayEvidence): GatewayEvidence {
  const fields: [string, string][] = [];
  if (typeof evidence.gatewayRequestId === "string") fields.push([evidenceHeaders[0], evidence.gatewayRequestId]);
  // Body-carried IDs must also be representable as HTTP field values. Unlike
  // native Headers, a JSON envelope can contain control characters or Unicode.
  if (typeof evidence.clientRequestId === "string" && /^[\t\x20-\x7e\x80-\xff]*$/.test(evidence.clientRequestId)) {
    fields.push([evidenceHeaders[1], evidence.clientRequestId]);
  }
  if (typeof evidence.dispatched === "boolean") fields.push([evidenceHeaders[2], String(evidence.dispatched)]);
  return parseGatewayEvidence(fields);
}

/** @internal Only adapter producers and the app-route transport opt in.
 * A gateway's header/event/payload cannot opt a normal Stream into this protocol.
 * The app route is the trust boundary across processes; no secret or signature
 * is placed in the stream. This is framing, not authentication of arbitrary URLs.
 */
export function acceptStreamAdapterResponse(response: Response): Response {
  if (response.headers.get(SDK_STREAM_FORMAT_HEADER) === SDK_STREAM_FORMAT) markOrigin(adapterResponses, response);
  return response;
}

/** @internal Keep owner headers for genuine gateway frames and later read errors.
 * App-supplied headers cannot override the protocol or its owning evidence.
 */
export function streamAdapterHeaders(evidence: GatewayEvidence, extra?: Record<string, string>): Headers {
  const headers = new Headers({ "Content-Type": "text/event-stream", "Cache-Control": "no-cache", Connection: "keep-alive", ...extra });
  const owner = cleanEvidence(evidence);
  for (const field of evidenceHeaders) headers.delete(field);
  if (owner.gatewayRequestId !== null) headers.set(evidenceHeaders[0], owner.gatewayRequestId);
  if (owner.clientRequestId !== null) headers.set(evidenceHeaders[1], owner.clientRequestId);
  if (typeof owner.dispatched === "boolean") headers.set(evidenceHeaders[2], String(owner.dispatched));
  headers.set(SDK_STREAM_FORMAT_HEADER, SDK_STREAM_FORMAT);
  return headers;
}

/** @internal The owning evidence of a stream handed to an adapter. A client's
 * StreamManager carries it; any other async iterable has none, so its evidence
 * is unknown rather than an error.
 */
export function adapterEvidence(stream: unknown): GatewayEvidence {
  const evidence = (stream as { gatewayEvidence?: unknown } | null | undefined)?.gatewayEvidence;
  return typeof evidence === "object" && evidence !== null ? (evidence as GatewayEvidence) : parseGatewayEvidence();
}

/** @internal The frame for an error that ended a stream. Only a failure the SDK
 * itself raised for a body it could not read or decode becomes an SDK frame,
 * and it carries no message: SDK diagnostics can contain response text, so the
 * receiver reconstructs a static diagnostic and applies guidance once. Every
 * other error (a gateway error frame, a misuse such as a stream that was
 * already consumed, an error an application iterable threw) keeps the existing
 * message/type/code/param frame and is never given body-failure handling.
 */
export function streamAdapterErrorEvent(error: unknown): string {
  const owner = sdkBodyFailureEvidence(error);
  if (owner) {
    const frame: SDKStreamErrorFrame = { sdk_error: { version: 1, evidence: cleanEvidence(owner) } };
    return `event: ${SDK_STREAM_ERROR_EVENT}\ndata: ${JSON.stringify(frame)}\n\n`;
  }
  const message = (error as { message?: unknown } | null | undefined)?.message;
  const payload: Record<string, string> = { message: typeof message === "string" ? message : "Stream error" };
  // A gateway error keeps its type, code and param. They are read from the
  // error's own fields: a StreamError another copy of the package raised is
  // not an instance of this copy's class.
  if (isStreamErrorShaped(error)) {
    for (const field of ["type", "code", "param"] as const) {
      const value = error[field];
      if (typeof value === "string" && value) payload[field] = value;
    }
  }
  return `data: ${JSON.stringify({ error: payload })}\n\n`;
}

function isStreamErrorShaped(value: unknown): value is Record<"type" | "code" | "param", unknown> {
  return typeof value === "object" && value !== null && (value as { name?: unknown }).name === "StreamError";
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function keys(value: Record<string, unknown>, allowed: string[]): boolean {
  return Object.keys(value).length === allowed.length && allowed.every(key => Object.prototype.hasOwnProperty.call(value, key));
}

/** @internal Called only AFTER gateway-frame classification. Invalid protocol
 * frames fail against the response owner; their untrusted evidence is not used.
 */
export function streamAdapterErrorFromEvent(response: Response, event: string | null, data: unknown, fallback: GatewayEvidence): StreamError | null {
  if (!hasOrigin(adapterResponses, response) || event !== SDK_STREAM_ERROR_EVENT) return null;
  if (record(data) && keys(data, ["sdk_error"])) {
    const frame = data.sdk_error;
    if (record(frame) && keys(frame, ["version", "evidence"]) && frame.version === 1) {
      const value = frame.evidence;
      if (record(value) && keys(value, ["dispatched", "gatewayRequestId", "clientRequestId"]) &&
          (value.dispatched === true || value.dispatched === false || value.dispatched === "unknown") &&
          (value.gatewayRequestId === null || typeof value.gatewayRequestId === "string") &&
          (value.clientRequestId === null || typeof value.clientRequestId === "string")) {
        const owner = cleanEvidence(value as unknown as GatewayEvidence);
        if (owner.dispatched === value.dispatched && owner.gatewayRequestId === value.gatewayRequestId && owner.clientRequestId === value.clientRequestId) {
          return streamBodyError("Failed to read stream body", owner);
        }
      }
    }
  }
  return streamBodyError("Invalid SDK stream error frame", fallback);
}
