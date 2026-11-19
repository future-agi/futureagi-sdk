// node --test typescript/futureagi/gateway-client/tests/parity/onekey-labels.test.mjs
import assert from "node:assert/strict";
import { test } from "node:test";
import labels from "./onekey-labels.cjs";

for (const code of ["managed_model_unpriced", "managed_model_ambiguous", "managed_resource_unsupported"]) {
  test(`${code} documents raw preservation and guarded accessors`, () => {
    assert.equal(labels.metadataAccess(code), "error.metadata retains unknown keys; model/candidates getters are type-guarded (null when absent or invalid)");
    assert.match(labels.metadataAccessJustification(code), /Both languages retain unknown metadata keys and type-guard model\/candidates/);
    assert.match(labels.metadataAccessJustification(code), /null instead of Python snake_case properties and None/);
  });
}

test("other refusal rows keep the generic accessor description", () => {
  for (const code of ["insufficient_credits", "managed_billing_unavailable", "managed_model_unpriced_extra", null, undefined]) {
    assert.equal(labels.metadataAccess(code), "error.metadata (Record<string, unknown>) and read-only camelCase getters; null when absent");
    assert.equal(labels.metadataAccessJustification(code), "TypeScript record, null and camelCase getters instead of Python dict, None and snake_case properties.");
  }
});

test("ancestry documentation matches omission of anonymous mixin layers", () => {
  class StatusError extends Error {}
  const mixin = (Base) => class extends Base {};
  class RefusalError extends mixin(StatusError) {}
  const error = new RefusalError();
  assert.equal(Object.getPrototypeOf(Object.getPrototypeOf(error)).constructor.name, "");
  assert.deepEqual(labels.namedAncestry(error), ["StatusError", "Error"]);
  assert.deepEqual(labels.namedAncestry(new Error()), []);
  assert.match(labels.ancestryJustification, /only named ancestry is reported/);
  assert.match(labels.ancestryJustification, /anonymous mixin layers are omitted/);
});

test("post-header difference scopes terminal errors to successful SDK-consumed bodies", () => {
  const row = labels.postHeaderBodyFailureDifference;
  assert.equal(row.field, "post_header_body_failure_evidence");
  assert.match(row.typescript, /terminal ResponseBodyError/);
  assert.match(row.typescript, /not APIConnectionError/);
  assert.match(row.typescript, /no automatic replay, even with a per-error retry policy/);
  assert.match(row.typescript, /partial streams are never replayed/);
  assert.match(row.typescript, /successful SDK-consumed JSON responses \(2xx\/246\)/);
  assert.match(row.typescript, /StreamError/);
  assert.match(row.typescript, /Caller-owned raw native readers/);
  assert.equal(row.python, "Python follows the same shared rule (Python parity table r6d); no Python runtime verification is claimed here.");
  assert.equal(row.justification, "Post-header body failures: when the SDK itself reads and decodes a successful (2xx or 246) response body - JSON, or a binary body the SDK reads for the caller - and that read or decode fails after the response headers arrived, the SDK raises a terminal error that keeps the captured gateway evidence and never replays the request automatically, under any retry policy. Error-status responses (4xx/5xx) keep their status- and header-driven retry rules even when their body cannot be read. Partial streams are never replayed; caller-owned raw readers belong to the caller.");
  assert.equal(Object.isFrozen(row), true);
});
