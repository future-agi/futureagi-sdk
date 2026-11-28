import { execFile } from "node:child_process";
import { join } from "node:path";
import { promisify } from "node:util";

import { CountingSink, proxyEnvironment } from "../__fixtures__/proxy-sink";

const senders = ["platform"] as const;
const hosts = ["127.0.0.1", "localhost"] as const;
const keys = Object.fromEntries(senders.map((sender) => [sender, [
  `marker-b-${sender}-key-0000000000`, `marker-b-${sender}-secret-0000000000`,
]]));
const controlKey = "marker-b-root-control-key-0000000000";
const packageRoot = join(__dirname, "..", "..", "..");

type RecordCalls = { captureEmpty: boolean; constructed: number; dispatched: number };
type Sends = { forms: { root: string }; outcomes: Record<string, { outcome: string }> };

async function runProbe<T>(proxy: CountingSink, args: string[], settings: Record<string, string> = {}) {
  const address = `http://127.0.0.1:${proxy.port}`;
  const restore = proxyEnvironment({ HTTP_PROXY: address, HTTPS_PROXY: address });
  const env = { ...process.env, ...settings };
  restore();
  delete env.FI_ALLOW_INSECURE_HTTP;
  delete env.PROBE_SLOT;
  const { stdout } = await promisify(execFile)(process.execPath, [
    require.resolve("tsx/cli"), join(__dirname, "../__fixtures__/runtime-undici-record-keyed-probe.mjs"), ...args,
  ], { cwd: packageRoot, env, encoding: "utf8", timeout: 30_000 });
  const lines = stdout.trim().split("\n");
  const calls = JSON.parse(lines.pop() ?? "") as RecordCalls;
  const result = JSON.parse(lines.pop() ?? "") as T;
  return { result, calls };
}

it("runtime fetch uses the Agent the application places in the dispatcher slot", async () => {
  const target = new CountingSink([controlKey]);
  const proxy = new CountingSink([controlKey]);
  try {
    await Promise.all([target.listen(), proxy.listen()]);
    const { result, calls } = await runProbe<{ outcome: string }>(proxy, ["control", String(target.port), controlKey]);
    process.stdout.write(`root runtime fetch control: ${result.outcome} target ${target.markerCount} proxy ${proxy.markerCount} proxy connections ${proxy.connections}\n`);
    expect(result.outcome).toBe("http:200");
    expect(target.markerCount).toBe(1);
    expect([proxy.markerCount, proxy.connections]).toEqual([0, 0]);
    expect(calls).toEqual({ captureEmpty: true, constructed: 1, dispatched: 1 });
  } finally {
    await Promise.all([target.close(), proxy.close()]);
  }
}, 45_000);

it("keyed loopback sends reach their targets without using the application's runtime undici record", async () => {
  const rows = senders.flatMap((sender) => hosts.map((host) => ({ sender, host, target: new CountingSink(keys[sender]) })));
  const proxy = new CountingSink(Object.values(keys).flat());
  try {
    await Promise.all([proxy.listen(), ...rows.map(({ target }) => target.listen())]);
    const { result, calls } = await runProbe<Sends>(proxy, [join(__dirname, "../__fixtures__/keyed-loopback-load-probe.mjs")], {
      PROBE_MODE: "cjs:root",
      PROBE_UNDICI: "unresolvable",
      PROBE_KEYS: JSON.stringify(keys),
      PROBE_TARGETS: JSON.stringify(Object.fromEntries(senders.map((sender) => [sender,
        Object.fromEntries(rows.filter((row) => row.sender === sender).map(({ host, target }) => [host, target.port])),
      ]))),
    });
    const observed = rows.map(({ sender, host, target }) => {
      const row = `${sender}@${host}`;
      const outcome = result.outcomes[row]?.outcome;
      process.stdout.write(`${row}: ${outcome} target ${target.markerCount} proxy ${proxy.markerCount} proxy connections ${proxy.connections}\n`);
      return { row, outcome, target: target.markerCount };
    });
    process.stdout.write(`root record Agent: constructed ${calls.constructed} dispatched ${calls.dispatched}\n`);
    expect(result.forms).toEqual({ root: "cjs" });
    expect(observed).toEqual(rows.map(({ sender, host }) => ({ row: `${sender}@${host}`, outcome: "sent", target: 2 })));
    expect([proxy.markerCount, proxy.connections]).toEqual([0, 0]);
    expect(calls).toEqual({ captureEmpty: true, constructed: 0, dispatched: 0 });
  } finally {
    await Promise.all([proxy.close(), ...rows.map(({ target }) => target.close())]);
  }
}, 45_000);
