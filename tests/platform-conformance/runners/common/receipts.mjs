/**
 * Writing a runner's receipts: results.jsonl (one line per case and mode) and summary.json.
 *
 * Before anything is written the text is scanned for every credential value the run held; a hit
 * refuses the write (the receipt would leak) and fails the run. Bodies are never written: a result
 * carries statuses, codes, ids and a parity record of shapes (lib/compare.mjs).
 */
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

export class LeakError extends Error {}

export function assertNoSecrets(text, secrets) {
  const hits = secrets.filter((s) => s && text.includes(s)).length;
  if (hits) throw new LeakError(`refusing to write a receipt: ${hits} credential value(s) appear in it`);
}

export function summarize(results) {
  const counts = { pass: 0, fail: 0, xfail: 0, xpass: 0, skip: 0 };
  const byFamily = {};
  for (const r of results) {
    counts[r.verdict] = (counts[r.verdict] ?? 0) + 1;
    const family = r.id.split(".")[0];
    byFamily[family] ??= { pass: 0, fail: 0, xfail: 0, xpass: 0, skip: 0 };
    byFamily[family][r.verdict] += 1;
  }
  return { total: results.length, counts, byFamily, failed: results.filter((r) => r.verdict === "fail").map((r) => ({ id: r.id, mode: r.mode, failures: r.failures.slice(0, 5) })) };
}

export function writeReceipts(outDir, { results, summary }, secrets = []) {
  mkdirSync(outDir, { recursive: true });
  const lines = `${results.map((r) => JSON.stringify(r)).join("\n")}\n`;
  const doc = `${JSON.stringify(summary, null, 2)}\n`;
  assertNoSecrets(lines, secrets);
  assertNoSecrets(doc, secrets);
  writeFileSync(path.join(outDir, "results.jsonl"), lines);
  writeFileSync(path.join(outDir, "summary.json"), doc);
  return { results: path.join(outDir, "results.jsonl"), summary: path.join(outDir, "summary.json") };
}
