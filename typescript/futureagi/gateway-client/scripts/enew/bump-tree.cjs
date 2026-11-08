#!/usr/bin/env node
// Copy the gateway client into a scratch tree with the version bumped, the way a release
// bumps it: typescript/futureagi/package.json's "version" and the VERSION line of
// gateway-client/src/constants.ts, both of which scripts/build.cjs checks. The copy holds
// what the build reads (src/, scripts/, package.json, tsconfig*.json) and links the
// client's node_modules, so `node <to>/gateway-client/scripts/build.cjs` builds it into
// <to>/dist/gateway. record-enew.sh's bump-* steps record and gate that build.
//   node bump-tree.cjs <typescript/futureagi> <scratch typescript/futureagi> <new version>
"use strict";
const { cpSync, mkdirSync, readFileSync, readdirSync, symlinkSync, writeFileSync } = require("node:fs");
const { join } = require("node:path");

const [from, to, next] = process.argv.slice(2);
if (!from || !to || !/^\d+\.\d+\.\d+$/.test(next ?? "")) {
  process.stderr.write("usage: bump-tree.cjs <typescript/futureagi> <scratch dir> <new x.y.z version>\n");
  process.exit(2);
}
const pkg = JSON.parse(readFileSync(join(from, "package.json"), "utf8"));
if (pkg.version === next) throw new Error(`the version is already ${next}`);
const gc = join(from, "gateway-client");
const out = join(to, "gateway-client");
mkdirSync(out, { recursive: true });
writeFileSync(join(to, "package.json"), JSON.stringify({ ...pkg, version: next }, null, 2) + "\n");
for (const name of ["src", "scripts", "package.json", ...readdirSync(gc).filter((n) => /^tsconfig.*\.json$/.test(n))]) {
  cpSync(join(gc, name), join(out, name), { recursive: true });
}
symlinkSync(join(gc, "node_modules"), join(out, "node_modules"), "dir");
const constants = join(out, "src", "constants.ts");
const line = (v) => `export const VERSION: string = "${v}";`;
const text = readFileSync(constants, "utf8");
if (text.split(line(pkg.version)).length !== 2) throw new Error(`src/constants.ts has no single line: ${line(pkg.version)}`);
writeFileSync(constants, text.replace(line(pkg.version), line(next)));
process.stdout.write(`${pkg.version} -> ${next} in ${to}\n`);
