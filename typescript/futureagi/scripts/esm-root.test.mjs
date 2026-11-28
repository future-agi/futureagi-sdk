import { Client } from "@future-agi/sdk";
import assert from "node:assert/strict";
import test from "node:test";

// Load the listener after the package, as in a consumer that only imports the client.
const { createServer } = await import("node:http");

test("ESM root Client sends an opted-in plain HTTP request", async () => {
  const received = [];
  const server = createServer((req, res) => {
    received.push([req.headers["x-api-key"], req.headers["x-secret-key"]]);
    res.writeHead(200, { "Content-Type": "application/json", Connection: "close" });
    res.end('{"ok":true}');
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  try {
    // The trailing dot requires an explicit opt-in, but the connection uses the numeric local address.
    const options = { apiKey: "test-api", secretKey: "test-secret", baseUrl: `http://127.0.0.1.:${server.address().port}`, maxRetries: 0, timeout: 3000 };
    await assert.rejects(new Client({ ...options, allowInsecureHttp: false }).request("GET", "/check"));
    assert.deepEqual(await new Client({ ...options, allowInsecureHttp: true }).request("GET", "/check"), { ok: true });
    assert.deepEqual(received, [[options.apiKey, options.secretKey]]);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
