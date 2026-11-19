// Shared by smoke.cjs and smoke.mjs: what a consumer does with each subpath
// once it has loaded it. Kept CommonJS so both entry points can use it.
"use strict";

const SUBPATHS = ["gateway", "gateway/testing", "gateway/express", "gateway/nextjs", "gateway/react"];

function exportKeys(mod) {
  return Object.keys(mod).filter((k) => k !== "__esModule" && k !== "default").sort();
}

function fakeFetch(seen) {
  return async (url, init) => {
    seen.push({ url: String(url), headers: init && init.headers });
    if (String(url).endsWith("/v1/chat/completions") && init && JSON.parse(init.body).stream) {
      const enc = new TextEncoder();
      const frames = [
        'data: {"id":"c1","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"he"},"finish_reason":null}]}\n\n',
        'data: {"id":"c1","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"llo"},"finish_reason":"stop"}]}\n\n',
        "data: [DONE]\n\n",
      ];
      const body = new ReadableStream({ start(c) { for (const f of frames) c.enqueue(enc.encode(f)); c.close(); } });
      return new Response(body, { status: 200, headers: { "content-type": "text/event-stream" } });
    }
    return new Response(
      JSON.stringify({ id: "c1", object: "chat.completion", created: 1, model: "m", choices: [{ index: 0, message: { role: "assistant", content: "hello" }, finish_reason: "stop" }] }),
      { status: 200, headers: { "content-type": "application/json", "x-agentcc-cost": "0.5" } },
    );
  };
}

async function exercise(mods) {
  const out = {};
  const gw = mods["gateway"];
  if (gw) {
    const seen = [];
    const client = new gw.AgentCC({ apiKey: "sk-smoke", baseUrl: "http://127.0.0.1:9/v1", fetch: fakeFetch(seen) });
    const r = await client.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }] });
    let streamed = "";
    for await (const chunk of await client.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }], stream: true })) {
      streamed += (chunk.choices[0] && chunk.choices[0].delta.content) || "";
    }
    out.gateway = { content: r.choices[0].message.content, cost: r.agentcc.cost, streamed, url: seen[0].url, userAgent: seen[0].headers["User-Agent"] };
  }
  const testing = mods["gateway/testing"];
  if (testing) {
    const mock = new testing.MockAgentCC();
    out.testing = { mock: typeof mock.chat.completions.create };
  }
  const express = mods["gateway/express"];
  if (express) out.express = { middleware: typeof express.agentccMiddleware({ apiKey: "k", baseUrl: "http://127.0.0.1:9" }) };
  const nextjs = mods["gateway/nextjs"];
  if (nextjs) out.nextjs = { response: nextjs.streamResponse((async function* () {})()) instanceof Response };
  return out;
}

module.exports = { SUBPATHS, exportKeys, exercise, fakeFetch };
