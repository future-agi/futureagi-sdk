import { execFile } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

import { CountingSink, proxyEnvironment } from "../__fixtures__/proxy-sink";
import { HttpsCountingTarget, TlsTerminatingProxySink, scratchCa } from "../__fixtures__/loopback-https-proven-direct-tls";

const exec = promisify(execFile);
const PACKAGE_ROOT = join(__dirname, "..", "..", "..");
const PROBE = join(__dirname, "../__fixtures__/keyed-loopback-node-transport-probe.mjs");
const MODES = ["esm", "request-cjs", "request-esm"] as const;
const SENDERS = ["platform"] as const;
const SCHEMES = ["http", "https"] as const;
const HOSTS = ["127.0.0.1", "localhost"] as const;
const PROXY_MODES = ["disabled", "enabled"] as const;

interface Row {
  mode: typeof MODES[number] | "runtime-fetch";
  sender: typeof SENDERS[number] | "runtime-fetch";
  scheme: typeof SCHEMES[number];
  host: typeof HOSTS[number];
  envProxy: typeof PROXY_MODES[number];
}

const ca = scratchCa();
let caDir: string;
let caFile: string;
beforeAll(() => {
  caDir = mkdtempSync(join(tmpdir(), "keyed-loopback-node-transport-"));
  caFile = join(caDir, "ca.pem");
  writeFileSync(caFile, ca.caPem);
});
afterAll(() => { if (caDir !== undefined) rmSync(caDir, { recursive: true, force: true }); });

function childEnvironment(row: Row, targetPort: number, proxyPort: number, markers: readonly string[]): NodeJS.ProcessEnv {
  const proxyUrl = `http://127.0.0.1:${proxyPort}`;
  const restore = proxyEnvironment({ HTTP_PROXY: proxyUrl, HTTPS_PROXY: proxyUrl, NO_PROXY: "" });
  try {
    const env: NodeJS.ProcessEnv = {
      ...process.env,
      NODE_EXTRA_CA_CERTS: caFile,
      PROBE_MODE: row.mode,
      PROBE_SENDER: row.sender,
      PROBE_BASE: `${row.scheme}://${row.host}:${targetPort}`,
      PROBE_MARKERS: JSON.stringify(markers),
    };
    if (row.envProxy === "enabled") env.NODE_USE_ENV_PROXY = "1";
    delete env.NODE_TLS_REJECT_UNAUTHORIZED;
    delete env.FI_ALLOW_INSECURE_HTTP;
    delete env.FI_EXTRA_HEADERS;
    return env;
  } finally {
    restore();
  }
}

async function observe(row: Row) {
  const markers = ["key", "secret"].map((kind) => `marker-node-transport-${row.sender}-${kind}-0000000000`);
  const tls = row.scheme === "https";
  const target = tls ? new HttpsCountingTarget(ca, markers) : new CountingSink(markers);
  const proxy = tls ? new TlsTerminatingProxySink(ca, markers) : new CountingSink(markers);
  await Promise.all([target.listen(), proxy.listen()]);
  try {
    const { stdout } = await exec(process.execPath, ["--import", require.resolve("tsx"), PROBE], {
      cwd: PACKAGE_ROOT,
      timeout: 12_000,
      env: childEnvironment(row, target.port, proxy.port, markers),
    });
    const { outcome } = JSON.parse(stdout.trim().split("\n").pop() ?? "{}") as { outcome: string };
    const { mode, sender, scheme, host, envProxy } = row;
    const targetMarkers = target.markerCount;
    const proxyMarkers = proxy.markerCount;
    const proxyConnections = proxy.connections;
    process.stdout.write(`${mode} ${sender} ${scheme}://${host} env-proxy=${envProxy}: ${outcome} target=${targetMarkers} proxy=${proxyMarkers} proxy-connections=${proxyConnections}\n`);
    return { outcome, targetMarkers, proxyMarkers, proxyConnections };
  } finally {
    await Promise.all([target.close(), proxy.close()]);
  }
}

const rows: Row[] = MODES.flatMap((mode) => SENDERS.flatMap((sender) => SCHEMES.flatMap((scheme) =>
  HOSTS.flatMap((host) => PROXY_MODES.map((envProxy) => ({ mode, sender, scheme, host, envProxy }))),
)));
const direct = { outcome: "sent", targetMarkers: 2, proxyMarkers: 0, proxyConnections: 0 };
const label = "$mode $sender to $scheme://$host with runtime proxy $envProxy";

// The runtime reads NODE_USE_ENV_PROXY for fetch on the supported release lines.
const [major, minor] = process.versions.node.split(".").map(Number) as [number, number];
const envProxyHonoured = major >= 24 || (major === 22 && minor >= 21);
const controls: Row[] = SCHEMES.flatMap((scheme) => PROXY_MODES
  .filter((envProxy) => envProxy === "disabled" || envProxyHonoured)
  .map((envProxy) => ({ mode: "runtime-fetch", sender: "runtime-fetch", scheme, host: "localhost", envProxy })));

it.concurrent.each(controls)(`sink control: ${label}`, async (row) => {
  const seen = await observe(row);
  if (row.envProxy === "disabled") {
    expect(seen).toEqual(direct);
  } else {
    expect(seen).toEqual({ outcome: "sent", targetMarkers: 0, proxyMarkers: 2, proxyConnections: 1 });
  }
}, 20_000);

it.concurrent.each(rows)(`${label}: the SDK sends both markers directly with undici unresolvable`, async (row) => {
  expect(await observe(row)).toEqual(direct);
}, 20_000);
