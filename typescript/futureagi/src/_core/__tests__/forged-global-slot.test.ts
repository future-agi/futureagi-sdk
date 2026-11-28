/**
 * A dispatcher the application writes itself (classes named `Agent` and `Pool`, with a `factory` slot) and puts in the
 * runtime's global dispatcher slot before the SDK is loaded does not stand for the runtime's own copy of undici: the
 * SDK counts it as proxied, refuses a keyed plain-http send through it, and the proxy sink it writes to sees no
 * connection and no marker. The dispatcher stays in the slot. Each case runs in a fresh child process.
 */
import { execFile } from "node:child_process";
import { join } from "node:path";

import { CountingSink, proxyEnvironment } from "../__fixtures__/proxy-sink";

const MARKER_KEY = "marker-forgedslot-key-0000000000";
const MARKER_SECRET = "marker-forgedslot-secret-0000000000";
const proxySink = new CountingSink([MARKER_KEY, MARKER_SECRET]);
const targetSink = new CountingSink([MARKER_KEY, MARKER_SECRET]);
let restoreEnv: () => void = () => undefined;
beforeAll(async () => {
  restoreEnv = proxyEnvironment();
  await Promise.all([proxySink.listen(), targetSink.listen()]);
});
afterAll(async () => { restoreEnv(); await Promise.all([proxySink.close(), targetSink.close()]); });
beforeEach(() => { proxySink.reset(); targetSink.reset(); });

async function probe(slot: "assign" | "define"): Promise<{ outcome: string; proxied: boolean; kept: boolean }> {
  const tsx = require.resolve("tsx/cli");
  const env: NodeJS.ProcessEnv = { ...process.env, PROBE_SLOT: slot, PROBE_PROXY_PORT: String(proxySink.port), PROBE_TARGET_PORT: String(targetSink.port), PROBE_KEY: MARKER_KEY, PROBE_SECRET: MARKER_SECRET };
  const stdout = await new Promise<string>((resolve, reject) => {
    execFile(process.execPath, [tsx, join(__dirname, "../__fixtures__/forged-slot-probe.ts")], { encoding: "utf8", timeout: 60_000, env }, (error, out, err) => (error ? reject(new Error(`${String(error)} ${err}`)) : resolve(out)));
  });
  return JSON.parse(stdout.trim().split("\n").pop() ?? "{}") as { outcome: string; proxied: boolean; kept: boolean };
}

describe("a dispatcher of the application's own put in the global dispatcher slot before the SDK is loaded", () => {
  it.each(["assign", "define"] as const)("is counted as proxied and gets no keyed send (slot set by %s)", async (slot) => {
    const result = await probe(slot);
    expect({ connections: proxySink.connections, markers: proxySink.markerCount }).toEqual({ connections: 0, markers: 0 });
    expect(result.proxied).toBe(true);
    expect(result.outcome).toBe("error:ConfigurationError");
    expect(result.kept).toBe(true);
    expect(targetSink.markerCount).toBe(0);
  }, 90_000);
});
