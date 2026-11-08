import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { loadCases, MUST_EXIST } from "../lib/cases.mjs";
import { buildContract, SCOPED_CONTRACT } from "../lib/contract.mjs";
import { validateSuite } from "../validate.mjs";

const scope = JSON.parse(readFileSync(new URL("../../../openapi/platform/scope.json", import.meta.url)));
const contract = buildContract({ openapi: JSON.parse(readFileSync(SCOPED_CONTRACT)), scope });
const cases = loadCases().cases;
const sdkOperations = [...contract.operations.values()].map((o) => ({ name: `${o.sdk.family}.${o.sdk.method}`, method: o.method, path: o.path }));
const originals = ["must-exist.host-guard.fi-keypair", "must-exist.host-guard.env-switches-ignored", "must-exist.planted-secret.scan", "gateway.credential-in-query", "gateway.mixed-credentials", "gateway.anonymous.forged-tenant-headers"];
const offered = originals.map((id) => `${id}.offered`);
const validate = (input) => validateSuite({ contract, cases: input, sdkOperations });

test("every security mechanism has a validated offered counterpart with the same payload and expectation", () => {
  const result = validate(cases);
  assert.equal(result.ok, true);
  for (const [index, id] of originals.entries()) {
    const original = cases.find((c) => c.id === id);
    const twin = cases.find((c) => c.id === offered[index]);
    assert.ok(twin, `${id} needs an offered counterpart`);
    for (const key of ["client", "call", "expect", "tenant", "modes", "runners", "tags"]) assert.deepEqual(twin[key], original[key], `${id}: ${key}`);
    const validated = result.perCase.find((c) => c.id === twin.id);
    assert.equal(validated.documented, true);
    assert.deepEqual(validated.errors, []);
    assert.ok(result.securityMustExist.includes(twin.id));
  }
  assert.equal(result.securityMustExist.length, 6);
  assert.ok(result.securityMustExist.every((id) => !result.notOffered.cases.some((c) => c.id === id)));
});

test("absence alone never clears a mandatory security mechanism", () => {
  const result = validate(cases.filter((c) => !offered.includes(c.id)));
  assert.equal(result.ok, false);
  assert.equal(result.securityMustExist.length, 0);
  assert.ok(result.securityErrors.length >= 6);
});

test("invalid security SDK vehicles fail even in the hidden scope", () => {
  // Preserve the original probe: changing only the three original must-exist vehicles must fail.
  const probeIds = originals.slice(0, 3);
  const result = validate(cases.map((c) => probeIds.includes(c.id) ? { ...c, sdk: { ...c.sdk, method: "missingSecurityVehicle" } } : c));
  assert.equal(result.ok, false);
  for (const id of probeIds) assert.ok(result.failing.some((c) => c.id === id), id);
  const offeredProbe = validate(cases.map((c) => offered.includes(c.id) ? { ...c, sdk: { ...c.sdk, method: "missingSecurityVehicle" } } : c));
  assert.equal(offeredProbe.ok, false);
  assert.equal(offeredProbe.securityMustExist.length, 0);
});

test("NOT-OFFERED counterparts are hard security errors rather than validation credit", () => {
  const openapi = JSON.parse(readFileSync(SCOPED_CONTRACT));
  delete openapi.paths["/workspace/capabilities"];
  const withoutCapabilities = { operations: scope.operations.filter((name) => name !== "platform.capabilities.get") };
  const hidden = buildContract({ openapi, scope: withoutCapabilities });
  const result = validateSuite({ contract: hidden, cases, sdkOperations: sdkOperations.filter((op) => op.name !== "platform.capabilities.get") });
  assert.equal(result.ok, false);
  assert.equal(result.securityMustExist.length, 0);
  for (const id of offered) assert.ok(result.securityErrors.some((error) => error.id === id), id);
});

test("an unpaired mandatory case cannot earn absence-only security credit", () => {
  const original = cases.find((c) => c.id === "gateway.anonymous.forged-tenant-headers");
  const synthetic = { ...structuredClone(original), id: "must-exist.unpaired-security", tags: [...original.tags, "must-exist"] };
  const result = validate([...cases, synthetic]);
  assert.equal(result.ok, false);
  const refusal = result.securityErrors.filter((error) => error.id === synthetic.id);
  assert.equal(refusal.length, 1);
  assert.match(refusal[0].message, /no validated offered counterpart/);
  assert.ok(!result.securityMustExist.includes(synthetic.id));
});

test("forged anonymous tenant selectors require their offered security twin", () => {
  const id = "gateway.anonymous.forged-tenant-headers";
  const result = validate(cases.filter((c) => c.id !== `${id}.offered`));
  assert.equal(result.ok, false);
  assert.ok(result.securityErrors.some((error) => error.id === id));
});

test("counterparts cannot change or omit a security assertion", () => {
  for (const id of offered) {
    const broken = cases.map((c) => c.id === id ? { ...c, expect: { errorClass: "MissingSecurityExpectation" } } : c);
    assert.equal(validate(broken).ok, false, id);
  }
  assert.ok(MUST_EXIST.every((id) => cases.some((c) => c.id === id)));
});
