import assert from "node:assert/strict";
import { test } from "node:test";
import { fixture, forgeClean, sample } from "./history-fixture.mjs";

const invalidPublic = /public revisions|remote-tracking|refs\/remotes\//u;

test("a forged record cannot declare a dry-run export public", (t) => {
  const { git, write, cut, verify } = fixture(t);
  write("docs/guide.md", `${sample}\n`);
  git("commit", "-qam", "candidate notes");
  const dry = cut({ ref: "export/dry", allowHygieneHits: true });
  write("docs/guide.md", "guide\n");
  git("commit", "-qam", "clean candidate");
  const later = cut({ onto: "export/dry", allowHygieneHits: true });
  assert.equal(later.hygiene.hits, 0);
  assert.equal(later.ancestry.hits, 1);
  const forged = { ...forgeClean(later), public: [...later.public, { rev: "export/dry", commit: dry.export.commit }] };
  for (const identitiesOnly of [false, true]) assert.match(verify(forged, { identitiesOnly }).problems.join("\n"), invalidPublic);
});

test("the public set is exactly the two remote-tracking revisions, not arbitrary remote refs or aliases", (t) => {
  const { git, cut, verify, base } = fixture(t);
  const record = cut();
  git("update-ref", "refs/remotes/origin/other", base);
  git("branch", "local-public", base);
  git("symbolic-ref", "refs/remotes/origin/main-alias", "refs/remotes/origin/main");
  const entry = (rev) => ({ rev, commit: base });
  const cases = [
    [entry("origin/main")],
    [entry("origin/main"), entry("origin/main")],
    [entry("origin/main"), entry("origin/other")],
    [...record.public, entry("origin/other")],
    [entry("origin/main"), entry("local-public")],
    [entry("origin/main"), entry(base)],
    [entry("origin/main"), entry("origin/dev^{commit}")]
  ];
  for (const publics of cases) {
    assert.match(verify({ ...record, public: publics }).problems.join("\n"), invalidPublic, JSON.stringify(publics));
  }
  for (const full of [false, true]) {
    const publics = ["main", "dev"].map((name) => entry(`${full ? "refs/remotes/" : ""}origin/${name}`));
    assert.deepEqual(verify({ ...record, public: publics }).problems, []);
  }
});

test("both recorded remote-tracking tips are pinned at cut time", (t) => {
  const { git, cut, verify } = fixture(t);
  const record = cut();
  for (const name of ["main", "dev"]) {
    const ref = `refs/remotes/origin/${name}`;
    const old = git("rev-parse", ref);
    git("update-ref", ref, "qualified");
    assert.match(verify(record).problems.join("\n"), /cut the export again and requalify/u);
    git("update-ref", ref, old);
  }
  assert.deepEqual(verify(record).problems, []);
});

test("a local branch cannot shadow the remote-tracking public name", (t) => {
  const { git, cut, verify, base } = fixture(t);
  const record = cut();
  git("branch", "origin/main", base);
  assert.match(verify(record).problems.join("\n"), invalidPublic);
  assert.throws(() => cut(), invalidPublic);
});

test("the CLI and API refuse to classify a dry-run or other local revision as public", (t) => {
  const { git, cut, cli } = fixture(t);
  const dry = cut({ ref: "export/dry", allowHygieneHits: true });
  for (const rev of ["export/dry", "refs/heads/export/dry", dry.export.commit, "origin/dev^{commit}"]) {
    assert.throws(() => cut({ publicRevs: ["origin/dev", rev], ref: "export/refused" }), invalidPublic);
    const result = cli(rev);
    assert.equal(result.status, 1, result.stderr);
    assert.match(result.stderr, invalidPublic);
    assert.equal(git("for-each-ref", "refs/heads/export/cli", "refs/heads/export/refused"), "");
  }
  assert.throws(() => cut({ main: "export/dry" }), invalidPublic, "main is not another trust escape");
});
