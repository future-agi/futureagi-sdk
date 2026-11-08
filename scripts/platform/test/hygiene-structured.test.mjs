import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { loadRules, scanPaths } from "../hygiene-scan.mjs";
import { loadTreeRules, scanTree } from "../hygiene-tree.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const platform = { ...loadRules(), exemptions: [] };
const original = loadTreeRules();
const tree = { ...original, exemptions: [], binaries: [], shas: { ...original.shas, reviewed: [] } };
const revision = "a1".repeat(20);
const marker = ["U", 7].join("");
const credential = ["ghp", "_", "X".repeat(36)].join("");
const prerelease = `19.0.0-rc-${revision.slice(0, 8)}-20240101`;
const integrity = `sha512-${"a".repeat(40)}+${marker}/${"b".repeat(43)}==`;

function repository(files) {
  const dir = mkdtempSync(path.join(tmpdir(), "structured-hygiene-"));
  const git = (...args) => execFileSync("git", ["-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", ...args], {
    cwd: dir, encoding: "utf8", env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" }
  });
  git("init", "-q");
  for (const [file, content] of Object.entries(files)) {
    mkdirSync(path.dirname(path.join(dir, file)), { recursive: true });
    writeFileSync(path.join(dir, file), content);
  }
  git("add", "-A");
  git("commit", "-qm", "fixture");
  return dir;
}
const scan = (files, extra = {}) => scanTree("HEAD", { cwd: repository(files), platform, tree, localOnly: [], ...extra }).hits;

const lockfiles = {
  "package-lock.json": JSON.stringify({ lockfileVersion: 3, packages: { "": { name: "example" }, "node_modules/example": {
    version: prerelease, integrity, peerDependencies: { react: `^18.0.0 || ${prerelease}` }, description: "clean"
  } } }, null, 2),
  "pnpm-lock.yaml": `lockfileVersion: '9.0'\npackages:\n  example@${prerelease}:\n    resolution: {integrity: ${integrity}}\n    peerDependencies:\n      react: '^18.0.0 || ${prerelease}'\n`,
  "poetry.lock": `[[package]]\nname = "example"\nversion = "${prerelease}"\nfiles = [{file = "example.whl", hash = "sha256:${"a1".repeat(32)}"}]\n[package.dependencies]\nreact = "^18.0.0 || ${prerelease}"\n`,
  "uv.lock": `version = 1\n[[package]]\nname = "example"\nversion = "${prerelease}"\nsource = {registry = "https://pypi.org/simple"}\nwheels = [{url = "https://example.org/example.whl", hash = "sha256:${"a1".repeat(32)}"}]\n`
};

for (const [file, content] of Object.entries(lockfiles)) {
  test(`${file}: structural digest and dependency versions are not prose`, () => {
    assert.deepEqual(scan({ [file]: content }), []);
    const rules = { ...platform, patterns: [...platform.patterns, { id: "sample-version", regex: revision.slice(0, 8) }] };
    const dir = repository({ [file]: content });
    assert.deepEqual(scanPaths([file], rules, dir).hits, []);
    const result = JSON.parse(execFileSync("python3", ["-I", "-c", `import importlib.util,json,pathlib,sys\np=pathlib.Path(sys.argv[1]);s=importlib.util.spec_from_file_location('scan',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nprint(json.dumps(m.scan_paths([sys.argv[3]],json.loads(sys.argv[4]),pathlib.Path(sys.argv[2]))[1]))`, path.join(root, "scripts/platform/hygiene_scan.py"), dir, file, JSON.stringify(rules)], { encoding: "utf8" }));
    assert.deepEqual(result, []);
  });
}

test("all other lockfile fields, keys, comments and non-lockfiles retain the content rules", () => {
  const files = {
    "package-lock.json": JSON.stringify({ packages: { "node_modules/example": { version: prerelease, integrity, description: `private ${revision}`, scripts: { install: credential }, [marker]: true } } }),
    "poetry.lock": `${lockfiles["poetry.lock"]}\n# ${marker}\n`,
    "code.py": `name = '${marker}'\n`,
    "notes.md": `Owned by ${marker}.\n${credential}\n`,
    "ordinary.json": JSON.stringify({ version: prerelease, integrity, description: revision })
  };
  const hits = scan(files);
  for (const [file, rule] of [["package-lock.json", "unreviewed-sha"], ["package-lock.json", "github-token"], ["package-lock.json", "stream-id"], ["poetry.lock", "stream-id"], ["code.py", "stream-id"], ["notes.md", "stream-id"], ["notes.md", "github-token"], ["ordinary.json", "unreviewed-sha"]]) {
    assert.ok(hits.some((h) => h.file === file && h.rule === rule), `${file}: ${rule}`);
  }
});

test("digest or version-like keys outside dependency metadata cannot conceal content", () => {
  const hits = scan({ "package-lock.json": JSON.stringify({ version: revision, integrity: marker, metadata: { version: revision, integrity: marker }, packages: { "node_modules/example": { version: credential, integrity: credential } } }) });
  assert.ok(hits.some((h) => h.rule === "stream-id"));
  assert.ok(hits.some((h) => h.rule === "unreviewed-sha"));
  assert.ok(hits.some((h) => h.rule === "github-token"));
});

test("malformed lockfiles fail closed rather than granting a filename exemption", () => {
  for (const file of Object.keys(lockfiles)) assert.ok(scan({ [file]: `{ broken ${revision}` }).length > 0, file);
});

test("provenance requires a current public-remote proof bound to this exact occurrence", () => {
  const source = "https://github.com/example/public";
  const files = { "openapi/tracing/source.json": JSON.stringify({ source, revision, description: revision }, null, 2) };
  const calls = [];
  const hits = scan(files, { verifyProvenance: (repo, sha) => { calls.push([repo, sha]); return true; } });
  assert.deepEqual(calls, [[source, revision]]);
  assert.equal(hits.filter((h) => h.rule === "unreviewed-sha").length, 1, "the description is not provenance");
  assert.equal(scan(files, { verifyProvenance: () => false }).filter((h) => h.rule === "unreviewed-sha").length, 2);
  assert.equal(scan(files, { verifyProvenance: () => { throw new Error("unavailable"); } }).filter((h) => h.rule === "unreviewed-sha").length, 2);
});

test("old place-only provenance pins cannot clear a private or unverified revision", () => {
  const hits = scan({ "openapi/platform/source.json": JSON.stringify({ repository: "example/private", commit: revision }) }, { verifyProvenance: () => false });
  assert.ok(hits.some((h) => h.rule === "unreviewed-sha"));
});

test("the current dependency lock is clean and its source provenance is checked rather than listed", () => {
  const file = "examples/gateway/typescript/package-lock.json";
  const source = "openapi/tracing/source.json";
  const doc = JSON.parse(readFileSync(path.join(root, source), "utf8"));
  const calls = [];
  const hits = scan({ [file]: readFileSync(path.join(root, file), "utf8"), [source]: JSON.stringify(doc, null, 2) }, {
    verifyProvenance: (repo, sha) => { calls.push([repo, sha]); return repo === doc.source && sha === doc.revision; }
  });
  assert.deepEqual(hits, []);
  assert.deepEqual(calls, [[doc.source, doc.revision]]);
});
