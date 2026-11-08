/**
 * intended-differences-ts.json: every listed difference names tests that
 * still exist, and no id clashes with the shared list
 * (tests/fixtures/gateway/intended-differences.json).
 */
import { describe, it, expect } from "@jest/globals";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const ROOT = join(__dirname, "..", "..");
const LIST = JSON.parse(readFileSync(join(__dirname, "intended-differences-ts.json"), "utf8")) as {
  differences: Array<{ id: string; lang: string; status: string; summary: string; golden_cases: unknown; tests: Array<{ file: string; title: string }> }>;
};
const SHARED = JSON.parse(readFileSync(join(ROOT, "..", "..", "..", "tests", "fixtures", "gateway", "intended-differences.json"), "utf8")) as {
  differences: Array<{ id: string }>;
};

describe("TypeScript intended differences", () => {
  it("lists D-06b, D-11b, D-14b and D-16b, each landed with a summary, golden cases and tests", () => {
    expect(LIST.differences.map((d) => d.id)).toEqual(["D-06b", "D-11b", "D-14b", "D-16b"]);
    for (const d of LIST.differences) {
      expect([d.id, d.lang, d.status]).toEqual([d.id, "ts", "landed"]);
      expect(d.summary.length).toBeGreaterThan(40);
      expect(d.golden_cases).toBeDefined();
      expect(d.tests.length).toBeGreaterThan(0);
    }
  });

  it("no id is already in the shared list", () => {
    const shared = new Set(SHARED.differences.map((d) => d.id));
    expect(LIST.differences.filter((d) => shared.has(d.id)).map((d) => d.id)).toEqual([]);
  });

  const refs = LIST.differences.flatMap((d) => d.tests.map((t) => [d.id, t.file, t.title] as const));
  it.each(refs)("%s: %s has the test %s", (_id, file, title) => {
    expect(readFileSync(join(ROOT, file), "utf8")).toContain(JSON.stringify(title));
  });
});
