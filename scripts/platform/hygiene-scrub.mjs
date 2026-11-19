#!/usr/bin/env node
/**
 * Reviewed rewrites for the hits of the tree scan, one exact line at a time.
 *
 *   node scripts/platform/hygiene-scrub.mjs --plan [<rev>] <map.json>
 *   node scripts/platform/hygiene-scrub.mjs --apply <map.json> [--check]
 *
 * `--plan` scans the tree of `rev` (default HEAD) and writes a map: one entry per line that has a hit,
 * with the file, the line number when planned, the rules it hits and the whole line as `text`, and
 * `replace: null`. A reviewer fills in `replace` (the new line, or several lines joined by "\n") or sets
 * `delete: true`; an entry left at null is skipped. Keep maps outside the repository: they quote the
 * lines they remove.
 *
 * `--apply` edits the working tree of the repository it runs in. Each entry rewrites every line of its
 * file that equals `text` exactly, so a map still applies after lines move. Identical entries in the same
 * transaction share the rewrite; conflicting replacements are refused. Nothing is written unless
 * every entry passes: the file is not generated (fix the generator's input instead), `text` is still
 * there (otherwise the entry is stale), and each new line has no hit under the tree rules. `--check`
 * runs the same checks and writes nothing. Exit 1 lists every problem.
 */

import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadRules, scanText } from "./hygiene-scan.mjs";
import { matchesAny, shaHits } from "./hygiene-shas.mjs";
import { loadTreeRules, rulesFor, scanTree } from "./hygiene-tree.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

/** The scrub map of `rev`: every line with a hit, plus the hits that are not about one line. */
export function planMap(rev = "HEAD", options = {}) {
  const cwd = options.cwd ?? ROOT;
  const result = scanTree(rev, options);
  const byLine = new Map();
  const findings = [];
  for (const hit of result.hits) {
    if (hit.line === 0) {
      findings.push(`${hit.file} ${hit.rule} ${hit.text}`);
      continue;
    }
    const key = `${hit.file}\0${hit.line}`;
    if (!byLine.has(key)) byLine.set(key, { path: hit.file, line: hit.line, rules: [], hits: [], generated: hit.generated });
    const entry = byLine.get(key);
    if (!entry.rules.includes(hit.rule)) entry.rules.push(hit.rule);
    entry.hits.push(`${hit.rule} ${hit.text}`);
  }
  const files = new Map();
  const entries = [...byLine.values()].sort((a, b) => (a.path === b.path ? a.line - b.line : a.path < b.path ? -1 : 1));
  for (const entry of entries) {
    if (!files.has(entry.path)) {
      const text = execFileSync("git", ["show", `${result.commit}:${entry.path}`], { cwd, encoding: "utf8", maxBuffer: 256 * 1024 * 1024 });
      files.set(entry.path, text.split("\n"));
    }
    entry.text = files.get(entry.path)[entry.line - 1];
    entry.replace = null;
  }
  return { rev: result.commit, tree: result.tree, entries, findings };
}

/** The new lines of one entry, or null when it is skipped. */
function newLines(entry) {
  if (entry.delete === true) return [];
  if (typeof entry.replace === "string") return entry.replace.split("\n");
  return null;
}

function lineHits(file, line, platform, tree) {
  const hits = [];
  for (const rules of rulesFor(file, platform, tree)) hits.push(...scanText(line, path.extname(file), rules));
  hits.push(...shaHits(file, line, tree.shas, new Set()));
  return hits;
}

/**
 * Check (and unless `check`, apply) a map to the working tree at `root`. Returns
 * `{ problems, applied, files }`; nothing is written when there are problems.
 */
export function applyMap(map, { root = ROOT, check = false, platform = loadRules(root), tree = loadTreeRules(root) } = {}) {
  const problems = [];
  const edits = new Map();
  const rewrites = new Map();
  let applied = 0;
  for (const entry of map.entries ?? []) {
    const lines = newLines(entry);
    if (lines === null) continue;
    const where = `${entry.path}:${entry.line ?? "?"}`;
    if (typeof entry.text !== "string" || entry.text === "") {
      problems.push(`${where}: the entry has no text to replace`);
      continue;
    }
    if (matchesAny(entry.path, tree.generated)) {
      problems.push(`${where}: a generated file; fix the generator's input and regenerate`);
      continue;
    }
    if (!edits.has(entry.path)) {
      try {
        edits.set(entry.path, readFileSync(path.join(root, entry.path), "utf8").split("\n"));
      } catch {
        problems.push(`${where}: the file is not in the working tree`);
        continue;
      }
    }
    const key = JSON.stringify([entry.path, entry.text]);
    const replacement = JSON.stringify(lines);
    if (rewrites.has(key)) {
      if (rewrites.get(key) !== replacement) problems.push(`${where}: conflicting replacements for the same original text`);
      else applied += 1;
      continue;
    }
    const current = edits.get(entry.path);
    const at = current.flatMap((line, index) => (line === entry.text ? [index] : []));
    if (at.length === 0) {
      problems.push(`${where}: stale: no line equals the entry's text`);
      continue;
    }
    for (const line of lines) {
      for (const hit of lineHits(entry.path, line, platform, tree)) problems.push(`${where}: the new line still hits ${hit.rule} ${hit.text}`);
    }
    for (const index of at.reverse()) current.splice(index, 1, ...lines);
    rewrites.set(key, replacement);
    applied += 1;
  }
  if (problems.length === 0 && !check) {
    for (const [file, lines] of edits) writeFileSync(path.join(root, file), lines.join("\n"));
  }
  return { problems, applied, files: edits.size };
}

function main(argv) {
  const [mode, ...rest] = argv;
  if (mode === "--plan" && (rest.length === 1 || rest.length === 2)) {
    const out = rest[rest.length - 1];
    const map = planMap(rest.length === 2 ? rest[0] : "HEAD");
    writeFileSync(out, `${JSON.stringify(map, null, 2)}\n`);
    process.stdout.write(`scrub: ${map.entries.length} line(s) to review, ${map.findings.length} other finding(s), written to ${out}\n`);
    return 0;
  }
  if (mode === "--apply" && (rest.length === 1 || (rest.length === 2 && rest[1] === "--check"))) {
    const check = rest[1] === "--check";
    const { problems, applied, files } = applyMap(JSON.parse(readFileSync(rest[0], "utf8")), { check });
    for (const p of problems) process.stderr.write(`scrub: ${p}\n`);
    const verb = check ? "checked" : problems.length === 0 ? "applied" : "not applied";
    process.stdout.write(`scrub: ${applied} entr${applied === 1 ? "y" : "ies"} over ${files} file(s) ${verb}, ${problems.length} problem(s)\n`);
    return problems.length === 0 ? 0 : 1;
  }
  process.stderr.write("usage: hygiene-scrub.mjs --plan [<rev>] <map.json> | --apply <map.json> [--check]\n");
  return 2;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exit(main(process.argv.slice(2)));
}
