#!/usr/bin/env node
/**
 * Validate every case against the case schema and the contract, and measure coverage.
 *
 *   node tests/platform-conformance/validate.mjs [--openapi <contract.json> --scope <scope.json>] [--sdk-root <tree>] [--cases <dir,...>] [--expectations <file>] [--out <receipt.json>]
 *
 * The contract defaults to the committed scoped platform contract. Exit 0 when every case validates
 * and every operation of the contract has at least one case; 1 otherwise. The receipt holds operation
 * keys, counts and errors, never the document.
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { harnessOf, loadCases, MUST_EXIST, scopeCases, withExpectations } from "./lib/cases.mjs";
import { sdkInventory } from "./lib/sdk-inventory.mjs";
import { validateSecurity } from "./lib/security.mjs";
import { buildContract, opKey, SCOPED_CONTRACT, validateCase } from "./lib/contract.mjs";
import { parseFlags } from "./runners/common/args.mjs";

export function validateSuite({ contract, cases, sdkOperations }) {
  const perCase = [];
  const notOffered = { count: 0, byNamespace: {}, cases: [] };
  for (const testCase of scopeCases(cases, contract)) {
    let verdict;
    if (testCase.offering?.status === "NOT-OFFERED") {
      const key = opKey(testCase.op.method, testCase.op.path);
      const namespace = testCase.offering.namespace;
      const contractAbsent = !contract.operations.has(key);
      const sdkAbsent = Array.isArray(sdkOperations) && !sdkOperations.some((o) =>
        o.name.startsWith(`${namespace}.`) || opKey(o.method, o.path) === key);
      const errors = [];
      if (!contractAbsent) errors.push(`${key} is still present in the scoped contract`);
      if (!sdkAbsent) errors.push(`${namespace} is present in the SDK or SDK absence evidence is missing`);
      notOffered.count += 1;
      notOffered.byNamespace[namespace] = (notOffered.byNamespace[namespace] ?? 0) + 1;
      notOffered.cases.push({ id: testCase.id, key, namespace, contractAbsent, sdkAbsent });
      verdict = { key, documented: false, errors, notes: ["NOT-OFFERED: contract and SDK absence required"] };
    } else verdict = validateCase(contract, testCase);
    perCase.push({ id: testCase.id, key: verdict.key, documented: verdict.documented, harness: harnessOf(testCase), errors: verdict.errors, notes: verdict.notes });
  }
  const covered = new Set(cases.filter((c) => c.op).map((c) => opKey(c.op.method, c.op.path)));
  const uncovered = [];
  const byFamily = {};
  for (const operation of contract.operations.values()) {
    const family = operation.sdk?.family ?? "unknown";
    byFamily[family] ??= { operations: 0, covered: 0 };
    byFamily[family].operations += 1;
    if (covered.has(operation.key)) byFamily[family].covered += 1;
    else uncovered.push(`${operation.key} (${family}.${operation.sdk?.method ?? "?"})`);
  }
  const ids = new Set(cases.map((c) => c.id));
  const missingMustExist = MUST_EXIST.filter((id) => !ids.has(id));
  const security = validateSecurity(cases, perCase);
  const failing = perCase.filter((c) => c.errors.length);
  return {
    cases: cases.length,
    notOffered,
    ...security,
    perCase,
    byHarness: cases.reduce((acc, c) => ((acc[harnessOf(c)] = (acc[harnessOf(c)] ?? 0) + 1), acc), {}),
    byFamily,
    uncovered,
    missingMustExist,
    failing,
    ok: failing.length === 0 && uncovered.length === 0 && missingMustExist.length === 0 && security.securityErrors.length === 0,
  };
}

export function main(argv) {
  const flags = parseFlags(argv, { values: ["openapi", "scope", "expectations", "out", "sdk-root"], lists: ["cases"] });
  const openapiFile = flags.openapi ?? SCOPED_CONTRACT;
  const openapiText = readFileSync(openapiFile, "utf8");
  if (flags.openapi && !flags.scope) throw new Error("an explicit contract requires its matching --scope");
  const scope = JSON.parse(readFileSync(flags.scope ?? new URL("../../openapi/platform/scope.json", import.meta.url), "utf8"));
  const contract = buildContract({ openapi: JSON.parse(openapiText), source: path.basename(openapiFile), text: openapiText, scope });
  const loaded = withExpectations(loadCases(undefined, flags.cases ?? []), flags.expectations);
  const result = validateSuite({ contract, cases: loaded.cases, sdkOperations: sdkInventory(flags["sdk-root"]) });
  const receipt = {
    schemaVersion: "platform-conformance-validation/v1",
    contract: { source: contract.source, sha256: contract.sha256, counts: contract.counts },
    schemaErrors: loaded.errors,
    ...result,
    ok: result.ok && loaded.errors.length === 0,
    validatedAt: new Date().toISOString(),
  };
  if (flags.out) {
    mkdirSync(path.dirname(flags.out), { recursive: true });
    writeFileSync(flags.out, `${JSON.stringify(receipt, null, 2)}\n`);
  }
  const fam = Object.entries(result.byFamily).map(([f, v]) => `${f}=${v.covered}/${v.operations}`).join(" ");
  process.stdout.write(`VALIDATE cases=${receipt.cases} not_offered=${result.notOffered.count} schema_errors=${loaded.errors.length} case_errors=${result.failing.length} uncovered=${result.uncovered.length} must_exist_missing=${result.missingMustExist.length} coverage ${fam} contract=${(contract.sha256 ?? "").slice(0, 12)} ok=${receipt.ok}\n`);
  for (const line of loaded.errors.slice(0, 20)) process.stdout.write(`  schema: ${line}\n`);
  for (const c of result.failing.slice(0, 40)) process.stdout.write(`  case ${c.id}: ${c.errors.join("; ")}\n`);
  for (const key of result.uncovered) process.stdout.write(`  uncovered: ${key}\n`);
  return receipt.ok ? 0 : 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) process.exit(main(process.argv.slice(2)));
