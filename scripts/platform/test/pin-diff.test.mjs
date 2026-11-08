import assert from "node:assert/strict";
import { test } from "node:test";
import { diffPins } from "../pin-diff.mjs";
import { buildPolicy, policyCounts, retryClass } from "../policy-model.mjs";
import { SCOPE, sampleContract } from "./fixtures.mjs";

test("retry classes follow the contract", () => {
  assert.equal(retryClass("POST", true, true), "keyed");
  assert.equal(retryClass("POST", true, null), "keyed");
  assert.equal(retryClass("POST", true, false), "keyed-not-durable");
  assert.equal(retryClass("DELETE", false, null), "http-idempotent");
  assert.equal(retryClass("PATCH", false, null), "unsafe");
  const counts = policyCounts(buildPolicy(sampleContract()).operations);
  assert.deepEqual(
    { k: counts.keyed, nd: counts["keyed-not-durable"], h: counts["http-idempotent"], u: counts.unsafe, s: counts.streams, p: counts.paginated },
    { k: 0, nd: 1, h: 3, u: 1, s: 1, p: 1 }
  );
});

test("the policy carries secrets, stream frames and the not-found rule", () => {
  const ops = Object.fromEntries(buildPolicy(sampleContract()).operations.map((o) => [o.name, o]));
  assert.deepEqual(ops["platform.things.create"].secret_fields, ["response.token"]);
  assert.equal(ops["platform.things.create"].key_required, true);
  assert.deepEqual(ops["platform.things.events"].stream.known_events, ["started"]);
  assert.equal(ops["platform.things.delete"].not_found_means_applied, true);
  assert.equal(ops["platform.things.list"].pagination.items_field, "things");
});

test("an identical pin has no changes", () => {
  const { added, removed, changes } = diffPins(sampleContract(), sampleContract(), SCOPE);
  assert.deepEqual([added, removed, changes], [[], [], []]);
});

test("breaking and additive changes are labelled", () => {
  const next = sampleContract();
  delete next.paths["/workspace/things/{id}"].delete;
  next.paths["/workspace/things"].get.parameters.push({ name: "limit", in: "query" });
  next.paths["/workspace/things"].post["x-omega-idempotency"].durable = true;
  next.paths["/workspace/things/{id}/events"].get["x-omega-stream"].kind = "sse-post";
  next.paths["/workspace/new"] = { get: { "x-omega-sdk": { family: "platform", method: "new.get" }, responses: {} } };
  const { added, removed, changes } = diffPins(sampleContract(), next, SCOPE);
  assert.deepEqual(added, ["platform.new.get"]);
  assert.deepEqual(removed, [{ name: "platform.things.delete", verdict: "BREAKING" }]);
  const byField = Object.fromEntries(changes.map((c) => [`${c.name} ${c.field}`, c.verdict]));
  assert.equal(byField["platform.things.list query"], "additive");
  assert.equal(byField["platform.things.create durable"], "additive");
  assert.equal(byField["platform.things.events stream"], "BREAKING");
});

test("losing durability or the idempotency flag is breaking; out-of-scope changes never are", () => {
  const before = sampleContract();
  before.paths["/workspace/things"].post["x-omega-idempotency"].durable = true;
  const after = sampleContract();
  const verdict = diffPins(before, after, SCOPE).changes.find((c) => c.field === "durable").verdict;
  assert.equal(verdict, "BREAKING");
  const dropped = sampleContract();
  dropped.paths["/workspace/things"].post["x-omega-idempotent"] = false;
  assert.ok(diffPins(sampleContract(), dropped, SCOPE).changes.some((c) => c.field === "idempotent" && c.verdict === "BREAKING"));
  assert.ok(diffPins(sampleContract(), dropped, { operations: ["platform.things.list"] }).changes.every((c) => c.verdict === "out-of-scope"));
});
