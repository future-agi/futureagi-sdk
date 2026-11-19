// node --test typescript/futureagi/gateway-client/tests/parity/hygiene.test.mjs
// No golden carries a local path (implementation, finding 1): the frame normalisation
// in harness/observe.mjs, the write-time guard in harness/hygiene.mjs against the
// shared conformance cases, and a scan of every committed golden.
import assert from "node:assert/strict";
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { LocalPathError, leaks, leaksIn, recorderRoots, writeChecked } from "./harness/hygiene.mjs";
import { clean, dump } from "./harness/observe.mjs";

const FIX = fileURLToPath(new URL("../../../../../tests/fixtures/gateway/", import.meta.url));
// Built here, so the repository never holds a local path literal.
const expand = (s) => s.replace(/\{(\w+)\}/g, (_, n) => (n === "file" ? "file:" + "//" : "/" + n));
const FILE_URL = "file:" + "//";
const VOLUMES = "/" + "Volumes";

for (const c of JSON.parse(readFileSync(FIX + "hygiene-cases.json", "utf8")).cases) {
  test(`conformance: ${c.name}`, () => {
    assert.deepEqual(leaks(expand(c.text), (c.roots ?? []).map(expand)), c.expect.map(expand));
  });
}

const REACT_LINE = (loc) =>
  `The above error occurred in the <Bare> component:\n\n    at Bare (${loc})\n\nConsider adding an error boundary to your tree to customize error handling behavior.`;

test("clean() replaces a whole frame location, line and column included", () => {
  const esm = REACT_LINE(`${FILE_URL}${VOLUMES}/example/checkout/typescript/cases/integrations.mjs:84:71`);
  const moved = REACT_LINE(`${FILE_URL}/srv/elsewhere/cases/integrations.mjs:90:3`);
  assert.equal(clean(esm), REACT_LINE("<frame>"));
  assert.equal(clean(moved), clean(esm), "another checkout or an edit above the line changes nothing");
  assert.deepEqual(leaks(esm), [FILE_URL, VOLUMES + "/"], "the raw line is what the guard refuses");
  assert.deepEqual(leaks(clean(esm)), []);
});

test("clean() covers CJS, node: and bare frames and leaves times and URLs alone", () => {
  assert.equal(clean("at f (/srv/x/dist/index.js:12:5)"), "at f (<frame>)");
  assert.equal(clean("at process.tick (node:internal/process/task_queues:95:5)"), "at process.tick (<frame>)");
  assert.equal(clean("    at /srv/x/y.js:3:4"), "    at <frame>");
  assert.equal(clean("at async Promise.all (index 0)"), "at async Promise.all (index 0)");
  assert.equal(clean("2025-10-23T00:00:05Z (2025-10-23T00:00:05)"), "2025-10-23T00:00:05Z (2025-10-23T00:00:05)");
  assert.equal(clean("GET https://gateway.example.test/v1/models"), "GET https://gateway.example.test/v1/models");
  assert.equal(clean("/srv/x/node_modules/react/index.js"), "<path>/node_modules/react/index.js");
});

test("writeChecked refuses a leaking value and writes nothing", () => {
  const dir = mkdtempSync(join(tmpdir(), "parity-hygiene-"));
  try {
    const file = join(dir, "area.json");
    const data = { cases: { c: { console: [["error", `at Bare (${FILE_URL}/srv/a/b.mjs:1:2)`]] } } };
    assert.throws(() => writeChecked(file, data, []), (err) => err instanceof LocalPathError && /cases\/c\/console\/0\/1/.test(err.message));
    assert.equal(existsSync(file), false);
    const roots = recorderRoots(dir);
    assert.throws(() => writeChecked(file, { out: join(dir, "x") }, roots), LocalPathError, "the output directory is a root");
    assert.throws(() => writeChecked(file, { cwd: process.cwd() }, roots), LocalPathError, "so is the working directory");
    assert.throws(() => writeChecked(file, { [`${FIX}x`]: 1 }, roots), LocalPathError, "a key is checked too");
    const ok = { cases: { c: { console: [["error", clean(`at Bare (${FILE_URL}/srv/a/b.mjs:1:2)`)]] } } };
    assert.equal(writeChecked(file, ok, roots), dump(ok));
    assert.equal(readFileSync(file, "utf8"), dump(ok));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

function goldenFiles(dir = join(FIX, "golden")) {
  return readdirSync(dir).sort().flatMap((n) => (statSync(join(dir, n)).isDirectory() ? goldenFiles(join(dir, n)) : n.endsWith(".json") ? [join(dir, n)] : []));
}

test("the integrations golden records React's component stack as at Bare (<frame>)", () => {
  const { cases } = JSON.parse(readFileSync(join(FIX, "golden/ts-integrations-1.0.0-esm/integrations.json"), "utf8"));
  for (const kind of ["chat", "completion", "object"]) {
    const [[level, line]] = cases[`integration.react.${kind}`].console;
    assert.equal(level, "error");
    assert.ok(line.includes("\n    at Bare (<frame>)\n"), line);
  }
});

test("no committed golden carries a local path", () => {
  const files = goldenFiles();
  assert.ok(files.length > 50, `found ${files.length} golden files`);
  const found = files.flatMap((f) => leaksIn(JSON.parse(readFileSync(f, "utf8")), [], f.slice(FIX.length)));
  assert.deepEqual(found, []);
});
