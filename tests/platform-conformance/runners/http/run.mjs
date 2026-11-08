#!/usr/bin/env node
/**
 * The `http` runner: raw HTTP, no SDK. It proves the contract itself.
 *
 *   node runners/http/run.mjs --target gateway --base <platform origin> --mode fi-keypair \
 *     --fixtures <secrets.json> --world <world.json> --exporter http://127.0.0.1:4318 --out <dir>
 *     [--openapi <contract.json>] [--expectations <file>] [--only 'sandboxes.*'] [--tags deterministic]
 *     [--exclude-tags live-model] [--allow host,..] [--harness <name> --harnesses <module.mjs>]
 *
 * The contract defaults to the committed scoped platform contract. `plain` is the built-in harness;
 * any other (a fault proxy, a feature toggle, a scripted fixture) comes from a `--harnesses` module
 * that exports `harnesses = { <name>: async ({ base, makeExecutor, fetchImpl, flags, fixtures }) =>
 * ({ run(testCase, mode), close(), info? }) }`.
 *
 * It refuses to start when the base URL or the exporter endpoint is unset or not allowed, arms the
 * egress guard for the whole process, and exits 0 (no fail verdicts), 1 (a case failed) or 3 (the
 * egress guard tripped, or a receipt would have leaked a credential).
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { loadCases, selectCases, withExpectations } from "../../lib/cases.mjs";
import { loadCompareRules, toParityRecord } from "../../lib/compare.mjs";
import { buildContract, SCOPED_CONTRACT } from "../../lib/contract.mjs";
import { createEgressGuard, requireEndpoints } from "../../guards/no-prod-egress/index.mjs";
import { newRunId, need, parseFlags } from "../common/args.mjs";
import { LeakError, summarize, writeReceipts } from "../common/receipts.mjs";
import { secretValues } from "./auth.mjs";
import { createExecutor } from "./execute.mjs";

const readJson = (file) => JSON.parse(readFileSync(file, "utf8"));

export async function main(argv) {
  const flags = parseFlags(argv, {
    values: ["target", "base", "mode", "fixtures", "world", "openapi", "expectations", "exporter", "out", "only", "run-id", "label", "harness", "harnesses", "fa-root", "toxiproxy-port"],
    lists: ["tags", "exclude-tags", "allow", "cases"],
  });
  const target = need(flags, "target");
  const base = flags.base;
  const allow = flags.allow ?? [];
  requireEndpoints({ base, exporter: flags.exporter }, allow);
  const guard = createEgressGuard({ allow }).install();
  const mode = need(flags, "mode");
  const runId = flags["run-id"] ?? newRunId();
  const openapiFile = flags.openapi ?? SCOPED_CONTRACT;
  const openapiText = readFileSync(openapiFile, "utf8");
  const contract = buildContract({ openapi: JSON.parse(openapiText), source: path.basename(openapiFile), text: openapiText });
  const fixtures = flags.fixtures ? readJson(flags.fixtures) : {};
  const world = flags.world ? readJson(flags.world) : {};
  const { cases, errors } = withExpectations(loadCases(undefined, flags.cases ?? []), flags.expectations);
  if (errors.length) throw new Error(`the cases do not validate:\n${errors.slice(0, 20).join("\n")}`);
  const selected = selectCases(cases, { only: flags.only, tags: flags.tags, excludeTags: flags["exclude-tags"], mode, runner: "http", harness: flags.harness ?? "plain" });
  const rules = loadCompareRules();
  const harnessName = flags.harness ?? "plain";
  const makeExecutor = (url) => createExecutor({ target, base: url, contract, fixtures, world, runId, fetchImpl: guard.fetch, log: (m) => process.stderr.write(`${m}\n`) });
  let harness;
  if (harnessName === "plain") harness = { run: makeExecutor(base), close: async () => {} };
  else {
    if (!flags.harnesses) throw new Error(`the ${harnessName} harness needs --harnesses <module.mjs>`);
    const { harnesses } = await import(pathToFileURL(path.resolve(flags.harnesses)).href);
    const make = harnesses?.[harnessName];
    if (typeof make !== "function") throw new Error(`${flags.harnesses} has no ${harnessName} harness`);
    harness = await make({ base, makeExecutor, fetchImpl: guard.fetch, flags, fixtures });
  }
  const results = [];
  for (const testCase of selected) {
    const result = await harness.run(testCase, mode);
    if (result.first) result.parity = toParityRecord(result.first, rules);
    delete result.first;
    results.push(result);
    process.stdout.write(`${result.verdict.padEnd(5)} ${mode} ${testCase.id}${result.failures?.length ? ` :: ${result.failures[0]}` : result.reason ? ` :: ${result.reason}` : ""}\n`);
  }
  await harness.close();
  const summary = {
    schemaVersion: "platform-conformance-http-summary/v1",
    harness: { name: harnessName, ...(harness.info ?? {}) },
    runId,
    label: flags.label ?? null,
    target,
    mode,
    base,
    exporter: flags.exporter,
    contract: { source: contract.source, sha256: contract.sha256, counts: contract.counts },
    selection: { harness: flags.harness ?? "plain", only: flags.only ?? null, tags: flags.tags ?? null, excludeTags: flags["exclude-tags"] ?? null, cases: selected.length },
    ...summarize(results),
    contractDrift: Object.fromEntries(results.filter((r) => r.contractDrift?.length).map((r) => [r.id, r.contractDrift])),
    egressGuard: guard.receipt(),
    finishedAt: new Date().toISOString(),
  };
  guard.uninstall();
  const out = need(flags, "out");
  try {
    writeReceipts(out, { results, summary }, secretValues(fixtures));
  } catch (error) {
    if (error instanceof LeakError) {
      process.stderr.write(`${error.message}\n`);
      return 3;
    }
    throw error;
  }
  process.stdout.write(`SUMMARY target=${target} mode=${mode} cases=${results.length} pass=${summary.counts.pass} fail=${summary.counts.fail} xfail=${summary.counts.xfail} xpass=${summary.counts.xpass} skip=${summary.counts.skip} egress_trips=${guard.trips.length}\n`);
  if (guard.tripped) return 3;
  return summary.counts.fail > 0 ? 1 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main(process.argv.slice(2)).then(
    (code) => process.exit(code),
    (error) => {
      process.stderr.write(`http runner: ${error.message}\n`);
      process.exit(2);
    },
  );
}
