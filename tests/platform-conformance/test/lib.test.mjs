// Unit tests for the language-neutral libraries: cases, errors, templates, expectations, compare.
import assert from "node:assert/strict";
import { mkdtempSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { applyExpectations, harnessOf, loadCases, MUST_EXIST, selectCases, SUITE_ROOT } from "../lib/cases.mjs";
import { compareRecords, loadCompareRules, toParityRecord } from "../lib/compare.mjs";
import { errorClassFor, normalizeError } from "../lib/errors.mjs";
import { checkOutcome } from "../lib/expect.mjs";
import { checkSchema } from "../lib/schema-check.mjs";
import { fill, fillPath } from "../lib/template.mjs";

test("every committed case validates, ids are unique and every must-exist case is present", () => {
  const { cases, errors } = loadCases();
  assert.deepEqual(errors, []);
  const ids = new Set(cases.map((c) => c.id));
  for (const id of MUST_EXIST) assert.ok(ids.has(id), id);
  for (const family of ["sandboxes", "runs", "platform", "deployments"]) assert.ok(cases.some((c) => c.family === family), family);
  assert.ok(cases.length >= 120, `${cases.length} cases`);
  assert.deepEqual(cases.filter((c) => c.expectedFailure || c.expect?.knownDrift || c.notes).map((c) => c.id), [], "the cases state the contract only");
});

test("an expectations file adds known gaps by case id, each with an owner", () => {
  const { cases } = loadCases();
  const merged = applyExpectations(cases, {
    cases: {
      "sandboxes.get.ok": { expectedFailure: { owner: "server", reason: "x" } },
      "sandboxes.list.ok": { expect: { knownDrift: { owner: "contract", reason: "y", messages: ["m"] } } },
    },
  });
  assert.deepEqual(merged.errors, []);
  const byId = new Map(merged.cases.map((c) => [c.id, c]));
  assert.equal(byId.get("sandboxes.get.ok").expectedFailure.owner, "server");
  assert.equal(byId.get("sandboxes.list.ok").expect.knownDrift.owner, "contract");
  assert.equal(byId.get("sandboxes.list.ok").expect.status, cases.find((c) => c.id === "sandboxes.list.ok").expect.status);
  const bad = applyExpectations(cases, { cases: { "no.such.case": {}, "sandboxes.get.ok": { expectedFailure: { reason: "no owner" } } } });
  assert.deepEqual(bad.errors, ["expectations: no case no.such.case", "expectations: sandboxes.get.ok expectedFailure has no owner"]);
});

test("extra case directories join a run, and only they may declare a gap inline", () => {
  const dir = mkdtempSync(path.join(os.tmpdir(), "extra-cases-"));
  const base = loadCases().cases.find((c) => c.id === "sandboxes.list.ok");
  const { file, family, ...extra } = { ...base, id: "sandboxes.list.private", expectedFailure: { owner: "server", reason: "x" } };
  writeFileSync(path.join(dir, "extra.json"), JSON.stringify({ schemaVersion: "sdk-conformance-cases/v1", family: "sandboxes", about: "extra", cases: [extra] }));
  const loaded = loadCases(undefined, [dir]);
  assert.deepEqual(loaded.errors, []);
  assert.equal(loaded.cases.find((c) => c.id === "sandboxes.list.private").expectedFailure.owner, "server");
  writeFileSync(path.join(dir, "dup.json"), JSON.stringify({ schemaVersion: "sdk-conformance-cases/v1", family: "sandboxes", about: "dup", cases: [{ ...extra, id: "sandboxes.list.ok" }] }));
  assert.ok(loadCases(undefined, [dir]).errors.some((e) => /duplicate id sandboxes.list.ok/.test(e)));
  rmSync(dir, { recursive: true, force: true });
});

test("selection is pure: by glob, tag, mode, runner and harness", () => {
  const { cases } = loadCases();
  const client = selectCases(cases, { harness: "client" });
  assert.ok(client.length >= 2 && client.every((c) => harnessOf(c) === "client"));
  assert.ok(selectCases(cases, { only: "sandboxes.get.*" }).every((c) => c.id.startsWith("sandboxes.get.")));
  assert.equal(selectCases(cases, { mode: "none", runner: "http", harness: "plain" }).every((c) => c.modes.includes("none")), true);
  assert.ok(selectCases(cases, { runner: "http" }).every((c) => !c.runners || c.runners.includes("http")));
});

test("the three error shapes and status-only bodies normalise to one record and class", () => {
  const h = (map) => (name) => map[name];
  assert.deepEqual(normalizeError(401, { error: "omega_unauthenticated", reason: "no credential", requestId: "r1" }, h({})), { status: 401, code: "omega_unauthenticated", shape: "gateway", reason: "no credential", requestId: "r1" });
  const ee = normalizeError(404, { error: { code: "not_found", message: "m" }, code: "not_found", message: "m", request_id: "u1" }, h({ "x-request-id": "g1" }));
  assert.equal(ee.code, "not_found");
  assert.equal(ee.shape, "ee");
  assert.equal(ee.requestId, "g1");
  assert.equal(ee.upstreamRequestId, "u1");
  assert.equal(normalizeError(400, { error: { code: "bad", message: "x", fix: "do y" } }).hint, "do y");
  const html = normalizeError(502, null, h({ "x-request-id": "g2" }));
  assert.deepEqual(html, { status: 502, code: "http_502", shape: "status-only", requestId: "g2" });
  assert.equal(normalizeError(503, { error: "product_paused", retryAfterSeconds: 30 }).retryAfterSeconds, 30);
  assert.equal(errorClassFor(302), "UnexpectedRedirectError");
  assert.equal(errorClassFor(404, "product_not_admitted"), "ProductNotAvailableError");
  assert.equal(errorClassFor(503, "product_paused"), "ProductPausedError");
  assert.equal(errorClassFor(503, "sandboxes_not_enabled"), "FeatureNotEnabledError");
  assert.equal(errorClassFor(409, "idempotency_key_in_progress"), "IdempotencyKeyInProgressError");
  assert.equal(errorClassFor(422, "idempotency_key_reused"), "IdempotencyKeyReusedError");
  assert.equal(errorClassFor(200), null);
});

test("templates fill whole values, parts and path parameters", () => {
  const ctx = { res: { sandbox: "sbx 1", n: 3 }, run: { short: "abc" } };
  assert.deepEqual(fill({ a: "${res.n}", b: "x-${run.short}", c: ["${res.sandbox}"] }, ctx), { a: 3, b: "x-abc", c: ["sbx 1"] });
  assert.throws(() => fill("${res.missing}", ctx), /unknown template value/);
  assert.equal(fillPath("/workspace/sandboxes/{sandbox}/files/{filePath}", { sandbox: "a b", filePath: "d/e f.txt" }), "/workspace/sandboxes/a%20b/files/d/e%20f.txt");
  assert.equal(fillPath("/workspace/workforce/agents/{id}/runs/{id}", ["a", "r"]), "/workspace/workforce/agents/a/runs/r");
  assert.throws(() => fillPath("/x/{id}/y/{id}", { id: "a" }), /repeats a parameter/);
});

test("expectations check status, code, class, fields, events, exit codes, resume order and leaks", () => {
  const outcome = { status: 200, body: { sandbox: { id: "s", state: "running" } }, events: [{ type: "started" }, { type: "exit", data: { exitCode: 3, seq: 5 } }], headers: {} };
  assert.equal(checkOutcome({ status: 200, fields: { "sandbox.id": "string", "sandbox.state": { oneOf: ["running"] } }, events: { include: ["exit"], last: "exit", exitCode: 3 } }, outcome).pass, true);
  assert.equal(checkOutcome({ events: { exitCode: 0 } }, outcome).pass, false);
  assert.equal(checkOutcome({ events: { afterSeq: 5 } }, outcome).pass, false);
  assert.equal(checkOutcome({ noLeak: ["running"] }, outcome).pass, false);
  assert.equal(checkOutcome({ status: 404, codePresent: true }, { status: 404, code: "http_404" }).pass, false);
});

test("compare.json: exact fields by value, shape-only fields by shape, an unlisted field fails", () => {
  const rules = loadCompareRules();
  const live = toParityRecord({ status: 201, body: { sandbox: { id: "sbx-1", state: "running", createdAt: "2026-10-20T00:00:00Z", bytes: 10 } }, requestId: "r-1" }, rules);
  const fake = toParityRecord({ status: 201, body: { sandbox: { id: "fake-9", state: "running", createdAt: "1970-01-01T00:00:00Z", bytes: 99 } }, requestId: "r-2" }, rules);
  assert.equal(compareRecords(live, fake, rules).match, true);
  const drift = toParityRecord({ status: 201, body: { sandbox: { id: "x", state: 7 } }, requestId: "r" }, rules);
  assert.equal(compareRecords(live, drift, rules).match, false);
  const extra = { ...fake, surprise: 1 };
  assert.match(compareRecords(live, extra, rules).differences.join(" "), /not listed in compare\.json/);
});

test("the structural schema checker covers the keywords the suite relies on", () => {
  const schema = { type: "object", required: ["a"], additionalProperties: false, properties: { a: { type: "integer", minimum: 1 }, b: { oneOf: [{ type: "string" }, { type: "null" }] }, c: { $ref: "#/$defs/c" } }, $defs: { c: { enum: ["x"] } } };
  assert.deepEqual(checkSchema(schema, { a: 1, b: null, c: "x" }), []);
  assert.equal(checkSchema(schema, { a: 0, z: 1, c: "y" }).length, 3);
});

test("every entry point that makes a request arms the process-wide egress guard first", () => {
  // A guard that covered one entry point was once described as covering the process. An
  // entry point (a CLI module) that sends a request must call guard.install() before it does; a
  // library module takes the fetch it is handed and is covered by the entry point that loads it.
  const entry = /process\.argv|^main\(\)/m;
  const sends = /\bfetch\(|\.request\(|\bfetchImpl\b|\bguard\.fetch\b/;
  const offenders = [];
  const seen = [];
  const walk = (dir) => {
    for (const name of readdirSync(dir)) {
      const full = path.join(dir, name);
      if (statSync(full).isDirectory()) {
        if (name !== "test" && name !== "node_modules") walk(full);
      } else if (name.endsWith(".mjs")) {
        const text = readFileSync(full, "utf8");
        if (!entry.test(text) || !sends.test(text)) continue;
        seen.push(path.relative(SUITE_ROOT, full));
        const installAt = text.search(/createEgressGuard\([^)]*\)\.install\(\)/);
        const firstSend = text.search(/^\s*(const|let)?[^\n]*\bawait fetch\(/m);
        if (installAt < 0 || (firstSend >= 0 && firstSend < installAt)) offenders.push(path.relative(SUITE_ROOT, full));
      }
    }
  };
  walk(SUITE_ROOT);
  assert.ok(seen.includes(path.join("runners", "http", "run.mjs")) && seen.includes(path.join("runners", "sdk", "run.mjs")), seen.join(","));
  assert.deepEqual(offenders, []);
});

test("every module in the suite is 400 lines or fewer", () => {
  const offenders = [];
  const walk = (dir) => {
    for (const name of readdirSync(dir)) {
      const full = path.join(dir, name);
      if (statSync(full).isDirectory()) walk(full);
      else if (/\.(mjs|js|py)$/.test(name)) {
        const lines = readFileSync(full, "utf8").split("\n").length;
        if (lines > 400) offenders.push(`${path.relative(SUITE_ROOT, full)}: ${lines}`);
      }
    }
  };
  walk(SUITE_ROOT);
  assert.deepEqual(offenders, []);
});

test("tenant floors and scopes: one admitting case per floor, and B's key with A's selectors per family", async () => {
  const { cases } = loadCases();
  const byRole = (role) => cases.filter((c) => c.tenant.role === role && !c.tags.includes("failure"));
  assert.ok(byRole("admin").some((c) => c.id === "platform.agents.retire.admin"), "an admin-floor route admits the admin");
  assert.ok(cases.some((c) => c.id === "platform.agents.retire.member-refused" && c.expect.status === 403), "and refuses a member");
  assert.ok(byRole("member").length >= 1 && byRole("viewer").length >= 1, "member and viewer floors admit their reads or writes");
  const forged = cases.filter((c) => c.tenant.scopeOrg);
  for (const family of ["sandboxes", "runs"]) assert.ok(forged.some((c) => c.family === family && c.repeat >= 5), family);
  for (const c of forged) {
    assert.notEqual(c.tenant.scopeOrg, c.tenant.org, c.id);
    assert.ok([c.expect.status].flat().every((status) => [401, 403, 404].includes(status)), `${c.id}: the refusal, not a leak`);
  }
  const { credentialFor } = await import("../runners/http/auth.mjs");
  const { sdkCredential } = await import("../runners/sdk/run.mjs");
  const fixtures = {
    ee: { A: { orgId: "oa", workspaceId: "wa", keys: { owner: "ka" } }, B: { orgId: "ob", workspaceId: "wb", keys: { owner: "kb" } } },
    fa: { A: { organizationId: "fa-a", workspaceId: "fw-a", tokens: { owner: "ta" } }, B: { organizationId: "fa-b", workspaceId: "fw-b", tokens: { owner: "tb" } } },
    fi: { A: { keys: { owner: { apiKey: "pa", secretKey: "sa" } } }, B: { keys: { owner: { apiKey: "pb", secretKey: "sb" } } } },
  };
  assert.deepEqual(credentialFor(fixtures, "ee-key", "B", "owner", { scopeOrg: "A" }).headers, { authorization: "Bearer kb", "x-omega-org": "oa", "x-omega-workspace": "wa" });
  assert.deepEqual(credentialFor(fixtures, "fa-session", "B", "owner", { scopeOrg: "A" }).headers, { authorization: "Bearer tb", "x-organization-id": "fa-a", "x-workspace-id": "fw-a" });
  assert.match(credentialFor(fixtures, "fi-keypair", "B", "owner", { scopeOrg: "A" }).skip, /no FI scope ids/);
  assert.deepEqual(credentialFor(fixtures, "fi-keypair", "B", "owner").headers, { "x-api-key": "pb", "x-secret-key": "sb" });
  assert.deepEqual(sdkCredential(fixtures, "ee-key", "B", "owner", "A"), { kind: "platform-token", apiKey: "kb", orgId: "oa", workspaceId: "wa" });
  assert.equal(sdkCredential(fixtures, "fi-keypair", "B", "owner", "A"), null);
  assert.equal(sdkCredential(fixtures, "fi-keypair", "B", "owner").apiKey, "pb");
});
