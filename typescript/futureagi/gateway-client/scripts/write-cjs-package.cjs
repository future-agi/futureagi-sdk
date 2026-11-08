#!/usr/bin/env node
// Mark dist/gateway/cjs as CommonJS and dist/gateway/esm as ES modules, so
// require() and import() each load their own build inside @future-agi/sdk
// ("type": "module"). This is agent-command-center-sdk the recorded revision's fix (its
// build:cjs ran it as `node -e`), as a file (D-13).
//   node scripts/write-cjs-package.cjs <dist/gateway dir>
"use strict";
const { mkdirSync, writeFileSync } = require("node:fs");
const { join, resolve } = require("node:path");

const dist = resolve(process.argv[2] || join(__dirname, "..", "..", "dist", "gateway"));
for (const [dir, type] of [["cjs", "commonjs"], ["esm", "module"]]) {
  mkdirSync(join(dist, dir), { recursive: true });
  writeFileSync(join(dist, dir, "package.json"), JSON.stringify({ type }) + "\n");
}
