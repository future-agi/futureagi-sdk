#!/usr/bin/env node
// Compare a recording of this client (record-enew.sh) with the @agentcc/client 1.0.1
// golden of the same module format.
//
//   node compare-enew.mjs --new <recording dir> --format esm|cjs [--report <out.json>]
//
// The differences allowed are the shared tests/fixtures/gateway/intended-differences.json
// plus this client's overlay, tests/gateway/intended-differences-e-new-ts.json. The
// client's entries (ids 'D-xx-ts' and 'TS-*', PORT_ID) live in the shared file once
// signed ('proven', with a reviewer record) and in the overlay while 'landed' (evidence
// and test id filled, reviewer record pending); both cover here. It passes only with 0
// unlisted differences, every entry of the client covering something and every one of
// its rules used. The release gate is the shared file's rule, under which only 'proven'
// entries cover, so the report also gives that strict count (strict_unlisted): 0
// exactly when no entry of the client waits for a reviewer. record-enew.sh also runs
// that gate on its own (tests/parity/compare.mjs with the shared file only).
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

const GC = fileURLToPath(new URL("../../", import.meta.url));
const FIXTURES = join(GC, "..", "..", "..", "tests", "fixtures", "gateway");
const OVERLAY = join(GC, "tests", "gateway", "intended-differences-e-new-ts.json");
const { compareCases, covers, diff, loadRecording, view } = await import(pathToFileURL(join(GC, "tests", "parity", "compare.mjs")).href);
const { checkLabel } = await import(pathToFileURL(join(GC, "tests", "parity", "labels.mjs")).href);

// The client's ids: '-ts' splits of the shared D-xx work list, 'TS-*' for changes
// without a D number (the overlay test holds every entry to this shape).
export const PORT_ID = /^(D-\d\d[a-z]?-ts|TS-[0-9.]+-[a-z0-9-]+)$/;

/** The client's entries still in the overlay (not yet signed into the shared file). */
export function overlayEntries(path = OVERLAY) {
  return JSON.parse(readFileSync(path, "utf8")).differences;
}

export function sharedEntries() {
  return JSON.parse(readFileSync(join(FIXTURES, "intended-differences.json"), "utf8")).differences;
}

/** Every entry of the client: those signed into the shared file, then the overlay's. */
export function portEntries(overlayPath = OVERLAY) {
  return [...sharedEntries().filter((e) => PORT_ID.test(e.id)), ...overlayEntries(overlayPath)];
}

export function compareNew(newDir, format, overlayPath = OVERLAY) {
  const label = `ts-client-1.0.1-${format}->e-new-ts-${format}`;
  const goldenDir = join(FIXTURES, "golden", `ts-client-1.0.1-${format}`);
  checkLabel(label, goldenDir, newDir);
  const shared = sharedEntries();
  const overlay = overlayEntries(overlayPath);
  const port = [...shared.filter((e) => PORT_ID.test(e.id)), ...overlay];
  const clash = overlay.map((e) => e.id).filter((id) => shared.some((s) => s.id === id));
  if (clash.length) throw new Error(`overlay ids must be new: ${clash.join(", ")}`);
  const golden = loadRecording(goldenDir).cases;
  const fresh = loadRecording(newDir).cases;
  const asProven = overlay.filter((e) => ["landed", "proven"].includes(e.status)).map((e) => ({ ...e, status: "proven" }));
  const report = compareCases(golden, fresh, [...shared, ...asProven], label);
  const changes = diff(view(golden), view(fresh));
  report.unused_overlay_rules = port.flatMap((e) => e.match.flatMap((rule, i) => (changes.some((d) => covers(rule, d)) ? [] : [`${e.id}: rule ${i} ${rule.path}`])));
  const ids = new Set(port.map((e) => e.id));
  report.unobserved_overlay = report.unobserved_proven.filter((id) => ids.has(id));
  report.awaiting_reviewer = port.filter((e) => e.status === "landed").map((e) => e.id).sort();
  report.ok = report.ok && !report.unused_overlay_rules.length && !report.unobserved_overlay.length;
  const strict = compareCases(golden, fresh, [...shared, ...overlay], label);
  report.strict_unlisted = strict.unlisted.length;
  report.strict_ok = strict.ok;
  return report;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const { values } = parseArgs({ options: { new: { type: "string" }, format: { type: "string" }, report: { type: "string" } } });
  if (!values.new || !["esm", "cjs"].includes(values.format)) {
    process.stderr.write("usage: compare-enew.mjs --new <recording dir> --format esm|cjs [--report <out.json>]\n");
    process.exit(2);
  }
  const report = compareNew(values.new, values.format);
  if (values.report) writeFileSync(values.report, JSON.stringify(report, null, 1) + "\n");
  const covered = Object.values(report.covered).reduce((a, b) => a + b, 0);
  process.stdout.write(`${report.label}: ok=${report.ok} unlisted=${report.unlisted.length} covered=${covered} in ${Object.keys(report.covered).length} entries; unused overlay rules=${report.unused_overlay_rules.length}; awaiting a reviewer record: ${report.awaiting_reviewer.length} entries\n`);
  process.stdout.write(`  strict rule (only signed entries cover; the release gate): ok=${report.strict_ok} unlisted=${report.strict_unlisted}\n`);
  for (const d of report.unlisted.slice(0, 40)) process.stdout.write(`  UNLISTED ${d.kind} ${d.path}\n`);
  for (const line of report.unused_overlay_rules.slice(0, 40)) process.stdout.write(`  UNUSED ${line}\n`);
  process.exit(report.ok ? 0 : 1);
}
