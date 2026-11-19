/**
 * The behaviour kept from @agentcc/client 1.0.1 that only an SDK gives is held
 * by named tests (kept-behaviours.json):
 * every item names at least one test, and every named test still exists in
 * its file, so the map cannot go stale silently. The tests themselves run in
 * this suite.
 */
import { describe, it, expect } from "@jest/globals";
import { readFileSync } from "node:fs";
import { join } from "node:path";

interface Ref {
  file: string;
  title: string;
}
const ROOT = join(__dirname, "..", "..");
const MAP = JSON.parse(readFileSync(join(__dirname, "kept-behaviours.json"), "utf8")) as {
  items: Record<string, { behaviour: string; tests: Ref[]; follow_up?: string }>;
};

describe("kept behaviours map", () => {
  it("covers the five kept behaviours, each with at least one test", () => {
    expect(Object.keys(MAP.items)).toEqual(["stream_error_frames", "request_header_helpers", "response_metadata_readers", "stream_usage", "sdk_headers_not_read"]);
    for (const item of Object.values(MAP.items)) expect(item.tests.length).toBeGreaterThan(0);
  });

  const refs = Object.entries(MAP.items).flatMap(([id, item]) => item.tests.map((t) => [id, t.file, t.title] as const));
  it.each(refs)("%s: %s has the test %s", (_id, file, title) => {
    const source = readFileSync(join(ROOT, file), "utf8");
    expect(source.includes(JSON.stringify(title)) || source.includes(`"${title}"`) || source.includes(`'${title}'`) || source.includes(`\`${title}\``)).toBe(true);
  });
});
