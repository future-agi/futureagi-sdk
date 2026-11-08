/**
 * The compare.json engine: turn a runner's outcome into a parity record, and compare two parity
 * records (the fake against the live rig, or one SDK against another) field by field.
 *
 * A parity record holds only fields named in compare.json. Comparing fails on any field listed
 * in neither `exact` nor `shapeOnly` (in either record), so an unlisted field cannot slip through.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { SUITE_ROOT } from "./cases.mjs";
import { jsonType } from "./schema-check.mjs";

export function loadCompareRules(file = path.join(SUITE_ROOT, "compare.json")) {
  const rules = JSON.parse(readFileSync(file, "utf8"));
  return {
    exact: new Set(Object.keys(rules.exact)),
    shapeOnly: new Set(Object.keys(rules.shapeOnly)),
    classes: Object.entries(rules.resultFieldClasses).map(([name, pattern]) => [name, new RegExp(pattern)]),
  };
}

/** Marks an empty array or object in a flattened map (its type, not a value). */
export const EMPTY = Symbol("empty-container");

/** Flatten a JSON value into dotted leaf paths (array items as [], so lengths do not matter). */
export function flatten(value, prefix = "", into = new Map()) {
  if (value !== null && typeof value === "object") {
    const entries = Array.isArray(value) ? value.map((item) => ["[]", item]) : Object.entries(value);
    if (entries.length === 0) into.set(prefix || "$", { [EMPTY]: Array.isArray(value) ? "array" : "object" });
    for (const [key, item] of entries) flatten(item, prefix ? `${prefix}.${key}` : key, into);
    return into;
  }
  into.set(prefix || "$", value);
  return into;
}

/** Build a parity record from an outcome. `extras` carries runner-extracted exact fields. */
export function toParityRecord(outcome, rules, extras = {}) {
  const record = {
    status: outcome.status ?? null,
    errorClass: outcome.errorClass ?? null,
    code: outcome.errorClass ? outcome.code ?? null : null,
    resultFields: {},
  };
  for (const name of ["requestId", "upstreamRequestId", "receiptId", "idempotencyKey"]) {
    if (outcome[name] !== undefined) record[name] = outcome[name];
  }
  if (outcome.body !== undefined && outcome.body !== null && !outcome.errorClass) {
    for (const [leaf, value] of flatten(outcome.body)) {
      const type = value !== null && typeof value === "object" && EMPTY in value ? value[EMPTY] : jsonType(value);
      const cls = rules.classes.find(([, pattern]) => pattern.test(leaf.replace(/\.\[\]/g, "")))?.[0];
      if (cls) (record[cls] ??= {})[leaf] = type;
      else record.resultFields[leaf] = type;
    }
  }
  for (const [name, value] of Object.entries(extras)) record[name] = value;
  return record;
}

function sameShape(a, b) {
  if (a === undefined || b === undefined) return a === b;
  if (jsonType(a) !== jsonType(b)) return false;
  if (a !== null && typeof a === "object") {
    const ka = Object.keys(a).sort();
    const kb = Object.keys(b).sort();
    return JSON.stringify(ka) === JSON.stringify(kb) && ka.every((k) => jsonType(a[k]) === jsonType(b[k]));
  }
  return true;
}

/** Compare two parity records. Returns { match, differences[] }. */
export function compareRecords(expected, actual, rules) {
  const differences = [];
  const fields = new Set([...Object.keys(expected), ...Object.keys(actual)]);
  for (const field of fields) {
    if (rules.exact.has(field)) {
      if (JSON.stringify(expected[field] ?? null) !== JSON.stringify(actual[field] ?? null)) {
        differences.push(`${field}: ${JSON.stringify(expected[field])} != ${JSON.stringify(actual[field])}`.slice(0, 400));
      }
    } else if (rules.shapeOnly.has(field)) {
      if (!sameShape(expected[field], actual[field])) differences.push(`${field}: shapes differ`);
    } else differences.push(`${field}: not listed in compare.json (unlisted fields fail)`);
  }
  return { match: differences.length === 0, differences };
}
