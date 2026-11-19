import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { loadCases, MUST_EXIST } from "../lib/cases.mjs";
import { buildContract, SCOPED_CONTRACT } from "../lib/contract.mjs";
import { validateSuite } from "../validate.mjs";

const openapi = JSON.parse(readFileSync(SCOPED_CONTRACT));
const scope = JSON.parse(readFileSync(new URL("../../../openapi/platform/scope.json", import.meta.url)));
const cases = loadCases().cases;
const features = JSON.parse(readFileSync(new URL("../../../openapi/connectors/features.json", import.meta.url)));
const credentialAbsences = features.credential_reads ? 0 : 4;
const contract = buildContract({ openapi, scope });
const sdkOperations = [...contract.operations.values()].map((o) => ({ name: `${o.sdk.family}.${o.sdk.method}`, method: o.method, path: o.path }));

test("hidden namespaces retain every case as explicit contract and SDK absence checks", () => {
  const result = validateSuite({ contract, cases, sdkOperations });
  assert.equal(result.cases, cases.length);
  assert.deepEqual(result.failing, []);
  assert.equal(result.notOffered?.count, 61 + credentialAbsences);
  assert.equal(result.notOffered?.byNamespace.sandboxes, 61);
  assert.equal(result.notOffered?.byNamespace["platform.credentials"] ?? 0, credentialAbsences);
  assert.equal(result.ok, true);
  assert.deepEqual(result.missingMustExist, []);
  assert.deepEqual(result.securityMustExist, MUST_EXIST.filter((id) => id.endsWith(".offered")));
  assert.deepEqual(result.securityErrors, []);
  assert.equal(result.notOffered.cases.filter((c) => MUST_EXIST.includes(c.id)).length, 6);
  for (const c of result.notOffered.cases) {
    assert.equal(c.contractAbsent, true);
    assert.equal(c.sdkAbsent, true);
  }
});

test("a hidden SDK operation is a failure, never an absence pass", () => {
  const result = validateSuite({ contract, cases, sdkOperations: [...sdkOperations, { name: "sandboxes.list", method: "GET", path: "/workspace/sandboxes" }] });
  assert.equal(result.ok, false);
  assert.ok(result.failing.some((c) => c.errors.some((e) => /SDK/.test(e))));
});

test("an in-scope route accidentally removed from the contract still fails", () => {
  const broken = structuredClone(openapi);
  delete broken.paths["/workspace/deployments"];
  assert.throws(() => buildContract({ openapi: broken, scope }), /scope/);
});

test("missing security cases and unknown routes cannot be hidden by scoping", () => {
  const result = validateSuite({ contract, cases: cases.filter((c) => !MUST_EXIST.includes(c.id)), sdkOperations });
  assert.deepEqual(result.missingMustExist, MUST_EXIST);
  assert.equal(result.ok, false);
  const typo = { ...cases.find((c) => c.id === "deployments.list.ok"), id: "deployments.typo", op: { method: "GET", path: "/workspace/deployments/typo" } };
  assert.equal(validateSuite({ contract, cases: [...cases, typo], sdkOperations }).ok, false);
});
