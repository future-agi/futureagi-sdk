/**
 * The SDK finds the `undici` package from its own module file whatever the application did to the V8 stack settings
 * before the SDK loaded: with a non-writable `Error.prepareStackTrace` it reads the first frame of the stack text, and
 * it puts both settings back as they were. With a non-writable `Error.stackTraceLimit` of 0 there is no frame to read,
 * and the loader finds no package (a keyed loopback send then goes through the SDK's node:http transport).
 */
import { execFile } from "node:child_process";
import { join } from "node:path";
import { promisify } from "node:util";

const run = promisify(execFile);
const tsx = require.resolve("tsx/cli");
const probe = join(__dirname, "../__fixtures__/module-loader-stack-settings-probe.mjs");
const loader = join(__dirname, "../module-loader.ts");

async function observe(mode: string): Promise<Record<string, unknown>> {
  const { stdout } = await run(process.execPath, [tsx, probe, loader], { env: { ...process.env, PROBE_STACK: mode }, timeout: 30_000 });
  const row = JSON.parse(stdout.trim().split("\n").pop() ?? "{}") as Record<string, unknown>;
  process.stdout.write(`module-loader ${mode}: ${JSON.stringify(row)}\n`);
  return row;
}

describe("the module loader and the application's stack settings", () => {
  it.each(["default", "locked-formatter"])("%s: finds the undici package and keeps both settings", async (mode) => {
    expect(await observe(mode)).toEqual({ mode, undiciAgent: "function", prepareKept: true, limitKept: true });
  }, 40_000);

  it("zero-limit: keeps both settings and finds no package", async () => {
    expect(await observe("zero-limit")).toEqual({ mode: "zero-limit", undiciAgent: "undefined", prepareKept: true, limitKept: true });
  }, 40_000);
});
