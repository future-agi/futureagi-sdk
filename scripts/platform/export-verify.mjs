#!/usr/bin/env node
/**
 * The check, at push time, that an export record still holds: run it after a fetch and before any
 * push, in the repository the export lives in.
 *
 *   node scripts/platform/export-verify.mjs <record.json>                    (the publication check)
 *   node scripts/platform/export-verify.mjs <record.json> --identities-only  (NOT a publication check)
 *
 * The record is what `public-history.mjs --record` writes; a wrapper may add fields. The publication
 * check fails closed, and trusts none of the record's own hygiene counts:
 * 1. the record is strict: `mode` "strict", `dryRun` false, zero hygiene and ancestry hits, and an
 *    author; a missing field fails like a wrong one;
 * 2. the public set is exactly remote-tracking origin/main and origin/dev, each still at its recorded
 *    commit; replacement refs and grafts files are refused before any object inspection;
 * 3. the export ref, when the record names one, still points at the export commit;
 * 4. the export's tree is the qualified tree, `git merge-tree --write-tree <main> <export>` gives
 *    that tree again, and the recorded base is an ancestor of the export;
 * 5. the strict tree scan of the export commit, rerun now, has no hit;
 * 6. the history audit (`history-audit.mjs`), rerun now, finds nothing in what the export adds to the
 *    public revisions: messages, identities and every entry those commits introduce. A shallow
 *    boundary in that unpublished range fails the audit, even when all recorded counts are zero.
 * The rules are the ones the qualified revision carries. `--identities-only` runs checks 2 to 4 alone,
 * for comparing a dry run's ids; it says it is not a publication check, and it is never the default.
 * Exit 0 when every check passes, 1 otherwise, 2 on usage.
 */

import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { assertRealHistory } from "./git-history-guard.mjs";
import { publicRevisionProblems } from "./public-revisions.mjs";
import { auditHistory, auditLine } from "./history-audit.mjs";
import { RULES_FILE, loadRules } from "./hygiene-scan.mjs";
import { TREE_RULES_FILE, hitLine, loadTreeRules, rulesAt, scanTree } from "./hygiene-tree.mjs";
import { mergeTreeWith } from "./public-history.mjs";

const HEX40 = /^[0-9a-f]{40}$/u;
const SHOWN = 20;

/** Trimmed stdout of a git command, or null when it fails. */
function tryGit(cwd, args) {
  try {
    return execFileSync("git", args, { cwd, env: { ...process.env, GIT_NO_REPLACE_OBJECTS: "1" }, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], maxBuffer: 64 * 1024 * 1024 }).trim();
  } catch {
    return null;
  }
}

const commitAt = (cwd, rev) => tryGit(cwd, ["rev-parse", "--verify", "--quiet", `${rev}^{commit}`]);
const treeAt = (cwd, rev) => tryGit(cwd, ["rev-parse", "--verify", "--quiet", `${rev}^{tree}`]);
const listed = (lines) => lines.slice(0, SHOWN).map((l) => `\n  ${l}`).join("") + (lines.length > SHOWN ? `\n  ... and ${lines.length - SHOWN} more` : "");

/** Check 1: why the record is not a strict, clean publication record (empty when it is one). */
export function recordProblems(record) {
  const out = [];
  if (record?.dryRun !== false) out.push(`the record is a dry run or does not say (dryRun ${JSON.stringify(record?.dryRun)}): cut it again in strict mode`);
  if (record?.mode !== "strict") out.push(`the record's mode is ${JSON.stringify(record?.mode)}, not "strict"`);
  const counts = [["hygiene.hits", record?.hygiene?.hits], ["ancestry.hits", record?.ancestry?.hits]];
  if (record && Object.hasOwn(record, "hygieneHits")) counts.push(["hygieneHits", record.hygieneHits]);
  for (const [name, value] of counts) if (value !== 0) out.push(`the record's ${name} is ${JSON.stringify(value)}, not 0`);
  if (!record?.author?.name || !record?.author?.email) out.push("the record names no author for the export's commits");
  return out;
}

/** Why the record's ids cannot be checked at all (null when they can). */
function unusable(cwd, record) {
  const q = record?.qualified;
  const e = record?.export;
  if (![q?.commit, q?.tree, e?.commit, e?.tree, record?.main?.commit].every((id) => HEX40.test(id ?? ""))) return "the record lacks the qualified, export or main ids";
  if (!Array.isArray(record.public) || record.public.length === 0) return "the record names no public revisions";
  const bad = record.public.find((p) => typeof p?.rev !== "string" || !HEX40.test(p?.commit ?? ""));
  if (bad !== undefined) return `a public revision entry is malformed: ${JSON.stringify(bad)}`;
  const missing = [q.commit, e.commit, record.main.commit, ...record.public.map((p) => p.commit)].find((id) => commitAt(cwd, id) === null);
  return missing === undefined ? null : `commit ${missing} is not in this repository`;
}

/** Checks 2 to 4: the record's ids against the repository as it is now. */
export function identityProblems(cwd, record) {
  try {
    assertRealHistory(cwd);
  } catch (error) {
    return [error.message];
  }
  const why = unusable(cwd, record);
  if (why) return [why];
  const q = record.qualified;
  const e = record.export;
  const out = publicRevisionProblems(cwd, record);
  // Never use an untrusted publication boundary to exclude history from the audit.
  if (out.length > 0) return out;
  if (record.ref?.name) {
    const at = commitAt(cwd, `refs/heads/${record.ref.name}`);
    if (at !== e.commit) out.push(`${record.ref.name} is at ${at ?? "nothing"}, not the export ${e.commit}`);
  }
  if (treeAt(cwd, q.commit) !== q.tree) out.push(`the qualified commit ${q.commit} does not have the recorded tree ${q.tree}`);
  const exportTree = treeAt(cwd, e.commit);
  if (exportTree !== q.tree || e.tree !== q.tree) out.push(`the export's tree ${exportTree ?? "(missing)"} is not the qualified tree ${q.tree}`);
  const merged = mergeTreeWith(cwd, record.main.commit, e.commit);
  if (merged !== q.tree) out.push(`merging the export into main gives ${merged ?? "a conflict"}, not the qualified tree ${q.tree}`);
  const base = record.onto?.commit;
  if (!HEX40.test(base ?? "") || tryGit(cwd, ["merge-base", "--is-ancestor", base, e.commit]) === null) out.push("the recorded base is not an ancestor of the export");
  return out;
}

/** Checks 5 and 6: the strict tree scan and the history audit, rerun now. */
export function hygieneProblems(cwd, record, { platform, tree, localOnly } = {}) {
  platform ??= rulesAt(cwd, record.qualified.commit, RULES_FILE, loadRules);
  tree ??= rulesAt(cwd, record.qualified.commit, TREE_RULES_FILE, loadTreeRules);
  const out = [];
  const scan = scanTree(record.export.commit, { cwd, platform, tree, localOnly });
  if (scan.hits.length > 0) out.push(`the export's tree has ${scan.hits.length} hygiene hit(s) under the strict scan:${listed(scan.hits.map(hitLine))}`);
  let audit;
  try {
    audit = auditHistory(cwd, {
      head: record.export.commit,
      publicCommits: record.public.map((p) => p.commit),
      platform,
      tree,
      identity: record.author,
      localOnly
    });
  } catch (error) {
    out.push(`the history audit could not complete: ${error.message}`);
    return { problems: out, files: scan.files, audited: null };
  }
  if (audit.hits.length > 0) out.push(`the export would publish ${audit.hits.length} hygiene hit(s) from history no public revision contains:${listed(audit.hits.map(auditLine))}`);
  return { problems: out, files: scan.files, audited: { commits: audit.commits, entries: audit.entries } };
}

/** Every check for one mode: `{ mode, problems }`; `mode` is "publication" or "identities-only". */
export function verifyRecord(cwd, record, { identitiesOnly = false, platform, tree, localOnly } = {}) {
  const identities = identityProblems(cwd, record);
  if (identitiesOnly) return { mode: "identities-only", problems: identities };
  const problems = [...recordProblems(record), ...identities];
  // Do not scan through a repository overlay or trust a malformed publication boundary.
  if (identities.length > 0) return { mode: "publication", problems };
  const hygiene = hygieneProblems(cwd, record, { platform, tree, localOnly });
  return { mode: "publication", problems: [...problems, ...hygiene.problems], files: hygiene.files, audited: hygiene.audited };
}

function main(argv) {
  const identitiesOnly = argv.includes("--identities-only");
  const rest = argv.filter((a) => a !== "--identities-only");
  if (rest.length !== 1 || rest[0].startsWith("-")) {
    process.stderr.write("usage: export-verify.mjs <record.json> [--identities-only]\n");
    return 2;
  }
  let record;
  try {
    record = JSON.parse(readFileSync(rest[0], "utf8"));
  } catch (error) {
    process.stderr.write(`export-verify: cannot read the record: ${error.message}\n`);
    return 1;
  }
  const result = verifyRecord(process.cwd(), record, { identitiesOnly });
  for (const p of result.problems) process.stderr.write(`export-verify: ${p}\n`);
  const ok = result.problems.length === 0;
  if (identitiesOnly) {
    process.stdout.write(`export-verify: IDENTITIES ONLY, NOT A PUBLICATION CHECK: ${ok ? "the ids hold" : `${result.problems.length} problem(s)`}; no hygiene check ran and the record's mode was not checked\n`);
  } else if (ok) {
    process.stdout.write(`export-verify: publication check passed: strict record, public revisions unchanged, both tree identities hold, strict scan of ${result.files} files and audit of ${result.audited.commits} unpublished commit(s) clean\n`);
  } else {
    process.stdout.write(`export-verify: publication check FAILED with ${result.problems.length} problem(s): do not push\n`);
  }
  return ok ? 0 : 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exit(main(process.argv.slice(2)));
}
