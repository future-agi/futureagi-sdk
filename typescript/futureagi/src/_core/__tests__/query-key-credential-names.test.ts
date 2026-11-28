import { execFile } from "node:child_process";
import { join } from "node:path";
import { promisify } from "node:util";

import { CountingSink } from "../__fixtures__/proxy-sink";
import { queryCarriesKey } from "../key-headers";

const marker = "marker-query-key-0000000000";
const origin = "http://127.0.0.1";
const credentialNames = [
  "fi_api_key", "fi_secret_key", "FI_API_KEY", "Fi-Api-Key", "fiapikey", "FI_SECRET_KEY",
  "fi%5Fapi%5Fkey", "FI%5FAPI%5FKEY", "auth[fi_api_key]", "access_token", "Access-Token", "api_key",
  "auth%25[fi%255Fapi%255Fkey]", "auth%25[fi%25255Fsecret%25255Fkey]", "auth%25[access%255Ftoken]",
];
const ordinaryNames = ["page", "limit", "q", "fi_project"];
const nameRows = [
  ...credentialNames.map((name) => ({ name, keyed: true })),
  ...ordinaryNames.map((name) => ({ name, keyed: false })),
];

describe("root query credential names", () => {
  it.each(nameRows)("classifies $name with a value as keyed: $keyed", ({ name, keyed }) => {
    const actual = queryCarriesKey(`${origin}/?${name}=${marker}`, undefined, { env: {} });
    process.stdout.write(`root query ${name}: outcome=${actual ? "keyed" : "unkeyed"} target=n/a proxy=n/a\n`);
    expect(actual).toBe(keyed);
  });
});

const runChild = promisify(execFile);
const [major = 0, minor = 0] = process.versions.node.split(".").map(Number);
const proxyTest = major >= 24 || (major === 22 && minor >= 21) ? it : it.skip;

async function send() {
  const sender = "runtimeFetch";
  const query = "page=2";
  const targetSink = new CountingSink([query]);
  const proxySink = new CountingSink([query]);
  await Promise.all([targetSink.listen(), proxySink.listen()]);
  try {
    const proxyUrl = `${origin}:${proxySink.port}`;
    const env: NodeJS.ProcessEnv = {
      ...process.env,
      NODE_USE_ENV_PROXY: "1",
      HTTP_PROXY: proxyUrl, http_proxy: proxyUrl,
      HTTPS_PROXY: proxyUrl, https_proxy: proxyUrl,
      ALL_PROXY: "", all_proxy: "", NO_PROXY: "", no_proxy: "",
      PROBE_SENDER: sender, PROBE_URL: `${origin}:${targetSink.port}/?${query}`,
    };
    for (const name of ["FI_API_KEY", "FI_SECRET_KEY", "FI_BEARER_TOKEN", "FI_ALLOW_INSECURE_HTTP"]) delete env[name];
    const { stdout } = await runChild(process.execPath, [
      require.resolve("tsx/cli"), join(__dirname, "../__fixtures__/unkeyed-loopback-env-proxy-probe.ts"),
    ], { env, encoding: "utf8", timeout: 15_000 });
    const result = JSON.parse(stdout.trim().split("\n").pop() ?? "") as { outcome: string; code: string; message: string };
    const target = { markers: targetSink.markerCount, connections: targetSink.connections };
    const proxy = { markers: proxySink.markerCount, connections: proxySink.connections };
    process.stdout.write(`${sender} ${query}: outcome=${result.outcome}${result.code ? `:${result.code}` : ""} target=${target.markers} proxy=${proxy.markers} targetConnections=${target.connections} proxyConnections=${proxy.connections}\n`);
    return { result, target, proxy };
  } finally {
    await Promise.all([targetSink.close(), proxySink.close()]);
  }
}

const noTraffic = { markers: 0, connections: 0 };

proxyTest("runtime fetch sends page=2 through the environment proxy", async () => {
  const { result, target, proxy } = await send();
  expect(result).toMatchObject({ outcome: "sent" });
  expect(target).toEqual(noTraffic);
  expect(proxy).toEqual({ markers: 1, connections: 1 });
}, 20_000);
