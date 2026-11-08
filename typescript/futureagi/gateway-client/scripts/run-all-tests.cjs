#!/usr/bin/env node
// `pnpm test` of typescript/futureagi once the gateway subpaths are
// registered in its package.json (registration-fragment.json scripts.test):
//
//   node gateway-client/scripts/run-all-tests.cjs [jest args...]
//
// Runs, in order:
//   1. the root jest (package.json "jest", roots <rootDir>/src) with the
//      arguments exactly as given;
//   2. the gateway client's jest (gateway-client/jest.config.cjs) with the
//      same arguments, so CI's `pnpm test --runInBand` reaches both and the
//      root run is what it was;
//   3. the parity comparator and golden hygiene tests with node's own test
//      runner (gateway-client/tests/parity/compare.test.mjs and
//      hygiene.test.mjs; they take no jest arguments).
// Every run happens even when an earlier one fails; the exit code is the
// first non-zero one. jest resolves from gateway-client/node_modules when
// that toolchain is installed, else from the root package.
"use strict";
const { spawnSync } = require("node:child_process");
const { existsSync } = require("node:fs");
const { join } = require("node:path");

const pkgDir = join(__dirname, "..", "..");
const gatewayDir = join(__dirname, "..");
const args = process.argv.slice(2);

const rootJest = require.resolve("jest/bin/jest", { paths: [pkgDir] });
const gatewayJest = existsSync(join(gatewayDir, "node_modules", "jest"))
  ? require.resolve("jest/bin/jest", { paths: [gatewayDir] })
  : rootJest;

/** The parity node tests, relative to typescript/futureagi. */
const PARITY_TESTS = ["compare.test.mjs", "hygiene.test.mjs"].map((f) => join("gateway-client", "tests", "parity", f));

function spawn(label, argv) {
  process.stdout.write(`\n== ${label}: node ${argv.join(" ")}\n`);
  const result = spawnSync(process.execPath, argv, { cwd: pkgDir, stdio: "inherit" });
  if (result.error) {
    process.stderr.write(`${label}: ${result.error.message}\n`);
    return 1;
  }
  return result.status === null ? 1 : result.status;
}

const root = spawn("@future-agi/sdk jest", [rootJest, ...args]);
const gateway = spawn("@future-agi/sdk/gateway* jest", [gatewayJest, "-c", join("gateway-client", "jest.config.cjs"), ...args]);
const parity = spawn("@future-agi/sdk/gateway* parity", ["--test", ...PARITY_TESTS]);
process.stdout.write(`\n== exit: @future-agi/sdk ${root}, @future-agi/sdk/gateway* ${gateway}, parity ${parity}\n`);
process.exit([root, gateway, parity].find((code) => code !== 0) ?? 0);
