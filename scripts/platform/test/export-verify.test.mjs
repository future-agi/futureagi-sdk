import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { recordProblems, verifyRecord } from "../export-verify.mjs";
import { RULES_FILE, loadRules } from "../hygiene-scan.mjs";
import { TREE_RULES_FILE, loadTreeRules } from "../hygiene-tree.mjs";
import { exportHistory } from "../public-history.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const cases = JSON.parse(readFileSync(path.join(here, "hygiene-tree-cases.json"), "utf8"));
// A synthetic stream id from the reviewed case table, never written here as a literal.
const STREAM_SAMPLE = cases.text.find((c) => c.rules.includes("stream-id")).text;
const platform = loadRules();
const policy = loadTreeRules();
const tree = { ...policy, binaries: [], exemptions: [], shas: { ...policy.shas, reviewed: [] } };
const MAP = {
  author: { name: "Example Maintainers", email: "maintainers@example.com" },
  date: "2026-01-02T03:04:05Z",
  modules: [{ paths: ["**"], message: "chore: the release tree" }]
};

function setup() {
  const dir = mkdtempSync(path.join(tmpdir(), "export-verify-"));
  const git = (...args) =>
    execFileSync("git", ["-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", ...args], {
      cwd: dir,
      encoding: "utf8",
      env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" }
    }).trim();
  const write = (rel, text) => {
    mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
    writeFileSync(path.join(dir, rel), text);
  };
  git("init", "-q", "-b", "dev");
  write("README.md", "readme\n");
  git("add", "-A");
  git("commit", "-q", "-m", "public base");
  git("branch", "main");
  for (const name of ["main", "dev"]) git("update-ref", `refs/remotes/origin/${name}`, name);
  git("checkout", "-q", "-b", "qualified");
  write("docs/guide.md", "guide\n");
  git("add", "-A");
  git("commit", "-q", "-m", "work");
  return { dir, git, write };
}

const cut = (dir, extra = {}) => exportHistory(dir, { qualified: "qualified", onto: "dev", main: "origin/main", publicRevs: ["origin/dev"], map: MAP, platform, tree, ...extra });
const verify = (dir, record, extra = {}) => verifyRecord(dir, record, { platform, tree, localOnly: [], ...extra });
const forgeClean = (r) => ({ ...r, mode: "strict", dryRun: false, hygiene: { hits: 0, allowed: false }, ancestry: { ...r.ancestry, hits: 0 } });

function leak(git, write) {
  write("docs/guide.md", `${STREAM_SAMPLE}\n`);
  git("commit", "-q", "-am", "a candidate with a hit");
}

test("a strict record passes the publication check; the ids-only mode is separate and says what it is", () => {
  const { dir } = setup();
  const record = cut(dir, { ref: "export/a" });
  assert.deepEqual([record.version, record.mode, record.dryRun], [2, "strict", false]);
  assert.deepEqual(record.public.map((p) => p.rev), ["origin/main", "origin/dev"]);
  assert.deepEqual(record.ancestry, { commits: 1, entries: 1, hits: 0 });
  assert.deepEqual(verify(dir, record), { mode: "publication", problems: [], files: 2, audited: { commits: 1, entries: 1 } });
  assert.deepEqual(verify(dir, record, { identitiesOnly: true }), { mode: "identities-only", problems: [] });
});

test("a dry-run record fails the publication check even though every id holds", () => {
  const { dir, git, write } = setup();
  leak(git, write);
  const dry = cut(dir, { ref: "export/dry", allowHygieneHits: true });
  assert.deepEqual([dry.mode, dry.dryRun, dry.hygiene.hits, dry.ancestry.hits], ["dry-run", true, 1, 1]);
  const problems = verify(dir, dry).problems;
  for (const expected of [/is a dry run/u, /mode is "dry-run", not "strict"/u, /hygiene\.hits is 1, not 0/u, /ancestry\.hits is 1, not 0/u, /tree has 1 hygiene hit\(s\) under the strict scan/u]) {
    assert.ok(problems.some((p) => expected.test(p)), `${expected}\n${problems.join("\n")}`);
  }
  assert.deepEqual(verify(dir, dry, { identitiesOnly: true }).problems, [], "the ids of a dry run hold");
  const aliased = { ...forgeClean(dry), hygieneHits: 1 };
  assert.ok(recordProblems(aliased).some((p) => /hygieneHits is 1, not 0/u.test(p)), "a wrapper's own count is checked too");
});

test("a record that claims to be clean is scanned again: the tree, then the history under it", () => {
  const { dir, git, write } = setup();
  leak(git, write);
  const dry = cut(dir, { ref: "export/dry", allowHygieneHits: true });
  assert.deepEqual(recordProblems(forgeClean(dry)), []);
  const tip = verify(dir, forgeClean(dry)).problems;
  assert.ok(tip.some((p) => /export's tree has 1 hygiene hit\(s\) under the strict scan:\n {2}hygiene: docs\/guide\.md:1 stream-id/u.test(p)), tip.join("\n"));
  write("docs/guide.md", "guide\n");
  git("commit", "-q", "-am", "a clean candidate");
  const over = cut(dir, { onto: "export/dry", ref: "export/dry", allowHygieneHits: true });
  assert.deepEqual([over.hygiene.hits, over.ancestry.hits], [0, 1], "a clean tip over the dry run's history");
  const history = verify(dir, forgeClean(over)).problems;
  assert.equal(history.length, 1, history.join("\n"));
  assert.match(history[0], /would publish 1 hygiene hit\(s\) from history no public revision contains:\n {2}[0-9a-f]{12} docs\/guide\.md:1 stream-id/u);
});

test("a record missing any field the check needs fails closed", () => {
  const { dir } = setup();
  const record = cut(dir);
  for (const field of ["dryRun", "mode", "hygiene", "ancestry", "author"]) {
    const { [field]: _dropped, ...rest } = record;
    assert.notDeepEqual(verify(dir, rest).problems, [], field);
  }
  const { public: _publics, ...noPublic } = record;
  assert.deepEqual(verify(dir, noPublic).problems, ["the record names no public revisions"]);
  const missing = "0".repeat(40);
  assert.deepEqual(verify(dir, { ...record, export: { ...record.export, commit: missing } }).problems, [`commit ${missing} is not in this repository`]);
  assert.deepEqual(verify(dir, { ...record, qualified: null }).problems, ["the record lacks the qualified, export or main ids"]);
  assert.notDeepEqual(verify(dir, null).problems, []);
});

test("a moved public revision or export ref fails both modes", () => {
  const { dir, git, write } = setup();
  const record = cut(dir, { ref: "export/a" });
  git("checkout", "-q", "main");
  write("NOTES.md", "later\n");
  git("add", "-A");
  git("commit", "-q", "-m", "main moved");
  git("update-ref", "refs/remotes/origin/main", "main");
  for (const identitiesOnly of [false, true]) {
    const problems = verify(dir, record, { identitiesOnly }).problems;
    assert.deepEqual(problems.map((p) => p.replace(/[0-9a-f]{40}/gu, "<id>")), ["origin/main is at <id>, not <id> as recorded: cut the export again and requalify"]);
  }
  git("checkout", "-q", "--detach", record.public[0].commit);
  git("branch", "-f", "main", record.public[0].commit);
  git("update-ref", "refs/remotes/origin/main", "main");
  assert.deepEqual(verify(dir, record).problems, [], "back where it was recorded");
  git("update-ref", "refs/heads/export/a", record.onto.commit);
  assert.deepEqual(verify(dir, record).problems.map((p) => p.replace(/[0-9a-f]{40}/gu, "<id>")), ["export/a is at <id>, not the export <id>"]);
});

test("the command line: a dry run is refused with exit 1, a strict record passes, and the ids-only mode names itself", () => {
  const { dir, git, write } = setup();
  const records = mkdtempSync(path.join(tmpdir(), "export-verify-records-"));
  // The rules the check reads when the scanned revision carries none: the working tree's copies.
  write(RULES_FILE, JSON.stringify(platform));
  write(TREE_RULES_FILE, JSON.stringify(tree));
  const strict = path.join(records, "strict.json");
  writeFileSync(strict, JSON.stringify(cut(dir, { ref: "export/a" })));
  leak(git, write);
  const dryFile = path.join(records, "dry.json");
  writeFileSync(dryFile, JSON.stringify(cut(dir, { ref: "export/dry", allowHygieneHits: true })));
  const cli = (...args) => spawnSync(process.execPath, [path.join(here, "../export-verify.mjs"), ...args], { cwd: dir, encoding: "utf8" });
  const passed = cli(strict);
  assert.equal(passed.status, 0, passed.stderr);
  assert.match(passed.stdout, /^export-verify: publication check passed: strict record/u);
  const refused = cli(dryFile);
  assert.equal(refused.status, 1);
  assert.match(refused.stdout, /publication check FAILED with \d+ problem\(s\): do not push/u);
  assert.match(refused.stderr, /export-verify: the record is a dry run/u);
  const ids = cli(dryFile, "--identities-only");
  assert.equal(ids.status, 0, ids.stderr);
  assert.match(ids.stdout, /IDENTITIES ONLY, NOT A PUBLICATION CHECK: the ids hold; no hygiene check ran/u);
  assert.equal(cli().status, 2);
  assert.equal(cli(path.join(records, "absent.json")).status, 1);
});
