/**
 * The runtime's environment proxy (`NODE_USE_ENV_PROXY=1`, Node 24) routes a request made through the runtime's default
 * HTTP agent, which axios uses when no agent is given. A keyed plain-http request of `HttpClient` / `APIKeyAuth` that the
 * opt-in allows goes straight to its host: its key bytes reach the target and no proxy. The child process is a real
 * runtime with the variable on; the listeners are the parent's loopback sockets, counted by connections and raw marker bytes.
 */
import { execFile } from "node:child_process";
import { join } from "node:path";

import { MARKER_KEY, Sink } from "../__fixtures__/plaintext-sinks";

const target = new Sink();
const proxy = new Sink("502 Bad Gateway");

beforeAll(async () => { await Promise.all([target.listen(), proxy.listen()]); });
afterAll(() => { target.close(); proxy.close(); });
beforeEach(() => { target.reset(); proxy.reset(); });

function runChild(extra: Record<string, string>): Promise<Record<string, string>> {
  const tsx = require.resolve("tsx/cli");
  const probe = join(__dirname, "../__fixtures__/axios-env-proxy-probe.ts");
  const env = {
    ...process.env, NODE_USE_ENV_PROXY: "1", PROBE_TARGET_PORT: String(target.port), PROBE_KEY: MARKER_KEY,
    HTTP_PROXY: `http://127.0.0.1:${proxy.port}`, http_proxy: `http://127.0.0.1:${proxy.port}`,
    HTTPS_PROXY: `http://127.0.0.1:${proxy.port}`, ALL_PROXY: `http://127.0.0.1:${proxy.port}`, ...extra,
  } as NodeJS.ProcessEnv;
  delete env.NO_PROXY; delete env.no_proxy; delete env.FI_ALLOW_INSECURE_HTTP;
  return new Promise((resolve, reject) => {
    execFile(process.execPath, [tsx, probe], { env, timeout: 60_000 }, (error, stdout) => {
      if (error !== null && stdout === "") reject(error);
      else resolve(JSON.parse(stdout.trim().split("\n").pop() as string) as Record<string, string>);
    });
  });
}

// the runtime reads NODE_USE_ENV_PROXY from Node.js 24 on
const runtimeProxy = Number(process.versions.node.split(".")[0]) >= 24 ? describe : describe.skip;

runtimeProxy("with the runtime's environment proxy on", () => {
  it("sends a keyed plain-http request of HttpClient and APIKeyAuth to its host, not through the proxy", async () => {
    await runChild({});
    // the control fetch is the one request the proxy carries: the environment proxy is on, and it is the runtime's
    expect(proxy.requests).toBe(1);
    expect(target.requests).toBe(5);
    expect(target.markerBytes).toBeGreaterThanOrEqual(5);
    expect(proxy.markerBytes).toBe(0);
  }, 90_000);

  it("answers every keyed request from the target", async () => {
    const seen = await runChild({});
    expect([seen.keyedDefault, seen.keyedCall, seen.keyedLayer, seen.keyedAuth, seen.keyedPrefixed]).toEqual(["200", "200", "200", "200", "200"]);
  }, 90_000);
});
