/* The probe is copied to /consumer, never into the extracted candidate. */
const fs = require('node:fs');
const { install } = require('/kit/network_node.cjs');
const { demand, run: config } = require('/kit/config_node.cjs');
const guard = install();
const checks = [];
async function check(name, action) {
  try { await action(); checks.push({ name, state: 'PASS' }); }
  catch (error) { checks.push({ name, state: 'FAIL', reason: error.code || error.constructor.name }); }
}
function skip(name, reason) { checks.push({ name, state: 'NOT-EVALUATED', reason }); }
async function main() {
  const policy = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const pkg = JSON.parse(fs.readFileSync('/consumer/node_modules/@future-agi/sdk/package.json', 'utf8'));
  await check('install.no-fi-script', () => demand(!(pkg.bin && typeof pkg.bin === 'object' && 'fi' in pkg.bin)));
  for (const mode of ['esm', 'cjs']) {
    const load = spec => mode === 'esm' ? import(spec) : Promise.resolve(require(spec));
    await check('install.' + mode + '.probe', async () => {
      const sdk = await load('@future-agi/sdk');
      await check('install.' + mode + '.client', () => new sdk.FutureAGIClient());
      const exports = new Set(['.', ...Object.keys(pkg.exports || {}), ...policy.node_entries]);
      for (const path of exports) {
        const spec = path === '.' ? '@future-agi/sdk' : '@future-agi/sdk/' + path.replace(/^\.\//, '');
        await check('install.' + mode + '.import.' + path, () => load(spec));
      }
      const client = new sdk.FutureAGIClient();
      for (const [namespace, spec] of Object.entries(policy.surfaces)) {
        if (policy.states[namespace].ts !== 'OFF') continue;
        for (const path of spec.ts_subpaths) {
          await check('absence.' + namespace + '.' + mode + '.subpath.' + path, async () => {
            try { await load('@future-agi/sdk/' + path); }
            catch (error) { demand(error.code === 'ERR_PACKAGE_PATH_NOT_EXPORTED'); return; }
            throw new Error('OFF subpath importable');
          });
        }
        for (const symbol of spec.root_exports) {
          await check('absence.' + namespace + '.' + mode + '.root-export.' + symbol, () => demand(!(symbol in sdk)));
        }
        for (const path of spec.ts_accessors) {
          await check('absence.' + namespace + '.' + mode + '.accessor.' + path, () => {
            let value = client;
            for (const part of path.split('.')) {
              if (value == null || !(part in value)) return;
              value = value[part];
            }
            throw new Error('OFF accessor present');
          });
        }
      }
      if (mode === 'esm' && process.env.CONSUMER_CONFIG === '1') await check('config.probe', () => config(check, skip, policy, sdk, load));
    });
  }
  const result = { runtime: process.version, checks, network: guard.evidence };
  fs.writeFileSync(process.argv[3], JSON.stringify(result, null, 2) + '\n');
  process.exitCode = Number(checks.some(c => c.state === 'FAIL') || guard.evidence.denied_count > 0);
}
main().catch(error => {
  fs.writeFileSync(process.argv[3], JSON.stringify({ checks: [{ name: 'install.probe', state: 'FAIL', reason: error.constructor.name }], network: guard.evidence }));
  process.exitCode = 1;
});
