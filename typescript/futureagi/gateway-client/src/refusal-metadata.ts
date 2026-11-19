/** Optional serializer mirrors are diagnostics, never authoritative evidence. */
export interface GatewayErrorMetadata extends Record<string, unknown> {
  dispatched?: unknown;
  request_id?: unknown;
}
export interface ManagedModelUnpricedMetadata extends GatewayErrorMetadata {
  model: string;
  reason: "unpriced";
}
export interface ManagedModelAmbiguousMetadata extends GatewayErrorMetadata {
  model: string;
  candidates: string[];
}

/** Validate producer fields without rejecting additive keys or old omissions. */
export function unpricedMetadata(metadata: Record<string, unknown> | null): ManagedModelUnpricedMetadata | null {
  return typeof metadata?.model === "string" && metadata.reason === "unpriced"
    ? metadata as ManagedModelUnpricedMetadata : null;
}
export function ambiguousMetadata(metadata: Record<string, unknown> | null): ManagedModelAmbiguousMetadata | null {
  return typeof metadata?.model === "string" && Array.isArray(metadata.candidates)
    && metadata.candidates.every((candidate) => typeof candidate === "string")
    ? metadata as ManagedModelAmbiguousMetadata : null;
}
