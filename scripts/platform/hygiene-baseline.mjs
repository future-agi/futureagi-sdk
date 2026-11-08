/**
 * A temporary, counted debt inventory for fast checks, not a publication waiver.
 * Entries hash the file, target, rule and exact source line. Changed text, paths and duplicate
 * occurrences fail. Removed debt fails too, requiring a reviewed downward update. The snapshot
 * contains no offending text, internal names or revision ids. Every baseline says what it is
 * (`kind: "hygiene-debt"`); one without that label is refused. Exports and push-time verification
 * always use the strict scan, and `hygiene-tree.mjs --findings` lists the debt to resolve.
 */
import { sha256 } from "./hygiene-names.mjs";

export const BASELINE_KIND = "hygiene-debt";
const NOTE = "Known hits carried by fast checks only, each still to be resolved. Not publication clearance: exports and push-time verification use the strict scan.";

const fingerprint = (hit) => `sha256:${sha256(JSON.stringify([
  hit.file, hit.target ?? "content", hit.rule, hit.contentSha256 ?? hit.text
]))}`;

/** Construct a snapshot for review. Never called automatically by a check. */
export function baselineFor(scan) {
  const entries = {};
  for (const hit of scan.hits) {
    const key = fingerprint(hit);
    entries[key] = (entries[key] ?? 0) + 1;
  }
  return { version: 1, kind: BASELINE_KIND, note: NOTE, entries: Object.fromEntries(Object.entries(entries).sort()) };
}

/** Only exact counted matches are carried; everything else remains a blocking hit. */
export function compareBaseline(scan, baseline) {
  if (baseline?.version !== 1 || baseline.kind !== BASELINE_KIND || !baseline.entries || typeof baseline.entries !== "object" || Array.isArray(baseline.entries)
    || Object.entries(baseline.entries).some(([key, count]) => !/^sha256:[0-9a-f]{64}$/u.test(key) || !Number.isSafeInteger(count) || count <= 0)) {
    throw new Error(`invalid baseline: expected version 1, kind "${BASELINE_KIND}" and positive counts keyed by sha256 fingerprints`);
  }
  const remaining = new Map(Object.entries(baseline.entries));
  const hits = [];
  let carried = 0;
  for (const hit of scan.hits) {
    const key = fingerprint(hit);
    const count = remaining.get(key) ?? 0;
    if (count > 0) {
      remaining.set(key, count - 1);
      carried += 1;
    } else hits.push(hit);
  }
  for (const [key, count] of remaining) {
    if (count > 0) hits.push({ file: "baseline", line: 0, rule: "stale-baseline", text: `${key}: prune ${count} removed occurrence(s)` });
  }
  return { ...scan, mode: "debt-ratchet", hits, baseline: { kind: BASELINE_KIND, carried, total: scan.hits.length } };
}
