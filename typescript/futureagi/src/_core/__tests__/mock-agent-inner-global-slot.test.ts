/**
 * An undici `MockAgent` sends every request it does not answer itself through the agent it holds. A `MockAgent` whose
 * agent hands requests to a proxy (`MockAgent({ agent: ProxyingAgent })`) is a proxying dispatcher: put in the
 * runtime's global dispatcher slot, in any form and under any load order, a keyed plain-http send of the platform client to
 * `127.0.0.1`, to `localhost`, or opted in to a name the shim answers with a loopback address, puts 0 marker bytes on
 * the proxy listener (the send is refused, or the SDK sends it to the host through a direct agent of its own).
 * With `MockAgent()` in the global slot, the SDK sends keyed requests to `127.0.0.1` and `localhost` through its own
 * direct transport. The mock answers sends to the opted-in `plain.example.test` because the URL host is not loopback,
 * even though the DNS shim maps it to a loopback address. Each load mode and slot form runs in a fresh child process
 * with per-send listener counts. A separate listener counts traffic routed by `NODE_USE_ENV_PROXY`.
 */
import { execFile } from "node:child_process";
import { join } from "node:path";

import { CountingSink, proxyEnvironment } from "../__fixtures__/proxy-sink";

const MARKER_KEY = "marker-mockagentinner-key-0000000000";
const MARKER_SECRET = "marker-mockagentinner-secret-0000000000";
const envProxySink = new CountingSink([MARKER_KEY, MARKER_SECRET]);
let restoreEnv: () => void = () => undefined;
beforeAll(async () => {
  restoreEnv = proxyEnvironment();
  await envProxySink.listen();
});
afterAll(async () => { restoreEnv(); await envProxySink.close(); });
beforeEach(() => { envProxySink.reset(); });

type Mode = "sdk-first" | "request" | "env-proxy" | "slot-first";
type Form = "setGlobalDispatcher" | "assign" | "define";
interface Row { sender: string; host: string; outcome: string; proxyMarkers: number; proxyTunnels: number; targetMarkers: number; targetConnections: number; mockAnswers: number }
interface Result { form: string; rows: Row[] }

async function probe(mode: Mode, form: Form, inner: "proxying" | "genuine"): Promise<Result> {
  const tsx = require.resolve("tsx/cli");
  const env: NodeJS.ProcessEnv = {
    ...process.env, PROBE_MODE: mode, PROBE_FORM: form, PROBE_INNER: inner, PROBE_KEY: MARKER_KEY, PROBE_SECRET: MARKER_SECRET,
    ...(mode === "env-proxy" ? { NODE_USE_ENV_PROXY: "1", HTTP_PROXY: `http://127.0.0.1:${envProxySink.port}`, NO_PROXY: "plain.example.test,localhost,127.0.0.1,::1" } : {}),
  };
  const stdout = await new Promise<string>((resolve, reject) => {
    execFile(process.execPath, [tsx, join(__dirname, "../__fixtures__/mock-agent-inner-probe.ts")], { encoding: "utf8", timeout: 60_000, env }, (error, out, err) => (error ? reject(new Error(`${String(error)} ${err}`)) : resolve(out)));
  });
  return JSON.parse(stdout.trim().split("\n").pop() ?? "{}") as Result;
}

/** Prints every row so the counts are visible in the run log. */
function report(label: string, result: Result): void {
  for (const row of result.rows) {
    process.stdout.write(`${label} [${result.form}] ${row.sender} -> ${row.host}: ${row.outcome}; proxy markers=${row.proxyMarkers} tunnels=${row.proxyTunnels}; target markers=${row.targetMarkers} connections=${row.targetConnections}; mock answers=${row.mockAnswers}; env proxy markers=${envProxySink.markerCount}\n`);
  }
}

const [major, minor] = process.versions.node.split(".").map(Number) as [number, number];
// the runtime reads NODE_USE_ENV_PROXY from Node.js 22.21 on in the 22 line, and in 24
const envProxyHonoured = major >= 24 || (major === 22 && minor >= 21) || major === 23;
const MODES: Mode[] = ["sdk-first", "request", "env-proxy", "slot-first"];
const FORMS: Form[] = ["setGlobalDispatcher", "assign", "define"];
const SENDERS = ["platform Client"];
const HOSTS = ["127.0.0.1", "localhost", "plain.example.test"];

describe("MockAgent({ agent: ProxyingAgent }) in the global dispatcher slot", () => {
  for (const mode of MODES) {
    for (const form of FORMS) {
      const run = mode === "env-proxy" && !envProxyHonoured ? it.skip : it;
      run(`load mode ${mode}, slot set by ${form}: every keyed plain-http send puts 0 marker bytes on the proxy listener`, async () => {
        const result = await probe(mode, form, "proxying");
        report(`${mode} proxying`, result);
        expect(result.form.startsWith("MockAgent:")).toBe(true);
        expect(result.rows.map((row) => `${row.sender} ${row.host}`)).toEqual(SENDERS.flatMap((sender) => HOSTS.map((host) => `${sender} ${host}`)));
        for (const row of result.rows) {
          const label = `${row.sender} -> ${row.host}`;
          expect({ label, markers: row.proxyMarkers, tunnels: row.proxyTunnels }).toEqual({ label, markers: 0, tunnels: 0 });
          // refused before any connection, or sent to the host through a direct agent of the SDK's
          const refused = row.outcome === "error:ConfigurationError:insecure_http_origin" || row.outcome === "error:ConfigurationError:caller_proxy";
          expect({ label, settled: refused || (row.outcome.startsWith("sent:") && row.targetMarkers > 0) }).toEqual({ label, settled: true });
          if (refused) expect({ label, connections: row.targetConnections }).toEqual({ label, connections: 0 });
        }
        expect(envProxySink.markerCount).toBe(0);
      }, 90_000);
    }
  }
  if (!envProxyHonoured) {
    it.skip(`NODE_USE_ENV_PROXY rows: Node.js ${process.versions.node} does not read NODE_USE_ENV_PROXY (22.21 and 24 do)`, () => undefined);
  }
});

describe("MockAgent() with no agent option in the global dispatcher slot", () => {
  for (const mode of MODES) {
    const run = mode === "env-proxy" && !envProxyHonoured ? it.skip : it;
    run(`load mode ${mode}: keyed loopback sends reach the target and the mock answers sends to the opted-in name`, async () => {
      const result = await probe(mode, "setGlobalDispatcher", "genuine");
      report(`${mode} genuine`, result);
      expect(result.form).toBe("MockAgent:--w");
      expect(result.rows.map((row) => `${row.sender} ${row.host}`)).toEqual(SENDERS.flatMap((sender) => HOSTS.map((host) => `${sender} ${host}`)));
      for (const row of result.rows) {
        const label = `${row.sender} -> ${row.host}`;
        const mockHandlesName = row.host === "plain.example.test";
        expect({ label, markers: row.proxyMarkers, tunnels: row.proxyTunnels }).toEqual({ label, markers: 0, tunnels: 0 });
        expect({ label, sent: row.outcome.startsWith("sent:"), answers: row.mockAnswers, markers: row.targetMarkers, connections: row.targetConnections })
          .toEqual({ label, sent: true, answers: mockHandlesName ? 1 : 0, markers: mockHandlesName ? 0 : 2, connections: mockHandlesName ? 0 : 1 });
      }
      expect(envProxySink.markerCount).toBe(0);
      expect(envProxySink.connections).toBe(0);
    }, 90_000);
  }
});
