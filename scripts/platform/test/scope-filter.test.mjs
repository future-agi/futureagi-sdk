import assert from "node:assert/strict";
import { test } from "node:test";
import { loadRules, scopeContract } from "../scope-filter.mjs";
import { sha256 } from "../hygiene-names.mjs";
import { structuralFindings } from "../openapi-walk.mjs";
import { SCOPE, sampleContract } from "./fixtures.mjs";

const rules = { ...loadRules(), wording: [] };

test("keeps only scoped operations and the components they reach", () => {
  const { spec, operations } = scopeContract(sampleContract(), SCOPE, rules);
  assert.deepEqual(operations, [
    "platform.things.create POST /workspace/things createThing",
    "platform.things.delete DELETE /workspace/things/{id} deleteThing",
    "platform.things.events GET /workspace/things/{id}/events streamThing",
    "platform.things.list GET /workspace/things listThings"
  ]);
  assert.equal(spec.paths["/workspace/things/{id}"].post, undefined, "human-only operation dropped");
  assert.deepEqual(Object.keys(spec.components.schemas).sort(), ["CreateThing", "Error", "Thing", "ThingFrame", "ThingList", "ThingStarted"]);
  assert.ok(spec.components.schemas.ThingStarted, "frame union members are reached through x-omega-stream and the discriminator");
  assert.deepEqual(Object.keys(spec.components.securitySchemes), ["FiKeyPair"]);
  assert.deepEqual(spec.tags.map((t) => t.name), ["Things"]);
});

test("strips every extension the allowlist does not name, and evidence", () => {
  const { spec } = scopeContract(sampleContract(), SCOPE, rules);
  const create = spec.paths["/workspace/things"].post;
  assert.deepEqual(create["x-omega-idempotency"], { durable: false, keyRequired: true });
  assert.equal(spec.paths["/workspace/things"].get["x-omega-auth-authority"], undefined);
  assert.equal(spec.paths["/workspace/things"].get.responses[404]["x-omega-error-codes"], undefined);
  assert.equal(spec.paths["/workspace/things/{id}/events"].get.responses[200].content["text/event-stream"].schema["x-omega-frames"], undefined);
  assert.equal(spec.components.schemas.Thing.properties.token["x-omega-secret"], true, "schema-level secret kept");
  assert.ok(spec.components.schemas.Thing.properties["x-weird"], "a property named x-... is a name, not an extension");
  assert.equal(spec["x-omega-deferred"], undefined);
  assert.equal(spec.info["x-omega-contract"], undefined);
  assert.deepEqual(structuralFindings(spec, rules), []);
});

test("writes its own info and servers", () => {
  const { spec } = scopeContract(sampleContract(), SCOPE, rules);
  assert.equal(spec.info.version, "1.0.0");
  assert.doesNotMatch(JSON.stringify(spec.info), /internal manifest/u);
  assert.equal(spec.servers[0].url, "/omega/api");
  assert.doesNotMatch(JSON.stringify(spec.servers), /\.invalid/u);
});

test("refuses a human-only, unknown or duplicated scope entry", () => {
  assert.throws(() => scopeContract(sampleContract(), { operations: [...SCOPE.operations, "platform.things.decide"] }, rules), /human-only/u);
  assert.throws(() => scopeContract(sampleContract(), { operations: ["platform.things.nope"] }, rules), /does not have/u);
  assert.throws(() => scopeContract(sampleContract(), { operations: ["platform.things.list", "platform.things.list"] }, rules), /twice/u);
});

test("wording patches are patterns that must match exactly once", () => {
  // a made-up internal document name, hashed into a copy of the rules as the real ones are
  const named = { ...rules, names: { ...rules.names, sha256: { ...rules.names.sha256, [sha256("zz-notes")]: "internal-plan" } } };
  const doc = sampleContract();
  doc.components.schemas.Error.description = "An error (ZZ-NOTES section 3.4).";
  assert.throws(() => scopeContract(doc, SCOPE, named), /hygiene: internal-plan/u);
  const patch = { pointer: "/components/schemas/Error/description", pattern: " \\([A-Z]{2}-[A-Z]{5} section 3\\.4\\)", replace: "$&" };
  const literal = scopeContract(doc, SCOPE, { ...named, wording: [patch] }).spec.components.schemas.Error.description;
  assert.equal(literal, "An error$&.", "the replacement is literal text");
  const patched = { ...named, wording: [{ ...patch, replace: "" }] };
  assert.equal(scopeContract(doc, SCOPE, patched).spec.components.schemas.Error.description, "An error.");
  doc.components.schemas.Error.description = "An error (ZZ-NOTES section 3.4) and (ZZ-NOTES section 3.4).";
  assert.throws(() => scopeContract(doc, SCOPE, patched), /found 2 times/u);
  doc.components.schemas.Error.description = "An error.";
  assert.throws(() => scopeContract(doc, SCOPE, patched), /found 0 times/u);
});

test("a forbidden key in a kept schema fails the build", () => {
  const doc = sampleContract();
  doc.components.schemas.Thing.properties.evidence = { type: "string" };
  doc.components.schemas.Thing.evidence = "leaked";
  assert.throws(() => scopeContract(doc, SCOPE, rules), /forbidden-key/u);
});
