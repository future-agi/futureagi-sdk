/**
 * When the runtime's own copy of undici is loaded before anything else (the `Request` global was touched, or the
 * process started with NODE_USE_ENV_PROXY=1), the runtime has made its agent and does not make another, and an
 * application can then put its own dispatcher in the global dispatcher slot in the form the runtime gives it. A
 * dispatcher of a subclass of the `undici` package's `Agent` whose `dispatch` hands requests to a `ProxyAgent` is not
 * the runtime's agent: the SDK loaded after it does not take its class for the runtime's own, does not build that
 * class, counts the dispatcher as proxied, and an opted-in keyed plain-http send puts no marker byte on the proxy sink
 * (refused, or sent to the host directly). Loading the SDK before the slot is set is the comparison case that shows the
 * sink counts nothing when the SDK reads the runtime's real agent. Each case runs in a fresh child process.
 */
import { execFile } from "node:child_process";
import { join } from "node:path";

import { CountingSink, proxyEnvironment } from "../__fixtures__/proxy-sink";

const MARKER_KEY = "marker-preloadedslot-key-0000000000";
const MARKER_SECRET = "marker-preloadedslot-secret-0000000000";
const proxySink = new CountingSink([MARKER_KEY, MARKER_SECRET]);
const targetSink = new CountingSink([MARKER_KEY, MARKER_SECRET]);
let restoreEnv: () => void = () => undefined;
beforeAll(async () => {
  restoreEnv = proxyEnvironment();
  await Promise.all([proxySink.listen(), targetSink.listen()]);
});
afterAll(async () => { restoreEnv(); await Promise.all([proxySink.close(), targetSink.close()]); });
beforeEach(() => { proxySink.reset(); targetSink.reset(); });

type Preload = "request" | "env-proxy";
interface Result { before: string; preloaded: string; form: string; outcome: string; proxied: boolean; constructed: number }

async function probe(preload: Preload, order: "slot-first" | "sdk-first"): Promise<Result> {
  const tsx = require.resolve("tsx/cli");
  const env: NodeJS.ProcessEnv = {
    ...process.env, PROBE_PRELOAD: preload, PROBE_ORDER: order,
    PROBE_PROXY_PORT: String(proxySink.port), PROBE_TARGET_PORT: String(targetSink.port), PROBE_KEY: MARKER_KEY, PROBE_SECRET: MARKER_SECRET,
    ...(preload === "env-proxy" ? { NODE_USE_ENV_PROXY: "1", HTTP_PROXY: `http://127.0.0.1:${proxySink.port}`, NO_PROXY: "plain.example.test,localhost,127.0.0.1,::1" } : {}),
  };
  const stdout = await new Promise<string>((resolve, reject) => {
    execFile(process.execPath, [tsx, join(__dirname, "../__fixtures__/preloaded-runtime-slot-probe.ts")], { encoding: "utf8", timeout: 60_000, env }, (error, out, err) => (error ? reject(new Error(`${String(error)} ${err}`)) : resolve(out)));
  });
  return JSON.parse(stdout.trim().split("\n").pop() ?? "{}") as Result;
}

/** What the proxy sink saw, printed so the count is visible in the run log. */
function seen(label: string, result: Result): { tunnels: number; markers: number } {
  const counts = { tunnels: proxySink.tunnels, markers: proxySink.markerCount };
  process.stdout.write(`${label}: proxy sink tunnels=${counts.tunnels} markers=${counts.markers} target markers=${targetSink.markerCount} ${JSON.stringify(result)}\n`);
  return counts;
}

const [major, minor] = process.versions.node.split(".").map(Number) as [number, number];
// the runtime reads NODE_USE_ENV_PROXY from Node.js 22.21 on in the 22 line, and in 24
const envProxyHonoured = major >= 24 || (major === 22 && minor >= 21) || major === 23;
const preloads: Preload[] = ["request", "env-proxy"];

describe("an application's proxying Agent subclass put in the global dispatcher slot after the runtime's undici is loaded", () => {
  for (const preload of preloads) {
    const run = preload === "env-proxy" && !envProxyHonoured ? it.skip : it;
    const label = `platform, runtime undici loaded by ${preload === "request" ? "touching Request" : "NODE_USE_ENV_PROXY=1"}`;

    run(`${label}: the keyed send puts no marker on the proxy sink and the SDK does not build the application's class`, async () => {
      const result = await probe(preload, "slot-first");
      const counts = seen(label, result);
      expect([result.before, result.preloaded]).toEqual(preload === "request" ? ["empty", "Agent:--w"] : ["EnvHttpProxyAgent:--w", "EnvHttpProxyAgent:--w"]);
      expect(result.form).toBe("ProxyingAgent:--w");
      expect(counts.markers).toBe(0);
      expect(counts.tunnels).toBe(0);
      expect(result.proxied).toBe(true);
      expect(result.constructed).toBe(0);
    }, 90_000);

    run(`${label}: with the SDK loaded before the slot is set, the proxy sink counts no marker`, async () => {
      const result = await probe(preload, "sdk-first");
      const counts = seen(`${label} (SDK first)`, result);
      expect([result.before, result.preloaded]).toEqual(preload === "request" ? ["empty", "Agent:--w"] : ["EnvHttpProxyAgent:--w", "EnvHttpProxyAgent:--w"]);
      expect(result.form).toBe("ProxyingAgent:--w");
      expect(counts.markers).toBe(0);
      expect(result.proxied).toBe(true);
      expect(result.constructed).toBe(0);
    }, 90_000);
  }

  if (!envProxyHonoured) {
    it.skip(`NODE_USE_ENV_PROXY cases: Node.js ${process.versions.node} does not read NODE_USE_ENV_PROXY (22.21 and 24 do)`, () => undefined);
  }
});
