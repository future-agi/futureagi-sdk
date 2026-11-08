import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { renderPython, renderTypeScript } from "../emit-policy.mjs";

const source = {
  source_label: "enterprise customer contract",
  source_digest: `sha256:${"ab".repeat(32)}`,
  scoped: { sha256: "cd".repeat(32) },
};
const model = { operations: [], events: [] };

test("private input provenance emits only a neutral label and content digest", () => {
  for (const render of [renderPython, renderTypeScript]) {
    const text = render(model, source);
    assert.ok(text.includes(source.source_digest));
    assert.ok(text.includes(source.source_label));
    assert.ok(!text.includes('"commit"'));
    assert.ok(!text.includes('"repository"'));
  }
});

test("policy generation refuses legacy private revision fields rather than copying them", () => {
  const legacy = { repository: "private/source", commit: "ef".repeat(20), path: "input.json", sha256: "ab".repeat(32), scoped: source.scoped };
  for (const render of [renderPython, renderTypeScript]) assert.throws(() => render(model, legacy), /provenance|source/i);
  for (const field of ["commit", "revision", "repository", "path", "sha256"]) {
    for (const render of [renderPython, renderTypeScript]) {
      assert.throws(() => render(model, { ...source, [field]: "ef".repeat(20) }), /provenance|source/i);
    }
  }
});

test("the committed private source pin is content addressed", () => {
  const pin = JSON.parse(readFileSync(new URL("../../../openapi/platform/source.json", import.meta.url)));
  assert.match(pin.source_digest ?? "", /^sha256:[a-f0-9]{64}$/);
  assert.equal(pin.source_label, "enterprise customer contract");
  for (const key of ["commit", "revision", "repository", "path", "sha256"]) assert.ok(!(key in pin), key);
});
