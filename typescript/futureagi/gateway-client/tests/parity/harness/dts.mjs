// The public .d.ts surface of an installed package, normalised: for each
// declaration file, the exported names and their kinds, plus a sha256 of the
// text with source-map comments removed.
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const DECL = /^export\s+(?:declare\s+)?(?:abstract\s+)?(class|function|const|let|interface|type|enum|namespace)\s+([A-Za-z_$][\w$]*)/gm;
const REEXPORT = /^export\s+(type\s+)?\{([^}]*)\}(?:\s+from\s+["']([^"']+)["'])?/gm;
const STAR = /^export\s+\*\s+(?:as\s+(\w+)\s+)?from\s+["']([^"']+)["']/gm;

function walk(dir, out = []) {
  for (const name of readdirSync(dir).sort()) {
    if (name === "node_modules") continue;
    const path = join(dir, name);
    if (statSync(path).isDirectory()) walk(path, out);
    else if (name.endsWith(".d.ts") || name.endsWith(".d.mts") || name.endsWith(".d.cts")) out.push(path);
  }
  return out;
}

export function declarations(text) {
  const names = [];
  for (const m of text.matchAll(DECL)) names.push(`${m[1]} ${m[2]}`);
  for (const m of text.matchAll(REEXPORT)) {
    for (const part of m[2].split(",").map((s) => s.trim()).filter(Boolean)) names.push(`${m[1] ? "type " : ""}re ${part}${m[3] ? ` <- ${m[3]}` : ""}`);
  }
  for (const m of text.matchAll(STAR)) names.push(`star ${m[1] ?? "*"} <- ${m[2]}`);
  return names.sort();
}

export function dtsSurface(packageDir) {
  const out = {};
  for (const file of walk(packageDir)) {
    const text = readFileSync(file, "utf8").replace(/^\/\/# sourceMappingURL=.*$/gm, "").trimEnd() + "\n";
    out[relative(packageDir, file)] = { sha256: createHash("sha256").update(text).digest("hex"), exports: declarations(text) };
  }
  return out;
}
