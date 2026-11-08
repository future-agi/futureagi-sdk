#!/usr/bin/env node
// Prove the ported suite runs every @agentcc/client 1.0.1 and @agentcc/react
// test it kept, under the same name, and that every one is accounted for
// (every kept test, under its 1.0.1 name).
//
//   node scripts/check-test-names.cjs <jest --json output>
//
// tests/port/vitest-the recorded revision.json is the @agentcc/client 1.0.1 run (420 tests,
// per file, in order); tests/port/react-vitest-the recorded revision.json the @agentcc/react
// run at the same commit (17 tests), whose files are named react/<file> here
// (they live in tests/react/). Files are named by their path under tests/.
// tests/port/manifest.json maps each baseline file to where its tests
// went: "port" (this suite, same file name), "shim" (S-bucket code that stays
// in the @agentcc/client 2.0 shim) or "live" (gateway-client/tests/
// live/, which needs a running gateway). A ported file may send single tests to the shim with
// "shim_tests". The check fails when:
//   - a 1.0.1 file has no manifest entry, or the manifest names a file 1.0.1 lacks;
//   - a ported file's test names differ from 1.0.1's in any way or order, after
//     removing its shim_tests;
//   - any test in the run did not pass;
//   - a shim_tests name is not a 1.0.1 test of that file.
// Tests the port added (new files, or names after the 1.0.1 ones in a file
// listed in "added") are counted and listed, never matched against 1.0.1.
"use strict";
const { readFileSync } = require("node:fs");
const { join, relative, sep } = require("node:path");

const testsDir = join(__dirname, "..", "tests");
const here = join(testsDir, "port");
const clientBaseline = JSON.parse(readFileSync(join(here, "vitest-legacy-client.json"), "utf8")).files;
const reactBaseline = JSON.parse(readFileSync(join(here, "react-vitest-legacy.json"), "utf8")).files;
const baseline = { ...clientBaseline };
for (const [file, tests] of Object.entries(reactBaseline)) baseline[`react/${file}`] = tests;
const manifest = JSON.parse(readFileSync(join(here, "manifest.json"), "utf8")).files;
const run = JSON.parse(readFileSync(process.argv[2], "utf8"));

const problems = [];
const ran = {};
for (const suite of run.testResults) {
  const file = relative(testsDir, suite.name).split(sep).join("/");
  if (suite.status !== "passed" && suite.assertionResults.length === 0) problems.push(`${file}: suite failed to run: ${(suite.message || "").split("\n")[0]}`);
  ran[file] = suite.assertionResults.map((a) => ({ name: [...a.ancestorTitles, a.title].join(" > "), status: a.status }));
}

const counts = { port: 0, shim: 0, live: 0, livePassedOffline: 0, added: 0 };
const addedNames = [];
for (const file of Object.keys(baseline)) if (!manifest[file]) problems.push(`${file}: 1.0.1 file has no manifest entry`);
for (const [file, entry] of Object.entries(manifest)) {
  const old = baseline[file];
  if (!old) {
    problems.push(`${file}: manifest names a file 1.0.1 does not have`);
    continue;
  }
  if (entry.to === "shim") {
    counts.shim += old.length;
    if (ran[file]) problems.push(`${file}: mapped to the shim but ran here`);
    continue;
  }
  if (entry.to === "live") {
    counts.live += old.length;
    counts.livePassedOffline += old.filter((t) => t.status === "passed").length;
    continue;
  }
  if (entry.to !== "port") {
    problems.push(`${file}: unknown destination ${entry.to}`);
    continue;
  }
  const shimTests = new Set(entry.shim_tests ? Object.keys(entry.shim_tests) : []);
  for (const name of shimTests) if (!old.some((t) => t.name === name)) problems.push(`${file}: shim_tests names "${name}", not a 1.0.1 test`);
  const kept = old.filter((t) => !shimTests.has(t.name)).map((t) => t.name);
  counts.shim += shimTests.size;
  const now = ran[file];
  if (!now) {
    problems.push(`${file}: ported, but not in this run`);
    continue;
  }
  const names = now.map((t) => t.name);
  const keptSet = new Set(kept);
  const same = names.filter((n) => keptSet.has(n));
  const missing = kept.filter((n) => !names.includes(n));
  if (missing.length) problems.push(`${file}: 1.0.1 tests missing: ${JSON.stringify(missing)}`);
  else if (JSON.stringify(same) !== JSON.stringify(kept)) problems.push(`${file}: the 1.0.1 tests run in another order`);
  const declared = new Set(entry.added ? Object.keys(entry.added) : []);
  const added = names.filter((n) => !keptSet.has(n));
  for (const n of added) if (!declared.has(n)) problems.push(`${file}: "${n}" is not a 1.0.1 test and the manifest does not list it under added`);
  for (const n of declared) if (!added.includes(n)) problems.push(`${file}: manifest lists "${n}" as added, but it did not run`);
  counts.port += kept.length - missing.length;
  counts.added += added.length;
  for (const n of added) addedNames.push(`${file}: ${n}`);
}
for (const [file, list] of Object.entries(ran)) {
  for (const t of list) if (t.status !== "passed") problems.push(`${file}: "${t.name}" ${t.status}`);
  if (!baseline[file]) {
    counts.added += list.length;
    for (const t of list) addedNames.push(`${file}: ${t.name}`);
  }
}

const count = (files) => Object.values(files).reduce((n, l) => n + l.length, 0);
const total = count(baseline);
const summary = {
  baseline_tests: total,
  baseline_by_package: { "@agentcc/client 1.0.1": count(clientBaseline), "@agentcc/react (client-patch-source)": count(reactBaseline) },
  ported_same_name: counts.port,
  to_shim: counts.shim,
  to_live: counts.live,
  live_tests_passing_offline_in_1_0_1: counts.livePassedOffline,
  accounted: counts.port + counts.shim + counts.live,
  added_by_port: counts.added,
  run: { tests: run.numTotalTests, passed: run.numPassedTests, failed: run.numFailedTests, pending: run.numPendingTests },
};
if (summary.accounted !== total) problems.push(`accounted ${summary.accounted} of ${total} 1.0.1 tests`);
process.stdout.write(JSON.stringify({ summary, added: addedNames, problems }, null, 1) + "\n");
process.exit(problems.length ? 1 : 0);
