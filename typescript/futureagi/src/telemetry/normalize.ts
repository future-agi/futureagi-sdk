import type { Attributes } from "./otel";

// The shared carrier-consumer contract, identical to @traceai/fi-core's runtime
// attribute processor and traceAI's Python carrier writer. Pinned by the shared
// processor_v1.json vectors, which must stay byte-identical across the repos.
const PREFIX = /^(fi\.skills\.|fi\.context\.|gen_ai\.agent\.)/;
const SKILL_LISTS: ReadonlySet<string> = new Set(["fi.skills.version_ids", "fi.skills.ids", "fi.skills.refs"]);
const MAX_ATTRIBUTES = 64;
const MAX_SKILLS = 32;
const MAX_SCAN = 256;
const short = (value: unknown): value is string => typeof value === "string" && Buffer.byteLength(value, "utf8") <= 256;

/** Bounded normalization of a carrier or registry snapshot before stamping.
 * Keeps at most 62 copied keys plus the derived skill count and truncation flag;
 * examines at most 256 keys and at most the list cap of items per list. */
export function normalizedCarrier(input: unknown): Attributes {
  const result: Record<string, string | number | boolean | readonly string[]> = {};
  if (!input || typeof input !== "object" || Array.isArray(input)) return Object.freeze(result);
  const source = input as Record<string, unknown>;
  let truncated = false, scanned = 0, kept = 0;
  for (const key in source) {
    if (++scanned > MAX_SCAN) break;
    if (!Object.prototype.hasOwnProperty.call(source, key)) continue;
    if (!short(key) || !PREFIX.test(key) || key === "fi.context.linked_skill_version_ids") continue;
    const value = source[key];
    let retained: string | number | boolean | readonly string[];
    if (typeof value === "string") {
      if (!short(value)) continue;
      retained = value;
    } else if (typeof value === "boolean" || (typeof value === "number" && Number.isFinite(value))) {
      retained = value;
    } else if (Array.isArray(value)) {
      const skillList = SKILL_LISTS.has(key), limit = skillList ? MAX_SKILLS : MAX_ATTRIBUTES;
      const head: string[] = [];
      let valid = true;
      for (let i = 0; i < Math.min(value.length, limit); i++) {
        const item: unknown = value[i];
        if (!short(item)) { valid = false; break; }
        head.push(item);
      }
      if (!valid) continue;
      if (skillList) truncated ||= value.length > MAX_SKILLS;
      else if (value.length > limit) continue;
      retained = Object.freeze(head);
    } else continue;
    if (!Object.prototype.hasOwnProperty.call(result, key)) kept++;
    result[key] = retained;
    if (kept === MAX_ATTRIBUTES - 2) break;
  }
  const versions = result["fi.skills.version_ids"];
  if (Array.isArray(versions)) result["fi.skills.count"] = versions.length;
  if (truncated) result["fi.skills.truncated"] = true;
  else if (result["fi.skills.truncated"] !== true) delete result["fi.skills.truncated"];
  return Object.freeze(result);
}
