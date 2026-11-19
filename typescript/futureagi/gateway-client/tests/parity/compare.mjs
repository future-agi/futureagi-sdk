// Compare a recording against a golden under intended-differences.json.
// The TypeScript twin of python/tests/gateway/parity/compare.py: the same view,
// diff, glob and coverage rules; both pass tests/fixtures/gateway/comparator-cases.json.
// Only a "proven" entry covers a difference; a "planned" one is a implementation's work
// list and is named beside the unlisted difference it would cover.
//
//   node compare.mjs --golden <dir> --new <dir> --label <golden>-><new> [--intended <file>]
// A label that does not fit the two directories is refused with exit 2 (labels.mjs).
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { LabelError, checkLabel } from "./labels.mjs";

export const MISSING = "<missing>";
const SET_KEYS = new Set(["exports", "public", "defined", "all", "__all__", "dir_public", "case_ids", "proto", "statics", "methods", "clientMethods", "valid", "valid_models", "model_info_keys"]);
const FIXTURES = fileURLToPath(new URL("../../../../../tests/fixtures/gateway/", import.meta.url));

const globCache = new Map();
export function matches(pattern, text) {
  if (!globCache.has(pattern)) {
    const source = [...pattern].map((c) => (c === "*" ? "[\\s\\S]*" : c === "?" ? "[\\s\\S]" : c.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&"))).join("");
    globCache.set(pattern, new RegExp(`^${source}$`));
  }
  return globCache.get(pattern).test(text);
}

const isPairList = (v) => Array.isArray(v) && v.every((p) => Array.isArray(p) && p.length === 2);

export function view(value) {
  if (Array.isArray(value)) return value.map(view);
  if (value && typeof value === "object") {
    const out = {};
    for (const [key, item] of Object.entries(value)) {
      if (key === "headers" && isPairList(item)) {
        const merged = {};
        for (const [name, val] of item) merged[name] = name in merged ? [...(Array.isArray(merged[name]) ? merged[name] : [merged[name]]), val] : val;
        out[key] = merged;
      } else if (SET_KEYS.has(key) && Array.isArray(item) && item.every((v) => typeof v === "string")) {
        out[key] = Object.fromEntries(item.map((n) => [n, true]));
      } else out[key] = view(item);
    }
    return out;
  }
  return value;
}

const isObject = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
const sameScalar = (a, b) => a === b || (Number.isNaN(a) && Number.isNaN(b));
// Python's json keeps int vs float apart (0 vs 0.0); JS cannot tell, so numbers compare by value.
const sortedKeys = (a, b) => [...new Set([...Object.keys(a), ...Object.keys(b)])].sort((x, y) => (x < y ? -1 : x > y ? 1 : 0));

export function diff(oldV, newV, path = "") {
  if (isObject(oldV) && isObject(newV)) {
    const out = [];
    for (const key of sortedKeys(oldV, newV)) {
      const sub = path ? `${path}/${key}` : key;
      if (!(key in newV)) out.push({ path: sub, kind: "removed", old: oldV[key], new: MISSING });
      else if (!(key in oldV)) out.push({ path: sub, kind: "added", old: MISSING, new: newV[key] });
      else out.push(...diff(oldV[key], newV[key], sub));
    }
    return out;
  }
  if (Array.isArray(oldV) && Array.isArray(newV)) {
    const out = [];
    for (let i = 0; i < Math.max(oldV.length, newV.length); i++) {
      const sub = `${path}/${i}`;
      if (i >= newV.length) out.push({ path: sub, kind: "removed", old: oldV[i], new: MISSING });
      else if (i >= oldV.length) out.push({ path: sub, kind: "added", old: MISSING, new: newV[i] });
      else out.push(...diff(oldV[i], newV[i], sub));
    }
    return out;
  }
  const bothScalar = !isObject(oldV) && !Array.isArray(oldV) && !isObject(newV) && !Array.isArray(newV);
  return bothScalar && sameScalar(oldV, newV) ? [] : [{ path, kind: "changed", old: oldV, new: newV }];
}

function canon(v) {
  if (Array.isArray(v)) return v.map(canon);
  if (isObject(v)) return Object.fromEntries(Object.keys(v).sort().map((k) => [k, canon(v[k])]));
  return v;
}
// The text an old/new regex sees: strings as they are, anything else as compact sorted JSON.
const scalarText = (v) => (typeof v === "string" ? v : JSON.stringify(canon(v)));

export function covers(rule, d) {
  if (!matches(rule.path ?? "*", d.path)) return false;
  if (rule.top_level && d.path.includes("/")) return false;
  if ((rule.kind ?? "any") !== "any" && rule.kind !== d.kind) return false;
  for (const side of ["old", "new"]) if (side in rule && !new RegExp(rule[side]).test(scalarText(d[side]))) return false;
  return true;
}

export function compareCases(golden, fresh, intended, label) {
  const rules = intended.filter((r) => (r.applies_to ?? []).some((p) => matches(p, label)));
  const hits = Object.fromEntries(rules.map((r) => [r.id, 0]));
  const unlisted = [];
  for (const d of diff(view(golden), view(fresh))) {
    const hit = rules.filter((r) => (r.match ?? []).some((m) => covers(m, d)));
    for (const r of hit) hits[r.id] += 1;
    // Only a proven entry covers (API contract 5.3: evidence, a test id, a reviewer).
    if (!hit.some((r) => r.status === "proven")) unlisted.push({ ...d, planned: hit.map((r) => r.id).sort() });
  }
  const unobserved = (status) => rules.filter((r) => r.status === status && hits[r.id] === 0).map((r) => r.id).sort();
  const proven = new Set(rules.filter((r) => r.status === "proven").map((r) => r.id));
  const covered = Object.fromEntries(Object.entries(hits).filter(([id, n]) => n && proven.has(id)).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)));
  return { label, ok: !unlisted.length && !unobserved("proven").length, unlisted, covered, unobserved_proven: unobserved("proven"), unobserved_planned: unobserved("planned") };
}

export function loadRecording(folder) {
  const index = JSON.parse(readFileSync(join(folder, "index.json"), "utf8"));
  const cases = {};
  for (const name of Object.keys(index.files ?? {}).sort()) Object.assign(cases, JSON.parse(readFileSync(join(folder, name), "utf8")).cases);
  const surface = {};
  for (const key of ["loads", "dts"]) if (key in index) surface[key] = index[key];
  if (Object.keys(surface).length) cases["<index>"] = surface;
  return { index, cases };
}

// Compare two recordings on disk; a label that does not fit them throws LabelError (labels.mjs).
export function compare(goldenDir, newDir, intendedFile, label) {
  checkLabel(label, goldenDir, newDir);
  const golden = loadRecording(goldenDir);
  const fresh = loadRecording(newDir);
  const report = compareCases(golden.cases, fresh.cases, JSON.parse(readFileSync(intendedFile, "utf8")).differences, label);
  report.environment_differences = diff(golden.index.environment ?? {}, fresh.index.environment ?? {});
  return report;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const { values } = parseArgs({ options: { golden: { type: "string" }, new: { type: "string" }, label: { type: "string" }, intended: { type: "string" } } });
  let report;
  try {
    report = compare(values.golden, values.new, values.intended ?? join(FIXTURES, "intended-differences.json"), values.label);
  } catch (err) {
    if (!(err instanceof LabelError)) throw err;
    process.stderr.write(`${err.message}\n`);
    process.exit(2);
  }
  process.stdout.write(`${report.label}: ok=${report.ok} unlisted=${report.unlisted.length} covered=${JSON.stringify(report.covered)} unobserved_proven=${JSON.stringify(report.unobserved_proven)}\n`);
  for (const d of report.unlisted.slice(0, 40)) process.stdout.write(`  UNLISTED ${d.kind} ${d.path}${d.planned.length ? ` (planned: ${d.planned.join(", ")})` : ""}\n`);
  process.exit(report.ok ? 0 : 1);
}
