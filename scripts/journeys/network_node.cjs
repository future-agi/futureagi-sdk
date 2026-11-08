/* Runtime guard installed before loading any candidate module. */
const net = require('node:net');
const dns = require('node:dns');
const dgram = require('node:dgram');
const { syncBuiltinESMExports } = require('node:module');
function loopback(host) {
  host = String(host).replace(/^\[|\]$/g, '');
  return host === 'localhost' || host === '::1' || host === '0:0:0:0:0:0:0:1' ||
    (net.isIP(host) === 4 && host.split('.')[0] === '127');
}
function install() {
  const evidence = { denied_count: 0, denied: [], loopback_count: 0 };
  function check(host) {
    if (loopback(host)) { evidence.loopback_count++; return; }
    evidence.denied_count++;
    evidence.denied.push({ host: String(host), phase: 'runtime' });
    const error = new Error('Consumer network guard refused a non-loopback destination');
    error.code = 'CONSUMER_EGRESS_REFUSED';
    throw error;
  }
  for (const key of ['lookup', 'resolve', 'resolve4', 'resolve6', 'resolveAny']) {
    if (typeof dns[key] !== 'function') continue;
    const original = dns[key];
    dns[key] = function(host, ...args) { check(host); return original.call(this, host, ...args); };
    if (typeof dns.promises[key] === 'function') {
      const originalPromise = dns.promises[key];
      dns.promises[key] = async function(host, ...args) { check(host); return originalPromise.call(this, host, ...args); };
    }
  }
  const connect = net.Socket.prototype.connect;
  net.Socket.prototype.connect = function(...args) {
    // net.connect passes its already-normalized [options, callback] array to
    // Socket.connect; normalizing that outer array again loses host entirely.
    const normalized = net._normalizeArgs(Array.isArray(args[0]) ? args[0] : args)[0];
    if (!normalized.path) check(normalized.host || 'localhost');
    return connect.apply(this, args);
  };
  const send = dgram.Socket.prototype.send;
  dgram.Socket.prototype.send = function(...args) {
    const address = args.slice(1).find(x => typeof x === 'string');
    check(address || '127.0.0.1');
    return send.apply(this, args);
  };
  const originalFetch = globalThis.fetch;
  if (originalFetch) globalThis.fetch = async function(input, init) {
    check(new URL(typeof input === 'string' || input instanceof URL ? input : input.url).hostname);
    return originalFetch(input, init);
  };
  syncBuiltinESMExports();
  return { evidence, check };
}
module.exports = { install, loopback };
