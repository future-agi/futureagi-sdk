/* These controls deliberately use APIs outside the process-local guard. */
const fs = require('node:fs');
const { spawnSync } = require('node:child_process');
const { Resolver } = require('node:dns').promises;
const guard = require('/kit/network_node.cjs').install();
(async () => {
  if (process.argv[2] === 'resolver') {
    const resolver = new Resolver({ timeout: 100, tries: 1 });
    resolver.setServers(['203.0.113.1']);
    try { await resolver.resolve4('consumer-control.invalid'); } catch {}
  } else {
    const code = process.argv[2] === 'child-tcp'
      ? "const s=require('node:net').connect(443,'203.0.113.1');s.on('error',()=>s.destroy());s.setTimeout(100,()=>s.destroy())"
      : "const s=require('node:dgram').createSocket('udp4');s.send('not-a-credential-payload',53,'203.0.113.1',()=>s.close())";
    const child = spawnSync(process.execPath, ['-e', code], { timeout: 5000 });
    if (child.status !== 0) throw new Error('Control child failed');
  }
  fs.writeFileSync('/result/probe.json', JSON.stringify({ checks: [{ name: 'install.control', state: 'PASS' }], network: guard.evidence }));
})().catch(error => { console.error(error); process.exitCode = 1; });
