#!/usr/bin/env node
// The ts runner shell: runners/sdk/run.mjs with --lang ts (see that file for every flag).
import { main } from "../sdk/run.mjs";

main(["--lang", "ts", ...process.argv.slice(2)]).then((code) => process.exit(code), (error) => {
  process.stderr.write(`ts runner: ${error.message}\n`);
  process.exit(2);
});
