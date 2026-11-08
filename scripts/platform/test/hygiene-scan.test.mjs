import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { checkNameList, nameCandidates, sha256 } from "../hygiene-names.mjs";
import { DEFAULT_PATHS, RULES_FILE, listFiles, loadRules, scanCommits, scanPaths, scanText } from "../hygiene-scan.mjs";

const rules = loadRules();
const cases = JSON.parse(readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), "hygiene-cases.json"), "utf8"));
const ids = (hits) => hits.map((h) => h.rule).sort();
// The real rules plus the made-up names of the shared cases (no real internal name is spelled here).
const withNames = {
  ...rules,
  names: { ...rules.names, sha256: { ...rules.names.sha256, ...Object.fromEntries(cases.names.map(([rule, name]) => [sha256(name), rule])) } }
};
// Each leak is assembled, so this file itself passes the scan it tests.
const LEAK = "see /Vol" + "umes/x and zz-example-internal";

function tree(files) {
  const dir = mkdtempSync(path.join(tmpdir(), "hygiene-"));
  for (const [rel, content] of Object.entries(files)) {
    mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
    writeFileSync(path.join(dir, rel), content);
  }
  return dir;
}

function git(dir, ...args) {
  return execFileSync("git", ["-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", ...args], {
    cwd: dir,
    encoding: "utf8",
    env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" }
  });
}

test("the shared cases: patterns and hashed names, as hygiene_scan.py reads them", () => {
  for (const c of cases.text) assert.deepEqual(ids(scanText(c.text, c.ext, withNames)), [...c.rules].sort(), c.text);
  for (const c of cases.candidates) assert.deepEqual(nameCandidates(c.line, c.maxWords), c.expect, c.line);
});

test("the rule file is scanned like any other file and passes its own scan", () => {
  const files = listFiles(DEFAULT_PATHS);
  assert.ok(files.includes(RULES_FILE));
  assert.ok(files.includes("scripts/platform/test/hygiene-cases.json"));
  assert.deepEqual(scanPaths(DEFAULT_PATHS, rules).hits, []);
  assert.ok(Object.keys(rules.names.sha256).length > 0);
});

test("the default scan covers both platform cores, their gate files included", () => {
  const files = listFiles(DEFAULT_PATHS);
  for (const file of ["python/fi/_core/policy.py", "typescript/futureagi/src/_core/policy.ts", "typescript/futureagi/src/_core/__tests__/gates.test.ts"]) {
    assert.ok(files.includes(file), file);
  }
});

test("outside a git checkout no file is skipped for its name or extension; only caches are", () => {
  const dir = tree({
    "kit/cases/x/hygiene-rules.json": JSON.stringify({ note: LEAK }),
    "kit/notes.csv": LEAK,
    "kit/dist/out.txt": LEAK,
    "kit/__pycache__/x.txt": LEAK,
    "kit/blob.bin": "abc\0def"
  });
  const found = scanPaths(["kit"], withNames, dir).hits.map((h) => `${h.file} ${h.rule}`).sort();
  assert.deepEqual(found, [
    "kit/blob.bin not-text",
    "kit/cases/x/hygiene-rules.json gcp-project",
    "kit/cases/x/hygiene-rules.json volumes-path",
    "kit/dist/out.txt gcp-project",
    "kit/dist/out.txt volumes-path",
    "kit/notes.csv gcp-project",
    "kit/notes.csv volumes-path"
  ]);
});

test("in a git checkout the scan reads every file git would commit, and nothing else", () => {
  const dir = tree({ ".gitignore": "kit/ignored/\n", "kit/tracked.md": LEAK, "kit/ignored/a.txt": LEAK, "kit/ignored/forced.txt": LEAK, "kit/new.txt": LEAK });
  git(dir, "init", "-q");
  git(dir, "add", ".gitignore", "kit/tracked.md");
  git(dir, "add", "-f", "kit/ignored/forced.txt");
  git(dir, "commit", "-q", "-m", "base");
  assert.deepEqual(listFiles(["kit"], dir), ["kit/ignored/forced.txt", "kit/new.txt", "kit/tracked.md"]);
  const found = [...new Set(scanPaths(["kit"], withNames, dir).hits.map((h) => h.file))].sort();
  assert.deepEqual(found, ["kit/ignored/forced.txt", "kit/new.txt", "kit/tracked.md"]);
});

test("OpenAPI files also get the structural checks", () => {
  const dir = tree({
    "a/spec.json": JSON.stringify({ openapi: "3.1.0", paths: { "/x": { get: { "x-omega-hub-auth": "s", responses: {} } } } }),
    "a/case.json": JSON.stringify({ evidence: "a case may name the evidence operation" })
  });
  const { files, hits } = scanPaths(["a"], rules, dir);
  assert.equal(files, 2);
  assert.deepEqual(hits.map((h) => `${h.file} ${h.rule}`), ["a/spec.json extension-not-allowed"]);
});

test("an exemption covers one line, by its hash, of one file for its listed rules; a stale one is a hit", () => {
  const marker = "/Vol" + "umes/";
  const exempt = `(re.compile(r"${marker}x"), "a local path"),`;
  const entry = { path: "gates.py", lineSha256: sha256(exempt), rules: ["volumes-path"], why: "its pattern list" };
  const local = { ...rules, exemptions: [entry] };
  const dir = tree({});
  const found = (text) => {
    writeFileSync(path.join(dir, "gates.py"), text);
    return scanPaths(["gates.py"], local, dir).hits.map((h) => `${h.line} ${h.rule}`).sort();
  };
  assert.deepEqual(found(`    ${exempt}\nsee ${marker}x\n`), ["2 volumes-path"]);
  assert.deepEqual(found(`    ${exempt}  # edited\n`), ["0 stale-exemption", "1 volumes-path"]);
  assert.deepEqual(found(`    ${exempt}\n`), []);
  entry.rules = ["home-path"];
  assert.deepEqual(found(`    ${exempt}\n`), ["0 stale-exemption", "1 volumes-path"]);
  entry.rules = ["volumes-path"];
  entry.lineSha256 = exempt;
  assert.ok(found(`    ${exempt}\n`).includes("0 invalid-exemption"), "a plain-text line is not accepted");
});

test("a malformed names block is a hit", () => {
  const bad = { ...rules, names: { maxWords: 0, sha256: { ABC: "rig", [sha256("x")]: "" } } };
  const found = scanPaths(["none"], bad, tree({})).hits.map((h) => `${h.rule} ${h.text}`);
  assert.equal(found.length, 3);
  assert.ok(found.every((f) => f.startsWith("invalid-names ")));
});

test("--names checks the plain list against the hashes, both ways", () => {
  const names = { maxWords: 4, sha256: { [sha256("zz-notes")]: "internal-plan", [sha256("zz.tool")]: "rig" } };
  assert.deepEqual(checkNameList("# comment\ninternal-plan zz-notes\nrig zz.tool\n", names), []);
  const problems = checkNameList("internal-plan zz-notes\ngcp-project zz.tool\nrig zz-other\nrig Zz-Notes\nrig\n", names);
  assert.deepEqual(problems.map((p) => p.split(":")[0]), ["line 2", "line 3", "line 4", "line 4", "line 5"]);
  assert.match(problems[0], /listed for rig, not gcp-project/u);
  assert.match(problems[1], /no hash for this name/u);
  assert.deepEqual(checkNameList("rig zz.tool\n", names), [`hash ${sha256("zz-notes").slice(0, 12)} (internal-plan) has no name in the list`]);
  const wide = { maxWords: 1, sha256: { [sha256("zz.tool")]: "rig" } };
  assert.match(checkNameList("rig zz.tool\n", wide)[0], /not one run of at most 1 words/u);
});

test("--commits scans commit messages with the same rules", () => {
  const dir = tree({});
  git(dir, "init", "-q");
  git(dir, "commit", "-q", "--allow-empty", "-m", "base");
  git(dir, "commit", "-q", "--allow-empty", "-m", "clean subject\n\nedits src/_core/policy" + ".ts; no internal names here");
  git(dir, "commit", "-q", "--allow-empty", "-m", "fix: port the kit (" + "D" + "S-EXAMPLE)\n\nbuilt under /Vol" + "umes/x from packages/server/src/a" + ".ts");
  const { commits, hits } = scanCommits("HEAD~2..HEAD", rules, dir);
  assert.equal(commits, 2);
  assert.deepEqual(hits.map((h) => `${h.line} ${h.rule}`).sort(), ["1 internal-id", "3 ee-source-path", "3 volumes-path"]);
});
