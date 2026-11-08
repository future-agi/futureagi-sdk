import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { test } from "node:test";
import { checkModuleSizes, countLines } from "../lint/module-size.mjs";
import { findUrlPaths } from "../lint/no-url-paths.mjs";
import { applyBaseline } from "../lint/tsdoc-coverage.mjs";

function tree(files) {
  const dir = mkdtempSync(path.join(tmpdir(), "lint-"));
  for (const [rel, text] of Object.entries(files)) {
    mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
    writeFileSync(path.join(dir, rel), text);
  }
  return dir;
}

test("module-size counts like an editor and exempts generated code", () => {
  assert.equal(countLines("a\nb\n"), 2);
  assert.equal(countLines(""), 0);
  const dir = tree({ "src/big.py": "x\n".repeat(401), "src/ok.ts": "x\n".repeat(400), "src/generated/huge.ts": "x\n".repeat(900) });
  const { files, over, absent } = checkModuleSizes(["src", "missing"], dir);
  assert.equal(files, 2);
  assert.deepEqual(over, [{ file: "src/big.py", lines: 401 }]);
  assert.deepEqual(absent, ["missing"]);
});

test("no-url-paths finds a hand-written route but not a comment, test or generated file", () => {
  const dir = tree({
    "fi/x/_client.py": 'PATH = "/workspace/sandboxes"\n# "/workspace/in-a-comment"\n',
    "fi/x/test_x.py": 'PATH = "/workspace/sandboxes"\n',
    "fi/x/generated/policy.py": 'PATH = "/workspace/sandboxes"\n',
    "src/y/client.ts": "const p = `/omega/api/workspace`;\n"
  });
  const { hits } = findUrlPaths(["fi", "src"], dir);
  assert.deepEqual(hits.map((h) => `${h.file}:${h.line}`), ["fi/x/_client.py:1", "src/y/client.ts:1"]);
});

test("no-url-paths allows the bare /omega/api mount and skips test fixtures", () => {
  const dir = tree({
    "src/_core/origins.ts": 'export const PLATFORM_PATH = "/omega/api";\n',
    "src/_core/client.ts": 'const p = "/omega/api/workspace/x";\n',
    "src/_core/__fixtures__/platform.ts": 'path: "/workspace/sandboxes",\n',
    "fi/_core/_client.py": 'PATH = "/agentcc/api-keys"\n'
  });
  const { hits } = findUrlPaths(["src", "fi"], dir);
  assert.deepEqual(hits.map((h) => `${h.file}:${h.line}`), ["src/_core/client.ts:1", "fi/_core/_client.py:1"]);
});

test("tsdoc baseline: a listed gap is known, a new gap fails, a fixed gap must leave the list", () => {
  const baseline = { "src/_core/index.ts": ["Page.items", "Handle.id"] };
  const now = { "src/_core/index.ts": ["Page.items", "Run.wait"], "src/runs/index.ts": ["Run.cancel"] };
  assert.deepEqual(applyBaseline(now, baseline), {
    failures: ["src/_core/index.ts: Run.wait", "src/runs/index.ts: Run.cancel"],
    known: ["src/_core/index.ts: Page.items"],
    stale: ["src/_core/index.ts: Handle.id"]
  });
  assert.deepEqual(applyBaseline({ "src/_core/index.ts": [] }, {}), { failures: [], known: [], stale: [] });
});
