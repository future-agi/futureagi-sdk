/**
 * Load and validate the language-neutral cases under tests/platform-conformance/cases/**.
 *
 * Every file is checked against schema/case-file.schema.json; ids are unique across files; a
 * must-exist case is tagged as one. The cases state the contract only: known server gaps and drift
 * are not in them, but in an expectations file a runner merges by case id (`--expectations`), each
 * with its owner. Filtering (by id glob, tag, mode, runner, family) is pure, so every runner selects
 * cases the same way.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { checkSchema } from "./schema-check.mjs";
import { familyOfPath } from "./contract.mjs";
import { SECURITY_IDS } from "./security.mjs";

/** Retain every scenario; a wholly unoffered namespace gains an explicit absence assertion.
 * Client security scenarios keep their original client payload, expectation and harness as well.
 * Unknown paths and missing operations within an offered namespace remain ordinary failures.
 */
export function scopeCases(cases, contract) {
  if (!contract.scope) return cases;
  const offered = new Set(contract.scope.operations.map((name) =>
    name.startsWith("platform.") ? name.split(".").slice(0, 2).join(".") : name.split(".")[0]));
  return cases.map((c) => {
    const namespace = c.sdk?.family === "platform"
      ? `platform.${c.sdk.method.split(".")[0]}` : familyOfPath(c.op.path);
    return namespace && !offered.has(namespace)
      ? { ...c, offering: { status: "NOT-OFFERED", namespace } }
      : c;
  });
}

export const SUITE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const CASES_DIR = path.join(SUITE_ROOT, "cases");
const SCHEMA = JSON.parse(readFileSync(path.join(SUITE_ROOT, "schema/case-file.schema.json"), "utf8"));

/** Every mandatory security scenario, including its offered-route counterpart. */
export const MUST_EXIST = SECURITY_IDS;

function listJson(dir) {
  const out = [];
  for (const name of readdirSync(dir).sort()) {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) out.push(...listJson(full));
    else if (name.endsWith(".json")) out.push(full);
  }
  return out;
}

/**
 * Load every case file. Returns { files, cases, errors } where each case carries `file`. `extra`
 * names more case directories (a private suite run through these runners): their cases are
 * validated the same way, and only they may declare a known gap inline.
 */
export function loadCases(dir = CASES_DIR, extra = []) {
  if (extra.length) {
    const parts = [loadCaseDir(dir), ...extra.map((d) => loadCaseDir(path.resolve(d), { inlineGaps: true }))];
    const seen = new Map();
    const errors = parts.flatMap((p) => p.errors);
    for (const c of parts.flatMap((p) => p.cases)) {
      if (seen.has(c.id)) errors.push(`duplicate id ${c.id} across case directories`);
      seen.set(c.id, true);
    }
    return { files: parts.flatMap((p) => p.files), cases: parts.flatMap((p) => p.cases), errors };
  }
  return loadCaseDir(dir);
}

function loadCaseDir(dir, { inlineGaps = false } = {}) {
  const files = listJson(dir);
  const cases = [];
  const errors = [];
  const seen = new Map();
  for (const file of files) {
    const rel = path.relative(dir, file);
    let doc;
    try {
      doc = JSON.parse(readFileSync(file, "utf8"));
    } catch (error) {
      errors.push(`${rel}: not JSON (${error.message})`);
      continue;
    }
    const schemaErrors = checkSchema(SCHEMA, doc, { root: SCHEMA });
    if (schemaErrors.length) errors.push(...schemaErrors.slice(0, 20).map((e) => `${rel}: ${e}`));
    for (const item of doc.cases ?? []) {
      if (seen.has(item.id)) errors.push(`${rel}: duplicate id ${item.id} (also in ${seen.get(item.id)})`);
      seen.set(item.id, rel);
      if (doc.family !== "cross" && item.op && !item.id.startsWith(`${doc.family}.`)) errors.push(`${rel}: ${item.id} is not under ${doc.family}.`);
      if (item.tags?.includes("must-exist") !== item.id?.startsWith("must-exist.")) errors.push(`${rel}: ${item.id} must-exist tag and id prefix disagree`);
      if (!inlineGaps && (item.expectedFailure || item.expect?.knownDrift)) errors.push(`${rel}: ${item.id} declares a known gap; gaps belong in an expectations file`);
      if (item.tenant?.role === "anonymous" && !item.modes?.every((m) => m === "none")) errors.push(`${rel}: ${item.id} anonymous cases run in mode none only`);
      if (item.tenant?.scopeOrg && (item.tenant.scopeOrg === item.tenant.org || item.modes?.includes("none"))) errors.push(`${rel}: ${item.id} tenant.scopeOrg must name the other org, in a credentialed mode`);
      cases.push({ ...item, family: doc.family === "cross" ? "cross" : doc.family, file: rel });
    }
  }
  return { files: files.map((f) => path.relative(dir, f)), cases, errors };
}

/**
 * Merge an expectations file onto loaded cases: `{ cases: { <id>: { expectedFailure, expect: {
 * knownDrift }, expectByMode: { <mode>: { knownDrift } } } } }`. Every entry must name a loaded case
 * and carry an owner; returns { cases, errors }.
 */
export function applyExpectations(cases, expectations) {
  const errors = [];
  const byId = new Map(cases.map((c) => [c.id, c]));
  for (const [id, entry] of Object.entries(expectations?.cases ?? {})) {
    if (!byId.has(id)) errors.push(`expectations: no case ${id}`);
    if (entry.expectedFailure && !entry.expectedFailure.owner) errors.push(`expectations: ${id} expectedFailure has no owner`);
  }
  const merged = cases.map((c) => {
    const entry = expectations?.cases?.[c.id];
    if (!entry) return c;
    const expectByMode = { ...(c.expectByMode ?? {}) };
    for (const [mode, extra] of Object.entries(entry.expectByMode ?? {})) expectByMode[mode] = { ...(expectByMode[mode] ?? {}), ...extra };
    return {
      ...c,
      ...(entry.expectedFailure ? { expectedFailure: entry.expectedFailure } : {}),
      expect: { ...c.expect, ...(entry.expect ?? {}) },
      ...(Object.keys(expectByMode).length ? { expectByMode } : {}),
    };
  });
  return { cases: merged, errors };
}

/** Load an expectations file and merge it (no file: the cases as they are). */
export function withExpectations(loaded, file) {
  if (!file) return loaded;
  const { cases, errors } = applyExpectations(loaded.cases, JSON.parse(readFileSync(file, "utf8")));
  return { ...loaded, cases, errors: [...loaded.errors, ...errors] };
}

function globToRegExp(glob) {
  return new RegExp(`^${glob.split("*").map((s) => s.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join(".*")}$`);
}

/** Pure selection. Each filter is optional; `only` is a comma list of id globs. */
export function selectCases(cases, { only, tags, excludeTags, mode, runner, family, harness } = {}) {
  const globs = only ? String(only).split(",").filter(Boolean).map(globToRegExp) : null;
  return cases.filter((c) =>
    (!globs || globs.some((g) => g.test(c.id))) &&
    (!tags || tags.every((t) => c.tags.includes(t))) &&
    (!excludeTags || !excludeTags.some((t) => c.tags.includes(t))) &&
    (!mode || c.modes.includes(mode)) &&
    (!runner || !c.runners || c.runners.includes(runner)) &&
    (!family || c.family === family) &&
    (!harness || harnessOf(c) === harness));
}

/**
 * Which harness runs a case: "plain" (the http executor as is), "client" (SDK client-side only),
 * "live-model", or one the http runner loads from a `--harnesses` module ("chaos", "rollout",
 * "fixture"); "measure" and "planned" cases are run by their own scripts.
 */
export function harnessOf(testCase) {
  if (testCase.plannedIn) return "planned";
  if (testCase.measuredBy) return "measure";
  if (testCase.client) return "client";
  if (testCase.tags.includes("live-model")) return "live-model";
  if (testCase.chaos) return "chaos";
  if (testCase.rollout) return "rollout";
  if (testCase.fixture) return "fixture";
  return "plain";
}

/** The expectation for one mode: `expectByMode[mode]` fields override `expect`. */
export function expectFor(testCase, mode) {
  return { ...testCase.expect, ...(testCase.expectByMode?.[mode] ?? {}) };
}
