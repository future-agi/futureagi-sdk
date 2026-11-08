import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { verifyRecord } from "../export-verify.mjs";
import { newCommits } from "../history-audit.mjs";
import { RULES_FILE, loadRules } from "../hygiene-scan.mjs";
import { TREE_RULES_FILE, loadTreeRules } from "../hygiene-tree.mjs";
import { exportHistory } from "../public-history.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const cases = JSON.parse(readFileSync(path.join(here, "hygiene-tree-cases.json"), "utf8"));
const sample = cases.text.find((c) => c.rules.includes("stream-id")).text;
const platform = loadRules();
const policy = loadTreeRules();
const tree = { ...policy, binaries: [], exemptions: [], shas: { ...policy.shas, reviewed: [] } };
const map = {
  author: { name: "Example Maintainers", email: "maintainers@example.com" },
  date: "2026-01-02T03:04:05Z",
  modules: [{ paths: ["**"], message: "docs: the release tree" }]
};
const incomplete = /incomplete unpublished ancestry: shallow commit/u;

function setup(t) {
  const dir = mkdtempSync(path.join(tmpdir(), "shallow-history-"));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const git = (...args) => execFileSync("git", [
    "-c", `user.name=${map.author.name}`, "-c", `user.email=${map.author.email}`,
    "-c", "commit.gpgsign=false", ...args
  ], {
    cwd: dir, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" }
  }).trim();
  const write = (file, text) => {
    mkdirSync(path.dirname(path.join(dir, file)), { recursive: true });
    writeFileSync(path.join(dir, file), text);
  };
  git("init", "-q", "-b", "main");
  write("README.md", "base\n");
  git("add", "-A");
  git("commit", "-qm", "public base");
  const base = git("rev-parse", "HEAD");
  git("branch", "dev");
  for (const name of ["main", "dev"]) git("update-ref", `refs/remotes/origin/${name}`, base);
  git("checkout", "-qb", "qualified");
  write("docs/guide.md", "guide\n");
  git("add", "-A");
  git("commit", "-qm", "candidate");
  const cut = (extra = {}) => exportHistory(dir, {
    qualified: "qualified", onto: base, main: "origin/main", publicRevs: ["origin/dev"], map, platform, tree, ...extra
  });
  const verify = (record, extra = {}) => verifyRecord(dir, record, { platform, tree, localOnly: [], ...extra });
  const shallow = (...commits) => writeFileSync(path.resolve(dir, git("rev-parse", "--git-path", "shallow")), commits.map((c) => `${c}\n`).join(""));
  const first = cut({ ref: "export/current" });
  const mergeSide = (text = sample) => {
    git("checkout", "-qb", "side", base);
    write("hidden.txt", `${text}\n`);
    git("add", "-A");
    git("commit", "-qm", "side notes");
    git("rm", "-q", "hidden.txt");
    git("commit", "-qm", "remove side notes");
    const side = git("rev-parse", "HEAD");
    git("checkout", "-qb", "onto", first.export.commit);
    git("merge", "--no-ff", "-qm", "merge side", "side");
    return side;
  };
  return { dir, git, write, base, cut, verify, shallow, first, mergeSide };
}

test("strict export rejects a shallow unpublished merge parent before advancing its ref", (t) => {
  const { git, cut, shallow, first, mergeSide } = setup(t);
  const side = mergeSide();
  shallow(side);
  assert.match(git("cat-file", "-p", side), /\nparent [0-9a-f]+\n/u, "the boundary is not a real root");
  assert.equal(git("rev-list", "--parents", "-1", side), side, "the revision walk hides its parent");
  assert.throws(() => cut({ onto: "onto", ref: "export/current" }), incomplete);
  assert.equal(git("rev-parse", "export/current"), first.export.commit);
  shallow();
  assert.throws(() => cut({ onto: "onto" }), /hidden\.txt:1 stream-id/u, "complete ancestry exposes the removed leak");
});

test("dry-run mode cannot represent an incomplete ancestry audit as a completed count", (t) => {
  const { git, cut, shallow, mergeSide } = setup(t);
  shallow(mergeSide());
  assert.throws(() => cut({ onto: "onto", ref: "export/dry", allowHygieneHits: true }), incomplete);
  assert.equal(git("for-each-ref", "refs/heads/export/dry"), "");
});

test("publication verification rejects a newly shallow side branch despite clean recorded counts and identities", (t) => {
  const { cut, verify, shallow, mergeSide } = setup(t);
  const side = mergeSide("public notes");
  const record = cut({ onto: "onto", ref: "export/current" });
  assert.deepEqual(verify(record).problems, []);
  shallow(side);
  assert.deepEqual(verify(record, { identitiesOnly: true }).problems, [], "tree identities alone still hold");
  const result = verify(record);
  assert.equal(result.mode, "publication");
  assert.match(result.problems.join("\n"), incomplete);
  shallow();
  assert.deepEqual(verify(record).problems, [], "restoring complete clean ancestry permits verification");
});

test("a forged clean record cannot use a shallow side branch to hide a removed ancestral hit", (t) => {
  const { cut, verify, shallow, mergeSide } = setup(t);
  const side = mergeSide();
  const dry = cut({ onto: "onto", allowHygieneHits: true });
  assert.equal(dry.hygiene.hits, 0);
  assert.equal(dry.ancestry.hits, 1);
  const record = { ...dry, mode: "strict", dryRun: false, ancestry: { ...dry.ancestry, hits: 0 } };
  shallow(side);
  assert.deepEqual(verify(record, { identitiesOnly: true }).problems, []);
  assert.match(verify(record).problems.join("\n"), incomplete);
  shallow();
  assert.match(verify(record).problems.join("\n"), /hidden\.txt:1 stream-id/u);
});

test("the publication CLI reports incomplete ancestry as a failed check, not clearance", (t) => {
  const { dir, write, cut, shallow, mergeSide } = setup(t);
  const side = mergeSide("public notes");
  const record = cut({ onto: "onto" });
  write("record.json", JSON.stringify(record));
  write(RULES_FILE, JSON.stringify(platform));
  write(TREE_RULES_FILE, JSON.stringify(tree));
  shallow(side);
  const result = spawnSync(process.execPath, [path.join(here, "../export-verify.mjs"), "record.json"], { cwd: dir, encoding: "utf8" });
  assert.equal(result.status, 1, result.stderr);
  assert.match(result.stderr, incomplete);
  assert.match(result.stdout, /publication check FAILED/u);
});

test("shallow boundaries already in trusted public ancestry remain exempt", (t) => {
  const { base, cut, verify, shallow } = setup(t);
  shallow(base);
  const record = cut();
  assert.equal(record.ancestry.commits, 1);
  assert.deepEqual(verify(record).problems, []);
});

test("a shallow qualified source outside exported ancestry does not block a complete export", (t) => {
  const { git, cut, verify, shallow } = setup(t);
  shallow(git("rev-parse", "qualified"));
  const record = cut();
  assert.deepEqual(verify(record).problems, []);
});

test("linked worktrees consult the shared repository shallow boundaries", (t) => {
  const { dir, git, base, shallow, mergeSide } = setup(t);
  const side = mergeSide("public notes");
  const linked = path.join(dir, "linked");
  git("worktree", "add", "--detach", linked, "onto");
  shallow(side);
  assert.throws(() => newCommits(linked, "HEAD", [base]), incomplete);
});

test("a genuine unpublished root remains auditable", (t) => {
  const { dir, git, base } = setup(t);
  assert.deepEqual(newCommits(dir, base, []), [{ commit: base, parents: [] }]);
});
