import { describe, expect, it } from "@jest/globals";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const ROOT = join(__dirname, "..", "..");
const TESTS = join(ROOT, "tests");
type Baseline = Record<string, { name: string }[]>;
type Manifest = Record<string, { to: string; shim_tests?: Record<string, string> }>;
const read = (name: string) => JSON.parse(readFileSync(join(TESTS, "port", name), "utf8")).files;
const baseline: Baseline = {
  ...read("vitest-legacy-client.json"),
  ...Object.fromEntries(Object.entries(read("react-vitest-legacy.json")).map(([file, tests]) => [`react/${file}`, tests])),
};
const manifest: Manifest = read("manifest.json");

function assertion(name: string, status = "passed") {
  const parts = name.split(" > ");
  const title = parts.pop()!;
  return { ancestorTitles: parts, title, status };
}

function passingRun() {
  const testResults = Object.entries(baseline)
    .filter(([file]) => manifest[file].to === "port")
    .map(([file, tests]) => ({
      name: join(TESTS, file),
      status: "passed",
      assertionResults: tests.filter((t) => !manifest[file].shim_tests?.[t.name]).map((t) => assertion(t.name)),
    }));
  return { testResults };
}

function check(run: ReturnType<typeof passingRun>) {
  const dir = mkdtempSync(join(tmpdir(), "gateway-test-names-"));
  try {
    const path = join(dir, "synthetic-jest.json");
    writeFileSync(path, JSON.stringify(run));
    const result = spawnSync(process.execPath, [join(ROOT, "scripts", "check-test-names.cjs"), path], { encoding: "utf8" });
    expect(result.error).toBeUndefined();
    return { status: result.status, output: JSON.parse(result.stdout) };
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

describe("original test-name registration", () => {
  it.each([0, 1])("drains large piped JSON before exiting with status %i", async (code) => {
    const { checkPipedDiagnostics } = require("./check-test-names-pipe.cjs");
    await checkPipedDiagnostics(code);
  }, 30000);

  it("accepts intentional one-key tests in new files without baseline entries", () => {
    const run = passingRun();
    for (const file of ["onekey-parity.test.ts", "onekey-refusals.test.ts"]) {
      run.testResults.push({ name: join(TESTS, file), status: "passed", assertionResults: [assertion("new refusal coverage")] });
    }
    const result = check(run);
    expect(result.status).toBe(0);
    expect(result.output.problems).toEqual([]);
    expect(result.output.added).toContain("onekey-parity.test.ts: new refusal coverage");
    expect(result.output.added).toContain("onekey-refusals.test.ts: new refusal coverage");
    expect(result.output.summary.accounted).toBe(result.output.summary.baseline_tests);
  });

  it("requires explicit added registration inside an existing ported file", () => {
    const run = passingRun();
    run.testResults[0].assertionResults.push(assertion("new refusal coverage"));
    const result = check(run);
    expect(result.status).toBe(1);
    expect(result.output.problems).toEqual([expect.stringContaining("the manifest does not list it under added")]);
  });

  it("rejects a missing original test", () => {
    const run = passingRun();
    run.testResults[0].assertionResults.pop();
    const result = check(run);
    expect(result.status).toBe(1);
    expect(result.output.problems).toContainEqual(expect.stringContaining("1.0.1 tests missing"));
  });

  it("rejects reordered original tests", () => {
    const run = passingRun();
    const suite = run.testResults.find((s) => s.assertionResults.length > 1)!;
    suite.assertionResults.reverse();
    const result = check(run);
    expect(result.status).toBe(1);
    expect(result.output.problems).toEqual([expect.stringContaining("the 1.0.1 tests run in another order")]);
  });

  it("rejects a failed new test rather than treating the added list as a failure", () => {
    const run = passingRun();
    run.testResults.push({
      name: join(TESTS, "onekey-parity.test.ts"), status: "failed",
      assertionResults: [assertion("new refusal coverage", "failed")],
    });
    const result = check(run);
    expect(result.status).toBe(1);
    expect(result.output.problems).toEqual(['onekey-parity.test.ts: "new refusal coverage" failed']);
  });
});
