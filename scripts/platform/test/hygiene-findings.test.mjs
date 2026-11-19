import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { BASELINE_KIND, baselineFor, compareBaseline } from "../hygiene-baseline.mjs";
import { classOf, findingsList, reasonFor } from "../hygiene-findings.mjs";
import { sha256 } from "../hygiene-names.mjs";
import { loadRules } from "../hygiene-scan.mjs";
import { TREE_RULES_FILE, loadTreeRules, scanTree } from "../hygiene-tree.mjs";

const source = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const cases = JSON.parse(readFileSync(path.join(source, "test/hygiene-tree-cases.json"), "utf8"));
// A synthetic stream id from the reviewed case table, never written here as a literal.
const STREAM_SAMPLE = cases.text.find((c) => c.rules.includes("stream-id")).text;
const platform = loadRules();
const policy = loadTreeRules();
const tree = { ...policy, binaries: [], exemptions: [], shas: { ...policy.shas, reviewed: [] } };

function repository(files) {
  const dir = mkdtempSync(path.join(tmpdir(), "hygiene-findings-"));
  const git = (...args) =>
    execFileSync("git", ["-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false", ...args], {
      cwd: dir,
      encoding: "utf8",
      env: { ...process.env, GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" }
    }).trim();
  git("init", "-q");
  for (const [file, content] of Object.entries(files)) {
    mkdirSync(path.dirname(path.join(dir, file)), { recursive: true });
    writeFileSync(path.join(dir, file), content);
  }
  git("add", "-A");
  git("commit", "-q", "-m", "base");
  return dir;
}

const LEAK_PATH = `docs/${STREAM_SAMPLE.replaceAll(" ", "-")}.md`;
const FILES = {
  "docs/a.md": `clean\n${STREAM_SAMPLE}\n`,
  "assets/x.bin": Buffer.from([0, 1, 2]),
  [LEAK_PATH]: "clean\n",
  "python/fi/generated/x.py": `# ${STREAM_SAMPLE}\n`
};

test("every rule a scan can report has a class and a reason", () => {
  const ids = new Set([
    ...platform.patterns.map((p) => p.id),
    ...policy.patterns.map((p) => p.id),
    ...Object.values(platform.names.sha256),
    ...Object.values(policy.names.sha256)
  ]);
  // The ids the scanning modules emit themselves, read from their sources so a new one cannot be missed.
  for (const file of readdirSync(source).filter((f) => f.endsWith(".mjs"))) {
    for (const m of readFileSync(path.join(source, file), "utf8").matchAll(/\brule: "([a-z][a-z-]*)"/gu)) ids.add(m[1]);
  }
  for (const id of ["unreviewed-sha", "binary-unreviewed", "stale-baseline", "forbidden-key"]) assert.ok(ids.has(id), id);
  for (const id of ids) {
    assert.notEqual(classOf(id), "other", id);
    assert.notEqual(reasonFor(id, { platform, tree: policy }), "a rule without a recorded reason", id);
  }
  assert.equal(classOf("not-a-rule"), "other");
  assert.equal(reasonFor("stream-id", { platform, tree: policy }), policy.patterns.find((p) => p.id === "stream-id").about);
});

test("the findings list gives path, line, class, rule and reason for every strict hit, in order", () => {
  const dir = repository(FILES);
  const scan = scanTree("HEAD", { cwd: dir, platform, tree, localOnly: [] });
  const list = findingsList(scan, { platform, tree });
  assert.deepEqual([list.version, list.kind, list.mode, list.commit, list.tree, list.files], [1, "hygiene-findings", "strict", scan.commit, scan.tree, 4]);
  assert.equal(list.total, scan.hits.length);
  assert.deepEqual(list.findings.map((f) => [f.path, f.line, f.target, f.class, f.rule, f.generated]), [
    ["assets/x.bin", 0, "file", "unreviewed-file", "binary-unreviewed", false],
    ["docs/a.md", 2, "content", "internal-reference", "stream-id", false],
    [LEAK_PATH, 0, "path", "internal-reference", "stream-id", false],
    ["python/fi/generated/x.py", 1, "content", "internal-reference", "stream-id", true]
  ]);
  assert.deepEqual(list.byClass, { "unreviewed-file": 1, "internal-reference": 3 });
  const [binary, content, named, generated] = list.findings;
  assert.equal(content.lineSha256, sha256(STREAM_SAMPLE), "the key an exact-line exemption would use");
  assert.ok(STREAM_SAMPLE.includes(content.match) && content.match.length > 0);
  assert.equal(content.reason, policy.patterns.find((p) => p.id === "stream-id").about);
  assert.equal(content.fix, "rewrite or remove the text");
  assert.equal(named.fix, "rename the path");
  assert.equal(named.lineSha256, null);
  assert.match(binary.fix, /sha256 of its bytes/u);
  assert.match(generated.fix, /generator's input/u);
  for (const f of list.findings) assert.deepEqual(Object.keys(f), ["path", "line", "target", "class", "rule", "reason", "match", "lineSha256", "generated", "fix"]);
});

test("the command line writes the strict list even under a debt baseline, and labels the ratchet as debt", () => {
  const dir = repository({ "docs/a.md": `${STREAM_SAMPLE}\n` });
  cpSync(source, path.join(dir, "scripts/platform"), { recursive: true });
  writeFileSync(path.join(dir, TREE_RULES_FILE), JSON.stringify(tree));
  const strict = scanTree("HEAD", { cwd: dir, platform, tree, localOnly: [] });
  assert.equal(strict.hits.length, 1);
  const baseline = path.join(dir, "baseline.json");
  writeFileSync(baseline, JSON.stringify(baselineFor(strict)));
  const cli = (...args) => spawnSync(process.execPath, [path.join(dir, "scripts/platform/hygiene-tree.mjs"), ...args], { cwd: dir, encoding: "utf8" });
  const findings = path.join(dir, "findings.json");
  const ratchet = cli("HEAD", "--baseline", baseline, "--findings", findings);
  assert.equal(ratchet.status, 0, ratchet.stderr);
  assert.match(ratchet.stdout, /DEBT RATCHET: 1 known hit\(s\) carried by .*, not resolved; not publication clearance/u);
  assert.match(ratchet.stdout, /0 hit\(s\) \(0 in generated files; debt ratchet, 1 strict\)/u);
  const list = JSON.parse(readFileSync(findings, "utf8"));
  assert.deepEqual([list.mode, list.total, list.findings[0].path, list.findings[0].rule], ["strict", 1, "docs/a.md", "stream-id"]);
  const plain = cli("HEAD", "--findings", path.join(dir, "strict.json"));
  assert.equal(plain.status, 1);
  assert.match(plain.stdout, /1 hit\(s\) \(0 in generated files; strict\)/u);
});

test("a baseline is labelled as debt, and one without the label is refused", () => {
  const dir = repository({ "docs/a.md": `${STREAM_SAMPLE}\n` });
  const scan = scanTree("HEAD", { cwd: dir, platform, tree, localOnly: [] });
  const baseline = baselineFor(scan);
  assert.equal(baseline.kind, BASELINE_KIND);
  assert.match(baseline.note, /Not publication clearance/u);
  const compared = compareBaseline(scan, baseline);
  assert.deepEqual([compared.mode, compared.hits.length, compared.baseline.kind, compared.baseline.carried], ["debt-ratchet", 0, BASELINE_KIND, 1]);
  const { kind: _kind, ...unlabelled } = baseline;
  assert.throws(() => compareBaseline(scan, unlabelled), /kind "hygiene-debt"/u);
  assert.equal(readdirSync(source).includes("hygiene-tree-baseline.json"), false, "no debt baseline is committed");
});
