#!/usr/bin/env node
// The live run's test names against tests/live/manifest.json.
//   node check-live-names.cjs <jest --json output>
// Every 1.0.1 live test the manifest sends to tests/live/<file> must have run in
// that file under the same name ("describe > test", vitest's form) and passed.
// Prints a JSON report; exit 1 on any missing, renamed or failed test.
"use strict";
const { readFileSync } = require("node:fs");
const { basename, join } = require("node:path");

const run = JSON.parse(readFileSync(process.argv[2], "utf8"));
const manifest = JSON.parse(readFileSync(join(__dirname, "manifest.json"), "utf8"));
const seen = new Map();
for (const file of run.testResults) {
  for (const t of file.assertionResults) {
    seen.set(`${basename(file.name)}::${[...t.ancestorTitles, t.title].join(" > ")}`, t.status);
  }
}
const problems = [];
let ported = 0;
for (const [file, tests] of Object.entries(manifest.files)) {
  for (const t of tests) {
    if (t.to === "shim") continue;
    ported += 1;
    const status = seen.get(`${file}::${t.name}`);
    if (status === undefined) problems.push(`${file}: "${t.name}" did not run`);
    else if (status !== "passed") problems.push(`${file}: "${t.name}" ${status}`);
  }
}
const report = { manifest_total: manifest.total, ported, to_shim: manifest.to_shim, run_tests: seen.size, run_passed: [...seen.values()].filter((s) => s === "passed").length, problems };
process.stdout.write(JSON.stringify(report, null, 1) + "\n");
process.exit(problems.length ? 1 : 0);
