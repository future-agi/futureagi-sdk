#!/usr/bin/env node
// The browser CORS case runner. Run it on a build machine only: it launches
// Chromium, Firefox and WebKit.
//
//   node cors-browser.cjs <bundle.js> <out.json>
//   (PLAYWRIGHT_MODULE or GW_PLAYWRIGHT = the playwright module; PLAYWRIGHT_BROWSERS_PATH set;
//    FI_GATEWAY_LIVE_BASE_URL and FI_GATEWAY_LIVE_KEYS from run-wire-suite.sh)
//
// Serves a page on its own origin that loads the bundle of cors-entry.ts, which
// calls the real gateway on another origin. Records, per engine, each attempt's
// outcome and what Playwright's network log shows of the gateway's answers. That
// log does not include the CORS preflight (OPTIONS) requests the engines send, so
// for each engine the runner also sends a direct OPTIONS request from Node, with
// the page's Origin and the request headers each attempt uses, and records the
// gateway's preflight answer (status and every access-control-* header); each is
// judged against the same expectation as the browser attempt. The key is passed in
// the page URL and never written out: the logs keep only methods, paths, statuses
// and the CORS headers.
"use strict";
const http = require("node:http");
const { readFileSync, writeFileSync, mkdirSync } = require("node:fs");
const { dirname } = require("node:path");

const [bundlePath, outPath] = process.argv.slice(2);
const pw = require(process.env.PLAYWRIGHT_MODULE || process.env.GW_PLAYWRIGHT || "playwright");
const base = process.env.FI_GATEWAY_LIVE_BASE_URL;
const key = JSON.parse(readFileSync(process.env.FI_GATEWAY_LIVE_KEYS, "utf8")).plain.key;
const bundle = readFileSync(bundlePath);
const page = http.createServer((req, res) => {
  if (req.url.startsWith("/bundle.js")) res.writeHead(200, { "content-type": "text/javascript" }).end(bundle);
  else res.writeHead(200, { "content-type": "text/html" }).end('<!doctype html><meta charset="utf-8"><title>s4</title><script type="module" src="/bundle.js"></script>');
});

// What each attempt must show with the default CORS lists (middleware/cors.go).
const EXPECT = { plain: true, stream: true, session_metadata_cache: true, property_header: true, trace_context: false, sdk_version_header: false };

// The request headers each attempt sends (the preflight's Access-Control-Request-Headers).
const BASE_HEADERS = ["authorization", "content-type"];
const ATTEMPT_HEADERS = {
  plain: BASE_HEADERS,
  stream: BASE_HEADERS,
  session_metadata_cache: [...BASE_HEADERS, "x-agentcc-cache-ttl", "x-agentcc-metadata", "x-agentcc-session-id"],
  property_header: [...BASE_HEADERS, "x-agentcc-property-tier"],
  trace_context: [...BASE_HEADERS, "traceparent"],
  sdk_version_header: [...BASE_HEADERS, "x-agentcc-sdk-version"],
};

function preflight(origin, requestHeaders) {
  const url = new URL("/v1/chat/completions", base);
  return new Promise((resolve) => {
    const req = http.request(url, {
      method: "OPTIONS",
      headers: { origin, "access-control-request-method": "POST", "access-control-request-headers": requestHeaders.join(",") },
    }, (res) => {
      res.resume();
      res.on("end", () => {
        const cors = Object.fromEntries(Object.entries(res.headers).filter(([k]) => k.startsWith("access-control-") || k === "vary"));
        resolve({ status: res.statusCode, headers: cors });
      });
    });
    req.on("error", (e) => resolve({ error: String(e && e.message) }));
    req.end();
  });
}

// A preflight allows the attempt when the origin is allowed and every requested header is listed.
function preflightAllows(answer, origin, requested) {
  const h = answer.headers || {};
  const allowOrigin = h["access-control-allow-origin"];
  if (!(answer.status >= 200 && answer.status < 300) || !(allowOrigin === "*" || allowOrigin === origin)) return false;
  const listed = String(h["access-control-allow-headers"] || "").toLowerCase().split(",").map((s) => s.trim());
  return listed.includes("*") || requested.every((name) => listed.includes(name));
}

async function directPreflights(origin) {
  const out = {};
  const problems = [];
  for (const [name, requested] of Object.entries(ATTEMPT_HEADERS)) {
    const answer = await preflight(origin, requested);
    const allows = preflightAllows(answer, origin, requested);
    out[name] = { origin, request_headers: requested, ...answer, allows };
    if (allows !== EXPECT[name]) problems.push(`direct preflight ${name}: expected ${EXPECT[name] ? "allowed" : "refused"}, got ${JSON.stringify(answer).slice(0, 200)}`);
  }
  return { out, problems };
}

function judge(r) {
  const problems = [];
  for (const [name, ok] of Object.entries(EXPECT)) {
    const got = r[name];
    if (!got) problems.push(`${name}: no result`);
    else if (got.ok !== ok) problems.push(`${name}: expected ${ok ? "success" : "a CORS refusal"}, got ${JSON.stringify(got).slice(0, 160)}`);
  }
  if (r.plain?.ok && !(r.plain.value.cost > 0 && r.plain.value.requestId)) problems.push("metadata headers not readable through CORS (expose list)");
  if (r.stream?.ok && r.stream.value !== "Hello world") problems.push(`stream text ${JSON.stringify(r.stream.value)}`);
  if (r.session_metadata_cache?.ok && r.session_metadata_cache.value.provider !== "mock-b") problems.push("metadata header not read (provider is not mock-b)");
  if (r.property_header?.ok && r.property_header.value.provider !== "mock-b") problems.push("property header not read (provider is not mock-b)");
  for (const h of ["x-agentcc-sdk-version", "user-agent"]) if ((r.dryHeaderNames || []).includes(h)) problems.push(`the browser client would send ${h}`);
  return problems;
}

(async () => {
  const port = await new Promise((resolve) => page.listen(0, "127.0.0.1", () => resolve(page.address().port)));
  const results = [];
  const origin = `http://127.0.0.1:${port}`;
  for (const name of ["chromium", "firefox", "webkit"]) {
    let browser;
    const network = [];
    const direct = await directPreflights(origin);
    try {
      browser = await pw[name].launch({ headless: true });
      const tab = await browser.newPage();
      tab.on("response", (resp) => {
        const req = resp.request();
        if (!req.url().startsWith(base)) return;
        const h = resp.headers();
        network.push({
          method: req.method(), path: new URL(req.url()).pathname, status: resp.status(),
          request_headers: req.method() === "OPTIONS" ? { "access-control-request-headers": req.headers()["access-control-request-headers"] || null } : undefined,
          allow_origin: h["access-control-allow-origin"] || null,
          allow_headers: req.method() === "OPTIONS" ? h["access-control-allow-headers"] || null : undefined,
        });
      });
      tab.on("requestfailed", (req) => {
        if (req.url().startsWith(base)) network.push({ method: req.method(), path: new URL(req.url()).pathname, failed: req.failure()?.errorText || "failed" });
      });
      await tab.goto(`http://127.0.0.1:${port}/?api=${encodeURIComponent(base)}&key=${encodeURIComponent(key)}`);
      await tab.waitForFunction(() => window.__s4, null, { timeout: 60000 });
      const r = await tab.evaluate(() => window.__s4);
      results.push({ engine: name, version: browser.version(), origin, result: r, network, direct_preflight: direct.out, problems: [...judge(r), ...direct.problems] });
    } catch (e) {
      results.push({ engine: name, origin, network, direct_preflight: direct.out, problems: [`did not run: ${String(e && e.message).split("\n")[0]}`, ...direct.problems] });
    } finally {
      if (browser) await browser.close();
    }
  }
  page.close();
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, JSON.stringify({ check: "browser CORS preflight against agentcc-gateway live-gateway-source (cors.enabled, default lists)", expect: EXPECT, results }, null, 1) + "\n");
  for (const r of results) process.stdout.write(`${r.engine} ${r.version || ""}: ${r.problems.length ? r.problems.join("; ") : "ok"}\n`);
  process.exit(results.some((r) => r.problems.length) ? 1 : 0);
})();
