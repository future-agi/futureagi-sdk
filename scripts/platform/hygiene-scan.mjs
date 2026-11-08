#!/usr/bin/env node
/**
 * The hygiene scan for public platform files. Fails on local paths, internal names, plan references,
 * EE source paths, secrets and placeholder hosts in any file; and, in an OpenAPI document, on any key
 * named `evidence` and any extension the allowlist does not name.
 *
 *   node scripts/platform/hygiene-scan.mjs [path ...]     (default: every platform path below)
 *   node scripts/platform/hygiene-scan.mjs --commits <base>..<head>
 *   node scripts/platform/hygiene-scan.mjs --names <file>
 *   node scripts/platform/hygiene-scan.mjs --hash <rule id> <name>
 *   node scripts/platform/hygiene-scan.mjs --tree [<rev>]   (every file a commit publishes: hygiene-tree.mjs)
 *
 * Which files: in a git checkout, every file git would commit under the paths (tracked, plus untracked
 * files that are not ignored); elsewhere (an exported tree), every file under them except interpreter
 * caches. No file is skipped for its name or extension, the rule file included: it is written so that
 * it passes its own scan. A file that is not UTF-8 text is a hit.
 *
 * `--commits` scans commit messages with both platform and whole-tree rules, including names and commit
 * ids, using the same checks as public-history.mjs. Run it before a public push: a published message
 * cannot be fixed. `--names` checks a
 * plain list of the internal names against the hashed ones (`hygiene-names.mjs`); `--hash` prints the
 * entry for a new name.
 *
 * The rules are `scripts/platform/hygiene-rules.json`; `hygiene_scan.py` runs the same rules in CI.
 * An exemption names one file, the sha256 of one line (stripped) and the rules that line may hit.
 * Every other line of that file is scanned as usual, and an exemption that matches nothing in a scanned
 * file is itself a hit, so a changed line cannot keep its pass.
 * Exit 1 lists every hit as `file:line rule text`.
 */

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync, realpathSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { checkNameList, nameHits, namesFindings, sha256 } from "./hygiene-names.mjs";
import { matchesAny, shaHits } from "./hygiene-shas.mjs";
import { lockfileProjection } from "./hygiene-lockfiles.mjs";
import { structuralFindings } from "./openapi-walk.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
export const RULES_FILE = "scripts/platform/hygiene-rules.json";
export const DEFAULT_PATHS = [
  "python/fi/evals",
  "python/tests/evals",
  "openapi/platform",
  "scripts/platform",
  "scripts/generate-platform-sdk.sh",
  "python/fi/_core",
  "python/fi/generated/platform",
  "python/tests/platform",
  "typescript/futureagi/src/_core",
  "typescript/futureagi/src/generated/platform",
  "tests/platform-conformance"
];
/** Outside a git checkout only: interpreter and package caches, which nothing commits. */
const CACHE_DIRS = new Set(["node_modules", "__pycache__", ".pytest_cache"]);
const HEX64 = /^[0-9a-f]{64}$/u;
const utf8 = new TextDecoder("utf-8", { fatal: true });

export function loadRules(root = ROOT) {
  return JSON.parse(readFileSync(path.join(root, RULES_FILE), "utf8"));
}

export const TREE_RULES_FILE = "scripts/platform/hygiene-tree-rules.json";

export function loadTreeRules(root = ROOT) {
  return JSON.parse(readFileSync(path.join(root, TREE_RULES_FILE), "utf8"));
}

export const underPlatform = (file) => DEFAULT_PATHS.some((p) => file === p || file.startsWith(`${p}/`));

/** The text rules for a file; path names do not inherit content-only path exclusions. */
export function rulesFor(file, platform, tree, { pathName = false } = {}) {
  const skip = underPlatform(file) ? [] : tree.inherit?.platformPathsOnly ?? [];
  const inherited = { patterns: platform.patterns.filter((p) => !skip.includes(p.id)), names: platform.names };
  const own = { patterns: (tree.patterns ?? []).filter((p) => pathName || !matchesAny(file, p.skipPaths)), names: tree.names };
  return [inherited, own];
}

function compiled(rules) {
  return rules.patterns.map((p) => ({ ...p, re: new RegExp(p.regex, "u") }));
}

/** Pattern and name hits in one text, by line. */
export function scanText(text, extension, rules, file = "") {
  const hits = [];
  const patterns = compiled(rules).filter((p) => !(p.skipExtensions ?? []).includes(extension)
    && (!p.paths || p.paths.includes(file)));
  text.split("\n").forEach((line, index) => {
    for (const p of patterns) {
      const m = p.re.exec(line);
      if (m) hits.push({ rule: p.id, line: index + 1, text: m[0] });
    }
    for (const h of nameHits(line, rules.names)) hits.push({ rule: h.rule, line: index + 1, text: h.text });
  });
  return hits;
}

/** Repository-relative files git would commit under `targets`, or null when `root` is not a checkout's top. */
function gitFiles(targets, root) {
  try {
    const top = execFileSync("git", ["rev-parse", "--show-toplevel"], { cwd: root, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    if (realpathSync(top) !== realpathSync(root)) return null;
    const out = execFileSync("git", ["ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", ...targets], {
      cwd: root,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      maxBuffer: 64 * 1024 * 1024
    });
    return [...new Set(out.split("\0").filter(Boolean))].sort().filter((rel) => existsSync(path.join(root, rel)));
  } catch {
    return null;
  }
}

function* walk(target) {
  if (statSync(target).isFile()) {
    yield target;
    return;
  }
  for (const entry of readdirSync(target, { withFileTypes: true }).sort((a, b) => (a.name < b.name ? -1 : 1))) {
    const full = path.join(target, entry.name);
    if (entry.isDirectory()) {
      if (!CACHE_DIRS.has(entry.name)) yield* walk(full);
    } else if (entry.isFile()) {
      yield full;
    }
  }
}

/** The repository-relative files the scan reads under `targets`. */
export function listFiles(targets, root = ROOT) {
  const fromGit = gitFiles(targets, root);
  if (fromGit !== null) return fromGit;
  const out = [];
  for (const target of targets) {
    const abs = path.resolve(root, target);
    if (existsSync(abs)) for (const file of walk(abs)) out.push(path.relative(root, file).split(path.sep).join("/"));
  }
  return out;
}

/** The exemption that covers a text hit, if any (same file, same line hash, a listed rule). */
function exemptionFor(rules, file, rule, lineText) {
  const digest = sha256(lineText);
  return (rules.exemptions ?? []).find((e) => e.path === file && e.lineSha256 === digest && e.rules.includes(rule));
}

/** Rule-file problems: malformed exemptions or names, and exemptions that name a scanned file but matched none of its lines. */
function ruleFindings(rules, scanned, used) {
  const out = namesFindings(rules.names).map((text) => ({ file: RULES_FILE, line: 0, rule: "invalid-names", text }));
  for (const e of rules.exemptions ?? []) {
    const valid = typeof e.path === "string" && typeof e.lineSha256 === "string" && HEX64.test(e.lineSha256);
    if (!valid || !Array.isArray(e.rules) || e.rules.length === 0 || !e.why) {
      out.push({ file: String(e.path), line: 0, rule: "invalid-exemption", text: "needs path, lineSha256, rules and why" });
    } else if (scanned.has(e.path) && !used.has(e)) {
      out.push({ file: e.path, line: 0, rule: "stale-exemption", text: e.lineSha256.slice(0, 12) });
    }
  }
  return out;
}

/** Every hit under `targets` (repository-relative). */
export function scanPaths(targets, rules, root = ROOT) {
  const hits = [];
  const scanned = new Set();
  const used = new Set();
  const files = listFiles(targets, root);
  for (const rel of files) {
    scanned.add(rel);
    let text;
    try {
      text = utf8.decode(readFileSync(path.join(root, rel)));
    } catch {
      text = "\0";
    }
    if (text.includes("\0")) {
      hits.push({ file: rel, rule: "not-text", line: 0, text: "not UTF-8 text, so it cannot be scanned" });
      continue;
    }
    const lines = text.split("\n");
    const projection = lockfileProjection(rel, text);
    hits.push(...projection.hits.map((hit) => ({ file: rel, ...hit })));
    for (const hit of scanText(projection.text, path.extname(rel), rules, rel)) {
      const exemption = exemptionFor(rules, rel, hit.rule, lines[hit.line - 1].trim());
      if (exemption) used.add(exemption);
      else hits.push({ file: rel, ...hit });
    }
    if (path.extname(rel) === ".json") {
      let doc;
      try {
        doc = JSON.parse(text);
      } catch {
        hits.push({ file: rel, rule: "invalid-json", line: 0, text: "" });
        continue;
      }
      if (doc && typeof doc === "object" && typeof doc.openapi === "string") {
        for (const f of structuralFindings(doc, rules)) hits.push({ file: rel, line: 0, rule: f.rule, text: `${f.text} at ${f.at}` });
      }
    }
  }
  hits.push(...ruleFindings(rules, scanned, used));
  return { files: files.length, hits };
}

/** Shared checks for export messages and pre-push history audits; no file-content exemptions apply. */
export function scanMessage(message, platform, tree) {
  const file = "COMMIT_MESSAGE.md";
  const hits = rulesFor(file, platform, tree).flatMap((rules) => scanText(message, ".md", rules));
  message.split("\n").forEach((line, index) => {
    for (const hit of shaHits(file, line, tree.shas, new Set())) hits.push({ line: index + 1, ...hit });
  });
  return hits;
}

/** Complete hygiene hits in every commit message in `range` (`git log` syntax). */
export function scanCommits(range, rules, cwd = ROOT, tree = loadTreeRules()) {
  const log = execFileSync("git", ["log", "--format=%H%x00%B%x1e", range], { cwd, encoding: "utf8" });
  const hits = [];
  let count = 0;
  for (const record of log.split("\x1e")) {
    const [sha, message] = record.replace(/^\n/u, "").split("\0");
    if (!sha || message === undefined) continue;
    count += 1;
    // a message is prose, scanned like a .md file: it may name an SDK source file, never an EE one
    for (const hit of scanMessage(message, rules, tree)) hits.push({ file: `commit ${sha.slice(0, 12)}`, ...hit });
  }
  return { commits: count, hits };
}

function main(argv) {
  const rules = loadRules();
  const [mode, ...rest] = argv;
  if (mode === "--hash") {
    if (rest.length !== 2) return usage();
    process.stdout.write(`${JSON.stringify(sha256(rest[1].toLowerCase()))}: ${JSON.stringify(rest[0])}\n`);
    return 0;
  }
  if (mode === "--names") {
    if (rest.length !== 1) return usage();
    const problems = checkNameList(readFileSync(rest[0], "utf8"), rules.names);
    for (const p of problems) process.stderr.write(`hygiene: names ${p}\n`);
    process.stdout.write(`hygiene: ${Object.keys(rules.names?.sha256 ?? {}).length} hashed names checked against the list, ${problems.length} problem(s)\n`);
    return problems.length === 0 ? 0 : 1;
  }
  if (mode === "--commits") {
    if (rest.length !== 1) return usage();
    const { commits, hits } = scanCommits(rest[0], rules);
    for (const h of hits) process.stderr.write(`hygiene: ${h.file} message line ${h.line} ${h.rule} ${h.text}\n`);
    process.stdout.write(`hygiene: ${commits} commit messages scanned, ${hits.length} hit(s)\n`);
    return hits.length === 0 ? 0 : 1;
  }
  const { files: count, hits } = scanPaths(argv.length > 0 ? argv : DEFAULT_PATHS, rules);
  for (const h of hits) process.stderr.write(`hygiene: ${h.file}:${h.line} ${h.rule} ${h.text}\n`);
  process.stdout.write(`hygiene: ${count} files scanned, ${hits.length} hit(s)\n`);
  return hits.length === 0 ? 0 : 1;
}

function usage() {
  process.stderr.write("usage: hygiene-scan.mjs [path ...] | --commits <base>..<head> | --names <file> | --hash <rule id> <name> | --tree [<rev>]\n");
  return 2;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const argv = process.argv.slice(2);
  // the tree scan is its own module, loaded only when asked for (it imports this one)
  if (argv[0] === "--tree") import("./hygiene-tree.mjs").then((tree) => process.exit(tree.main(argv)));
  else process.exit(main(argv));
}
