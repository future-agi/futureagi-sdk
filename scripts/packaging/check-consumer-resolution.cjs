#!/usr/bin/env node
// Resolve every export of an unpacked candidate from an external TS consumer.
// The export map, not a maintained list of entry points, defines the matrix.
"use strict";
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { createRequire } = require("node:module");
const ts = createRequire(path.resolve(__dirname, "../../typescript/futureagi/package.json"))("typescript");

const [directory, ...args] = process.argv.slice(2);
if (!directory || args.length % 2 || args.some((arg, i) => i % 2 === 0 && arg !== "--absent")) {
  throw new Error("Usage: check-consumer-resolution.cjs <unpacked package> [--absent <subpath>]...");
}
const packageDir = fs.realpathSync(directory);
const pkg = JSON.parse(fs.readFileSync(path.join(packageDir, "package.json"), "utf8"));
const absent = args.filter((_, i) => i % 2 === 1).map((key) => key.startsWith("./") ? key : `./${key}`);
const publicSubpaths = Object.keys(pkg.exports);
const errors = [];
const results = [];
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), "sdk-consumer-resolution-"));
const modes = [
  { name: "Node10", resolution: ts.ModuleResolutionKind.Node10, module: ts.ModuleKind.CommonJS },
  { name: "Node16/import", resolution: ts.ModuleResolutionKind.Node16, module: ts.ModuleKind.Node16, mode: ts.ModuleKind.ESNext },
  { name: "Node16/require", resolution: ts.ModuleResolutionKind.Node16, module: ts.ModuleKind.Node16, mode: ts.ModuleKind.CommonJS },
  { name: "Bundler/import", resolution: ts.ModuleResolutionKind.Bundler, module: ts.ModuleKind.Preserve, mode: ts.ModuleKind.ESNext },
  { name: "Bundler/require", resolution: ts.ModuleResolutionKind.Bundler, module: ts.ModuleKind.Preserve, mode: ts.ModuleKind.CommonJS },
];

function declaration(target, conditions) {
  if (typeof target === "string" || target === null) return target;
  for (const [condition, value] of Object.entries(target ?? {})) {
    if (conditions.has(condition)) {
      const match = declaration(value, conditions);
      if (match !== undefined) return match;
    }
  }
}

try {
  const installed = path.join(scratch, "node_modules", pkg.name);
  fs.mkdirSync(path.dirname(installed), { recursive: true });
  fs.symlinkSync(packageDir, installed, "dir");
  const consumer = path.join(scratch, "consumer.ts");
  fs.writeFileSync(consumer, "export {};\n");
  if (!publicSubpaths.length || !publicSubpaths.includes(".")) errors.push("Candidate must export its root");
  for (const subpath of absent) {
    if (subpath in pkg.exports) errors.push(`Hidden export remains: ${subpath}`);
    for (const [range, mappings] of Object.entries(pkg.typesVersions ?? {})) {
      if (subpath.slice(2) in mappings) errors.push(`Hidden typesVersions mapping remains: ${range}/${subpath}`);
    }
  }
  for (const subpath of [...new Set([...publicSubpaths, ...absent])]) {
    if (subpath !== "." && (!subpath.startsWith("./") || subpath.includes("*"))) {
      errors.push(`Export needs concrete consumer cases: ${subpath}`);
      continue;
    }
    const specifier = pkg.name + (subpath === "." ? "" : subpath.slice(1));
    for (const config of modes) {
      const { resolvedModule } = ts.resolveModuleName(specifier, consumer, {
        moduleResolution: config.resolution, module: config.module,
      }, ts.sys, undefined, undefined, config.mode);
      const resolved = resolvedModule?.resolvedFileName;
      let expected = null;
      if (!absent.includes(subpath)) {
        const conditions = new Set(["types", "default", config.mode === ts.ModuleKind.ESNext ? "import" : "require"]);
        if (config.resolution !== ts.ModuleResolutionKind.Bundler) conditions.add("node");
        const target = subpath === "." && config.name === "Node10" ? pkg.types : declaration(pkg.exports[subpath], conditions);
        if (!target || !/\.d\.(?:ts|mts|cts)$/.test(target)) {
          errors.push(`${config.name} ${specifier}: no public declaration target`);
        } else {
          expected = path.resolve(packageDir, target);
          if (!fs.existsSync(expected)) errors.push(`${config.name} ${specifier}: declaration missing from artifact`);
        }
        if (!resolved) errors.push(`${config.name} ${specifier}: unresolved`);
        else if (expected && path.resolve(resolved) !== expected) errors.push(`${config.name} ${specifier}: resolved the wrong declaration`);
      } else if (resolved) {
        errors.push(`${config.name} ${specifier}: hidden subpath still resolves`);
      }
      results.push({ subpath, resolver: config.name, expected, resolved: resolved ?? null });
    }
  }
} finally {
  fs.rmSync(scratch, { recursive: true, force: true });
}
console.log(JSON.stringify({ package: pkg.name, typescript: ts.version, exports: publicSubpaths, absent, results, errors }, null, 2));
process.exitCode = errors.length ? 1 : 0;
