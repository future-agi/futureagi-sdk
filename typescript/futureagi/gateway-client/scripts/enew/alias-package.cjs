#!/usr/bin/env node
// Write package.json for the E-NEW alias: @agentcc/client's four 1.0.1 subpaths,
// each pointing straight at the built gateway client files under dist/{esm,cjs}.
//   node alias-package.cjs <package dir> <version>
"use strict";
const { writeFileSync } = require("node:fs");
const { join } = require("node:path");

const [dir, version] = process.argv.slice(2);
const entry = (name) => ({
  import: { types: `./dist/esm/${name}.d.ts`, default: `./dist/esm/${name}.js` },
  require: { types: `./dist/cjs/${name}.d.ts`, default: `./dist/cjs/${name}.js` },
});
const pkg = {
  name: "@agentcc/client",
  version,
  description: "E-NEW parity install: the built @future-agi/sdk/gateway client under the 1.0.1 package layout",
  type: "module",
  main: "./dist/cjs/index.js",
  module: "./dist/esm/index.js",
  types: "./dist/esm/index.d.ts",
  exports: {
    ".": entry("index"),
    "./testing": entry("testing"),
    "./express": entry("express"),
    "./nextjs": entry("nextjs"),
  },
};
writeFileSync(join(dir, "package.json"), JSON.stringify(pkg, null, 2) + "\n");
