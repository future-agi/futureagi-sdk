/**
 * Transport evidence describes one owning final HTTP response, never a billing
 * decision. A true dispatch bit means a provider attempt, not a charge; false on
 * a successful submission says nothing about subsequent execution. Only the
 * authoritative settlement record determines charges or releases.
 *
 * Browser WebSockets cannot expose the 101 headers: parse undefined headers to
 * retain unknown evidence. Never inspect application frames or trailers as a
 * substitute. A browser's CORS-hidden field is unobservable, not absent. These
 * client types describe the normative contract, not deployed gateway coverage.
 */
export type DispatchState = boolean | "unknown";
export interface GatewayEvidence {
  readonly dispatched: DispatchState;
  readonly gatewayRequestId: string | null;
  readonly clientRequestId: string | null;
}
export interface GatewayEvidenceOptions {
  /** False when absent headers may be hidden (for example by CORS). */
  readonly headersObservable?: boolean;
  /** False for adapters known to discard duplicate fields. */
  readonly cardinalityObservable?: boolean;
}
export type GatewayEvidenceHeaders = Headers | readonly (readonly [string, string])[];
type Presence = "absent" | "present" | "unobservable";
const presence = new WeakMap<GatewayEvidence, Presence>();
const responses = new WeakMap<Response, GatewayEvidence>();
const capturedHeaders = new WeakMap<Headers, GatewayEvidence>();
const ULID = /^[0-7][0-9A-HJKMNP-TV-Z]{25}$/;

/** Parse only the three allowlisted final-response fields, never body mirrors.
 * Fetch combines duplicates with commas, which fail singleton validation. Pass
 * raw pairs when available; a lossy adapter must declare its limitations.
 */
export function parseGatewayEvidence(headers?: GatewayEvidenceHeaders, options: GatewayEvidenceOptions = {}): GatewayEvidence {
  const fields = new Map<string, string[]>([
    ["x-agentcc-dispatched", []], ["x-agentcc-request-id", []], ["x-agentcc-client-request-id", []],
  ]);
  if (headers) {
    for (const [name, value] of headers) fields.get(name.toLowerCase())?.push(value);
  }
  const dispatch = fields.get("x-agentcc-dispatched")!;
  const ids = fields.get("x-agentcc-request-id")!;
  const clients = fields.get("x-agentcc-client-request-id")!;
  const cardinality = options.cardinalityObservable !== false;
  const token = cardinality && dispatch.length === 1 ? dispatch[0].replace(/^[ \t]+|[ \t]+$/g, "") : null;
  const evidence: GatewayEvidence = Object.freeze({
    dispatched: token === "true" ? true : token === "false" ? false : "unknown",
    gatewayRequestId: cardinality && ids.length === 1 && ids[0].length === 26 && ULID.test(ids[0]) ? ids[0] : null,
    clientRequestId: cardinality && clients.length === 1 && !clients[0].includes(",") ? clients[0] : null,
  });
  presence.set(evidence, ids.length > 0 ? "present"
    : headers && cardinality && options.headersObservable !== false ? "absent" : "unobservable");
  return evidence;
}

/** Internal retry guard: invalid identity is still a present field. */
export function gatewayRequestIdPresence(evidence: GatewayEvidence): Presence {
  return presence.get(evidence) ?? "unobservable";
}

/** Capture immediately after fetch, before callbacks or any body consumption. */
export function captureGatewayEvidence(response: Response, options: GatewayEvidenceOptions = {}): GatewayEvidence {
  const evidence = parseGatewayEvidence(response.headers, {
    ...options,
    headersObservable: options.headersObservable !== false && !["cors", "opaque", "opaqueredirect"].includes(response.type),
  });
  responses.set(response, evidence);
  capturedHeaders.set(response.headers, evidence);
  return evidence;
}

/** Evidence sidecar for raw/binary/native responses; does not rewrite the body. */
export function getGatewayEvidence(response: Response): GatewayEvidence {
  return responses.get(response) ?? captureGatewayEvidence(response);
}

/** Reuse the owning snapshot when metadata or error wrappers read the headers. */
export function evidenceFromHeaders(headers: Headers): GatewayEvidence {
  return capturedHeaders.get(headers) ?? parseGatewayEvidence(headers);
}
