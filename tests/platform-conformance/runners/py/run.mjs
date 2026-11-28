#!/usr/bin/env node
// The py runner shell: runners/sdk/run.mjs with --lang py (see that file for every flag).
import { main } from "../sdk/run.mjs";

main(["--lang", "py", ...process.argv.slice(2)]).then((code) => process.exit(code), (error) => {
  process.stderr.write(`py runner: ${error.message}\n`);
  process.exit(2);
});
