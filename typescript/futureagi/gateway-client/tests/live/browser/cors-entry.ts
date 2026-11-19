// The browser CORS preflight case:
// a page on one origin uses @future-agi/sdk/gateway (bundled from source by esbuild)
// against the REAL agentcc-gateway at the recorded revision on another origin, with the
// gateway's default CORS lists (cors.enabled, nothing else set). cors-browser.cjs
// runs it in Chromium, Firefox and WebKit. The gateway origin and this run's key
// come from the page's query string; the result goes to window.__s4.
import { AgentCC } from "../../../src/index.js";

const q = new URLSearchParams(location.search);
const base = q.get("api") as string;
const key = q.get("key") as string;
// A prompt of its own per page load: the org cache is on, and a cache hit carries no
// x-agentcc-cost, which would hide whether the cost header is readable through CORS.
const PARAMS = { model: "gpt-4o-mini", messages: [{ role: "user" as const, content: `browser s4 ${crypto.randomUUID()}` }] };
const out: Record<string, unknown> = {};
const failure = (e: any) => `${e && e.name}: ${e && e.message}`.slice(0, 200);
const mk = (extra: Record<string, unknown> = {}) => new AgentCC({ apiKey: key, baseUrl: base, dangerouslyAllowBrowser: true, maxRetries: 0, ...extra });

async function attempt(name: string, fn: () => Promise<unknown>) {
  try {
    out[name] = { ok: true, value: await fn() };
  } catch (e) {
    out[name] = { ok: false, error: failure(e) };
  }
}

(async () => {
  const c = mk();
  out.dryHeaderNames = Object.keys(c.chat.completions.dryRun(PARAMS).headers).map((h) => h.toLowerCase()).sort();
  // The SDK's default request: Authorization and Content-Type only.
  await attempt("plain", async () => {
    const r = await c.chat.completions.create(PARAMS);
    return { content: r.choices[0].message.content, requestId: r.agentcc!.requestId, cost: r.agentcc!.cost, provider: r.agentcc!.provider };
  });
  await attempt("stream", async () => {
    let text = "";
    for await (const ch of await c.chat.completions.create({ ...PARAMS, stream: true })) text += ch.choices[0]?.delta?.content ?? "";
    return text;
  });
  // Session id, metadata, cache headers: all on the default allow list.
  await attempt("session_metadata_cache", async () => {
    const s = mk({ sessionId: "s-browser", metadata: { tier: "gold" } });
    const r = await s.chat.completions.create({ ...PARAMS, cache_ttl: 60 });
    return { provider: r.agentcc!.provider };
  });
  // x-agentcc-property-<k>: answered dynamically by the preflight (requestedPropertyHeaders).
  await attempt("property_header", async () => {
    const r = await c.chat.completions.create({ ...PARAMS, extra_headers: { "x-agentcc-property-tier": "gold" } });
    return { provider: r.agentcc!.provider };
  });
  // traceContext sends traceparent, which the default allow list does not name.
  await attempt("trace_context", async () => {
    const r = await mk({ traceContext: true }).chat.completions.create(PARAMS);
    return { requestId: r.agentcc!.requestId };
  });
  // x-agentcc-sdk-version (what 1.x sent from browsers too): not on the allow list.
  await attempt("sdk_version_header", async () => {
    const r = await mk({ defaultHeaders: { "x-agentcc-sdk-version": "browser" } }).chat.completions.create(PARAMS);
    return { requestId: r.agentcc!.requestId };
  });
  (window as any).__s4 = out;
})();
