#!/usr/bin/env node
// Peer-dependency check for the packed-tarball installs:
//
//   node check-install-logs.cjs <out dir>
//
// Reads every npm install log pack-checks.sh wrote into <out dir>
// (install-*.log, matrix-install-*.log, matrix-tree-*.log, tsc-install.log)
// and fails when any of them has an ERESOLVE line. npm can resolve a peer
// conflict by overriding it ("npm warn ERESOLVE overriding peer dependency")
// and still exit 0, so the install step's exit code alone does not prove the
// optional react peer installs cleanly.
//
// Prints one JSON object { logs, eresolve: [{ log, line }] }. Exit 0 when no
// log has ERESOLVE, 1 when one does, 2 when there are no install logs at all
// (a check that read nothing must not pass).
"use strict";
const { readdirSync, readFileSync } = require("node:fs");
const { join } = require("node:path");

const INSTALL_LOG = /^(install-.*|matrix-install-.*|matrix-tree-.*|tsc-install)\.log$/;

function scan(dir) {
  const logs = readdirSync(dir).filter((name) => INSTALL_LOG.test(name)).sort();
  const eresolve = [];
  for (const log of logs) {
    for (const line of readFileSync(join(dir, log), "utf8").split("\n")) {
      if (line.includes("ERESOLVE")) eresolve.push({ log, line: line.trim() });
    }
  }
  return { logs, eresolve };
}

if (require.main === module) {
  const dir = process.argv[2];
  if (!dir) {
    process.stderr.write("usage: check-install-logs.cjs <out dir>\n");
    process.exit(2);
  }
  const result = scan(dir);
  process.stdout.write(JSON.stringify(result, null, 1) + "\n");
  process.exit(result.logs.length === 0 ? 2 : result.eresolve.length > 0 ? 1 : 0);
}

module.exports = { scan, INSTALL_LOG };
