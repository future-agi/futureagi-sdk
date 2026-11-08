#!/usr/bin/env node
/**
 * No URL path string in a hand-written platform module: every call goes through a generated policy
 * entry, by SDK name. Scans source modules (tests and test fixtures excluded) in both languages for
 * string literals that look like an API path. Comment lines may describe a path and are skipped. The
 * rule (pattern, skipped directories and files) is `url-path-rule.json`, which the Python gate reads too.
 *
 *   node scripts/platform/lint/no-url-paths.mjs [dir ...]     (default: roots.mjs SOURCE_ROOTS)
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { REPO, SOURCE_ROOTS } from "./roots.mjs";

export const RULE = JSON.parse(readFileSync(new URL("./url-path-rule.json", import.meta.url), "utf8"));
/** A quoted literal that starts with an API path (the bare `/omega/api` mount is not one). */
export const PATH_LITERAL = new RegExp(RULE.pattern, "u");
const SKIP_DIRS = new Set(RULE.skipDirs);
const SKIP_FILE = new RegExp(RULE.skipFiles, "u");

function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!SKIP_DIRS.has(entry.name)) yield* walk(full);
    } else if (RULE.extensions.includes(path.extname(entry.name)) && !SKIP_FILE.test(entry.name)) {
      yield full;
    }
  }
}

export function findUrlPaths(roots, repoRoot = REPO) {
  const hits = [];
  const absent = [];
  let files = 0;
  for (const root of roots) {
    const abs = path.resolve(repoRoot, root);
    if (!existsSync(abs)) {
      absent.push(root);
      continue;
    }
    for (const file of walk(abs)) {
      files += 1;
      readFileSync(file, "utf8")
        .split("\n")
        .forEach((line, index) => {
          const comment = RULE.commentPrefixes.some((p) => line.trim().startsWith(p));
          if (!comment && PATH_LITERAL.test(line)) hits.push({ file: path.relative(repoRoot, file), line: index + 1, text: line.trim() });
        });
    }
  }
  return { files, hits, absent };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const roots = process.argv.slice(2);
  const { files, hits, absent } = findUrlPaths(roots.length > 0 ? roots : SOURCE_ROOTS);
  for (const hit of hits) process.stderr.write(`no-url-paths: ${hit.file}:${hit.line}: ${hit.text}\n`);
  process.stdout.write(`no-url-paths: ${files} modules checked, ${hits.length} path literal(s); not present yet: ${absent.join(", ") || "none"}\n`);
  process.exit(hits.length === 0 ? 0 : 1);
}
