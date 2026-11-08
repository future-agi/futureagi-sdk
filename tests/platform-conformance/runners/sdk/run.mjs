#!/usr/bin/env node
/**
 * The runner shell for an SDK under test: `ts`, `py` or `fake`. Case selection,
 * templating, expectations and receipts are the same code the http runner uses; only the call goes
 * through the SDK, loaded BY PATH:
 *
 *   node runners/sdk/run.mjs --lang ts   --client-ts <built packages/client dir>   --base <url> ...
 *   node runners/sdk/run.mjs --lang py   --client-py <wheel or source dir> [--python <bin>] --base <url> ...
 *   node runners/sdk/run.mjs --lang fake --testkit <dir>                         (the network is denied)
 *     common: --mode ee-key|fa-session|fi-keypair --fixtures <secrets> --world <ids> --exporter <url>
 *             --out <dir> [--only globs] [--tags ..] [--run-id id]
 *
 * It refuses to start when a base URL (not for fake) or the exporter endpoint is unset, and arms the
 * egress guard (deny-all for fake). Exit 0 / 1 (a case failed) / 3 (guard tripped or a leak).
 */
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { expectFor, harnessOf, loadCases, selectCases, withExpectations } from "../../lib/cases.mjs";
import { loadCompareRules, toParityRecord } from "../../lib/compare.mjs";
import { checkOutcome } from "../../lib/expect.mjs";
import { fill } from "../../lib/template.mjs";
import { createEgressGuard, requireEndpoints } from "../../guards/no-prod-egress/index.mjs";
import { newRunId, need, parseFlags } from "../common/args.mjs";
import { LeakError, summarize, writeReceipts } from "../common/receipts.mjs";
import { secretValues } from "../http/auth.mjs";
import { loadJsBinding, startPythonBinding } from "./bindings.mjs";

const readJson = (file) => JSON.parse(readFileSync(file, "utf8"));

/**
 * The credential an SDK is constructed with, by mode (structured, unlike raw headers). `scopeOrg`
 * (tenant.scopeOrg) builds `org`'s credential with the other org's scope ids: the forged selector.
 */
export function sdkCredential(fixtures, mode, org, role, scopeOrg = org) {
  if (mode === "ee-key") {
    const t = fixtures?.ee?.[org];
    const s = fixtures?.ee?.[scopeOrg];
    return t?.keys?.[role] && s ? { kind: "platform-token", apiKey: t.keys[role], orgId: s.orgId, workspaceId: s.workspaceId } : null;
  }
  if (mode === "fi-keypair") {
    const pair = fixtures?.fi?.[org]?.keys?.[role];
    const s = fixtures?.fi?.[scopeOrg];
    return pair && (scopeOrg === org || s?.workspaceId) ? { kind: "fi-keypair", apiKey: pair.apiKey, secretKey: pair.secretKey, workspaceId: s?.workspaceId } : null;
  }
  if (mode === "fa-session") {
    const t = fixtures?.fa?.[org];
    const s = fixtures?.fa?.[scopeOrg];
    return t?.tokens?.[role] && s ? { kind: "session", token: t.tokens[role], organizationId: s.organizationId, workspaceId: s.workspaceId } : null;
  }
  return { kind: "none" };
}

/**
 * An outcome with no status (a client-side refusal, or an SDK error that carries none) cannot be
 * checked against a status, but it must not pass one either: a 2xx expectation fails when the SDK
 * raised, and an error status is met only by the error class the case names.
 */
export function statuslessFailures(expect, outcome) {
  if (outcome.status !== null || expect.status === undefined) return [];
  const statuses = Array.isArray(expect.status) ? expect.status : [expect.status];
  if (outcome.errorClass === null) return [];
  if (statuses.every((s) => s >= 200 && s < 300)) return [`expected status ${statuses.join("|")}; the SDK raised ${outcome.errorClass} with no status`];
  if (expect.errorClass === undefined) return [`expected status ${statuses.join("|")}; the SDK reported no status (${outcome.errorClass}) and the case names no error class to match`];
  return [];
}

export async function runCase({ testCase, mode, binding, baseUrl, fetchImpl, fixtures, world, runId, rules }) {
  const { org, role, resourceOrg, scopeOrg } = testCase.tenant;
  const ctx = { run: { id: runId, short: runId.slice(-8) }, own: world?.[org] ?? {}, res: world?.[resourceOrg ?? org] ?? {}, ids: {}, cap: {} };
  const result = { id: testCase.id, mode, tenant: testCase.tenant, sdk: testCase.sdk, attempts: [], failures: [] };
  for (const need of testCase.needs ?? []) if (!(need in ctx.res) && !(need in ctx.own)) return { ...result, verdict: "skip", reason: `world has no ${need}` };
  if (testCase.setup?.length) return { ...result, verdict: "skip", reason: "setup steps run in the http runner; an SDK runner gets them with the test kit's world parity" };
  const expect = fill(expectFor(testCase, mode), ctx);
  let outcome;
  if (harnessOf(testCase) === "client") {
    if (typeof binding.clientCase !== "function") return { ...result, verdict: "skip", reason: "the binding has no clientCase()" };
    const value = await binding.clientCase(fill(testCase.client, ctx), { fetch: fetchImpl });
    if (value?.skip) return { ...result, verdict: "skip", reason: value.skip };
    outcome = { status: null, errorClass: value?.errorClass ?? null, code: value?.code ?? null, body: null, events: [] };
    if (value?.networkRequests) result.failures.push(`the client made ${value.networkRequests} network request(s) before refusing`);
  } else {
    const credential = sdkCredential(fixtures, mode, org, role, scopeOrg ?? org);
    if (!credential) return { ...result, verdict: "skip", reason: `no ${mode} ${role} credential for org ${org}` };
    const client = binding.createClient({ baseUrl, credential, fetch: fetchImpl, options: { maxRetries: 0 } });
    const args = fill(testCase.args ?? { ...(testCase.call?.params ?? {}), ...(testCase.call?.query ?? {}), ...(testCase.call?.body !== undefined ? { body: testCase.call.body } : {}) }, ctx);
    try {
      const value = await binding.call(client, testCase.sdk, args, {});
      outcome = { status: value?.$status ?? 200, errorClass: null, code: null, body: value, events: Array.isArray(value?.$events) ? value.$events : [] };
    } catch (error) {
      const d = binding.describeError(error) ?? {};
      outcome = { status: d.status ?? null, errorClass: d.errorClass ?? "SDKException", code: d.code ?? null, requestId: d.requestId, upstreamRequestId: d.upstreamRequestId, body: null, events: [] };
    }
  }
  const checked = checkOutcome({ ...expect, status: outcome.status === null ? undefined : expect.status }, outcome);
  result.failures.push(...checked.failures, ...statuslessFailures(expect, outcome));
  result.attempts.push({ status: outcome.status, errorClass: outcome.errorClass, code: outcome.code, requestId: outcome.requestId });
  result.parity = toParityRecord(outcome, rules);
  const xf = testCase.expectedFailure && (!testCase.expectedFailure.modes || testCase.expectedFailure.modes.includes(mode));
  const passed = result.failures.length === 0;
  result.verdict = xf ? (passed ? "xpass" : "xfail") : passed ? "pass" : "fail";
  return result;
}

export async function main(argv) {
  const flags = parseFlags(argv, {
    values: ["lang", "client-ts", "client-py", "testkit", "python", "binding-module", "base", "mode", "fixtures", "world", "exporter", "out", "only", "run-id", "expectations"],
    lists: ["tags", "allow", "cases"],
  });
  const lang = need(flags, "lang");
  const allow = flags.allow ?? [];
  const fake = lang === "fake";
  requireEndpoints(fake ? { exporter: flags.exporter } : { base: flags.base, exporter: flags.exporter }, allow);
  const guard = createEgressGuard({ allow, denyAll: fake }).install();
  const loaded = lang === "py"
    ? await startPythonBinding({ client: need(flags, "client-py"), python: flags.python, bindingModule: flags["binding-module"], allow })
    : await loadJsBinding(need(flags, fake ? "testkit" : "client-ts"));
  const mode = need(flags, "mode");
  const runId = flags["run-id"] ?? newRunId();
  const fixtures = flags.fixtures ? readJson(flags.fixtures) : {};
  const world = flags.world ? readJson(flags.world) : {};
  const { cases, errors } = withExpectations(loadCases(undefined, flags.cases ?? []), flags.expectations);
  if (errors.length) throw new Error(`the cases do not validate:\n${errors.slice(0, 10).join("\n")}`);
  const selected = selectCases(cases, { only: flags.only, tags: flags.tags, mode, runner: lang }).filter((c) => ["plain", "client"].includes(harnessOf(c)));
  const rules = loadCompareRules();
  const results = [];
  for (const testCase of selected) {
    const result = await runCase({ testCase, mode, binding: loaded.binding, baseUrl: fake ? "http://fake.invalid" : flags.base, fetchImpl: guard.fetch, fixtures, world, runId, rules });
    results.push(result);
    process.stdout.write(`${result.verdict.padEnd(5)} ${lang} ${mode} ${testCase.id}${result.failures[0] ? ` :: ${result.failures[0]}` : result.reason ? ` :: ${result.reason}` : ""}\n`);
  }
  const pyGuard = loaded.guardReceipt ? await loaded.guardReceipt() : null;
  await loaded.close?.();
  guard.uninstall();
  const summary = { schemaVersion: "sdk-conformance-sdk-summary/v1", runId, lang, mode, package: loaded.package, base: fake ? null : flags.base, exporter: flags.exporter, ...summarize(results), egressGuard: guard.receipt(), pythonEgressGuard: pyGuard, finishedAt: new Date().toISOString() };
  try {
    writeReceipts(need(flags, "out"), { results, summary }, secretValues(fixtures));
  } catch (error) {
    if (error instanceof LeakError) return 3;
    throw error;
  }
  process.stdout.write(`SUMMARY lang=${lang} mode=${mode} package=${loaded.package?.name ?? loaded.package?.module ?? "?"} cases=${results.length} pass=${summary.counts.pass} fail=${summary.counts.fail} skip=${summary.counts.skip} egress_trips=${guard.trips.length + (pyGuard?.trips?.length ?? 0)}\n`);
  if (guard.tripped || pyGuard?.trips?.length) return 3;
  return summary.counts.fail > 0 ? 1 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main(process.argv.slice(2)).then((code) => process.exit(code), (error) => {
    process.stderr.write(`sdk runner: ${error.message}\n`);
    process.exit(2);
  });
}
