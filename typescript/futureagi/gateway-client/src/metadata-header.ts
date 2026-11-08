// ---------------------------------------------------------------------------
// x-agentcc-metadata is one header in every spelling. Header names are
// case-insensitive, and fetch joins two spellings of one name with ", ",
// which for this JSON header is not JSON. So wherever header layers are
// merged (the client's request headers, a resource's per-request headers,
// the headers a callback sees), every spelling of this name is the same
// key: a later layer's value replaces each earlier spelling and is kept as
// `x-agentcc-metadata`. Every other name merges exactly as Object.assign
// merges it.
// ---------------------------------------------------------------------------

import { HEADER_METADATA } from "./constants.js";

/** Whether `name` is x-agentcc-metadata, in any spelling. */
export function isMetadataHeader(name: string): boolean {
  return name.toLowerCase() === HEADER_METADATA;
}

/** Whether `headers` carries x-agentcc-metadata, in any spelling. */
export function hasMetadataHeader(headers: Record<string, string> | null | undefined): boolean {
  return headers != null && Object.keys(headers).some(isMetadataHeader);
}

/** Set x-agentcc-metadata to `value`, removing every other spelling of it first. */
export function setMetadataHeader(headers: Record<string, string>, value: string): void {
  for (const name of Object.keys(headers)) {
    if (name !== HEADER_METADATA && isMetadataHeader(name)) delete headers[name];
  }
  headers[HEADER_METADATA] = value;
}

/**
 * `Object.assign(target, source)` for one layer of headers, except that
 * x-agentcc-metadata in any spelling goes through `setMetadataHeader`, so the
 * result holds it at most once. Returns `target`.
 */
export function assignHeaders(
  target: Record<string, string>,
  source: Record<string, string> | null | undefined,
): Record<string, string> {
  if (source == null) return target;
  for (const [name, value] of Object.entries(source)) {
    if (isMetadataHeader(name)) setMetadataHeader(target, value);
    else target[name] = value;
  }
  return target;
}
