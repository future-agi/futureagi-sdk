#!/usr/bin/env node
// Record the TypeScript case catalog against one installed target.
//
//   node record.mjs --install <dir> --target client|integrations --format esm|cjs --out <dir>
//
// <dir>/node_modules holds the packages under test (installed from the E-OLD
// tarballs by tests/fixtures/gateway/e-old/record-e-old.sh). Writes one JSON
// file per catalog area and index.json (environment, load results, public
// .d.ts surface, case ids and each area file's sha256). Two runs must be
// byte-identical, also from another checkout and install path; a file that would
// carry a local path is refused, not written (harness/hygiene.mjs).
import { createHash } from "node:crypto";
import { join } from "node:path";
import { parseArgs } from "node:util";
import { dtsSurface } from "./harness/dts.mjs";
import { recorderRoots, writeChecked } from "./harness/hygiene.mjs";
import { exportKeys, load, packageJson } from "./harness/load.mjs";
import { runCase } from "./harness/runner.mjs";

const FORMAT = 1;
const TARGETS = {
  client: {
    packages: { "@agentcc/client": [".", "./testing", "./express", "./nextjs"] },
    cases: ["./cases/client-core.mjs", "./cases/client-errors.mjs", "./cases/client-streams.mjs", "./cases/client-extras.mjs"],
  },
  integrations: {
    // The integration packages load first, so a CJS require() of each one
    // resolves @agentcc/client itself, as it would in a user's process.
    packages: {
      "@agentcc/langchain": ["."],
      "@agentcc/llamaindex": ["."],
      "@agentcc/react": ["."],
      "@agentcc/vercel": ["."],
      "@agentcc/client": ["."],
    },
    cases: ["./cases/integrations.mjs"],
  },
};
const VERSIONS_OF = ["@agentcc/client", "@agentcc/langchain", "@agentcc/llamaindex", "@agentcc/react", "@agentcc/vercel", "@ai-sdk/openai", "react", "react-test-renderer", "zod"];

function clearEnv() {
  for (const key of Object.keys(process.env)) if (/^(AGENTCC_|FI_|OPENAI_)/.test(key)) delete process.env[key];
}

function versions(install) {
  const out = {};
  for (const name of VERSIONS_OF) {
    try {
      out[name] = packageJson(install, name).version;
    } catch {
      out[name] = null;
    }
  }
  return out;
}

async function main() {
  const { values } = parseArgs({ options: { install: { type: "string" }, target: { type: "string" }, format: { type: "string" }, out: { type: "string" } } });
  const spec = TARGETS[values.target];
  if (!spec || !values.install || !values.out || !["esm", "cjs"].includes(values.format)) throw new Error("usage: --install <dir> --target client|integrations --format esm|cjs --out <dir>");
  clearEnv();
  const loads = {};
  const loaded = new Map();
  const loadPackage = async (name, sub = ".") => {
    const key = `${name} ${sub}`;
    if (!loaded.has(key)) loaded.set(key, await load(values.install, name, sub, values.format));
    const result = loaded.get(key);
    if (!result.ok) throw Object.assign(new Error(`load failed: ${result.spec}: ${result.error.message}`), { load: result.error });
    return result;
  };
  for (const [name, subs] of Object.entries(spec.packages)) {
    for (const sub of subs) {
      const result = await load(values.install, name, sub, values.format);
      loaded.set(`${name} ${sub}`, result);
      loads[result.spec] = result.ok ? { ok: true, exports: exportKeys(result.module) } : { ok: false, error: result.error };
    }
  }
  const dts = {};
  for (const name of Object.keys(spec.packages)) dts[name] = dtsSurface(join(values.install, "node_modules", name));
  const main = loaded.get("@agentcc/client .");
  const child = { install: values.install, format: values.format, main: "@agentcc/client" };
  const target = { module: main.ok ? main.module : null, mainLoad: main.ok ? null : main.error, loadSub: (sub) => loadPackage("@agentcc/client", sub), loadPackage, child };
  const byArea = {};
  const ids = [];
  const skipped = [];
  for (const path of spec.cases) {
    const { cases } = await import(path);
    for (const testCase of cases()) {
      if (!main.ok && values.target === "client") {
        skipped.push(testCase.id);
        continue;
      }
      ids.push(testCase.id);
      (byArea[testCase.area] ??= {})[testCase.id] = await runCase(testCase, target);
    }
  }
  const roots = recorderRoots(values.install, values.out);
  const files = {};
  for (const area of Object.keys(byArea).sort()) {
    const text = writeChecked(join(values.out, `${area}.json`), { format: FORMAT, area, cases: byArea[area] }, roots);
    files[`${area}.json`] = createHash("sha256").update(text).digest("hex");
  }
  const environment = { node: process.version, format: values.format, target: values.target, versions: versions(values.install) };
  writeChecked(join(values.out, "index.json"), { format: FORMAT, environment, loads, dts, case_ids: ids, skipped_load_failed: skipped.length, files }, roots);
  process.stderr.write(`recorded ${ids.length} cases (${skipped.length} skipped) in ${Object.keys(files).length} areas -> ${values.out}\n`);
}

main().catch((err) => {
  process.stderr.write(`record.mjs: ${err.stack ?? err}\n`);
  process.exit(1);
});
