#!/usr/bin/env node
// Pack the registered SDK as a candidate tarball. The gateway client ships:
// dist/gateway, its five export entries, typesVersions mappings and the
// optional React peer are kept exactly as package.json registers them.
"use strict";
const { execFileSync } = require("node:child_process");
const { cpSync, existsSync, mkdirSync, readFileSync, writeFileSync } = require("node:fs");
const { join, resolve } = require("node:path");

const pkgDir = resolve(__dirname, "..", "..");
const repo = resolve(pkgDir, "..", "..");
const args = process.argv.slice(2);
const positional = args.filter((arg) => !arg.startsWith("--"));
if (positional.length !== 1 || args.some((arg) => arg.startsWith("--"))) {
  throw new Error("Usage: stage-package.cjs <new output directory>");
}
const out = resolve(positional[0]);
const stage = join(out, "package");
if (existsSync(stage)) throw new Error("Choose a new output directory; existing artifacts are not overwritten");
const pkg = JSON.parse(readFileSync(join(pkgDir, "package.json"), "utf8"));
if (!existsSync(join(pkgDir, "dist", "esm", "index.js"))) throw new Error("Build the root package first");
for (const entry of ["esm/index.js", "cjs/index.js"]) {
  if (!existsSync(join(pkgDir, "dist", "gateway", entry))) throw new Error("Build the gateway first (pnpm run build includes build:gateway)");
}
if (!pkg.files.includes("dist/gateway") || !Object.keys(pkg.exports).some((key) => key.startsWith("./gateway"))) {
  throw new Error("package.json must register the gateway (files and exports)");
}
// Consumers install built code. No lifecycle may rebuild or enable a surface.
delete pkg.scripts;
delete pkg.devDependencies;
delete pkg.jest;
mkdirSync(stage, { recursive: true });
writeFileSync(join(stage, "package.json"), JSON.stringify(pkg, null, 2) + "\n");
writeFileSync(join(out, "package.json"), JSON.stringify(pkg, null, 2) + "\n");
for (const name of ["README.md", "CHANGELOG.md"]) {
  if (existsSync(join(pkgDir, name))) cpSync(join(pkgDir, name), join(stage, name));
}
for (const name of ["LICENSE", "NOTICE"]) cpSync(join(repo, name), join(stage, name));
for (const dir of ["esm", "src", "esnext", "gateway"]) {
  const from = join(pkgDir, "dist", dir);
  if (existsSync(from)) cpSync(from, join(stage, "dist", dir), { recursive: true });
}
const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const report = execFileSync(npm, ["pack", "--ignore-scripts", "--json", "--pack-destination", out], { cwd: stage, encoding: "utf8" });
writeFileSync(join(out, "pack.json"), report);
writeFileSync(join(out, "mode.json"), JSON.stringify({ gateway: "on" }) + "\n");
const [{ filename }] = JSON.parse(report);
process.stdout.write(join(out, filename) + "\n");
