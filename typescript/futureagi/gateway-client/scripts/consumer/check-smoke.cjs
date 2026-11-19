#!/usr/bin/env node
// Judge one consumer's smoke output against the API snapshot.
//   node check-smoke.cjs <api-snapshot.json> <smoke json> [--no-react]
// Every subpath in the snapshot must load, export exactly its runtime names
// (value exports; types have no runtime key) and resolve to its own build
// (dist/gateway/esm under import(), dist/gateway/cjs under require()); the
// client must answer through the fake fetch with the D-07 base URL. With
// --no-react, ./gateway/react must fail to load because react is absent.
"use strict";
const { readFileSync } = require("node:fs");

const [snapPath, smokePath, flag] = process.argv.slice(2);
const snap = JSON.parse(readFileSync(snapPath, "utf8")).subpaths;
const run = JSON.parse(readFileSync(smokePath, "utf8").trim().split("\n").pop());
const problems = [];
if (run.fatal) problems.push(`fatal: ${run.fatal.split("\n")[0]}`);
const dir = run.format === "esm" ? "dist/gateway/esm/" : "dist/gateway/cjs/";
for (const [sub, names] of Object.entries(snap)) {
  const key = sub.replace(/^\.\//, "");
  const load = run.loads && run.loads[key];
  const expected = Object.entries(names).filter(([, kind]) => kind !== "type").map(([n]) => n).sort();
  if (key === "gateway/react" && flag === "--no-react") {
    if (!load || load.ok) problems.push(`${key}: loaded without react installed`);
    else if (!/react/.test(load.message)) problems.push(`${key}: failed for another reason: ${load.message}`);
    continue;
  }
  if (!load || !load.ok) {
    problems.push(`${key}: did not load: ${load ? `${load.code} ${load.message}` : "absent"}`);
    continue;
  }
  const got = [...load.exports].sort();
  if (JSON.stringify(got) !== JSON.stringify(expected)) {
    problems.push(`${key}: exports differ: missing ${JSON.stringify(expected.filter((n) => !got.includes(n)))}, extra ${JSON.stringify(got.filter((n) => !expected.includes(n)))}`);
  }
  if (load.file && !load.file.includes(`node_modules/@future-agi/sdk/${dir}`)) problems.push(`${key}: resolved to ${load.file}, not ${dir}`);
}
const u = run.used || {};
if (snap["./gateway"]) {
  if (!u.gateway || u.gateway.content !== "hello" || u.gateway.streamed !== "hello" || u.gateway.cost !== 0.5) problems.push(`gateway: request through the client failed: ${JSON.stringify(u.gateway)}`);
  else if (u.gateway.url !== "http://127.0.0.1:9/v1/chat/completions") problems.push(`gateway: sent to ${u.gateway.url}`);
}
if (snap["./gateway/react"] && flag !== "--no-react") {
  if (!u.react || !/true:1:false/.test(u.react.direct) || !/0:true:true/.test(u.react.route)) problems.push(`react: render failed: ${JSON.stringify(u.react)}`);
}
process.stdout.write(JSON.stringify({ format: run.format, node: run.node, react: u.react ? u.react.version : null, problems }) + "\n");
process.exit(problems.length ? 1 : 0);
