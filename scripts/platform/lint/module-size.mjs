#!/usr/bin/env node
/**
 * Every platform module stays at 400 lines or fewer. Checks both languages.
 *
 *   node scripts/platform/lint/module-size.mjs [dir ...]     (default: roots.mjs SIZE_ROOTS)
 *
 * Generated code (`generated/`, `_gen/`) is exempt: it is checked by regeneration instead. Sync twins
 * written by scripts/platform/unasync.py count, like their async source. Exit 1 lists every module over.
 */

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { REPO, SIZE_ROOTS } from "./roots.mjs";

export const MAX_LINES = 400;
const EXTENSIONS = new Set([".ts", ".mts", ".mjs", ".js", ".cjs", ".py", ".sh"]);
const SKIP_DIRS = new Set(["node_modules", "dist", "_gen", "generated", "__pycache__", ".venv"]);

function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (!SKIP_DIRS.has(entry.name)) yield* walk(path.join(dir, entry.name));
    } else if (EXTENSIONS.has(path.extname(entry.name)) && !entry.name.endsWith(".d.ts")) {
      yield path.join(dir, entry.name);
    }
  }
}

/** Count lines the way editors do (a final newline does not add a line). */
export function countLines(text) {
  if (text === "") return 0;
  const lines = text.split("\n").length;
  return text.endsWith("\n") ? lines - 1 : lines;
}

export function checkModuleSizes(roots, repoRoot = REPO) {
  const over = [];
  const absent = [];
  let files = 0;
  for (const root of roots) {
    const abs = path.resolve(repoRoot, root);
    if (!existsSync(abs) || !statSync(abs).isDirectory()) {
      absent.push(root);
      continue;
    }
    for (const file of walk(abs)) {
      files += 1;
      const lines = countLines(readFileSync(file, "utf8"));
      if (lines > MAX_LINES) over.push({ file: path.relative(repoRoot, file), lines });
    }
  }
  return { files, over, absent };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const roots = process.argv.slice(2);
  const { files, over, absent } = checkModuleSizes(roots.length > 0 ? roots : SIZE_ROOTS);
  for (const { file, lines } of over) process.stderr.write(`module-size: ${file} has ${lines} lines (max ${MAX_LINES})\n`);
  process.stdout.write(`module-size: ${files} modules checked, ${over.length} over ${MAX_LINES} lines; not present yet: ${absent.join(", ") || "none"}\n`);
  process.exit(over.length === 0 ? 0 : 1);
}
