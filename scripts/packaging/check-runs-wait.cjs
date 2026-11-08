#!/usr/bin/env node
/** Check reactivation against the installed tarball, not a source-path import. */
const assert = require("node:assert/strict");
const { createRequire } = require("node:module");
const { resolve } = require("node:path");
const load = createRequire(resolve(process.argv[2], "package.json"));
const { FutureAGIClient } = load("@future-agi/sdk");
const { Run } = load("@future-agi/sdk/agents/runs");

(async () => {
  for (const method of ["send", "retry", "resume"]) {
    const before = { conversation: { id: "run-a", status: method === "retry" ? "error" : "done" } };
    const receipt = { accepted: true };
    const after = { conversation: { id: "run-a", status: "done" }, messages: [{ id: "new-message" }] };
    const responses = [before, receipt, { conversation: { id: "run-a", status: "active" } }, after];
    const requests = [];
    const client = new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://127.0.0.1:9000",
      fetch: async (input, init) => {
        const request = new Request(input, init); requests.push(request.method);
        assert.ok(responses.length, "unexpected request");
        return new Response(JSON.stringify(responses.shift()), { status: 200, headers: { "content-type": "application/json" } });
      },
    });
    const run = await client.agents.runs.get("run-a");
    assert.ok(run instanceof Run);
    assert.deepEqual(await run[method](method === "send" ? { input: "next" } : {}), receipt);
    assert.equal(await run.wait({ timeout: 1, sleep: async () => {} }), run);
    assert.deepEqual(requests, ["GET", "POST", "GET", "GET"]);
    assert.deepEqual(run.response, after);
    console.log(`PASS: installed tarball ${method} waits for its new turn`);
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
