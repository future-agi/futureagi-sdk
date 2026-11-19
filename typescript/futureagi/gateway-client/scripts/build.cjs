#!/usr/bin/env node
// Build the gateway subpaths into typescript/futureagi/dist/gateway/{esm,cjs}
// (the root package's build:gateway runs this).
//   node gateway-client/scripts/build.cjs
// Run it after the root build: the root's prebuild (rimraf dist) removes
// dist/ whole.
"use strict";
const { execFileSync } = require("node:child_process");
const { rmSync } = require("node:fs");
const { join } = require("node:path");

const root = join(__dirname, "..");
const pkgVersion = require(join(root, "..", "package.json")).version;
const constants = require("node:fs").readFileSync(join(root, "src", "constants.ts"), "utf8");
// VERSION is declared `string`: with a literal type, tsc writes the version into
// constants.d.ts, so every release would change that declaration file's text, which the
// E-NEW release gate pins (scripts/enew/record-enew.sh, its bump-* steps check this).
if (!constants.includes(`export const VERSION: string = "${pkgVersion}";`)) {
  throw new Error(
    `gateway-client/src/constants.ts must say: export const VERSION: string = "${pkgVersion}"; ` +
      `(typescript/futureagi/package.json's version, declared string so constants.d.ts carries no version) (D-03)`,
  );
}
const out = join(root, "..", "dist", "gateway");
const tsc = require.resolve("typescript/bin/tsc", { paths: [root] });
rmSync(out, { recursive: true, force: true });
for (const config of ["tsconfig.esm.json", "tsconfig.cjs.json"]) {
  execFileSync(process.execPath, [tsc, "-p", join(root, config)], { stdio: "inherit" });
}
execFileSync(process.execPath, [join(__dirname, "write-cjs-package.cjs"), out], { stdio: "inherit" });
