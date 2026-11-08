// Offline, exact-revision proof driver. Installs are performed separately.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const ROOT = process.env.SDK_REPO_ROOT;
const HELPERS = process.env.SDK_HELPER_ROOT ?? ROOT;
const OUT = process.env.SDK_OUTPUT_DIR;
if (!ROOT || !OUT || !process.env.SDK_COMMIT || !process.env.SDK_TREE) throw new Error('Explicit proof paths and revision required');
fs.mkdirSync(OUT); // Every run owns a new, empty output directory.
const PKG = path.join(ROOT, 'typescript/futureagi/gateway-client');
const HELPER_PKG = path.join(HELPERS, 'typescript/futureagi/gateway-client');
const BASE = process.env.SDK_BASE === 'true';
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const write = (name, data) => fs.writeFileSync(path.join(OUT, name), JSON.stringify(data, null, 2) + '\n', { flag: 'wx' });
function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => {
    const file = path.join(dir, e.name);
    return e.isDirectory() ? walk(file) : e.isFile() ? [file] : [];
  }).sort();
}
const checks = [];
function run(name, args, expected = 'zero') {
  const result = spawnSync(process.execPath, args, { cwd: PKG, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024, timeout: 600000, env: process.env });
  const stdout = result.stdout ?? '', stderr = result.stderr ?? '';
  checks.push({ name, exit: result.status, signal: result.signal, error: result.error?.code ?? null, expected,
    stdout_sha256: hash(stdout), stderr_sha256: hash(stderr), stdout_tail: stdout.slice(-4000), stderr_tail: stderr.slice(-4000) });
  return result.status === 0;
}
const jest = (name, files = []) => run(name, ['node_modules/jest/bin/jest.js', '-c', 'jest.config.cjs', '--runInBand', '--ci', ...(files.length ? ['--runTestsByPath', ...files] : []), '--json', '--outputFile=' + path.join(OUT, name + '.raw.json')], BASE && name.startsWith('overlay-') ? 'behavioral-red' : 'zero');
run('typecheck-source', ['node_modules/typescript/bin/tsc', '-p', 'tsconfig.json', '--noEmit']);
run('typecheck-tests', ['node_modules/typescript/bin/tsc', '-p', 'tsconfig.typecheck.json']);
const built = run('build', ['scripts/build.cjs']);
const buildRoot = path.join(ROOT, 'typescript/futureagi/dist/gateway');
if (built) write('build-manifest.json', {
  head_sha: process.env.SDK_COMMIT, tree_sha: process.env.SDK_TREE, node: process.version,
  typescript: require(path.join(PKG, 'node_modules/typescript/package.json')).version,
  source_sha256_by_file: Object.fromEntries(walk(path.join(PKG, 'src')).map(f => [path.relative(ROOT, f), hash(fs.readFileSync(f))])),
  build_sha256_by_file: Object.fromEntries(walk(buildRoot).map(f => [path.relative(buildRoot, f), hash(fs.readFileSync(f))])),
  fresh_esm: true, fresh_cjs: true,
});
jest('ci-jest');
if (fs.existsSync(path.join(OUT, 'ci-jest.raw.json'))) run('ported-test-names', ['scripts/check-test-names.cjs', path.join(OUT, 'ci-jest.raw.json')]);
run('ci-parity', ['--test', 'tests/parity/compare.test.mjs', 'tests/parity/hygiene.test.mjs']);
jest('body-evidence', ['tests/response-body-evidence.test.ts', 'tests/resource-body-evidence.test.ts']);
run('labels', ['--test', 'tests/parity/onekey-labels.test.mjs']);
// Preserve the base's original CI result; overlay only tests from the final head.
const overlay = ['tests/unknown-dispatch-cases.cjs', 'tests/unknown-dispatch.test.ts', 'tests/unknown-dispatch-built.test.mjs', 'tests/parity/onekey-labels.test.mjs', 'tests/body-failure-guidance-cases.cjs', 'tests/body-failure-guidance.test.ts', 'tests/body-failure-guidance-built.test.mjs'];
if (BASE) for (const file of overlay) fs.copyFileSync(path.join(HELPER_PKG, file), path.join(PKG, file));
write('test-input-manifest.json', { commit: process.env.SDK_HELPER_COMMIT ?? process.env.SDK_COMMIT,
  files: Object.fromEntries(overlay.map(f => [f, hash(fs.readFileSync(path.join(PKG, f)))])) });
run('overlay-labels', ['--test', 'tests/parity/onekey-labels.test.mjs'], BASE ? 'behavioral-red' : 'zero');
jest('overlay-dispatch', ['tests/unknown-dispatch.test.ts']);
jest('overlay-guidance', ['tests/body-failure-guidance.test.ts']);
if (built) {
  run('built-dispatch', ['--test', 'tests/unknown-dispatch-built.test.mjs'], BASE ? 'behavioral-red' : 'zero');
  run('built-guidance', ['--test', 'tests/body-failure-guidance-built.test.mjs'], BASE ? 'behavioral-red' : 'zero');
  run('parity-generation', [path.join(HELPER_PKG, 'tests/parity/generate-refusal-table.cjs')]);
}
const suites = {};
for (const name of ['ci-jest', 'body-evidence', 'overlay-dispatch', 'overlay-guidance']) {
  const file = path.join(OUT, name + '.raw.json');
  if (!fs.existsSync(file)) continue;
  const j = JSON.parse(fs.readFileSync(file));
  const reduced = { passed: j.numPassedTests, failed: j.numFailedTests, pending: j.numPendingTests, suites: j.numTotalTestSuites, runtime_error_suites: j.numRuntimeErrorTestSuites,
    tests: j.testResults.flatMap(r => r.assertionResults.map(t => ({ file: path.relative(ROOT, r.name), name: t.fullName, status: t.status, failure: t.failureMessages.join('\n').slice(-3000) }))),
    suite_errors: j.testResults.filter(r => r.status === 'failed' && !r.assertionResults.some(t => t.status === 'failed')).map(r => ({ file: path.relative(ROOT, r.name), message: r.message.slice(-4000) })) };
  write(name + '.json', reduced);
  suites[name] = { passed: reduced.passed, failed: reduced.failed, pending: reduced.pending, runtime_error_suites: reduced.runtime_error_suites };
}
const unexpected = checks.filter(c => c.expected === 'zero' ? c.exit !== 0 : c.exit === 0 || c.exit === null);
write('proof-summary.json', { commit: process.env.SDK_COMMIT, tree: process.env.SDK_TREE, base: BASE, node: process.version, recorded_at: new Date().toISOString(), checks, suites, unexpected: unexpected.map(c => c.name) });
// Only reduced JSON and short tails leave the sandbox; no complete logs.
for (const file of walk(OUT)) {
  if (!file.endsWith('.json') || file.endsWith('.raw.json')) continue;
  const bytes = fs.readFileSync(file);
  console.log('SDK_ARTIFACT ' + JSON.stringify({ name: path.basename(file), sha256: hash(bytes), data_base64: bytes.toString('base64') }));
}
process.exitCode = unexpected.length || Object.values(suites).some(s => s.runtime_error_suites) ? 1 : 0;
