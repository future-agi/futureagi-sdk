#!/usr/bin/env node
/**
 * Compare two copies of the platform contract (the current pin and a candidate) by their policy tables.
 *
 *   node scripts/platform/pin-diff.mjs <current.json> <candidate.json> [--scope openapi/platform/scope.json]
 *   node scripts/platform/pin-diff.mjs --counts <contract.json>     # one file's sha256, counts and families
 *
 * Prints each file's sha256 and counts (keyed, keyed-not-durable, http-idempotent, unsafe, human-only,
 * streams, paginated), the operations added and removed, and every changed policy field, each labelled
 * BREAKING or additive. With --scope, a change to an operation outside the scope is labelled out-of-scope
 * and never counts as breaking. Exit 0 always; scripts/platform/check-pin.sh reads the BREAKING count.
 */

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { METHODS } from "./openapi-walk.mjs";
import { buildPolicy, policyCounts } from "./policy-model.mjs";

/**
 * Each policy field and the direction that breaks a released SDK: it sends a request the server now
 * refuses, or it retries an operation the server no longer makes safe to retry (an idempotency flag
 * dropped, durability lost, a destroy that no longer reports not-found as applied). The retry class is
 * derived from method, idempotent and durable, so it is not compared on its own.
 */
const RULES = {
  method: () => "BREAKING",
  path: () => "BREAKING",
  path_params: () => "BREAKING",
  body: () => "BREAKING",
  content_type: () => "BREAKING",
  stream: () => "BREAKING",
  pagination: () => "BREAKING",
  query: (a, b) => (a.every((q) => b.includes(q)) ? "additive" : "BREAKING"),
  headers: (a, b) => (a.every((h) => b.includes(h)) ? "additive" : "BREAKING"),
  idempotent: (a, b) => (a && !b ? "BREAKING" : "additive"),
  durable: (a, b) => (a !== false && b === false ? "BREAKING" : "additive"),
  key_required: (a, b) => (!a && b ? "BREAKING" : "additive"),
  replay_omits: (a, b) => (b.every((x) => a.includes(x)) ? "additive" : "BREAKING"),
  not_found_means_applied: (a, b) => (a && !b ? "BREAKING" : "additive"),
  secret_fields: (a, b) => (a.every((x) => b.includes(x)) ? "additive" : "BREAKING"),
  role: () => "BREAKING",
  operation_id: () => "additive",
  timeout: () => "additive",
  rate: () => "additive",
  multi_segment: () => "BREAKING",
  stop: () => "additive"
};

function sha256(file) {
  return createHash("sha256").update(readFileSync(file)).digest("hex");
}

function humanOnly(doc) {
  const out = new Set();
  for (const item of Object.values(doc.paths ?? {})) {
    for (const m of METHODS) {
      const op = item[m];
      if (op && op["x-omega-human-only"] === true) out.add(`${op["x-omega-sdk"].family}.${op["x-omega-sdk"].method}`);
    }
  }
  return out;
}

/** The comparison as data: `{ files, added, removed, changes }`. */
export function diffPins(currentDoc, candidateDoc, scope) {
  const inScope = scope ? new Set(scope.operations) : undefined;
  const current = new Map(buildPolicy(currentDoc).operations.map((o) => [o.name, o]));
  const candidate = new Map(buildPolicy(candidateDoc).operations.map((o) => [o.name, o]));
  const human = humanOnly(candidateDoc);
  const label = (name, verdict) => (inScope && !inScope.has(name) ? "out-of-scope" : verdict);
  const added = [...candidate.keys()].filter((n) => !current.has(n)).sort();
  const removed = [...current.keys()].filter((n) => !candidate.has(n)).sort().map((name) => ({ name, verdict: label(name, "BREAKING") }));
  const changes = [];
  for (const [name, before] of current) {
    const after = candidate.get(name);
    if (!after) continue;
    if (human.has(name) && inScope?.has(name)) changes.push({ name, field: "human_only", before: false, after: true, verdict: "BREAKING" });
    for (const field of Object.keys(RULES)) {
      const a = before[field];
      const b = after[field];
      if (JSON.stringify(a) === JSON.stringify(b)) continue;
      changes.push({ name, field, before: a, after: b, verdict: label(name, RULES[field](a, b)) });
    }
  }
  return { added, removed, changes };
}

function countsLine(label, file, doc) {
  const policy = buildPolicy(doc);
  const counts = policyCounts(policy.operations);
  const human = humanOnly(doc);
  const keyedHuman = policy.operations.filter((o) => o.idempotent && human.has(o.name)).length;
  return `${label}: sha256 ${sha256(file)}\n  ${JSON.stringify({ ...counts, human_only: human.size, keyed_human_only: keyedHuman })}`;
}

function familiesOf(doc) {
  const names = buildPolicy(doc).operations.map((o) => o.name.split("."));
  return [...new Set(names.map((n) => (n[0] === "platform" ? `${n[0]}.${n[1]}` : n[0])))].sort();
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url) && process.argv[2] === "--counts") {
  const file = process.argv[3];
  const doc = JSON.parse(readFileSync(file, "utf8"));
  process.stdout.write(`${countsLine(path.basename(file), file, doc)}\n  families: ${familiesOf(doc).join(", ")}\n`);
  process.exit(0);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  const scopeAt = args.indexOf("--scope");
  const scope = scopeAt >= 0 ? JSON.parse(readFileSync(args[scopeAt + 1], "utf8")) : undefined;
  const [currentFile, candidateFile] = args.filter((_, i) => i !== scopeAt && i !== scopeAt + 1);
  if (!currentFile || !candidateFile) {
    process.stderr.write("usage: pin-diff.mjs <current.json> <candidate.json> [--scope scope.json]\n");
    process.exit(2);
  }
  const currentDoc = JSON.parse(readFileSync(currentFile, "utf8"));
  const candidateDoc = JSON.parse(readFileSync(candidateFile, "utf8"));
  const { added, removed, changes } = diffPins(currentDoc, candidateDoc, scope);
  const out = [countsLine("current", currentFile, currentDoc), countsLine("candidate", candidateFile, candidateDoc)];
  out.push(`added (${added.length}): ${added.join(", ") || "none"}`);
  out.push(`removed (${removed.length}): ${removed.map((r) => `${r.name} [${r.verdict}]`).join(", ") || "none"}`);
  out.push(`changed (${changes.length}):`);
  for (const c of changes) out.push(`  [${c.verdict}] ${c.name} ${c.field}: ${JSON.stringify(c.before)} -> ${JSON.stringify(c.after)}`);
  const breaking = removed.filter((r) => r.verdict === "BREAKING").length + changes.filter((c) => c.verdict === "BREAKING").length;
  out.push(`BREAKING: ${breaking}`);
  process.stdout.write(`${out.join("\n")}\n`);
}
