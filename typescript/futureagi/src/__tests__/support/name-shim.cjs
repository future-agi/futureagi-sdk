// Resolves the test host name below to the loopback address; every other name resolves as usual.
const dns = require("node:dns");

const HOST = "guard-target.futureagi.com";
const original = dns.lookup;

dns.lookup = function lookup(hostname, options, callback) {
  if (typeof options === "function") {
    callback = options;
    options = {};
  }
  if (String(hostname).toLowerCase() === HOST) {
    const all = typeof options === "object" && options !== null && options.all === true;
    process.nextTick(() => (all ? callback(null, [{ address: "127.0.0.1", family: 4 }]) : callback(null, "127.0.0.1", 4)));
    return {};
  }
  return original.call(dns, hostname, options, callback);
};
