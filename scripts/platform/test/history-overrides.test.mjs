import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { chmodSync, mkdirSync, readFileSync, symlinkSync, writeFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { verifyRecord } from "../export-verify.mjs";
import { auditHistory } from "../history-audit.mjs";
import { readBlobs, rulesAt, scanTree } from "../hygiene-tree.mjs";
import { fixture, forgeClean, platform, sample, tree } from "./history-fixture.mjs";

const override = /history overrides are not allowed: (refs\/replace|info\/grafts|GIT_REPLACE_REF_BASE)/u;

function setEnv(t, name, value) {
  const original = process.env[name];
  process.env[name] = value;
  t.after(() => {
    if (original === undefined) delete process.env[name];
    else process.env[name] = original;
  });
}

for (const kind of ["replacement graft", "alternate replacement graft", "replaced blob", "grafts file"]) {
  test(`${kind} cannot hide published objects from any gate`, (t) => {
    const { dir, git, write, base, cut, verify, mergeSide } = fixture(t);
    const first = cut({ ref: "export/current" });
    let dry;
    let install;
    if (kind === "replaced blob") {
      write("docs/guide.md", `${sample}\n`);
      git("commit", "-qam", "candidate notes");
      dry = cut({ allowHygieneHits: true });
      const leaking = git("rev-parse", "qualified:docs/guide.md");
      const clean = git("rev-parse", `${first.export.commit}:docs/guide.md`);
      install = () => {
        git("replace", leaking, clean);
        assert.equal(git("show", "qualified:docs/guide.md"), "guide", "ordinary git hides the blob");
        assert.equal(readBlobs([leaking], dir).get(leaking).toString(), `${sample}\n`, "object reads ignore replacement blobs");
      };
    } else {
      const { side, leaking } = mergeSide(first);
      dry = cut({ onto: "onto", allowHygieneHits: true });
      install = () => {
        if (kind === "alternate replacement graft") setEnv(t, "GIT_REPLACE_REF_BASE", "refs/alt/");
        if (kind.endsWith("replacement graft")) git("replace", "--graft", side, base);
        else writeFileSync(path.resolve(dir, git("rev-parse", "--git-path", "info/grafts")), `${side} ${base}\n`);
        assert.ok(!git("rev-list", "onto").split("\n").includes(leaking), "ordinary traversal hides the leaking parent");
      };
    }
    assert.equal(dry.ancestry.hits, 1, "the unmodified audit sees the leak");
    install();
    assert.throws(() => scanTree("qualified", { cwd: dir, platform, tree }), override);
    assert.throws(() => auditHistory(dir, { head: dry.export.commit, publicCommits: [base], platform, tree }), override);
    assert.throws(() => rulesAt(dir, "qualified", "rules.json", () => ({})), override, "a refusal cannot become fallback rules");
    for (const allowHygieneHits of [false, true]) {
      assert.throws(() => cut({ onto: dry.export.commit, ref: "export/current", allowHygieneHits }), override);
      assert.equal(git("rev-parse", "export/current"), first.export.commit, "a refusal never moves the export ref");
    }
    for (const identitiesOnly of [false, true]) {
      const result = verify(forgeClean(dry), { identitiesOnly });
      assert.match(result.problems.join("\n"), override);
    }
  });
}

for (const kind of ["empty", "dangling symlink"]) {
  test(`even an ${kind} shared grafts file fails closed in a linked worktree`, (t) => {
    const { dir, git, cut } = fixture(t);
    const record = cut();
    const linked = path.join(dir, "linked");
    git("worktree", "add", "--detach", linked, "qualified");
    const grafts = path.resolve(dir, git("rev-parse", "--git-path", "info/grafts"));
    if (kind === "empty") writeFileSync(grafts, "");
    else symlinkSync("missing-grafts", grafts);
    assert.match(verifyRecord(linked, record, { platform, tree }).problems.join("\n"), override);
  });
}

for (const base of ["", "refs/replace/", "refs/alt/"]) {
  test(`an explicitly set replacement namespace ${JSON.stringify(base)} fails closed without refs`, (t) => {
    const { dir, git, base: publicBase, cut, verify } = fixture(t);
    const record = cut({ ref: "export/current" });
    setEnv(t, "GIT_REPLACE_REF_BASE", base);
    const refusal = /history overrides are not allowed: GIT_REPLACE_REF_BASE/u;
    assert.throws(() => scanTree("qualified", { cwd: dir, platform, tree }), refusal);
    assert.throws(() => auditHistory(dir, { head: record.export.commit, publicCommits: [publicBase], platform, tree }), refusal);
    assert.throws(() => rulesAt(dir, "qualified", "rules.json", () => ({})), refusal);
    for (const allowHygieneHits of [false, true]) {
      assert.throws(() => cut({ ref: "export/current", allowHygieneHits }), refusal);
      assert.equal(git("rev-parse", "export/current"), record.export.commit);
    }
    for (const identitiesOnly of [false, true]) {
      assert.match(verify(record, { identitiesOnly }).problems.join("\n"), refusal);
    }
  });
}

test("every git spawn in the export gates forces raw object semantics", (t) => {
  const { dir, git, cut } = fixture(t);
  setEnv(t, "GIT_NO_REPLACE_OBJECTS", "0");
  // Log actual child environments: an exit-code assertion can be swallowed by a git caller.
  writeFileSync(path.join(dir, "rules.json"), "{}");
  git("add", "rules.json");
  git("commit", "-qm", "test rules");
  const realGit = execFileSync("/bin/sh", ["-c", "command -v git"], { encoding: "utf8" }).trim();
  const wrapper = path.join(dir, "bin/git");
  mkdirSync(path.dirname(wrapper));
  const log = path.join(dir, "git-calls.log");
  setEnv(t, "GIT_CALL_LOG", log);
  writeFileSync(wrapper, `#!/bin/sh\nprintf '%s\\t%s\\n' "$GIT_NO_REPLACE_OBJECTS" "$*" >> "$GIT_CALL_LOG"\nexec "${realGit}" "$@"\n`);
  chmodSync(wrapper, 0o755);
  setEnv(t, "PATH", `${path.dirname(wrapper)}:${process.env.PATH}`);
  assert.deepEqual(rulesAt(dir, "qualified", "rules.json", () => { throw new Error("rule read failed"); }), {});
  const record = cut();
  assert.deepEqual(verifyRecord(dir, record, { platform, tree }).problems, []);
  assert.equal(scanTree("qualified", { cwd: dir, platform, tree }).hits.length, 0);
  const calls = readFileSync(log, "utf8").trimEnd().split("\n");
  assert.ok(calls.some((call) => call.endsWith("\trev-list --all --not --remotes")), "annotation traversal was exercised");
  assert.deepEqual(calls.filter((call) => !call.startsWith("1\t")), [], "every logged git call must force raw object semantics");
});
