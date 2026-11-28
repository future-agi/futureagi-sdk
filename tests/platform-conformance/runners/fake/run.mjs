#!/usr/bin/env node
// The fake runner shell: runners/sdk/run.mjs with --lang fake (see that file for every flag).
import { main } from "../sdk/run.mjs";

main(["--lang", "fake", ...process.argv.slice(2)]).then((code) => process.exit(code), (error) => {
  process.stderr.write(`fake runner: ${error.message}\n`);
  process.exit(2);
});
