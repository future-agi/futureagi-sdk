import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { sha256 } from "../hygiene-names.mjs";
import { loadRules, scanCommits } from "../hygiene-scan.mjs";
import { applyMap, planMap } from "../hygiene-scrub.mjs";
import { shaFindings, shaHits } from "../hygiene-shas.mjs";
import { loadTreeRules, scanTree } from "../hygiene-tree.mjs";
import { exportHistory, messageHits } from "../public-history.mjs";

const platform = loadRules();
const realTree = loadTreeRules();
const tree = { ...realTree, binaries: [], exemptions: [], shas: { ...realTree.shas, reviewed: [] } };
// Deliberately synthetic values; none identifies an actual commit, work stream or decision.
const revision = "a1".repeat(20);
const stream = ["U", 29].join("");
const decision = ["ruling", 999].join(" ");
const source = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ids = (hits) => hits.map((h) => h.rule).sort();

function repository(files = {}) {
  const dir = mkdtempSync(path.join(tmpdir(), "hygiene-regression-"));
  const git = (...args) => execFileSync("git", ["-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", ...args], {
    cwd: dir, encoding: "utf8", env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" }
  }).trim();
  const write = (file, content) => {
    mkdirSync(path.dirname(path.join(dir, file)), { recursive: true });
    writeFileSync(path.join(dir, file), content);
  };
  git("init", "-q");
  for (const [file, content] of Object.entries(files)) write(file, content);
  git("add", "-A");
  git("commit", "-q", "--allow-empty", "-m", "base");
  return { dir, git, write };
}

for (const key of ["sha", "gateway_sha", "commit", "digest", "checksum", "shasum", "sha1_computed", "npm_pack_shasum", "sha256", "integrity"]) {
  test(`abbreviated revisions under ${key} require review`, () => {
    assert.deepEqual(ids(shaHits("tests/fixture.json", JSON.stringify({ [key]: revision.slice(0, 10) }), tree.shas, new Set())), ["unreviewed-sha"]);
  });
}

test("digest exemptions use exact keys, full lengths and the matched value occurrence", () => {
  const full = "a1".repeat(20);
  for (const key of ["npm_pack_shasum", "sha1_computed"]) {
    assert.deepEqual(shaHits("tests/fixture.json", JSON.stringify({ [key]: full }), tree.shas, new Set()), []);
  }
  for (const key of ["sha", "gateway_sha", "sha1", "commit_sha256", "shasum_revision", "integrity", "sha256", "shasum", "digest", "checksum"]) {
    assert.deepEqual(ids(shaHits("tests/fixture.json", JSON.stringify({ [key]: full }), tree.shas, new Set())), ["unreviewed-sha"], key);
  }
  const mixed = JSON.stringify({ npm_pack_shasum: full, commit: full });
  assert.deepEqual(ids(shaHits("tests/fixture.json", mixed, tree.shas, new Set())), ["unreviewed-sha"]);
  assert.deepEqual(ids(shaHits("tests/fixture.json", `{'sha1_computed': '${full}', 'revision': '${full}'}`, tree.shas, new Set())), ["unreviewed-sha"]);
  assert.equal(shaHits("openapi/platform/source.json", JSON.stringify({ commit: revision, revision }), tree.shas, new Set()).length, 2);
});

test("malformed digest-key policies fail closed", () => {
  for (const digestKeys of [["sha.*"], { digest: [10] }, { digest: [] }, { digest: [40, "64"] }]) {
    const shas = { ...tree.shas, digestKeys };
    assert.deepEqual(ids(shaFindings(shas, new Set())), ["invalid-digest-keys"]);
    assert.deepEqual(ids(shaHits("notes.json", JSON.stringify({ digest: revision }), shas, new Set())), ["unreviewed-sha"]);
  }
});

test("published names are scanned independently of their text or binary contents", () => {
  const paths = [`docs/${stream}-PORT.md`, `docs/${revision}.md`, `docs/${decision}.md`, "docs/zz-hidden-notes/readme.md", `assets/${stream}.bin`, "go/l" + "anes/notes.md"];

  const bytes = Buffer.from([0, 1, 2]);
  const { dir } = repository(Object.fromEntries(paths.map((file) => [file, file.endsWith(".bin") ? bytes : "clean\n"])));
  const rules = {
    ...tree,
    names: { maxWords: 4, sha256: { [sha256("zz-hidden-notes")]: "internal-doc" } },
    binaries: [{ path: paths[4], sha256: sha256(bytes.toString()), why: "fixture" }],
    exemptions: [{ path: paths[0], lineSha256: sha256(paths[0]), rules: ["stream-id"], why: "content only" }]
  };
  const result = scanTree("HEAD", { cwd: dir, platform, tree: rules, localOnly: [] });
  const expected = ["stream-id", "unreviewed-sha", "decision-ref", "internal-doc", "stream-id", "process-word"];
  paths.forEach((file, index) => {
    assert.ok(result.hits.some((hit) => hit.file === file && hit.line === 0 && hit.rule === expected[index]), file);
  });
  assert.ok(!result.hits.some((hit) => hit.rule === "binary-unreviewed"));
});

test("a path-only leak prevents an export before any branch is created", () => {
  const { dir, git, write } = repository({ "README.md": "clean\n" });
  const base = git("rev-parse", "HEAD");
  for (const name of ["main", "dev"]) git("update-ref", `refs/remotes/origin/${name}`, base);
  write(`docs/${stream}-PORT.md`, "clean\n");
  git("add", "-A");
  git("commit", "-q", "-m", "docs: notes");
  const map = { author: { name: "Example", email: "example@example.com" }, date: "2026-01-02T03:04:05Z", modules: [{ paths: ["**"], message: "docs: notes" }] };
  assert.throws(() => exportHistory(dir, { qualified: "HEAD", onto: base, main: "origin/main", publicRevs: ["origin/dev"], map, ref: "export/test", platform, tree }), /qualified tree has .* hygiene hit/u);
  assert.equal(git("for-each-ref", "refs/heads/export"), "");
});

for (const deleting of [false, true]) {
  test(`a fully completed plan handles repeated leaking lines (${deleting ? "delete" : "replace"})`, () => {
    const text = `# ${stream}\nvalue = 1\n# ${stream}\n`;
    const { dir } = repository({ "src/x.py": text });
    const map = planMap("HEAD", { cwd: dir, platform, tree, localOnly: [] });
    for (const entry of map.entries) {
      if (deleting) entry.delete = true;
      else entry.replace = "# platform core";
    }
    assert.deepEqual(applyMap(map, { root: dir, check: true, platform, tree }).problems, []);
    assert.equal(readFileSync(path.join(dir, "src/x.py"), "utf8"), text);
    assert.deepEqual(applyMap(map, { root: dir, platform, tree }).problems, []);
    assert.equal(readFileSync(path.join(dir, "src/x.py"), "utf8"), deleting ? "value = 1\n" : "# platform core\nvalue = 1\n# platform core\n");
    assert.ok(applyMap(map, { root: dir, platform, tree }).problems.some((p) => p.includes("stale")), "a later transaction must still reject stale entries");
  });
}

test("conflicting duplicate rewrites are refused atomically", () => {
  const text = `# ${stream}\n`;
  const { dir } = repository({ "src/x.py": text });
  const entry = { path: "src/x.py", line: 1, text: text.trim(), replace: "# platform core" };
  const map = { entries: [entry, { ...entry, line: 3, replace: "# different" }] };
  const result = applyMap(map, { root: dir, platform, tree });
  assert.ok(result.problems.length > 0);
  assert.equal(readFileSync(path.join(dir, "src/x.py"), "utf8"), text);
});

test("pre-push history audits and export messages enforce the same complete rules", () => {
  const { dir, git } = repository();
  const message = `docs: ${stream}, ${decision}, private commit ${revision}`;
  git("commit", "-q", "--allow-empty", "-m", message);
  const expected = ["decision-ref", "stream-id", "unreviewed-sha"];
  const result = scanCommits("HEAD~1..HEAD", platform, dir);
  assert.equal(result.commits, 1);
  assert.deepEqual(ids(result.hits), expected);
  const exported = messageHits([message], platform, tree);
  for (const rule of expected) assert.ok(exported.some((hit) => hit.includes(rule)));
  const safe = "docs: explain public platform usage";
  git("commit", "-q", "--allow-empty", "-m", safe);
  assert.deepEqual(scanCommits("HEAD~1..HEAD", platform, dir).hits, []);
});

test("the documented commit-message CLI fails closed on whole-tree rules", () => {
  const { dir, git } = repository();
  cpSync(source, path.join(dir, "scripts/platform"), { recursive: true });
  git("commit", "-q", "--allow-empty", "-m", `docs: ${stream}, ${decision}, private commit ${revision}`);
  const result = spawnSync(process.execPath, [path.join(dir, "scripts/platform/hygiene-scan.mjs"), "--commits", "HEAD~1..HEAD"], { cwd: dir, encoding: "utf8" });
  assert.equal(result.status, 1, result.stdout + result.stderr);
  for (const rule of ["stream-id", "decision-ref", "unreviewed-sha"]) assert.ok(result.stderr.includes(rule), rule);
});
