#!/usr/bin/env node
// D-18 in real browsers. Run it on a build machine, not a laptop: it
// launches Chromium, Firefox and WebKit.
//
//   node d18-browser.cjs <bundle.js> <out.json>   (PLAYWRIGHT_MODULE, PLAYWRIGHT_BROWSERS_PATH set)
//
// The page (one origin) loads the esbuild bundle of d18-entry.mjs, built from
// the packed tarball; the "gateway" (another origin) answers with the CORS
// policy of agentcc-gateway's middleware/cors.go at the recorded revision as its
// defaults are (allowed and exposed header lists copied verbatim), and a
// canned completion. Per engine the page must: refuse construction without
// dangerouslyAllowBrowser; send neither x-agentcc-sdk-version nor its own
// User-Agent; pass the real preflight and read the answer and its metadata,
// plain and streamed; and see the browser block the negative control.
"use strict";
const http = require("node:http");
const { readFileSync, writeFileSync } = require("node:fs");

const [bundlePath, outPath] = process.argv.slice(2);
const { chromium, firefox, webkit } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

// cors.go defaultCORSHeaders / defaultExposedHeaders at the recorded revision.
const ALLOW = ["Authorization", "Content-Type", "X-Agentcc-Trace-Id", "X-Agentcc-Timeout", "X-Agentcc-Request-Timeout", "X-Agentcc-User-Id", "X-Agentcc-Session-Id", "X-Agentcc-Config", "X-Guardrail-Policy", "Cache-Control", "X-Agentcc-Session-Name", "X-Agentcc-Session-Path", "X-Agentcc-Request-Id", "X-Agentcc-Metadata", "X-Agentcc-Cache-Ttl", "X-Agentcc-Cache-Namespace", "X-Agentcc-Cache-Force-Refresh", "X-Agentcc-Provider-Lock", "X-Agentcc-Complexity-Override", "X-Agentcc-Guardrail-Policy", "X-Agentcc-Max-Attempts", "X-Agentcc-Retry-Delay-Ms", "X-Agentcc-Backoff", "X-Agentcc-Auto-Preference", "X-Agentcc-Log-Content"];
const EXPOSE = ["X-Agentcc-Request-Id", "X-Agentcc-Trace-Id", "X-Agentcc-Provider", "X-Agentcc-Model-Used", "X-Agentcc-Latency-Ms", "X-Agentcc-Cost", "X-Agentcc-Cache", "X-Agentcc-Timeout-Ms", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "X-Agentcc-Client-Request-Id", "X-Agentcc-Config-Ignored", "X-Agentcc-Guardrail-Triggered", "X-Agentcc-Guardrail-Action", "X-Agentcc-Guardrails-Triggered", "X-Agentcc-Fallback-Used", "X-Agentcc-Routing-Strategy", "X-Agentcc-Credits-Remaining", "X-Ratelimit-Limit-Requests", "X-Ratelimit-Remaining-Requests", "X-Ratelimit-Reset-Requests"];

const seen = [];
const gateway = http.createServer((req, res) => {
  const origin = req.headers.origin;
  if (origin) {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Expose-Headers", EXPOSE.join(", "));
  }
  if (req.method === "OPTIONS") {
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", ALLOW.join(", "));
    res.setHeader("Access-Control-Max-Age", "86400");
    res.writeHead(204).end();
    return;
  }
  let body = "";
  req.on("data", (c) => (body += c));
  req.on("end", () => {
    seen.push({ method: req.method, url: req.url, headers: req.headers });
    const stream = JSON.parse(body || "{}").stream === true;
    res.setHeader("x-agentcc-request-id", "gw-browser-1");
    res.setHeader("x-agentcc-cost", "0.25");
    if (stream) {
      res.writeHead(200, { "content-type": "text/event-stream" });
      res.end(['{"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"hel"},"finish_reason":null}]}', '{"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"lo"},"finish_reason":"stop"}]}', "[DONE]"].map((f) => `data: ${f}\n\n`).join(""));
    } else {
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ id: "c", object: "chat.completion", created: 1, model: "m", choices: [{ index: 0, message: { role: "assistant", content: "hello from the gateway" }, finish_reason: "stop" }] }));
    }
  });
});
const bundle = readFileSync(bundlePath);
const page = http.createServer((req, res) => {
  if (req.url.startsWith("/bundle.js")) res.writeHead(200, { "content-type": "text/javascript" }).end(bundle);
  else res.writeHead(200, { "content-type": "text/html" }).end('<!doctype html><meta charset="utf-8"><title>d18</title><script type="module" src="/bundle.js"></script>');
});
const listen = (server) => new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server.address().port)));

function judge(engine, r, requests) {
  const problems = [];
  if (r.refused !== true) problems.push(`construction without dangerouslyAllowBrowser was not refused (${JSON.stringify(r.refusedMessage)})`);
  for (const h of ["x-agentcc-sdk-version", "user-agent"]) if (r.dryHeaderNames.includes(h)) problems.push(`dryRun headers include ${h}`);
  for (const h of ["authorization", "content-type"]) if (!r.dryHeaderNames.includes(h)) problems.push(`dryRun headers lack ${h}`);
  if (r.content !== "hello from the gateway") problems.push(`plain request: ${r.requestError || r.content}`);
  if (r.cost !== 0.25 || r.requestId !== "gw-browser-1") problems.push(`metadata not readable through CORS: cost ${r.cost}, requestId ${r.requestId}`);
  if (r.streamed !== "hello") problems.push(`streamed request: ${r.streamError || r.streamed}`);
  if (!/APIConnectionError/.test(r.controlError || "")) problems.push(`negative control was not blocked by the browser: ${r.controlError}`);
  const posts = requests.filter((q) => q.method === "POST");
  if (posts.length !== 2) problems.push(`the gateway saw ${posts.length} POSTs, expected 2 (the control must not reach it)`);
  for (const q of posts) {
    if (q.headers.authorization !== "Bearer vk-browser") problems.push("a POST lacked the gateway key");
    if ("x-agentcc-sdk-version" in q.headers) problems.push("a POST carried x-agentcc-sdk-version");
    if (/futureagi-typescript/.test(q.headers["user-agent"] || "")) problems.push("a POST carried the SDK User-Agent");
  }
  return { engine, result: r, gateway_saw: posts.map((q) => ({ url: q.url, session: q.headers["x-agentcc-session-id"] || null, ua: (q.headers["user-agent"] || "").slice(0, 60) })), problems };
}

(async () => {
  const apiPort = await listen(gateway);
  const pagePort = await listen(page);
  const results = [];
  for (const [name, type] of [["chromium", chromium], ["firefox", firefox], ["webkit", webkit]]) {
    seen.length = 0;
    let browser;
    try {
      browser = await type.launch({ headless: true });
      const tab = await browser.newPage();
      const logs = [];
      tab.on("console", (m) => logs.push(`${m.type()}: ${m.text()}`.slice(0, 200)));
      await tab.goto(`http://127.0.0.1:${pagePort}/?api=${encodeURIComponent(`http://127.0.0.1:${apiPort}`)}`);
      await tab.waitForFunction(() => window.__d18, null, { timeout: 30000 });
      const r = await tab.evaluate(() => window.__d18);
      results.push({ version: browser.version(), ...judge(name, r, [...seen]), console: logs.slice(0, 10) });
    } catch (e) {
      results.push({ engine: name, problems: [`did not run: ${String(e && e.message).split("\n")[0]}`] });
    } finally {
      if (browser) await browser.close();
    }
  }
  gateway.close();
  page.close();
  writeFileSync(outPath, JSON.stringify({ check: "D-18 browser case", cors: "agentcc-gateway middleware/cors.go defaults at live-gateway-source", results }, null, 1) + "\n");
  const failed = results.filter((r) => r.problems.length);
  for (const r of results) process.stdout.write(`${r.engine} ${r.version || ""}: ${r.problems.length ? r.problems.join("; ") : "ok"}\n`);
  process.exit(failed.length ? 1 : 0);
})();
