import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
const read = (file) => JSON.parse(readFileSync(new URL(`../../../${file}`, import.meta.url)));

test("connector snapshots and wrapper maps expose only content provenance", () => {
  const source = read("openapi/connectors/source.json");
  assert.deepEqual(read("openapi/connectors/wrapper-map.json").sources, source);
  for (const pin of Object.values(source)) {
    assert.match(pin.source_digest ?? "", /^sha256:[a-f0-9]{64}$/);
    assert.ok(pin.source_label);
    assert.ok(!("commit" in pin));
    assert.ok(!("path" in pin));
  }
  assert.deepEqual(Object.keys(read("openapi/connectors/ee.json").info).sort(), ["title", "version"]);
});
