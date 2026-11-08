#!/usr/bin/env node
/** Compile the run subpath in an installed tarball consumer with both supported TS resolvers. */
import { writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";

const consumer = resolve(process.argv[2]);
const absent = process.argv.includes("--expect-absent");
writeFileSync(resolve(consumer, "runs-consumer.ts"), `
import { Run, Runs, Ratings } from "@future-agi/sdk/agents/runs";
declare const run: Run;
declare const runs: Runs;
declare const ratings: Ratings;
const completed: Promise<Run> = run.wait({ timeout: 1 });
const created: Promise<Run> = runs.create({ input: "hello", wait: true });
void [completed, created, ratings.summary()];
`);
let failed = false;
for (const [resolution, module] of [["node", "CommonJS"], ["Node16", "Node16"]]) {
  const result = spawnSync(process.execPath, [resolve(consumer, "node_modules/typescript/bin/tsc"),
    "--noEmit", "--strict", "--target", "ES2022", "--esModuleInterop", "--skipLibCheck",
    "--module", module, "--moduleResolution", resolution, "runs-consumer.ts"], { cwd: consumer, encoding: "utf8" });
  const output = `${result.stdout ?? ""}${result.stderr ?? ""}`;
  const diagnostics = output.match(/error TS\d+:/g) ?? [];
  const ok = absent ? result.status === 2 && diagnostics.length === 1 && diagnostics[0] === "error TS2307:" && output.includes("@future-agi/sdk/agents/runs") : result.status === 0;
  console.log(`${resolution}: ${ok ? "PASS" : "FAIL"} (${absent ? "absent" : "resolved"})`);
  if (!ok) { console.error(output || result.error); failed = true; }
}
process.exitCode = failed ? 1 : 0;
