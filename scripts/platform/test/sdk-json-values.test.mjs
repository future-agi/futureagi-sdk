import assert from "node:assert/strict";
import test from "node:test";
import { normalize } from "../../normalize-sdk-json-values.mjs";

test("upstream JSON values retain primitives, arrays, objects and null", () => {
  const converted = normalize({ properties: { input: { type: "object", "x-json-value": true },
    requiredInput: { type: "object", "x-json-value": true, nullable: false } } });
  const input = converted.properties.input.anyOf;
  assert.deepEqual(input.map(schema => schema.type), ["boolean", "number", "string", "array", "object"]);
  assert.equal(input.at(-1).nullable, true);
  assert.equal(converted.properties.requiredInput.anyOf.at(-1).nullable, undefined);
  assert.deepEqual(normalize(converted), converted);
});

test("public descriptions retain behavior without private tracker references", () => {
  const ticket = "T" + "H" + "-" + "8057";
  assert.equal(normalize({ description: `Deleted calls are included (${ticket}).` }).description,
    "Deleted calls are included.");
  assert.equal(normalize({ operationId: ticket }).operationId, ticket);
});

test("nullable enums retain a single null value", () => {
  const schema = { type: "string", nullable: true, enum: ["one"] };
  assert.deepEqual(normalize(schema).enum, ["one", null]);
  assert.deepEqual(normalize(normalize(schema)), normalize(schema));
});
