import { execFile } from "node:child_process";
import { join } from "node:path";
import { promisify } from "node:util";

import type { ProxyKind, RefusalResult } from "../__fixtures__/env-proxy-refusal-message-probe";
import { CountingSink } from "../__fixtures__/proxy-sink";

const run = promisify(execFile);
const marker = "marker-root-proxy-refusal-key-0000000000";
const target = new CountingSink([marker]);
const proxy = new CountingSink([marker]);
const kinds: ProxyKind[] = ["ProxyAgent", "EnvHttpProxyAgent"];

beforeAll(async () => {
  await Promise.all([target.listen(), proxy.listen()]);
});
beforeEach(() => { target.reset(); proxy.reset(); });
afterAll(async () => {
  await Promise.all([target.close(), proxy.close()]);
});

it.each(kinds)("names the global %s when the plain HTTP route retains it", async (kind) => {
  const { stdout } = await run(process.execPath, [
    require.resolve("tsx/cli"), join(__dirname, "../__fixtures__/env-proxy-refusal-message-probe.ts"),
    kind, `http://127.1:${target.port}/labels?api_key=${marker}`, `http://127.0.0.1:${proxy.port}`,
  ], { encoding: "utf8", timeout: 30_000 });
  const result = JSON.parse(stdout) as RefusalResult;
  const dispatcherNames = result.message.match(/\b(?:EnvHttpProxyAgent|ProxyAgent)\b/gu)?.join(",") ?? "unnamed";
  process.stdout.write(`root ${kind}: ${result.code ?? "allowed"} dispatcher=${dispatcherNames} target=${target.markerCount} proxy=${proxy.markerCount}\n`);
  expect(result.callerProxied).toBe(true);
  expect(result.code).toBe("insecure_http_origin");
  expect(proxy.connections).toBe(0);
  expect(proxy.markerCount).toBe(0);
  expect(target.connections).toBe(0);
  expect(target.markerCount).toBe(0);
  expect(result.message).toMatch(new RegExp(`\\b${kind}\\b`, "u"));
}, 45_000);
