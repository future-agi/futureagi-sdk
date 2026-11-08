import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { loadRules } from "../hygiene-scan.mjs";
import { shaHits, shaTokens } from "../hygiene-shas.mjs";
import { loadTreeRules, scanTree } from "../hygiene-tree.mjs";

const source = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const revision = "a1".repeat(20);
const decision = ["ruling", 999].join(" ");
const platform = loadRules();
const policy = loadTreeRules();
const tree = { ...policy, binaries: [], exemptions: [], shas: { ...policy.shas, reviewed: [] } };

function repository(files) {
  const dir = mkdtempSync(path.join(tmpdir(), "hygiene-hardening-"));
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

const scan = (dir) => scanTree("HEAD", { cwd: dir, platform, tree, localOnly: [] });

test("negative examples are plainly reviewable, not Unicode-escaped identifiers", () => {
  const text = readFileSync(path.join(source, "test/hygiene-tree-cases.json"), "utf8");
  assert.doesNotMatch(text, /\\u[0-9a-f]{4}/iu);
  const cases = JSON.parse(text);
  assert.equal(cases.synthetic, true);
  // The only revision-shaped sample is an intentionally repeated pair, never a repository commit.
  for (const c of cases.text) {
    for (const { token } of shaTokens(c.text)) assert.equal(token.toLowerCase(), revision);
  }
});

test("synthetic fixture exemptions cover only the reviewed source lines", () => {
  const file = "scripts/platform/test/hygiene-tree-cases.json";
  const text = readFileSync(path.join(source, "test/hygiene-tree-cases.json"), "utf8");
  const { dir, git, write } = repository({ [file]: text });
  const reviewed = { ...tree, exemptions: policy.exemptions };
  const inspect = () => scanTree("HEAD", { cwd: dir, platform, tree: reviewed, localOnly: [] });
  assert.deepEqual(inspect().hits, []);
  const sample = JSON.parse(text).text.find((c) => c.rules.includes("stream-id")).text;
  write(file, text.replace(sample, `${sample} changed`));
  git("commit", "-qam", "change a fixture");
  assert.ok(inspect().hits.some((h) => h.rule === "stream-id"));
  assert.ok(inspect().hits.some((h) => h.rule === "stale-exemption"));
});

test("revision prefixes separated by dash or underscore, and uppercase revisions, are checked", () => {
  for (const value of [`rev-${revision}`, `sha-${revision.slice(0, 10)}`, `_${revision}`, revision.toUpperCase()]) {
    assert.equal(shaHits("notes.txt", value, tree.shas, new Set()).length, 1, value);
  }
  assert.deepEqual(shaTokens("123e4567-e89b-12d3-a456-426614174000"), [], "a complete UUID is not a commit");
});

test("only the observed package digest keys exempt full SHA-1-shaped values", () => {
  for (const key of ["digest", "checksum", "sha", "gateway_sha", "commit"]) {
    assert.equal(shaHits("fixture.json", JSON.stringify({ [key]: revision }), tree.shas, new Set()).length, 1, key);
  }
  for (const key of ["npm_pack_shasum", "sha1_computed"]) {
    assert.deepEqual(shaHits("fixture.json", JSON.stringify({ [key]: revision }), tree.shas, new Set()), []);
  }
});

test("printable ASCII escapes cannot conceal identifiers in JSON or source text", () => {
  const escaped = String.fromCharCode(92) + "u0072" + decision.slice(1);
  const { dir } = repository({
    "plain.json": JSON.stringify({ text: decision }),
    "escaped.json": `{"text":"${escaped}"}`,
    "escaped.js": `const text = "${escaped}";`,
    "nested.json": JSON.stringify({ rows: [{ text: decision }] }).replace("ruling", String.fromCharCode(92) + "u0072uling")
  });
  const hits = scan(dir).hits;
  assert.ok(hits.some((h) => h.file === "plain.json" && h.rule === "decision-ref"));
  for (const file of ["escaped.json", "escaped.js", "nested.json"]) {
    assert.ok(hits.some((h) => h.file === file && h.rule === "ascii-escape"), file);
  }
});

test("the baseline is a counted fingerprint set, never a rule or path-wide exemption", async () => {
  const { baselineFor, compareBaseline } = await import("../hygiene-baseline.mjs");
  const { dir, git, write } = repository({ "notes.txt": `old ${decision}\n` });
  const before = scan(dir);
  const baseline = baselineFor(before);
  assert.deepEqual(compareBaseline(before, baseline).hits, []);
  assert.ok(!JSON.stringify(baseline).includes(decision));
  write("notes.txt", `new ${decision}\n`);
  git("commit", "-qam", "different context");
  assert.ok(compareBaseline(scan(dir), baseline).hits.some((h) => h.rule === "decision-ref"));
  write("notes.txt", `old ${decision}\nold ${decision}\n`);
  git("commit", "-qam", "duplicate");
  assert.equal(compareBaseline(scan(dir), baseline).hits.filter((h) => h.rule === "decision-ref").length, 1);
  write("notes.txt", "clean\n");
  git("commit", "-qam", "scrub");
  assert.ok(compareBaseline(scan(dir), baseline).hits.some((h) => h.rule === "stale-baseline"), "debt removal requires pruning the baseline");
  assert.throws(() => compareBaseline(before, { version: 1, entries: { bad: -1 } }), /invalid baseline/u);
});

test("the CLI uses the baseline only when explicitly requested; export scans remain strict", async () => {
  const { baselineFor } = await import("../hygiene-baseline.mjs");
  const { dir } = repository({ "notes.txt": `${decision}\n` });
  cpSync(source, path.join(dir, "scripts/platform"), { recursive: true });
  writeFileSync(path.join(dir, "scripts/platform/hygiene-tree-rules.json"), JSON.stringify(tree));
  writeFileSync(path.join(dir, "baseline.json"), JSON.stringify(baselineFor(scan(dir))));
  const cli = (...args) => spawnSync(process.execPath, [path.join(dir, "scripts/platform/hygiene-tree.mjs"), ...args], { cwd: dir, encoding: "utf8" });
  assert.equal(cli("HEAD", "--baseline", path.join(dir, "baseline.json")).status, 0);
  assert.equal(cli("HEAD").status, 1);
  assert.notEqual(cli("HEAD", "--baseline", "missing.json").status, 0);
});

test("fast checks invoke the whole-tree gate before code generation", () => {
  const shell = readFileSync(path.join(source, "check.sh"), "utf8");
  assert.match(shell, /hygiene-tree\.mjs HEAD/u);
  assert.doesNotMatch(shell, /--baseline|HYGIENE_STRICT/u, "fast checks cannot opt out of strict hygiene");
  assert.ok(shell.indexOf("node scripts/platform/hygiene-tree.mjs HEAD") < shell.indexOf('step "1. sha pin"'));
});
