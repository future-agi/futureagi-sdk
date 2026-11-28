import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { buildHistory } from "../public-history.mjs";
import { fixture, map } from "./history-fixture.mjs";

const trailer = "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>";

test("every module commit ends with exactly the reviewed attribution trailer", (t) => {
  // The cloud checkpoint supplies the actual external reviewed map; ordinary runs exercise the same contract.
  const reviewed = process.env.PUBLIC_HISTORY_MODULE_MAP
    ? JSON.parse(readFileSync(process.env.PUBLIC_HISTORY_MODULE_MAP, "utf8"))
    : { ...map, trailers: [trailer] };
  assert.deepEqual(reviewed.trailers, [trailer]);
  const { dir, git, base } = fixture(t);
  const blob = git("rev-parse", "qualified:docs/guide.md");
  // Exercise every module, including groups that happen to be empty in any particular candidate.
  const groups = reviewed.modules.map((_, i) => [{ path: `module-${i}.txt`, mode: "100644", oid: blob, deleted: false }]);
  const commits = buildHistory(dir, { ontoCommit: base, groups, ...reviewed });
  assert.equal(commits.length, reviewed.modules.length);
  for (const { commit } of commits) {
    const message = git("show", "-s", "--format=%B", commit);
    assert.equal(message.split("\n").at(-1), trailer);
    assert.deepEqual(message.split("\n").filter((line) => /^Co-Authored-By:/iu.test(line)), [trailer]);
  }
});
