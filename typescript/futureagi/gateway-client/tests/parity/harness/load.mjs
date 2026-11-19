// Load a package subpath from an install directory, as ESM (import) or CJS (require).
//
// The ESM entry is read from the package's own "exports" map (the "import"
// condition), so the recorder never depends on where it lives itself. A load
// failure is returned, not thrown: @agentcc/client 1.0.0's require() fails
// (delta D-13) and that failure is part of the golden.
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { observeError } from "./observe.mjs";

function pick(entry, condition) {
  if (typeof entry === "string") return entry;
  if (!entry || typeof entry !== "object") return undefined;
  const hit = entry[condition] ?? entry.default ?? entry.node;
  return typeof hit === "string" ? hit : pick(hit, "default");
}

export function packageJson(installDir, name) {
  return JSON.parse(readFileSync(join(installDir, "node_modules", name, "package.json"), "utf8"));
}

export function esmEntry(installDir, name, subpath = ".") {
  const pkg = packageJson(installDir, name);
  const target = pkg.exports ? pick(pkg.exports[subpath], "import") : subpath === "." ? (pkg.module ?? pkg.main) : undefined;
  if (!target) throw new Error(`no ESM entry for ${name} ${subpath}`);
  return join(installDir, "node_modules", name, target);
}

export async function load(installDir, name, subpath, format) {
  const spec = subpath === "." ? name : `${name}/${subpath.replace(/^\.\//, "")}`;
  try {
    if (format === "cjs") {
      const req = createRequire(join(installDir, "package.json"));
      return { ok: true, module: req(spec), spec };
    }
    return { ok: true, module: await import(pathToFileURL(esmEntry(installDir, name, subpath)).href), spec };
  } catch (err) {
    const seen = observeError(err);
    return { ok: false, error: { name: seen.__exception__, code: err.code ?? null, message: seen.message.split("\n")[0] }, spec };
  }
}

export function exportKeys(module) {
  return Object.keys(module)
    .filter((k) => k !== "__esModule" && k !== "default")
    .sort();
}
