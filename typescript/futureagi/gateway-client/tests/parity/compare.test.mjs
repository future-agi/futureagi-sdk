// node --test typescript/futureagi/gateway-client/tests/parity/compare.test.mjs
// The TypeScript comparator against the shared conformance cases and the real
// goldens, and the TS catalog code against what the goldens recorded.
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { compare, compareCases, loadRecording } from "./compare.mjs";
import { LabelError, labelProblems } from "./labels.mjs";

const FIX = fileURLToPath(new URL("../../../../../tests/fixtures/gateway/", import.meta.url));
const read = (name) => JSON.parse(readFileSync(FIX + name, "utf8"));
const INTENDED = read("intended-differences.json").differences;

for (const c of read("comparator-cases.json").cases) {
  test(`conformance: ${c.name}`, () => {
    const r = compareCases(c.golden, c.new, c.intended, c.label);
    assert.deepEqual(
      { ok: r.ok, unlisted: r.unlisted.map((d) => [d.path, d.kind, d.planned]), covered: r.covered, unobserved_proven: r.unobserved_proven, unobserved_planned: r.unobserved_planned },
      c.expect,
    );
  });
}

const golden = (name) => loadRecording(FIX + "golden/" + name).cases;

test("1.0.0 -> 1.0.1 (ESM) is exactly D-01a, D-01b, D-01c", () => {
  const r = compareCases(golden("ts-client-1.0.0-esm"), golden("ts-client-1.0.1-esm"), INTENDED, "ts-client-1.0.0-esm->ts-client-1.0.1-esm");
  assert.equal(r.ok, true, JSON.stringify(r.unlisted.slice(0, 3)));
  assert.deepEqual(Object.keys(r.covered).sort(), ["D-01a", "D-01b", "D-01c"]);
});

test("1.0.0 -> 1.0.1 (CJS) includes D-01d", () => {
  const r = compareCases(golden("ts-client-1.0.0-cjs"), golden("ts-client-1.0.1-cjs"), INTENDED, "ts-client-1.0.0-cjs->ts-client-1.0.1-cjs");
  assert.equal(r.ok, true, JSON.stringify(r.unlisted.slice(0, 3)));
  assert.ok("D-01d" in r.covered);
});

// implementation: a planned entry covers nothing (finding 1), and D-01a matches only
// what 1.0.1 changed, between the two fixed goldens (finding 2).
const tampered = (name, edit) => {
  const cases = structuredClone(golden(name));
  edit(cases);
  return cases;
};
const unlisted = (r) => r.unlisted.map((d) => [d.path, d.kind, d.planned]);

test("a planned entry does not hide a changed Python stream chunk", () => {
  const fresh = tampered("py-agentcc-1.0.0", (c) => {
    c["stream.fixture.normal_stream.iter[sync]"].result.items[0].data.choices[0].delta.content = "TAMPERED";
  });
  const r = compareCases(golden("py-agentcc-1.0.0"), fresh, INTENDED, "py-agentcc-1.0.0->e-new-py");
  assert.equal(r.ok, false);
  assert.deepEqual(r.covered, {});
  assert.deepEqual(unlisted(r), [["stream.fixture.normal_stream.iter[sync]/result/items/0/data/choices/0/delta/content", "changed", ["D-02"]]]);
});

test("D-01a does not cover a dropped stream chunk", () => {
  const fresh = tampered("ts-client-1.0.1-esm", (c) => c["stream.fixture.normal_stream.iter"].result.items.pop());
  const r = compareCases(golden("ts-client-1.0.0-esm"), fresh, INTENDED, "ts-client-1.0.0-esm->ts-client-1.0.1-esm");
  assert.deepEqual(unlisted(r), [["stream.fixture.normal_stream.iter/result/items/2", "removed", []]]);
});

test("D-01 never applies to a new recording judged against 1.0.0", () => {
  const fresh = tampered("ts-client-1.0.0-esm", (c) => {
    c["stream.fixture.normal_stream.iter"].result.items.pop();
    c["stream.malformed.choices_null.final"].result.consumed.drainedError.message = "TAMPERED";
  });
  const r = compareCases(golden("ts-client-1.0.0-esm"), fresh, INTENDED, "ts-client-1.0.0-esm->e-new-ts-esm");
  assert.deepEqual(r.covered, {});
  assert.equal(r.unlisted.length, 2);
});

test("1.0.1 ESM and CJS record the same behaviour", () => {
  const r = compareCases(golden("ts-client-1.0.1-esm"), golden("ts-client-1.0.1-cjs"), [], "x");
  assert.deepEqual(r.unlisted, []);
});

// The twin of test_python_golden_is_current_with_the_catalog_code, for every
// TypeScript golden in catalog.json: a case added or renamed in cases/ without
// re-recording fails here. ts-client-1.0.0-cjs runs no case (its require()
// fails), so it must count every client case as skipped instead.
const CASE_FILES = { client: ["client-core", "client-errors", "client-streams", "client-extras"], integrations: ["integrations"] };
async function catalogIds(target) {
  const ids = [];
  for (const f of CASE_FILES[target]) ids.push(...(await import(`./cases/${f}.mjs`)).cases().map((c) => c.id));
  assert.equal(new Set(ids).size, ids.length, `duplicate case ids in the ${target} catalog`);
  return ids;
}
const TS_GOLDENS = Object.entries(read("catalog.json").goldens).filter(([, g]) => g.lang.startsWith("ts"));

test("every TypeScript golden in the catalog is checked for currency", () => {
  assert.deepEqual(TS_GOLDENS.map(([n]) => n).sort(), ["ts-client-1.0.0-cjs", "ts-client-1.0.0-esm", "ts-client-1.0.1-cjs", "ts-client-1.0.1-esm", "ts-integrations-1.0.0-cjs", "ts-integrations-1.0.0-esm"]);
});

for (const [name, g] of TS_GOLDENS) {
  test(`the ${name} golden is current with the catalog code`, async () => {
    const target = g.lang === "ts-integrations" ? "integrations" : "client";
    const ids = await catalogIds(target);
    const { index } = loadRecording(FIX + "golden/" + name);
    assert.equal(index.environment.target, target);
    assert.equal(index.environment.format, name.slice(-3));
    if (g.runs_cases) {
      assert.deepEqual(index.case_ids, ids);
      assert.equal(index.skipped_load_failed, 0);
    } else {
      assert.deepEqual(index.case_ids, []);
      assert.equal(index.skipped_load_failed, ids.length);
    }
  });
}

// Every method the golden's own surface.runtime tree records for a top-level
// resource has a resource.<name>.<method> case. The tree does not descend into
// sub-resources (chat.completions, audio.*); their cases are listed by name in
// cases/client-core.mjs.
test("the client golden has a case for every recorded resource method", () => {
  const recorded = loadRecording(FIX + "golden/ts-client-1.0.1-esm");
  const { tree } = recorded.cases["surface.runtime"].result;
  const ids = recorded.index.case_ids;
  const missing = [];
  for (const [name, { methods }] of Object.entries(tree)) {
    for (const m of methods) if (m !== "constructor" && !ids.some((id) => id === `resource.${name}.${m}` || id.startsWith(`resource.${name}.${m}.`))) missing.push(`${name}.${m}`);
  }
  assert.deepEqual(missing, []);
});

// implementation, finding 4: a label must describe its two recordings, so a port cannot
// borrow D-01 (proven only between the fixed goldens) by naming 1.0.1 as its new side.
const G = (name) => FIX + "golden/" + name;
const LABEL_D01 = "ts-client-1.0.0-esm->ts-client-1.0.1-esm";
function withCopy(name, edit, fn) {
  const dir = mkdtempSync(join(tmpdir(), "parity-label-"));
  try {
    const dest = join(dir, name);
    cpSync(G(name), dest, { recursive: true });
    if (edit) {
      const file = join(dest, "resources.json");
      const data = JSON.parse(readFileSync(file, "utf8"));
      edit(data.cases);
      writeFileSync(file, JSON.stringify(data));
    }
    return fn(dest);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}
const dropRequest = (cases) => Object.values(cases).find((c) => c.requests?.length).requests.pop();

test("a fresh copy of the 1.0.1 golden passes under the D-01 label", () => {
  withCopy("ts-client-1.0.1-esm", null, (fresh) => {
    const r = compare(G("ts-client-1.0.0-esm"), fresh, FIX + "intended-differences.json", LABEL_D01);
    assert.equal(r.ok, true);
    assert.deepEqual(Object.keys(r.covered).sort(), ["D-01a", "D-01b", "D-01c"]);
  });
});

test("a port recording cannot borrow the D-01 label (API and CLI)", () => {
  withCopy("ts-client-1.0.1-esm", dropRequest, (port) => {
    assert.throws(() => compare(G("ts-client-1.0.0-esm"), port, FIX + "intended-differences.json", LABEL_D01), (e) => e instanceof LabelError && /byte for byte/.test(e.message));
    const cli = spawnSync(process.execPath, [fileURLToPath(new URL("./compare.mjs", import.meta.url)), "--golden", G("ts-client-1.0.0-esm"), "--new", port, "--label", LABEL_D01], { encoding: "utf8" });
    assert.equal(cli.status, 2, cli.stderr);
    assert.match(cli.stderr, /refused/);
  });
});

for (const [golden, label, reason] of [
  ["ts-client-1.0.1-esm", "ts-client-1.0.0-esm->e-new-ts-esm", "not the committed golden"],
  ["ts-client-1.0.0-esm", "ts-client-1.0.0-esm->e-new-ts-esm", "judged against ts-client-1.0.1-esm"],
  ["py-agentcc-1.0.0", "py-agentcc-1.0.0->e-new-ts-esm", "judged against"],
  ["ts-client-1.0.1-cjs", "ts-client-1.0.1-cjs->e-new-ts-esm", "judged against"],
  ["py-agentcc-1.0.0", "py-agentcc-1.0.0->my-port", "neither a golden nor a new recording"],
  ["py-agentcc-1.0.0", "py-agentcc-1.0.0", "is not <golden>-><new>"],
  ["py-agentcc-1.0.0", "agentcc-1.0.0->e-new-py", "is not a golden"],
]) {
  test(`label refused: ${label} on ${golden}`, () => {
    const problems = labelProblems(label, G(golden), G(golden));
    assert.ok(problems.some((p) => p.includes(reason)), JSON.stringify(problems));
    assert.throws(() => compare(G(golden), G(golden), FIX + "intended-differences.json", label), LabelError);
  });
}

test("a modified golden under the golden's name is refused; every documented comparison is accepted", () => {
  withCopy("py-agentcc-1.0.0", dropRequest, (fake) => {
    assert.deepEqual(labelProblems("py-agentcc-1.0.0->e-new-py", fake, G("py-agentcc-1.0.0")), [`--golden ${fake} is not the committed golden py-agentcc-1.0.0`]);
  });
  const catalog = read("catalog.json");
  for (const [fresh, baselines] of Object.entries(catalog.comparisons.new_recordings)) {
    for (const old of baselines) assert.deepEqual(labelProblems(`${old}->${fresh}`, G(old), G(old)), [], `${old}->${fresh}`);
  }
});
