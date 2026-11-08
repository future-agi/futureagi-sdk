import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { sha256 } from "../hygiene-names.mjs";
import { loadRules } from "../hygiene-scan.mjs";
import { loadTreeRules } from "../hygiene-tree.mjs";
import { exportHistory } from "../public-history.mjs";

const cases = JSON.parse(readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), "hygiene-tree-cases.json"), "utf8"));
// A synthetic stream id from the reviewed case table, never written here as a literal.
const STREAM_SAMPLE = cases.text.find((c) => c.rules.includes("stream-id")).text;
const platform = loadRules();
const DOC = "zz-design-notes";
const tree = { ...loadTreeRules(), binaries: [], exemptions: [], shas: { ...loadTreeRules().shas, reviewed: [] }, names: { maxWords: 4, sha256: { [sha256(DOC)]: "internal-doc" } } };
const AUTHOR = { name: "Example Maintainers", email: "maintainers@example.com" };
const MAP = {
  author: AUTHOR,
  date: "2026-01-02T03:04:05Z",
  trailers: ["Signed-off-by: Example Maintainers <maintainers@example.com>"],
  modules: [
    { paths: ["src/**"], message: "feat: the source modules" },
    { paths: ["docs/**", "bin/**"], message: "docs: notes and scripts" },
    { paths: ["**"], message: "chore: everything else" }
  ]
};
const LEAK = `per the ${DOC}`;

function setup() {
  const dir = mkdtempSync(path.join(tmpdir(), "public-history-"));
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
  write("src/a.txt", "a1\n");
  write("docs/old.md", "old\n");
  git("add", "-A");
  git("commit", "-q", "-m", "public base");
  git("branch", "main");
  for (const name of ["main", "dev"]) git("update-ref", `refs/remotes/origin/${name}`, name);
  git("checkout", "-q", "-b", "qualified");
  write("src/a.txt", "a2\n");
  write("src/b.txt", "b\n");
  rmSync(path.join(dir, "docs/old.md"));
  write("docs/new.md", "new\n");
  write("bin/run.sh", "#!/bin/sh\necho ok\n");
  execFileSync("chmod", ["+x", path.join(dir, "bin/run.sh")]);
  symlinkSync("README.md", path.join(dir, "LINK.md"));
  git("add", "-A");
  git("commit", "-q", "-m", "work in progress, with internal notes");
  write("src/b.txt", "b2\n");
  git("commit", "-q", "-am", "more internal notes");
  return { dir, git, write };
}

const run = (dir, extra = {}) => exportHistory(dir, { qualified: "qualified", onto: "dev", main: "origin/main", publicRevs: ["origin/dev"], map: MAP, platform, tree, ...extra });

test("one commit per module whose last tree is the qualified tree; merging into main gives that tree", () => {
  const { dir, git } = setup();
  const record = run(dir);
  const q = git("rev-parse", "qualified^{tree}");
  assert.equal(record.export.tree, q);
  assert.deepEqual(record.identities, { exportTreeEqualsQualified: true, mergeTreeWithMain: q, mergeTreeEqualsQualified: true });
  assert.deepEqual(record.export.commits.map((c) => [c.subject, c.paths]), [["feat: the source modules", 2], ["docs: notes and scripts", 3], ["chore: everything else", 1]]);
  const touched = record.export.commits.map((c) => git("diff-tree", "-r", "--no-commit-id", "--name-only", `${c.commit}^`, c.commit).split("\n").sort());
  assert.deepEqual(touched, [["src/a.txt", "src/b.txt"], ["bin/run.sh", "docs/new.md", "docs/old.md"], ["LINK.md"]]);
  assert.equal(git("rev-list", "--count", `dev..${record.export.commit}`), "3");
  assert.equal(git("rev-parse", `${record.export.commits[0].commit}^`), git("rev-parse", "dev"));
  assert.equal(git("ls-tree", record.export.commit, "bin/run.sh").split(" ")[0], "100755");
  assert.equal(git("ls-tree", record.export.commit, "LINK.md").split(" ")[0], "120000");
  const who = git("log", "--format=%an <%ae> %at | %cn <%ce> %ct", `dev..${record.export.commit}`).split("\n");
  const at = String(Date.parse(MAP.date) / 1000);
  assert.deepEqual([...new Set(who)], [`Example Maintainers <maintainers@example.com> ${at} | Example Maintainers <maintainers@example.com> ${at}`]);
  assert.match(git("log", "-1", "--format=%B", record.export.commit), /^chore: everything else\n\nSigned-off-by: Example Maintainers/u);
  assert.equal(record.ref, null);
  assert.equal(git("for-each-ref", "refs/heads/export"), "", "no ref moves unless one is named");
});

test("the same inputs give the same commits; the ref is created, kept, and only fast-forwarded", () => {
  const { dir, git, write } = setup();
  const first = run(dir, { ref: "export/test" });
  assert.equal(first.ref.move, "created");
  assert.equal(run(dir).export.commit, first.export.commit, "deterministic");
  assert.equal(run(dir, { ref: "export/test" }).ref.move, "unchanged");
  git("checkout", "-q", "qualified");
  write("src/c.txt", "c\n");
  git("add", "-A");
  git("commit", "-q", "-m", "a later candidate");
  assert.throws(() => run(dir, { ref: "export/test" }), /does not contain: use a new ref, or --onto export\/test/u);
  assert.equal(git("rev-parse", "export/test"), first.export.commit, "a refused move leaves the ref");
  const recut = run(dir, { ref: "export/test", onto: "export/test" });
  assert.equal(recut.ref.move, "fast-forwarded");
  assert.deepEqual(recut.export.commits.map((c) => c.subject), ["feat: the source modules"]);
  assert.equal(recut.export.tree, git("rev-parse", "qualified^{tree}"));
});

test("every check runs before any ref moves: unmatched paths, message hits, tree hits, a diverged main", () => {
  const { dir, git, write } = setup();
  const narrow = { ...MAP, modules: MAP.modules.slice(0, 2) };
  assert.throws(() => run(dir, { map: narrow, ref: "export/a" }), /no module matches 1 path\(s\): LINK\.md/u);
  const leaky = { ...MAP, modules: [{ paths: ["**"], message: `chore: ${LEAK}` }] };
  assert.throws(() => run(dir, { map: leaky, ref: "export/a" }), /commit messages have hygiene hits:\n {2}module 1 message line 1: internal-doc/u);
  assert.throws(() => run(dir, { map: { ...MAP, date: "" } }), /needs author\.name, author\.email, date and modules/u);
  git("checkout", "-q", "qualified");
  write("docs/new.md", `${LEAK}\n`);
  git("commit", "-q", "-am", "a leak");
  assert.throws(() => run(dir, { ref: "export/a" }), /the qualified tree has 1 hygiene hit/u);
  const allowed = run(dir, { allowHygieneHits: true });
  assert.deepEqual(allowed.hygiene, { hits: 1, allowed: true });
  git("checkout", "-q", "main");
  write("README.md", "changed on main\n");
  git("commit", "-q", "-am", "main moved");
  git("update-ref", "refs/remotes/origin/main", "main");
  git("checkout", "-q", "qualified");
  write("README.md", "changed differently\n");
  git("commit", "-q", "-am", "a conflicting change");
  let error;
  assert.throws(() => run(dir, { ref: "export/a", allowHygieneHits: true }), (e) => ((error = e), /merging into main gives a conflict/u.test(e.message)));
  assert.equal(error.record.identities.exportTreeEqualsQualified, true);
  assert.equal(git("for-each-ref", "refs/heads/export"), "", "no check failure moved a ref");
});

test("a strict cut onto an earlier dry-run export is refused while that export's history carries a hit", () => {
  const { dir, git, write } = setup();
  git("checkout", "-q", "qualified");
  write("docs/new.md", `${STREAM_SAMPLE}\n`);
  git("commit", "-q", "-am", "an intermediate candidate");
  const dry = run(dir, { ref: "export/test", allowHygieneHits: true });
  assert.equal(dry.hygiene.hits, 1);
  assert.equal(git("show", `${dry.export.commit}:docs/new.md`), STREAM_SAMPLE, "the dry-run export carries the text");
  write("docs/new.md", "new\n");
  git("commit", "-q", "-am", "a clean candidate");
  // The clean tip alone passes; the history under it does not, so following the re-cut advice
  // (`--onto <previous export>`) must not publish the dry-run commit.
  assert.throws(
    () => run(dir, { ref: "export/test", onto: "export/test" }),
    /would publish 1 hygiene hit\(s\) from history no public revision contains:\n {2}[0-9a-f]{12} docs\/new\.md:1 stream-id/u
  );
  assert.equal(git("rev-parse", "export/test"), dry.export.commit, "the refused cut leaves the ref");
  assert.throws(() => run(dir, { onto: dry.export.commit }), /would publish 1 hygiene hit/u, "a commit id is audited the same way");
  const clean = run(dir, { ref: "export/clean" });
  assert.equal(clean.ref.move, "created", "the same tip cut onto the public base is accepted");
  assert.throws(() => git("merge-base", "--is-ancestor", dry.export.commit, clean.export.commit), "the accepted export does not contain the dry-run commit");
});

test("a base's own commits are audited unless the remote-tracking public boundary contains them", () => {
  const { dir, git, write } = setup();
  git("checkout", "-q", "dev");
  write("docs/dev-notes.md", `${STREAM_SAMPLE}\n`);
  git("add", "-A");
  git("commit", "-q", "-m", "a commit only the base branch has");
  git("rm", "-q", "docs/dev-notes.md");
  git("commit", "-q", "-m", "and its removal");
  // A clean local base is not public: only the remote-tracking tips define that boundary.
  let error;
  assert.throws(() => run(dir, { ref: "export/b" }), (e) => ((error = e), /would publish 5 hygiene hit\(s\)/u.test(e.message)));
  const lines = error.message.split("\n").slice(1).map((l) => l.trim().split(" ").slice(1, 3).join(" ")).sort();
  assert.deepEqual(lines, [
    "author:0 foreign-identity",
    "author:0 foreign-identity",
    "committer:0 foreign-identity",
    "committer:0 foreign-identity",
    "docs/dev-notes.md:1 stream-id"
  ]);
  assert.equal(git("for-each-ref", "refs/heads/export"), "", "nothing moved");
  assert.throws(() => run(dir, { publicRevs: ["dev"] }), /public revisions/u);
  git("update-ref", "refs/remotes/origin/dev", "dev");
  const named = run(dir, { ref: "export/b" });
  assert.deepEqual(named.public.map((p) => p.rev), ["origin/main", "origin/dev"]);
  assert.equal(named.ancestry.hits, 0);
  assert.equal(named.mode, "strict");
  assert.equal(named.dryRun, false);
});
