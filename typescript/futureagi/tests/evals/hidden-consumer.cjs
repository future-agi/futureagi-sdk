#!/usr/bin/env node
/** Verify the disabled template-runner surface in a clean, installed consumer. */
"use strict";
const assert = require("node:assert/strict");
const { readFileSync, readdirSync } = require("node:fs");
const { resolve, join } = require("node:path");
const { spawnSync } = require("node:child_process");

const consumer = resolve(process.argv[2]);
const packageDir = join(consumer, "node_modules", "@future-agi", "sdk");
const manifest = JSON.parse(readFileSync(join(packageDir, "package.json"), "utf8"));
for (const key of Object.keys(manifest.exports)) {
  assert.ok(!key.startsWith("./evals"), `Unexpected export: ${key}`);
}
for (const mapping of Object.values(manifest.typesVersions ?? {})) {
  assert.ok(!Object.keys(mapping).some((key) => key.startsWith("evals")), "Unexpected evals type entry");
}
for (const section of ["dependencies", "devDependencies", "optionalDependencies", "peerDependencies"]) {
  assert.ok(!manifest[section]?.["@future-agi/ai-evaluation"], "Retired evaluation dependency");
}
function walk(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    assert.ok(!/^evals(?:\.|$)/.test(entry.name), `Unexpected evals artifact: ${join(directory, entry.name)}`);
    if (entry.isDirectory()) walk(join(directory, entry.name));
  }
}
walk(join(packageDir, "dist"));
const readme = readFileSync(join(packageDir, "README.md"), "utf8");
assert.ok(!readme.includes("@future-agi/sdk/evals"), "README advertises a disabled subpath");
assert.ok(!readme.includes("@future-agi/ai-evaluation"), "README advertises a retired dependency");

const checks = `
  const assert = await import('node:assert/strict');
  for (const name of ['Evaluator', 'EvalTemplateManager', 'Protect', 'Templates', 'Execution', 'evaluate']) {
    assert.equal(Object.hasOwn(sdk, name), false, 'Unexpected root export: ' + name);
  }
  const body = { eval_name: 'is_json', inputs: { output: '{"answer":42}' }, is_async: false };
  let calls = 0;
  const result = { status: true, result: [{ evaluations: [{ name: 'is_json', output: true, runtime: 0 }] }] };
  const client = new sdk.FutureAGIClient({
    apiKey: 'personal-fixture', secretKey: 'personal-fixture-secret',
    baseUrl: 'http://127.0.0.1:9019', retries: 0,
    fetch: async (request) => {
      calls++;
      assert.equal(request.url, 'http://127.0.0.1:9019/sdk/api/v1/new-eval/');
      assert.equal(request.method, 'POST');
      assert.equal(request.headers.get('X-Api-Key'), 'personal-fixture');
      assert.deepEqual(await request.json(), body);
      return new Response(JSON.stringify(result), { headers: { 'Content-Type': 'application/json' } });
    },
  });
  assert.equal(client.evals.evaluate, undefined);
  assert.deepEqual(await client.evals.runV2(body), result);
  assert.equal(calls, 1);
  const missing = new sdk.FutureAGIClient({ apiKey: '', secretKey: '', fetch: () => { throw new Error('Unexpected transport'); } });
  await assert.rejects(missing.evals.runV2(body), sdk.CredentialsMissingError);
`;
for (const mode of ["module", "commonjs"]) {
  const load = mode === "module"
    ? `const sdk = await import('@future-agi/sdk');`
    : `const sdk = require('@future-agi/sdk');`;
  const absence = mode === "module"
    ? `await assert.rejects(import('@future-agi/sdk/evals'), { code: 'ERR_PACKAGE_PATH_NOT_EXPORTED' });`
    : `assert.throws(() => require('@future-agi/sdk/evals'), { code: 'ERR_PACKAGE_PATH_NOT_EXPORTED' });`;
  const code = `(async () => { ${load} ${checks} ${absence} })().catch(e => { console.error(e); process.exitCode = 1; });`;
  const run = spawnSync(process.execPath, [`--input-type=${mode}`, "--eval", code], {
    cwd: consumer, encoding: "utf8", env: { ...process.env, FI_API_KEY: "", FI_SECRET_KEY: "", FI_EXTRA_HEADERS: "" },
  });
  assert.equal(run.status, 0, `${mode}: ${run.stderr || run.error || run.stdout}`);
}
process.stdout.write("PASS: evals artifact absence, ESM/CJS import refusal, and deterministic REST contracts\n");
