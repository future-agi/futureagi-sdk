/**
 * A request to a loopback host when the process started with NODE_USE_ENV_PROXY=1 and a proxy variable set: the
 * runtime's undici loads at start-up and its `EnvHttpProxyAgent` is the global dispatcher, which applies NO_PROXY itself.
 *
 * - The runtime's fetch called bare is the comparison row and follows NO_PROXY exactly.
 * - A keyed send to the same host with the platform `Client` uses the SDK's direct transport regardless of NO_PROXY.
 *   The target receives the HTTP key markers or the HTTPS handshake attempt;
 *   the proxy receives neither a connection nor a marker.
 *
 * Rows: 127.0.0.1 and localhost, http:// and https:// (the target sink speaks no TLS, so an https row shows where the
 * connection went and ends in a handshake failure, not an answer), NO_PROXY listing the host or not. Each row runs in a
 * fresh child process with its own pair of sinks.
 */
import { execFile } from "node:child_process";
import { join } from "node:path";

import { CountingSink, proxyEnvironment } from "../__fixtures__/proxy-sink";

const MARKER_KEY = "marker-unkeyedloopback-key-0000000000";
const PATH_MARKER = "marker-unkeyedloopback-path-0000000000";
const CREDENTIAL_VARIABLES = ["FI_API_KEY", "FI_SECRET_KEY", "FI_BEARER_TOKEN"];

type Sender = "runtimeFetch" | "platformClient";
type NoProxy = "listed" | "unlisted";
interface Row { sender: Sender; host: string; scheme: "http" | "https"; noProxy: NoProxy }
interface SinkCounts { connections: number; tunnels: number; markers: number }
interface Seen { outcome: string; code: string; message: string; target: SinkCounts; proxy: SinkCounts }

const UNKEYED: Sender[] = ["runtimeFetch"];
const KEYED: Sender[] = ["platformClient"];
const ROWS: Row[] = [];
for (const noProxy of ["listed", "unlisted"] as NoProxy[]) {
  for (const scheme of ["http", "https"] as const) {
    for (const host of ["127.0.0.1", "localhost"]) {
      for (const sender of [...UNKEYED, ...KEYED]) ROWS.push({ sender, host, scheme, noProxy });
    }
  }
}
const label = (row: Row): string => `${row.sender} ${row.scheme}://${row.host} NO_PROXY ${row.noProxy === "listed" ? "lists the host" : "does not list the host"}`;

function counts(sink: CountingSink): SinkCounts {
  return { connections: sink.connections, tunnels: sink.tunnels, markers: sink.markerCount };
}

async function probe(row: Row): Promise<Seen> {
  const proxySink = new CountingSink([MARKER_KEY, PATH_MARKER]);
  const targetSink = new CountingSink([MARKER_KEY, PATH_MARKER]);
  await Promise.all([proxySink.listen(), targetSink.listen()]);
  try {
    const proxy = `http://127.0.0.1:${proxySink.port}`;
    const noProxy = row.noProxy === "listed" ? row.host : "unlisted.invalid";
    const keyed = KEYED.includes(row.sender);
    const env: NodeJS.ProcessEnv = {
      ...process.env, PROBE_SENDER: row.sender, PROBE_KEY: MARKER_KEY,
      PROBE_URL: `${row.scheme}://${row.host}:${targetSink.port}/${keyed ? "probe" : PATH_MARKER}`,
      NODE_USE_ENV_PROXY: "1", HTTP_PROXY: proxy, http_proxy: proxy, HTTPS_PROXY: proxy, https_proxy: proxy, NO_PROXY: noProxy, no_proxy: noProxy,
    };
    for (const name of CREDENTIAL_VARIABLES) delete env[name];
    const tsx = require.resolve("tsx/cli");
    const stdout = await new Promise<string>((resolve, reject) => {
      execFile(process.execPath, [tsx, join(__dirname, "../__fixtures__/unkeyed-loopback-env-proxy-probe.ts")], { encoding: "utf8", timeout: 60_000, env }, (error, out, err) => (error ? reject(new Error(`${String(error)} ${err}`)) : resolve(out)));
    });
    // a socket the sink holds open (an https handshake it does not answer) closes within the sink's own timeout
    await new Promise((resolve) => setTimeout(resolve, 50));
    const result = JSON.parse(stdout.trim().split("\n").pop() ?? "{}") as { outcome: string; code: string; message: string };
    return { ...result, target: counts(targetSink), proxy: counts(proxySink) };
  } finally {
    await Promise.all([proxySink.close(), targetSink.close()]);
  }
}

/** Runs `rows` in child processes, `width` at a time. */
async function runAll(rows: Row[], width: number): Promise<Map<string, Seen>> {
  const seen = new Map<string, Seen>();
  let next = 0;
  await Promise.all(Array.from({ length: width }, async () => {
    while (next < rows.length) {
      const row = rows[next++] as Row;
      seen.set(label(row), await probe(row));
    }
  }));
  return seen;
}

/** Whether the outcome is one of the SDK's refusals of a send it judged. */
function refusal(seen: Seen): boolean {
  return seen.code === "insecure_http_origin" || seen.code === "caller_proxy" || /^Refusing/u.test(seen.message);
}

const [major, minor] = process.versions.node.split(".").map(Number) as [number, number];
// the runtime reads NODE_USE_ENV_PROXY from Node.js 22.21 on in the 22 line, and in 24
const envProxyHonoured = major >= 24 || (major === 22 && minor >= 21) || major === 23;
const run = envProxyHonoured ? it : it.skip;

let results = new Map<string, Seen>();
let restoreEnv: () => void = () => undefined;
beforeAll(async () => {
  restoreEnv = proxyEnvironment();
  if (envProxyHonoured) results = await runAll(ROWS, 4);
}, 300_000);
afterAll(() => restoreEnv());

function seenFor(row: Row): Seen {
  const seen = results.get(label(row));
  if (seen === undefined) throw new Error(`no result for ${label(row)}`);
  process.stdout.write(`${label(row)}: target ${JSON.stringify(seen.target)} proxy ${JSON.stringify(seen.proxy)} outcome ${JSON.stringify({ outcome: seen.outcome, code: seen.code, message: seen.message.slice(0, 160) })}\n`);
  return seen;
}

describe("an unkeyed loopback request with the runtime's own EnvHttpProxyAgent from NODE_USE_ENV_PROXY=1", () => {
  for (const row of ROWS.filter((r) => r.sender === "runtimeFetch")) {
    run(`${label(row)}: the bare runtime fetch goes where NO_PROXY sends it`, () => {
      const seen = seenFor(row);
      expect(refusal(seen)).toBe(false);
      if (row.noProxy === "listed") {
        expect(seen.proxy.connections).toBe(0);
        expect(seen.target.connections).toBeGreaterThanOrEqual(1);
      } else {
        expect(seen.target.connections).toBe(0);
        expect(seen.proxy.tunnels).toBeGreaterThanOrEqual(1);
      }
      if (row.scheme === "http") {
        expect(seen.outcome).toBe("sent");
        expect((row.noProxy === "listed" ? seen.target : seen.proxy).markers).toBeGreaterThanOrEqual(1);
      }
    });
  }
});

describe("a keyed loopback request in the same setups", () => {
  for (const row of ROWS.filter((r) => KEYED.includes(r.sender))) {
    const route = row.scheme === "http"
      ? "sends the key directly to the target without contacting the proxy"
      : "connects directly to the target for TLS without contacting the proxy";
    run(`${label(row)}: ${route}`, () => {
      const seen = seenFor(row);
      expect(seen.proxy).toEqual({ connections: 0, tunnels: 0, markers: 0 });
      expect(seen.target.connections).toBeGreaterThanOrEqual(1);
      expect(refusal(seen)).toBe(false);
      if (row.scheme === "http") {
        expect(seen.outcome).toBe("sent");
        expect(seen.target.markers).toBe(2);
      } else {
        expect(seen.outcome).not.toBe("sent");
        expect(seen.target.markers).toBe(0);
      }
      expect(seen.message).not.toContain(MARKER_KEY);
    });
  }
});

if (!envProxyHonoured) {
  it.skip(`NODE_USE_ENV_PROXY rows: Node.js ${process.versions.node} does not read NODE_USE_ENV_PROXY (22.21 and 24 do)`, () => undefined);
}
