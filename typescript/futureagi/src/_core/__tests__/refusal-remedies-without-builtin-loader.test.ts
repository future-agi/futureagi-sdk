import { execFile } from "node:child_process";
import { join } from "node:path";
import { promisify } from "node:util";

interface Counts { connections: number; bytes: number; markers: number }
interface Result {
  outcome: string;
  code?: string;
  message?: string;
  markerInMessage?: boolean;
  target: Counts;
  proxy: Counts;
}

const empty = { connections: 0, bytes: 0, markers: 0 };
const unproven = "Load the SDK as CommonJS, or run it on a Node.js that provides process.getBuiltinModule.";
const globalAgent = "Load the SDK as CommonJS and install an Agent of the undici package with that package's setGlobalDispatcher";
const https = ", or set the base URL to an https:// address on a host that is not loopback.";
const probe = join(__dirname, "../__fixtures__/refusal-remedies-without-builtin-loader-probe.mjs");

const rows = [
  { host: "local", dispatcher: "none", ending: unproven, steps: ["commonjs", "builtin"] },
  { host: "local", dispatcher: "global", ending: unproven, steps: ["commonjs", "builtin"] },
  { host: "local", dispatcher: "foreign", ending: `${globalAgent}.`, steps: ["commonjs-global"] },
  { host: "named", dispatcher: "none", ending: globalAgent + https, steps: ["commonjs-global", "https"] },
  { host: "named", dispatcher: "global", ending: globalAgent + https, steps: ["commonjs-global", "https"] },
];

it.each(rows)("keyed HTTP to $host with $dispatcher dispatcher: remedies for an ES module without the built-in loader", async ({ host, dispatcher, ending, steps }) => {
  const runnable = steps.filter((step) => step !== "builtin" || typeof process.getBuiltinModule === "function");
  const { stdout } = await promisify(execFile)(process.execPath, [probe, "scenario", host, dispatcher, ...runnable], { timeout: 55_000 });
  const results = JSON.parse(stdout) as Record<string, Result>;
  for (const [step, { outcome, code, target, proxy }] of Object.entries(results)) {
    process.stdout.write(`platform ${host}/${dispatcher} ${step}: ${outcome}${code ? `:${code}` : ""} target=${target.bytes}B/${target.markers} markers proxy=${proxy.bytes}B\n`);
  }
  const first = results.initial;
  expect(first).toMatchObject({
    outcome: "ConfigurationError", code: "insecure_http_origin", markerInMessage: false,
    moduleForm: "esm", usingBuiltin: false, loaderReadsHttp: false, target: empty, proxy: empty,
  });
  for (const step of runnable) {
    const isCommonJS = step.startsWith("commonjs");
    expect(results[step]).toMatchObject({
      outcome: "delivered", moduleForm: isCommonJS ? "cjs" : "esm", usingBuiltin: step === "builtin",
      loaderReadsHttp: isCommonJS || step === "builtin", target: { connections: 1, markers: 1 }, proxy: empty,
    });
    expect(results[step].target.bytes).toBeGreaterThan(0);
  }
  expect(first.message).not.toMatch(/(?:Install|Pass) an Agent of the undici package|Install the undici package/u);
  expect(first.message?.slice(-ending.length)).toBe(ending);
}, 60_000);
