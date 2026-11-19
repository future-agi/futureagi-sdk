#!/usr/bin/env node
/**
 * The hygiene scan of a whole committed tree: every file a commit would publish, read from the object
 * store, so a commit is scanned exactly as it would be pushed (no checkout, no untracked files).
 * Published path names are checked too, including binaries and submodules; path hits use line 0 and
 * target "path", and cannot be suppressed by line-content exemptions.
 *
 *   node scripts/platform/hygiene-tree.mjs [<rev>] [--json <file>]    (default rev: HEAD)
 *   node scripts/platform/hygiene-tree.mjs HEAD --findings <file>   (strict findings list, hygiene-findings.mjs)
 *   node scripts/platform/hygiene-tree.mjs HEAD --baseline <file>   (debt ratchet: fast checks only)
 *   node scripts/platform/hygiene-tree.mjs HEAD --write-baseline <new-file> (propose a debt inventory)
 * A baseline is a counted debt inventory (hygiene-baseline.mjs), never a clearance: it counts exact
 * source-line fingerprints, including their paths and rules, and additions and removals fail until
 * reviewed. Exports and push-time verification never use one. A passing ratchet is not a clean tree.
 *   node scripts/platform/hygiene-tree.mjs --names <file>
 *   node scripts/platform/hygiene-scan.mjs --tree [<rev>]             (the same scan)
 *
 * Two rule sets apply. The public-platform rules (`hygiene-rules.json`) apply to every file: under the
 * platform paths exactly as `hygiene-scan.mjs` applies them, structural OpenAPI checks included;
 * elsewhere without the patterns `inherit.platformPathsOnly` names. The tree rules
 * (`hygiene-tree-rules.json`) add patterns (each may skip path globs), hashed names checked like
 * `hygiene-names.mjs` (their plain list is kept outside this repository; `--names` checks the two agree),
 * commit ids (`hygiene-shas.mjs`) and reviewed binaries: a file that is not UTF-8 text is a hit unless
 * its path and the sha256 of its bytes are listed. A submodule is always a hit.
 *
 * A hit in a generated file (`generated` globs) is marked so: fix the generator's input and regenerate,
 * never edit the file. Exemptions from both rule files apply (one line of one file, by the sha256 of
 * the stripped line, for the listed rules); an exemption, reviewed commit or reviewed binary that
 * matches nothing scanned is itself a hit. The rules are read from the scanned revision when it has
 * them, else from this checkout. Exit 1 lists every hit as `file:line rule text`.
 */

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { assertRealHistory } from "./git-history-guard.mjs";
import { baselineFor, compareBaseline } from "./hygiene-baseline.mjs";
import { findingsList } from "./hygiene-findings.mjs";
import { checkNameList, namesFindings, sha256 } from "./hygiene-names.mjs";
import { RULES_FILE, TREE_RULES_FILE, loadRules, loadTreeRules, rulesFor, scanText, underPlatform } from "./hygiene-scan.mjs";
export { TREE_RULES_FILE, loadTreeRules, rulesFor } from "./hygiene-scan.mjs";
import { annotate, globRegExp, localOnlyCommits, matchesAny, shaFindings, shaHits } from "./hygiene-shas.mjs";
import { structuralFindings } from "./openapi-walk.mjs";
import { lockfileProjection } from "./hygiene-lockfiles.mjs";
import { createProvenanceVerifier, provenanceOccurrences } from "./hygiene-provenance.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const HEX64 = /^[0-9a-f]{64}$/u;
const utf8 = new TextDecoder("utf-8", { fatal: true });

/** A rule file as the scanned revision carries it, else as the working tree at `root` has it. */
export function rulesAt(root, rev, file, load) {
  assertRealHistory(root);
  try {
    return JSON.parse(execFileSync("git", ["show", `${rev}:${file}`], { cwd: root, env: { ...process.env, GIT_NO_REPLACE_OBJECTS: "1" }, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], maxBuffer: 64 * 1024 * 1024 }));
  } catch {
    return load(root);
  }
}

function git(cwd, args, input) {
  return execFileSync("git", args, { cwd, input, env: { ...process.env, GIT_NO_REPLACE_OBJECTS: "1" }, maxBuffer: 1024 * 1024 * 1024, stdio: [input === undefined ? "ignore" : "pipe", "pipe", "pipe"] });
}

/** Every entry of a commit's tree: `{ mode, type, oid, path }`, sorted by path. */
export function treeEntries(rev, cwd = ROOT) {
  const out = git(cwd, ["ls-tree", "-r", "-z", "--full-tree", rev]).toString("utf8");
  return out
    .split("\0")
    .filter(Boolean)
    .map((record) => {
      const tab = record.indexOf("\t");
      const [mode, type, oid] = record.slice(0, tab).split(" ");
      return { mode, type, oid, path: record.slice(tab + 1) };
    });
}

/** The bytes of each blob, by object id, read in one `git cat-file --batch`. */
export function readBlobs(oids, cwd = ROOT) {
  const unique = [...new Set(oids)];
  const blobs = new Map();
  if (unique.length === 0) return blobs;
  const out = git(cwd, ["cat-file", "--batch"], `${unique.join("\n")}\n`);
  let at = 0;
  while (at < out.length) {
    const eol = out.indexOf(10, at);
    const [oid, type, size] = out.subarray(at, eol).toString("utf8").split(" ");
    if (type === "missing" || size === undefined) throw new Error(`hygiene: object ${oid} is missing`);
    const start = eol + 1;
    blobs.set(oid, out.subarray(start, start + Number(size)));
    at = start + Number(size) + 1;
  }
  return blobs;
}

function decode(bytes) {
  try {
    const text = utf8.decode(bytes);
    return text.includes("\0") ? null : text;
  } catch {
    return null;
  }
}

/** Rule-file problems of the tree rules: malformed entries and reviewed binaries that matched nothing. */
function treeRuleFindings(tree, scannedBinaries) {
  const out = namesFindings(tree.names).map((text) => ({ file: TREE_RULES_FILE, line: 0, rule: "invalid-names", text }));
  for (const b of tree.binaries ?? []) {
    if (typeof b.path !== "string" || !HEX64.test(b.sha256 ?? "") || !b.why) {
      out.push({ file: TREE_RULES_FILE, line: 0, rule: "invalid-binary-review", text: "needs path, sha256 and why" });
    } else if (!scannedBinaries.has(`${b.path}\0${b.sha256}`)) {
      out.push({ file: b.path, line: 0, rule: "stale-binary-review", text: `${b.sha256.slice(0, 12)} matches no binary in the tree` });
    }
  }
  for (const g of [...(tree.generated ?? []), ...(tree.patterns ?? []).flatMap((p) => p.skipPaths ?? [])]) {
    try {
      globRegExp(g);
    } catch {
      out.push({ file: TREE_RULES_FILE, line: 0, rule: "invalid-glob", text: g });
    }
  }
  return out;
}

function exemptionFindings(exemptions, scanned, used) {
  const out = [];
  for (const e of exemptions) {
    const valid = typeof e.path === "string" && typeof e.lineSha256 === "string" && HEX64.test(e.lineSha256);
    if (!valid || !Array.isArray(e.rules) || e.rules.length === 0 || !e.why) {
      out.push({ file: String(e.path), line: 0, rule: "invalid-exemption", text: "needs path, lineSha256, rules and why" });
    } else if (scanned.has(e.path) && !used.has(e)) {
      out.push({ file: e.path, line: 0, rule: "stale-exemption", text: e.lineSha256.slice(0, 12) });
    }
  }
  return out;
}

/** Published names are scanned even for binaries and submodules; content exemptions never cover them. */
function scanPath(file, ctx) {
  const hits = rulesFor(file, ctx.platform, ctx.tree, { pathName: true }).flatMap((rules) => scanText(file, path.extname(file), rules));
  // A path is not a key/value document, so digest and pin exemptions cannot apply to its characters.
  hits.push(...shaHits(file, file, { reviewed: ctx.tree.shas?.reviewed }, ctx.usedShas));
  return hits.map((hit) => ({ ...hit, file, line: 0, target: "path" }));
}

/** The hits of one text file. */
function scanFile(file, text, ctx) {
  const hits = [];
  const lines = text.split("\n");
  const ext = path.extname(file);
  const projection = lockfileProjection(file, text);
  hits.push(...projection.hits.map((hit) => ({ file, ...hit })));
  for (const rules of rulesFor(file, ctx.platform, ctx.tree)) {
    for (const hit of scanText(projection.text, ext, rules)) hits.push({ file, ...hit });
  }
  // The tree rule file lists reviewed commits; naming them there is not a use.
  const used = file === TREE_RULES_FILE ? new Set() : ctx.usedShas;
  const verified = provenanceOccurrences(file, projection.text, ctx.verifyProvenance);
  let offset = 0;
  projection.text.split("\n").forEach((line, index) => {
    const positions = new Set([...verified].filter((at) => at >= offset && at < offset + line.length).map((at) => at - offset));
    for (const h of shaHits(file, line, ctx.tree.shas, used, positions)) hits.push({ file, line: index + 1, rule: h.rule, text: annotate(h.text, ctx.localOnly) });
    offset += line.length + 1;
  });
  if (ext === ".json" && underPlatform(file)) {
    let doc;
    try {
      doc = JSON.parse(text);
    } catch {
      return [...hits, { file, line: 0, rule: "invalid-json", text: "" }];
    }
    if (doc && typeof doc === "object" && typeof doc.openapi === "string") {
      for (const f of structuralFindings(doc, ctx.platform)) hits.push({ file, line: 0, rule: f.rule, text: `${f.text} at ${f.at}` });
    }
  }
  return hits.filter((hit) => {
    if (hit.line === 0) return true;
    const digest = sha256(lines[hit.line - 1].trim());
    hit.contentSha256 = digest;
    const e = ctx.exemptions.find((x) => x.path === file && x.lineSha256 === digest && x.rules.includes(hit.rule));
    if (e) ctx.usedExemptions.add(e);
    return !e;
  });
}

/**
 * Every hit in the tree of `rev` (a commit, or a tree id). Returns `{ commit, tree, files, hits }`
 * (`commit` is null for a bare tree); a hit is `{ file, line, rule, text, generated }`.
 */
export function scanTree(rev = "HEAD", { cwd = ROOT, platform = loadRules(), tree = loadTreeRules(), localOnly, verifyProvenance } = {}) {
  assertRealHistory(cwd);
  // a commit, or a bare tree (for example the tree `git merge-tree --write-tree` prints for a merge not yet made)
  let commit = null;
  try {
    commit = git(cwd, ["rev-parse", "--verify", "--quiet", `${rev}^{commit}`]).toString("utf8").trim();
  } catch {
    commit = null;
  }
  const treeId = git(cwd, ["rev-parse", "--verify", `${commit ?? rev}^{tree}`]).toString("utf8").trim();
  const entries = treeEntries(treeId, cwd);
  const ctx = scanContext({ cwd, platform, tree, localOnly, verifyProvenance });
  let hits;
  try { hits = scanEntries(entries, ctx, cwd); }
  finally { if (!verifyProvenance) ctx.verifyProvenance.close(); }
  hits.push(...exemptionFindings(ctx.exemptions, ctx.scanned, ctx.usedExemptions));
  hits.push(...shaFindings(tree.shas, ctx.usedShas).map((f) => ({ file: TREE_RULES_FILE, line: 0, ...f })));
  hits.push(...treeRuleFindings(tree, ctx.scannedBinaries));
  if (ctx.scanned.has(RULES_FILE)) hits.push(...namesFindings(platform.names).map((text) => ({ file: RULES_FILE, line: 0, rule: "invalid-names", text })));
  for (const hit of hits) hit.generated = matchesAny(hit.file, tree.generated);
  return { commit, tree: treeId, files: entries.length, hits };
}
/** The state one scan shares across its entries: the rules, and which exemptions and reviews matched. */
export function scanContext({ cwd = ROOT, platform, tree, localOnly, verifyProvenance }) {
  return {
    verifyProvenance: verifyProvenance ?? createProvenanceVerifier(),
    platform,
    tree,
    exemptions: [...(platform.exemptions ?? []), ...(tree.exemptions ?? [])],
    reviewed: new Map((tree.binaries ?? []).filter((b) => typeof b.path === "string" && HEX64.test(b.sha256 ?? "") && b.why).map((b) => [b.path, b])),
    usedExemptions: new Set(),
    usedShas: new Set(),
    scanned: new Set(),
    scannedBinaries: new Set(),
    localOnly: localOnly ?? localOnlyCommits(cwd)
  };
}

/**
 * The hits of some tree entries (`{ mode, type, oid, path }`), path names included. Whole-tree findings
 * (exemptions and reviews that matched nothing) are not judged here: part of a tree cannot show them.
 */
export function scanEntries(entries, ctx, cwd = ROOT) {
  const blobs = readBlobs(entries.filter((e) => e.type === "blob").map((e) => e.oid), cwd);
  const hits = [];
  for (const entry of entries) {
    ctx.scanned.add(entry.path);
    hits.push(...scanPath(entry.path, ctx));
    if (entry.type !== "blob") {
      hits.push({ file: entry.path, line: 0, rule: "submodule", text: `a ${entry.type} entry is not published as files` });
      continue;
    }
    const bytes = blobs.get(entry.oid);
    const text = decode(bytes);
    if (text === null) {
      const digest = sha256Bytes(bytes);
      ctx.scannedBinaries.add(`${entry.path}\0${digest}`);
      if (ctx.reviewed.get(entry.path)?.sha256 !== digest) {
        hits.push({ file: entry.path, line: 0, rule: "binary-unreviewed", text: `not UTF-8 text (sha256 ${digest})` });
      }
      continue;
    }
    hits.push(...scanFile(entry.path, text, ctx));
  }
  for (const hit of hits) hit.generated = matchesAny(hit.file, ctx.tree.generated);
  return hits;
}

function sha256Bytes(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

/** The report line of one hit. */
export function hitLine(h) {
  return `hygiene: ${h.file}:${h.line} ${h.rule} ${h.text}${h.generated ? " [generated: fix the generator input]" : ""}`;
}

export function main(argv) {
  const args = [...argv];
  if (args[0] === "--tree") args.shift();
  if (args[0] === "--names") {
    if (args.length !== 2) return usage();
    const problems = checkNameList(readFileSync(args[1], "utf8"), loadTreeRules().names);
    for (const p of problems) process.stderr.write(`hygiene: tree names ${p}\n`);
    process.stdout.write(`hygiene: ${Object.keys(loadTreeRules().names?.sha256 ?? {}).length} hashed tree names checked against the list, ${problems.length} problem(s)\n`);
    return problems.length === 0 ? 0 : 1;
  }
  const options = {};
  for (const flag of ["--json", "--findings", "--baseline", "--write-baseline"]) {
    const at = args.indexOf(flag);
    if (at === -1) continue;
    if (!args[at + 1] || args[at + 1].startsWith("--")) return usage();
    options[flag] = args[at + 1];
    args.splice(at, 2);
  }
  if (args.length > 1 || (args[0] ?? "").startsWith("-") || (options["--baseline"] && options["--write-baseline"])) return usage();
  const rev = args[0] ?? "HEAD";
  const rules = { platform: rulesAt(ROOT, rev, RULES_FILE, loadRules), tree: rulesAt(ROOT, rev, TREE_RULES_FILE, loadTreeRules) };
  const strict = scanTree(rev, rules);
  let result = strict;
  if (options["--write-baseline"]) {
    writeFileSync(options["--write-baseline"], `${JSON.stringify(baselineFor(strict), null, 2)}\n`, { flag: "wx" });
    process.stdout.write("hygiene: proposed debt baseline written for review; the strict result below still applies\n");
  }
  // The findings list is always the strict result: debt carried by a baseline still has to be resolved.
  if (options["--findings"]) writeFileSync(options["--findings"], `${JSON.stringify(findingsList(strict, rules), null, 2)}\n`);
  if (options["--baseline"]) {
    result = compareBaseline(strict, JSON.parse(readFileSync(options["--baseline"], "utf8")));
    process.stdout.write(`hygiene: DEBT RATCHET: ${result.baseline.carried} known hit(s) carried by ${options["--baseline"]}, not resolved; not publication clearance (exports and push-time checks are strict)\n`);
  }
  for (const h of result.hits) process.stderr.write(`${hitLine(h)}\n`);
  if (options["--json"]) writeFileSync(options["--json"], `${JSON.stringify(result, null, 2)}\n`);
  const generated = result.hits.filter((h) => h.generated).length;
  const mode = options["--baseline"] ? `debt ratchet, ${strict.hits.length} strict` : "strict";
  process.stdout.write(`hygiene: tree ${result.tree} of ${result.commit ?? "no commit"}: ${result.files} files scanned, ${result.hits.length} hit(s) (${generated} in generated files; ${mode})\n`);
  return result.hits.length === 0 ? 0 : 1;
}

function usage() {
  process.stderr.write("usage: hygiene-tree.mjs [<rev>] [--json <file>] [--findings <file>] [--baseline <file> | --write-baseline <new-file>] | --names <file>\n");
  return 2;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exit(main(process.argv.slice(2)));
}
