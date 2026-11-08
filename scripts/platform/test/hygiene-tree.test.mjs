import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { sha256 } from "../hygiene-names.mjs";
import { loadRules, scanText } from "../hygiene-scan.mjs";
import { annotate, globRegExp, shaHits, shaTokens } from "../hygiene-shas.mjs";
import { TREE_RULES_FILE, loadTreeRules, rulesFor, scanTree } from "../hygiene-tree.mjs";

// Synthetic repositories do not inherit file-content exemptions from the real checkout.
const platform = { ...loadRules(), exemptions: [] };
const realTree = loadTreeRules();
const cases = JSON.parse(readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), "hygiene-tree-cases.json"), "utf8"));
const withNames = {
  ...realTree,
  names: { ...realTree.names, sha256: { ...realTree.names.sha256, ...Object.fromEntries(cases.names.map(([rule, name]) => [sha256(name), rule])) } }
};
// Synthetic examples are reviewed in the shared case table.
const LEAK_WORD = cases.text.find((c) => c.rules.includes("process-word")).text;
const LEAK_ID = cases.text.find((c) => c.rules.includes("stream-id")).text;

function lineRules(file, line, tree) {
  const ids = [];
  for (const rules of rulesFor(file, platform, tree)) ids.push(...scanText(line, path.extname(file), rules).map((h) => h.rule));
  ids.push(...shaHits(file, line, tree.shas, new Set()).map((h) => h.rule));
  return [...new Set(ids)].sort();
}

function git(dir, args, input) {
  return execFileSync("git", ["-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", ...args], {
    cwd: dir,
    input,
    encoding: "utf8",
    env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" }
  }).trim();
}

/** A repository with one commit of `files` (text or Buffer); returns its directory. */
function repo(files) {
  const dir = mkdtempSync(path.join(tmpdir(), "hygiene-tree-"));
  git(dir, ["init", "-q"]);
  for (const [rel, content] of Object.entries(files)) {
    mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
    writeFileSync(path.join(dir, rel), content);
  }
  git(dir, ["add", "-A"]);
  git(dir, ["commit", "-q", "-m", "base"]);
  return dir;
}

const found = (result) => result.hits.map((h) => `${h.file}:${h.line} ${h.rule}${h.generated ? " generated" : ""}`).sort();
const noReviews = (tree, extra = {}) => ({ ...tree, binaries: [], shas: { ...tree.shas, reviewed: [] }, exemptions: [], ...extra });

test("the shared tree cases: every rule the tree scan applies at each path", () => {
  for (const c of cases.text) {
    const expected = [...c.rules];
    // Historical place-only samples now need a public ancestry proof too. Keep
    // their reviewed fixture bytes unchanged; this assertion is strictly stronger.
    if (/"(?:commit|backend_revision)":/u.test(c.text) && !expected.includes("unreviewed-sha")) expected.push("unreviewed-sha");
    assert.deepEqual(lineRules(c.path, c.text, withNames), expected.sort(), `${c.path}: ${c.text}`);
  }
});

test("commit-like tokens: 7 to 40 hex with a digit and a letter, standing alone", () => {
  const tokens = (line) => shaTokens(line).map((t) => t.token);
  const a = "ab12" + "cd3";
  assert.deepEqual(tokens(`at ${a}, (${a}) and \`${a}\``), [a, a, a]);
  assert.deepEqual(tokens(`${a}-x x-${a} x_${a} 0x${a} ${a}g ${"ab12" + "cd"}`), [a, a, a]);
  assert.deepEqual(tokens(`${"a1".repeat(20)} ${"a1".repeat(20)}b`), ["a1".repeat(20)]);
  assert.deepEqual(tokens("1234567 abcdefa"), []);
  assert.equal(annotate(a, [`${a}${"0".repeat(33)}`]), `${a} (a commit no remote branch contains)`);
  assert.equal(annotate(a, []), a);
});

test("globs: * stays in one directory, ** crosses them", () => {
  assert.ok(globRegExp("openapi/sdk/*-source.json").test("openapi/sdk/lifecycle-source.json"));
  assert.ok(!globRegExp("openapi/sdk/*-source.json").test("openapi/sdk/x/y-source.json"));
  assert.ok(globRegExp("go/**").test("go/futureagi/a/b.go"));
  assert.ok(!globRegExp("go/**").test("gox/a.go"));
  assert.ok(globRegExp("a.b").test("a.b") && !globRegExp("a.b").test("axb"));
});

test("a committed tree is read from the object store: text, generated, binary and submodule hits", () => {
  const dir = repo({
    "README.md": "clean\n",
    "docs/notes.md": `one\n${LEAK_WORD}\n`,
    "python/fi/generated/x.py": `# ${LEAK_ID}\n`,
    "assets/logo.png": Buffer.from([0x89, 0x50, 0x4e, 0x47, 0, 1, 2])
  });
  const head = git(dir, ["rev-parse", "HEAD"]);
  git(dir, ["update-index", "--add", "--cacheinfo", `160000,${head},vendor/sub`]);
  git(dir, ["commit", "-q", "-m", "sub"]);
  writeFileSync(path.join(dir, "docs/untracked.md"), `${LEAK_WORD}\n`);
  writeFileSync(path.join(dir, "README.md"), `${LEAK_WORD}\n`);
  const result = scanTree("HEAD", { cwd: dir, platform, tree: noReviews(realTree), localOnly: [] });
  assert.equal(result.commit, git(dir, ["rev-parse", "HEAD"]));
  assert.equal(result.tree, git(dir, ["rev-parse", "HEAD^{tree}"]));
  assert.equal(result.files, 5);
  assert.deepEqual(found(result), [
    "assets/logo.png:0 binary-unreviewed",
    "docs/notes.md:2 process-word",
    "python/fi/generated/x.py:1 stream-id generated",
    "vendor/sub:0 submodule"
  ]);
  const before = scanTree("HEAD~1", { cwd: dir, platform, tree: noReviews(realTree), localOnly: [] });
  assert.equal(before.files, 4, "any revision can be scanned without a checkout");
  const bare = scanTree(git(dir, ["rev-parse", "HEAD~1^{tree}"]), { cwd: dir, platform, tree: noReviews(realTree), localOnly: [] });
  assert.deepEqual([bare.commit, bare.files, bare.hits.length], [null, 4, before.hits.length], "so can a bare tree");
});

test("binaries pass only by path and the sha256 of their bytes; an unused review is a hit", () => {
  const bytes = Buffer.from([0, 1, 2, 3]);
  const dir = repo({ "a.bin": bytes });
  const digest = createHash("sha256").update(bytes).digest("hex");
  const scan = (binaries) => found(scanTree("HEAD", { cwd: dir, platform, tree: noReviews(realTree, { binaries }), localOnly: [] }));
  assert.deepEqual(scan([{ path: "a.bin", sha256: digest, why: "a fixture" }]), []);
  assert.deepEqual(scan([{ path: "a.bin", sha256: "0".repeat(64), why: "a fixture" }]), ["a.bin:0 binary-unreviewed", "a.bin:0 stale-binary-review"]);
  assert.deepEqual(scan([{ path: "a.bin", sha256: digest, why: "a fixture" }, { path: "gone.bin", sha256: digest, why: "x" }]), ["gone.bin:0 stale-binary-review"]);
  assert.deepEqual(scan([{ path: "a.bin", sha256: digest }]), ["a.bin:0 binary-unreviewed", `${TREE_RULES_FILE}:0 invalid-binary-review`]);
});

test("commit ids: unverified pins fail, unused reviews are hits, local-only commits are named", () => {
  const dir = repo({ "a.txt": "first\n" });
  const first = git(dir, ["rev-parse", "HEAD"]);
  const published = "abcdef" + "1234567";
  const listedOnly = "fedcba" + "987654";
  mkdirSync(path.join(dir, "openapi/platform"), { recursive: true });
  mkdirSync(path.join(dir, "scripts/platform"), { recursive: true });
  writeFileSync(path.join(dir, "openapi/platform/source.json"), `{\n  "commit": "${first}"\n}\n`);
  writeFileSync(path.join(dir, "notes.md"), `merged at ${first}\nsee ${published.slice(0, 7)} upstream\n`);
  writeFileSync(path.join(dir, TREE_RULES_FILE), `{ "reviewed": "${listedOnly}" }\n`);
  git(dir, ["add", "-A"]);
  git(dir, ["commit", "-q", "-m", "second"]);
  const reviewed = [
    { sha: published, repository: "example/public", why: "a public commit" },
    { sha: listedOnly, repository: "example/public", why: "named only in the rule file" }
  ];
  const result = scanTree("HEAD", { cwd: dir, platform, tree: noReviews(realTree, { shas: { pins: realTree.shas.pins, reviewed } }) });
  assert.deepEqual(result.hits.map((h) => `${h.file}:${h.line} ${h.rule} ${h.text}`).sort(), [
    `notes.md:1 unreviewed-sha ${first} (a commit no remote branch contains)`,
    `openapi/platform/source.json:2 unreviewed-sha ${first} (a commit no remote branch contains)`,
    `${TREE_RULES_FILE}:0 stale-sha-review ${listedOnly} (example/public) is named by no scanned file`
  ]);
});

test("exemptions cover one line of one file for the listed rules; a stale one is a hit", () => {
  const dir = repo({ "docs/a.md": `${LEAK_ID}\n${LEAK_ID}!\n` });
  const exempt = (rules) => noReviews(realTree, { exemptions: [{ path: "docs/a.md", lineSha256: sha256(LEAK_ID), rules, why: "a fixture" }] });
  const scan = (tree) => found(scanTree("HEAD", { cwd: dir, platform, tree, localOnly: [] }));
  assert.deepEqual(scan(exempt(["stream-id"])), ["docs/a.md:2 stream-id"]);
  assert.deepEqual(scan(exempt(["team-ref"])), ["docs/a.md:0 stale-exemption", "docs/a.md:1 stream-id", "docs/a.md:2 stream-id"]);
  assert.deepEqual(scan(noReviews(realTree, { exemptions: [{ path: "docs/a.md", rules: ["stream-id"] }] })).slice(0, 1), ["docs/a.md:0 invalid-exemption"]);
});

test("the tree tooling and its rule file pass their own tree scan", () => {
  const own = /^scripts\/platform\/(?:hygiene-(?:tree|shas|scrub|scan|baseline|findings)|public-history|history-audit|export-verify|test\/(?:hygiene-tree|hygiene-scrub|hygiene-regressions|hygiene-hardening|hygiene-findings|public-history|export-verify))/u;
  const result = scanTree("HEAD");
  assert.deepEqual(result.hits.filter((h) => own.test(h.file)), []);
  assert.ok(result.files > 0);
  assert.ok(Object.keys(realTree.names.sha256).length > 0);
});
