#!/usr/bin/env node
/**
 * A reviewed public history for a qualified commit: one commit per module, on top of a public base,
 * whose last tree is exactly the qualified tree. What was built and tested is what is published.
 *
 *   node scripts/platform/public-history.mjs --qualified <rev> --onto <rev> --main <rev> \
 *     --modules <map.json> [--public <rev> ...] [--ref <branch>] [--record <file.json>] [--allow-hygiene-hits]
 *
 * The module map (kept outside the repository, so changing how the history is cut never changes the
 * qualified tree) names the author, a fixed date, trailers and the modules in commit order:
 * `{ "author": { "name", "email" }, "date": "<ISO 8601>", "trailers": [...],
 *    "modules": [{ "paths": ["<glob>", ...], "message": "<subject>\n\n<body>" }, ...] }`.
 * Each path that differs between the base and the qualified tree goes to the first module whose glob
 * matches it (`*` stays inside one directory, `**` crosses them); a path no module matches is an error,
 * and a module that matches nothing makes no commit. Author and committer are both the map's author at
 * the map's date, so the same inputs always give the same commit ids.
 *
 * Before any ref moves, every check must pass:
 * 1. every commit message has no hit under the hygiene rules (tree and platform);
 * 2. the qualified tree has no hygiene hit (`--allow-hygiene-hits` records them instead, for a dry run);
 * 3. the last commit's tree equals the qualified tree;
 * 4. `git merge-tree --write-tree <main> <export>` merges cleanly to that same tree, so the release
 *    pull request into main yields exactly the qualified tree;
 * 5. everything the export would publish is audited (`history-audit.mjs`): every commit no public
 *    revision contains, with its message, its identity (the map's author) and every entry it
 *    introduces. Public means exactly remote-tracking origin/main (`--main`) and origin/dev
 *    (`--public`, the default), resolved under refs/remotes/. Never declare `--onto` or an earlier
 *    export public: a strict cut onto one is accepted only if its own history is clean. A dry run
 *    records audit hits instead of failing. Both modes refuse replacement refs, grafts files and
 *    shallow unpublished ancestry. Obtain complete, unmodified ancestry first; no ref moves on refusal.
 * The ref then moves only forward: it is created, left as is, or fast-forwarded; anything else is
 * refused (start a new ref, or cut onto the previous export with --onto). `--record` writes the ids
 * the release record needs, with `mode` ("strict" or "dry-run") and the public revisions it trusted;
 * `export-verify.mjs` checks such a record again at push time. Exit 1 on any failed check.
 */

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { assertRealHistory } from "./git-history-guard.mjs";
import { publicRevisions, remoteRevision } from "./public-revisions.mjs";
import { auditHistory, auditLine, changedPaths } from "./history-audit.mjs";
import { RULES_FILE, loadRules, scanMessage } from "./hygiene-scan.mjs";
import { globRegExp } from "./hygiene-shas.mjs";
import { TREE_RULES_FILE, loadTreeRules, rulesAt, scanTree } from "./hygiene-tree.mjs";

export { changedPaths } from "./history-audit.mjs";

const NO_COMMIT = "0".repeat(40);
const SHOWN = 20;

function git(cwd, args, { env, input } = {}) {
  return execFileSync("git", args, {
    cwd,
    input,
    encoding: "utf8",
    env: { ...process.env, ...env, GIT_NO_REPLACE_OBJECTS: "1" },
    maxBuffer: 256 * 1024 * 1024,
    stdio: [input === undefined ? "ignore" : "pipe", "pipe", "pipe"]
  }).trim();
}

const commitOf = (cwd, rev) => git(cwd, ["rev-parse", "--verify", `${rev}^{commit}`]);
const treeOf = (cwd, rev) => git(cwd, ["rev-parse", "--verify", `${rev}^{tree}`]);

/** Each changed path's module index; throws on a path no module matches. */
export function assignModules(changes, modules) {
  const globs = modules.map((m) => (m.paths ?? []).map(globRegExp));
  const unmatched = [];
  const groups = modules.map(() => []);
  for (const change of changes) {
    const index = globs.findIndex((list) => list.some((re) => re.test(change.path)));
    if (index === -1) unmatched.push(change.path);
    else groups[index].push(change);
  }
  if (unmatched.length > 0) throw new Error(`no module matches ${unmatched.length} path(s): ${unmatched.slice(0, 10).join(", ")}`);
  return groups;
}

/** Hygiene hits in the commit messages, as text. */
export function messageHits(messages, platform, tree) {
  const out = [];
  messages.forEach((message, index) => {
    for (const hit of scanMessage(message, platform, tree)) out.push(`module ${index + 1} message line ${hit.line}: ${hit.rule} ${hit.text}`);
  });
  return out;
}

const fullMessage = (module, trailers) => (trailers?.length ? `${module.message.trim()}\n\n${trailers.join("\n")}\n` : `${module.message.trim()}\n`);

/** Write the module commits; returns `[{ commit, tree, subject, paths }]`. Moves no ref. */
export function buildHistory(cwd, { ontoCommit, groups, modules, author, date, trailers }) {
  const env = {
    GIT_AUTHOR_NAME: author.name,
    GIT_AUTHOR_EMAIL: author.email,
    GIT_AUTHOR_DATE: date,
    GIT_COMMITTER_NAME: author.name,
    GIT_COMMITTER_EMAIL: author.email,
    GIT_COMMITTER_DATE: date
  };
  const scratch = mkdtempSync(path.join(tmpdir(), "public-history-"));
  const indexEnv = { ...env, GIT_INDEX_FILE: path.join(scratch, "index") };
  const commits = [];
  try {
    git(cwd, ["read-tree", ontoCommit], { env: indexEnv });
    let parent = ontoCommit;
    groups.forEach((changes, i) => {
      if (changes.length === 0) return;
      const info = changes.map((c) => (c.deleted ? `0 ${NO_COMMIT}\t${c.path}` : `${c.mode} ${c.oid}\t${c.path}`)).join("\0");
      git(cwd, ["update-index", "-z", "--index-info"], { env: indexEnv, input: `${info}\0` });
      const tree = git(cwd, ["write-tree"], { env: indexEnv });
      const message = fullMessage(modules[i], trailers);
      parent = git(cwd, ["-c", "commit.gpgsign=false", "commit-tree", tree, "-p", parent, "-F", "-"], { env, input: message });
      commits.push({ commit: parent, tree, subject: message.split("\n")[0], paths: changes.length });
    });
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
  return commits;
}

/** The tree `git merge-tree --write-tree` gives for main and the export, or null on a conflict. */
export function mergeTreeWith(cwd, main, head) {
  try {
    return git(cwd, ["merge-tree", "--write-tree", main, head]).split("\n")[0];
  } catch {
    return null;
  }
}

/** Create or fast-forward `refs/heads/<ref>` to `commit`; refuse any other move. */
export function moveRef(cwd, ref, commit) {
  const full = `refs/heads/${ref}`;
  let old = null;
  try {
    old = git(cwd, ["rev-parse", "--verify", "--quiet", full]);
  } catch {
    old = null;
  }
  if (old === commit) return "unchanged";
  if (old !== null) {
    try {
      git(cwd, ["merge-base", "--is-ancestor", old, commit]);
    } catch {
      throw new Error(`${ref} is at ${old.slice(0, 12)}, which the new export does not contain: use a new ref, or --onto ${ref}`);
    }
  }
  git(cwd, ["update-ref", "-m", "public history", full, commit, old ?? NO_COMMIT]);
  return old === null ? "created" : "fast-forwarded";
}

/** The whole procedure. Returns the record; throws on a failed check before any ref moves. */
export function exportHistory(cwd, { qualified, onto, main, publicRevs = ["origin/dev"], map, mapSha256, ref, allowHygieneHits = false, platform, tree }) {
  assertRealHistory(cwd);
  const resolved = publicRevisions(cwd, [main, ...publicRevs]);
  if (remoteRevision(cwd, main).ref !== "refs/remotes/origin/main") throw new Error("main must be the remote-tracking refs/remotes/origin/main revision");
  platform ??= rulesAt(cwd, qualified, RULES_FILE, loadRules);
  tree ??= rulesAt(cwd, qualified, TREE_RULES_FILE, loadTreeRules);
  const q = { commit: commitOf(cwd, qualified), tree: treeOf(cwd, qualified) };
  const base = { commit: commitOf(cwd, onto), tree: treeOf(cwd, onto) };
  const mainCommit = resolved[0].commit;
  const publics = resolved.map(({ rev, commit }) => ({ rev, commit }));
  const modules = map.modules ?? [];
  if (!map.author?.name || !map.author?.email || !map.date || modules.length === 0) throw new Error("the module map needs author.name, author.email, date and modules");
  const messages = modules.map((m) => fullMessage(m, map.trailers));
  const badMessages = messageHits(messages, platform, tree);
  if (badMessages.length > 0) throw new Error(`commit messages have hygiene hits:\n  ${badMessages.join("\n  ")}`);
  const scan = scanTree(q.commit, { cwd, platform, tree });
  if (scan.hits.length > 0 && !allowHygieneHits) throw new Error(`the qualified tree has ${scan.hits.length} hygiene hit(s); run hygiene-tree.mjs ${q.commit.slice(0, 12)}`);
  const groups = assignModules(changedPaths(cwd, base.tree, q.tree), modules);
  const commits = buildHistory(cwd, { ontoCommit: base.commit, groups, modules, author: map.author, date: map.date, trailers: map.trailers });
  const head = commits.length > 0 ? commits[commits.length - 1].commit : base.commit;
  const headTree = treeOf(cwd, head);
  const merged = mergeTreeWith(cwd, mainCommit, head);
  const record = {
    version: 2,
    mode: allowHygieneHits ? "dry-run" : "strict",
    dryRun: allowHygieneHits,
    qualified: q,
    onto: base,
    main: { commit: mainCommit },
    public: publics,
    export: { commit: head, tree: headTree, commits },
    identities: { exportTreeEqualsQualified: headTree === q.tree, mergeTreeWithMain: merged, mergeTreeEqualsQualified: merged === q.tree },
    hygiene: { hits: scan.hits.length, allowed: scan.hits.length > 0 },
    ancestry: null,
    author: map.author,
    date: map.date,
    moduleMapSha256: mapSha256 ?? null,
    ref: null
  };
  if (!record.identities.exportTreeEqualsQualified) throw Object.assign(new Error("the export's tree is not the qualified tree"), { record });
  if (!record.identities.mergeTreeEqualsQualified) {
    throw Object.assign(new Error(`merging into main gives ${merged ?? "a conflict"}, not the qualified tree ${q.tree}`), { record });
  }
  const audit = auditHistory(cwd, { head, publicCommits: publics.map((p) => p.commit), platform, tree, identity: map.author });
  record.ancestry = { commits: audit.commits, entries: audit.entries, hits: audit.hits.length };
  if (audit.hits.length > 0 && !allowHygieneHits) {
    const more = audit.hits.length > SHOWN ? `\n  ... and ${audit.hits.length - SHOWN} more` : "";
    const lines = audit.hits.slice(0, SHOWN).map(auditLine).join("\n  ");
    throw Object.assign(new Error(`the export would publish ${audit.hits.length} hygiene hit(s) from history no public revision contains:\n  ${lines}${more}`), { record });
  }
  if (ref) record.ref = { name: ref, move: moveRef(cwd, ref, head) };
  return record;
}

function option(args, name) {
  const at = args.indexOf(name);
  return at === -1 ? undefined : args[at + 1];
}

/** Every value of a repeatable option. */
function options(args, name) {
  return args.flatMap((a, i) => (a === name && args[i + 1] !== undefined ? [args[i + 1]] : []));
}

function main(argv) {
  const need = ["--qualified", "--onto", "--main", "--modules"];
  if (need.some((n) => !option(argv, n)) || options(argv, "--public").some((v) => v.startsWith("--"))) {
    process.stderr.write("usage: public-history.mjs --qualified <rev> --onto <rev> --main <rev> --modules <map.json> [--public <rev> ...] [--ref <branch>] [--record <file>] [--allow-hygiene-hits]\n");
    return 2;
  }
  const bytes = readFileSync(option(argv, "--modules"));
  const args = {
    qualified: option(argv, "--qualified"),
    onto: option(argv, "--onto"),
    main: option(argv, "--main"),
    publicRevs: options(argv, "--public").length ? options(argv, "--public") : ["origin/dev"],
    map: JSON.parse(bytes.toString("utf8")),
    mapSha256: createHash("sha256").update(bytes).digest("hex"),
    ref: option(argv, "--ref"),
    allowHygieneHits: argv.includes("--allow-hygiene-hits")
  };
  let record;
  try {
    record = exportHistory(process.cwd(), args);
  } catch (error) {
    process.stderr.write(`public-history: ${error.message}\n`);
    if (error.record && option(argv, "--record")) writeFileSync(option(argv, "--record"), `${JSON.stringify(error.record, null, 2)}\n`);
    return 1;
  }
  if (option(argv, "--record")) writeFileSync(option(argv, "--record"), `${JSON.stringify(record, null, 2)}\n`);
  const e = record.export;
  const a = record.ancestry;
  process.stdout.write(
    `public-history: ${record.mode}: ${e.commits.length} commit(s) onto ${record.onto.commit.slice(0, 12)}; export ${e.commit} tree ${e.tree} = qualified ${record.qualified.commit.slice(0, 12)}; ` +
      `merge with main ${record.main.commit.slice(0, 12)} gives the same tree; hygiene hits ${record.hygiene.hits}; ` +
      `${a.commits} unpublished commit(s) audited (${a.entries} entries), ${a.hits} hit(s); ref ${record.ref ? `${record.ref.name} ${record.ref.move}` : "not moved"}\n`
  );
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exit(main(process.argv.slice(2)));
}
