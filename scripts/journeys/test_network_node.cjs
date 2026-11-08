const assert = require('node:assert/strict');
const { install, loopback } = require('./network_node.cjs');
const guard = install();
const net = require('node:net');
const dns = require('node:dns');
async function main() {
  assert.equal(loopback('127.0.0.1.example'), false);
  assert.equal(loopback('::1'), true);
  assert.throws(() => net.connect(443, '203.0.113.1'), /network guard/);
  assert.throws(() => dns.lookup('api.futureagi.com', () => {}), /network guard/);
  await assert.rejects(fetch('https://api.openai.com'), /network guard/);
  await assert.rejects(dns.promises.lookup('api.anthropic.com'), /network guard/);
  assert.equal(guard.evidence.denied_count, 4);
  console.log('Node network guard: four forbidden destinations refused before resolution or connection');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
