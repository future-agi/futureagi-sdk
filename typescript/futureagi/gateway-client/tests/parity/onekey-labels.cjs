// Descriptions shared by the offline refusal-table generator and its checks.
// These labels describe observed behavior; they do not change retry policy.
const guardedMetadataCodes = new Set([
  "managed_model_unpriced",
  "managed_model_ambiguous",
  "managed_resource_unsupported",
]);

function metadataAccess(code) {
  return guardedMetadataCodes.has(code)
    ? "error.metadata retains unknown keys; model/candidates getters are type-guarded (null when absent or invalid)"
    : "error.metadata (Record<string, unknown>) and read-only camelCase getters; null when absent";
}

function metadataAccessJustification(code) {
  return guardedMetadataCodes.has(code)
    ? "Both languages retain unknown metadata keys and type-guard model/candidates; TypeScript exposes camelCase getters and null instead of Python snake_case properties and None."
    : "TypeScript record, null and camelCase getters instead of Python dict, None and snake_case properties.";
}

function namedAncestry(error) {
  const names = [];
  for (let prototype = Object.getPrototypeOf(Object.getPrototypeOf(error));
    prototype;
    prototype = Object.getPrototypeOf(prototype)) {
    if (prototype.constructor === Object) break;
    if (prototype.constructor.name) names.push(prototype.constructor.name);
  }
  return names;
}

const ancestryJustification = "JavaScript Error replaces Python SDKException; only named ancestry is reported, and anonymous mixin layers are omitted.";

const postHeaderBodyFailureDifference = Object.freeze({
  field: "post_header_body_failure_evidence",
  typescript: "Body read/decode failures on successful SDK-consumed JSON responses (2xx/246) raise terminal ResponseBodyError (an AgentCCError, not APIConnectionError) with no automatic replay, even with a per-error retry policy. Error-status bodies keep status- and header-driven retry rules. JSON body failures and StreamError reader failures retain the captured owning evidence; partial streams are never replayed. Caller-owned raw native readers retain the Response sidecar.",
  python: "Python follows the same shared rule (Python parity table r6d); no Python runtime verification is claimed here.",
  justification: "Post-header body failures: when the SDK itself reads and decodes a successful (2xx or 246) response body - JSON, or a binary body the SDK reads for the caller - and that read or decode fails after the response headers arrived, the SDK raises a terminal error that keeps the captured gateway evidence and never replays the request automatically, under any retry policy. Error-status responses (4xx/5xx) keep their status- and header-driven retry rules even when their body cannot be read. Partial streams are never replayed; caller-owned raw readers belong to the caller.",
});

module.exports = {
  metadataAccess,
  metadataAccessJustification,
  namedAncestry,
  ancestryJustification,
  postHeaderBodyFailureDifference,
};
