import assert from "node:assert/strict";
import { test } from "node:test";
import { contentDigest, pinInput, sourceProvenance, verifyInput } from "../source-pin.mjs";

test("rebuilding projects legacy metadata to content provenance and verifies exact bytes", () => {
  const bytes = Buffer.from('{"openapi":"3.1.0"}\n');
  const legacy = { commit: "ef".repeat(20), repository: "private/source", path: "contract.json", sha256: contentDigest(bytes).slice(7), pinned: "2026-10-28" };
  const pin = pinInput(legacy, bytes, bytes);
  assert.deepEqual(sourceProvenance(pin), { source_label: "enterprise customer contract", source_digest: contentDigest(bytes) });
  assert.equal(JSON.stringify(pin).includes(legacy.commit), false);
  assert.equal(JSON.stringify(pin).includes(legacy.repository), false);
  verifyInput(pin, bytes);
  assert.throws(() => verifyInput(pin, Buffer.from("changed")), /digest mismatch/);
  assert.throws(() => pinInput(pin, Buffer.from("changed"), bytes), /digest mismatch/);
  assert.throws(() => sourceProvenance({ ...pin, commit: legacy.commit }), /provenance/);
});
