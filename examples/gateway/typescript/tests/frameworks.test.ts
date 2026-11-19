import assert from "node:assert/strict";
import { test } from "node:test";
import net from "node:net";
import { createServer } from "node:http";
import { ask as langchain } from "../langchain.js";
import { ask as vercel } from "../vercel.js";
import { createApp } from "../express.js";
import { POST } from "../app/api/chat/route.js";
import { resetAgentCCClient } from "@future-agi/sdk/gateway/nextjs";
import { answer, key, mockGateway, configure, listen, close } from "./mock-gateway.js";

for (const [name, ask] of [["langchain", langchain], ["vercel", vercel]] as const) {
  test(`${name} calls MockAgentCC through the stock framework`, async () => {
    const gateway = await mockGateway();
    const restore = configure(gateway.url);
    try {
      assert.equal(await ask("Hello"), answer);
      assert.equal(gateway.mock.chat.completions.calls.length, 1);
      assert.equal(gateway.calls.length, 1);
      const call = gateway.calls[0];
      assert.equal(call.path, "/v1/chat/completions");
      assert.equal(call.headers.authorization, `Bearer ${key}`);
      assert.equal(call.headers["x-agentcc-session-id"], `example-${name}`);
      assert.equal(call.headers["openai-organization"], undefined);
      assert.equal(call.headers["openai-project"], undefined);
      assert.equal(call.body.model, "example-model");
      assert.equal(call.body.messages.at(-1)?.content, "Hello");
      assert.equal(call.headers["x-agentcc-config"], undefined);
      gateway.refuse(401);
      await assert.rejects(ask("Hello"));
      assert.equal(gateway.calls.length, 2, "No retries on a refused key");
    } finally { restore(); await gateway.close(); }
  });

  test(`${name} fails closed without a gateway key or with a platform key pair`, async () => {
    const gateway = await mockGateway();
    const restore = configure(gateway.url);
    try {
      delete process.env.FI_GATEWAY_API_KEY;
      await assert.rejects(ask("Hello"));
      process.env.FI_GATEWAY_API_KEY = key;
      process.env.FI_API_KEY = key;
      process.env.FI_SECRET_KEY = "mock-platform-secret";
      await assert.rejects(ask("Hello"));
      assert.equal(gateway.calls.length, 0);
    } finally { restore(); await gateway.close(); }
  });
}

test("Express middleware carries the session and validates input before the gateway", async () => {
  const gateway = await mockGateway();
  const restore = configure(gateway.url);
  const server = createServer(createApp());
  const url = await listen(server);
  const submit = (body: unknown) => fetch(`${url}/api/chat`, {
    method: "POST", headers: { "Content-Type": "application/json", "x-request-id": "example-express" },
    body: JSON.stringify(body),
  });
  try {
    assert.equal((await submit({ messages: [] })).status, 400);
    assert.equal(gateway.calls.length, 0);
    const response = await submit({ messages: [{ role: "user", content: "Hello" }], model: "untrusted" });
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), { text: answer });
    assert.equal(gateway.calls[0].headers["x-agentcc-session-id"], "example-express");
    assert.equal(gateway.calls[0].body.model, "example-model");
    assert.equal(gateway.mock.chat.completions.calls.length, 1);
    gateway.refuse(401);
    assert.equal((await submit({ messages: [{ role: "user", content: "Hello" }] })).status, 502);
  } finally { await close(server); restore(); await gateway.close(); }
});

test("Next route validates input and returns SSE without exposing its credential", async () => {
  const gateway = await mockGateway();
  const restore = configure(gateway.url);
  resetAgentCCClient();
  const submit = (body: unknown, origin = "http://localhost:3000") => POST(new Request("http://localhost:3000/api/chat", {
    method: "POST", headers: { "Content-Type": "application/json", origin }, body: JSON.stringify(body),
  }));
  try {
    assert.equal((await submit({ messages: [] })).status, 400);
    assert.equal((await submit({}, "https://other.invalid")).status, 403);
    assert.equal(gateway.calls.length, 0);
    const response = await submit({ messages: [{ role: "user", content: "Hello" }], model: "untrusted" });
    assert.equal(response.headers.get("content-type"), "text/event-stream");
    const text = await response.text();
    assert.ok(text.includes(answer));
    assert.ok(text.endsWith("data: [DONE]\n\n"));
    assert.ok(!text.includes(key));
    assert.equal(gateway.calls[0].body.stream, true);
    assert.equal(gateway.calls[0].body.model, "example-model");
    assert.equal(gateway.mock.chat.completions.calls.length, 1);
    gateway.refuse(401);
    assert.equal((await submit({ messages: [{ role: "user", content: "Hello" }] })).status, 502);
  } finally { resetAgentCCClient(); restore(); await gateway.close(); }
});

test("Next and Express still reject empty user and assistant content before the gateway", async () => {
  const gateway = await mockGateway();
  const restore = configure(gateway.url);
  resetAgentCCClient();
  const server = createServer(createApp());
  const url = await listen(server);
  try {
    for (const role of ["user", "assistant"]) {
      for (const content of ["", " \n\t "]) {
        const init = { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
          messages: [{ role: "user", content: "Hello" }, { role, content }],
        }) };
        assert.equal((await POST(new Request("http://localhost:3000/api/chat", init))).status, 400);
        assert.equal((await fetch(`${url}/api/chat`, init)).status, 400);
      }
    }
    assert.equal(gateway.calls.length, 0);
  } finally { await close(server); resetAgentCCClient(); restore(); await gateway.close(); }
});

test("Next route compares browser Origin with HTTP Host when its internal URL is normalized", async () => {
  const request = (origin: string) => new Request("http://localhost:3000/api/chat", {
    method: "POST", headers: { host: "127.0.0.1:3000", origin, "Content-Type": "application/json" },
    body: JSON.stringify({ messages: [] }),
  });
  assert.equal((await POST(request("http://127.0.0.1:3000"))).status, 400, "Same origin reaches input validation");
  assert.equal((await POST(request("http://other.invalid:3000"))).status, 403);
});

test("network guard rejects non-loopback destinations before connecting", () => {
  const socket = new net.Socket();
  try {
    assert.throws(() => socket.connect({ host: "192.0.2.1", port: 443 }), /network guard/);
  } finally { socket.destroy(); }
});
