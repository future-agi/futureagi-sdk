#!/usr/bin/env node
// esbuild metafile check: a browser bundle of a
// gateway subpath holds only the entry and files of
// @future-agi/sdk/dist/gateway/esm/, and its only external import is react
// (the react subpath's optional peer). So no node:* module, openai, axios,
// winston, form-data or uuid, and never the root barrel.
//   node check-metafile.cjs <meta.json> <entry>
"use strict";
const { readFileSync } = require("node:fs");
const [metaPath, entry] = process.argv.slice(2);
const meta = JSON.parse(readFileSync(metaPath, "utf8"));
const problems = [];
const inputs = Object.keys(meta.inputs);
for (const input of inputs) {
  if (input === entry || input.endsWith(`/${entry}`)) continue;
  if (!/node_modules\/@future-agi\/sdk\/dist\/gateway\/esm\//.test(input)) problems.push(`bundled ${input}`);
}
const externals = new Set();
for (const [file, info] of Object.entries(meta.inputs)) {
  for (const imp of info.imports || []) if (imp.external) externals.add(imp.path);
}
for (const ext of externals) if (ext !== "react") problems.push(`external import ${ext}`);
for (const bad of ["node:", "openai", "axios", "winston", "form-data", "uuid", "dist/esm/", "dist/src/"]) {
  for (const input of inputs) if (input.includes(bad) && !input.includes("dist/gateway/esm/")) problems.push(`${bad} in ${input}`);
}
process.stdout.write(JSON.stringify({ entry, inputs: inputs.length, externals: [...externals], problems }) + "\n");
process.exit(problems.length ? 1 : 0);
