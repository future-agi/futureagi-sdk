import assert from "node:assert/strict";
import { test } from "node:test";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { once } from "node:events";
import { resolve } from "node:path";
import { writeFile } from "node:fs/promises";
import { setTimeout } from "node:timers/promises";
import { mockGateway, answer, key, configure, listen, close } from "./mock-gateway.js";

test("Next.js serves the actual page and streaming route against MockAgentCC", { timeout: 120_000 }, async () => {
  const gateway = await mockGateway();
  const restore = configure(gateway.url);
  const reservation = createServer();
  const url = await listen(reservation);
  await close(reservation);
  const port = new URL(url).port;
  let log = "";
  const child = spawn(process.execPath, ["node_modules/next/dist/bin/next", "dev", "--hostname", "127.0.0.1", "--port", port], {
    env: { ...process.env, NODE_OPTIONS: `--conditions=futureagi-gateway-preview --import=${resolve("tests/network-guard.mjs")}` },
    stdio: ["ignore", "pipe", "pipe"],
  });
  child.stdout.on("data", (chunk) => { log += chunk; });
  child.stderr.on("data", (chunk) => { log += chunk; });
  const exited = once(child, "exit");
  try {
    let page: Response | undefined;
    for (let attempt = 0; attempt < 120; attempt++) {
      assert.equal(child.exitCode, null, "Next exited before serving the example");
      try { page = await fetch(url, { signal: AbortSignal.timeout(30_000) }); } catch { /* Startup has no socket yet. */ }
      if (page) break;
      await setTimeout(250);
    }
    assert.equal(page?.status, 200, "Next page must compile and render");
    const html = await page!.text();
    assert.ok(html.includes("Gateway chat example"));
    assert.ok(!html.includes(key));
    const response = await fetch(`${url}/api/chat`, {
      method: "POST", headers: { "Content-Type": "application/json", origin: url },
      body: JSON.stringify({ messages: [{ role: "user", content: "Hello" }] }),
      signal: AbortSignal.timeout(30_000),
    });
    assert.equal(response.status, 200);
    assert.match(response.headers.get("content-type")!, /text\/event-stream/);
    const text = await response.text();
    assert.ok(text.includes(answer));
    assert.ok(text.endsWith("data: [DONE]\n\n"));
    assert.equal(gateway.mock.chat.completions.calls.length, 1);
    assert.equal(gateway.calls[0].body.stream, true);
  } finally {
    child.kill("SIGTERM");
    const timeout = globalThis.setTimeout(() => child.kill("SIGKILL"), 5000);
    await exited;
    clearTimeout(timeout);
    await writeFile(resolve("../../../out/next-server.log"), log);
    restore(); await gateway.close();
  }
});
