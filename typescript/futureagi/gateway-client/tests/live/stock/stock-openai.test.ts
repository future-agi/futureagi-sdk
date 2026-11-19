/**
 * The stock openai-node SDK (4.104.0, ./package.json) pointed at agentcc-gateway
 * the recorded revision through openaiOptions().
 *
 * - openaiOptions() sets OpenAI-Organization and OpenAI-Project to null so
 *   openai-node drops them: with OPENAI_ORG_ID / OPENAI_PROJECT_ID set, neither
 *   header may reach the gateway (this case is what proves it).
 * - The key is always explicit: OPENAI_API_KEY never reaches the gateway.
 * - The stock SDK streaming on a warm cache entry.
 * Requests go through the wire tap, so the test sees what openai-node sent.
 * Skipped when ./node_modules/openai is absent (run-wire-suite.sh installs it).
 */
import { describe, expect, it } from "@jest/globals";
import { openaiOptions } from "../../../src/index.js";
import { LIVE, live, marker, MODEL, record, sha12, tapRecords, user } from "../_live.js";

let OpenAI: any = null;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const mod = require("openai");
  OpenAI = mod.default ?? mod.OpenAI ?? mod;
} catch {
  OpenAI = null;
}
const describeStock = OpenAI && LIVE ? describe : describe.skip;

function stock() {
  const saved = { ...process.env };
  Object.assign(process.env, { OPENAI_API_KEY: "openai-key-that-must-not-be-sent", OPENAI_ORG_ID: "org-live-stock", OPENAI_PROJECT_ID: "proj-live-stock" });
  const opts = openaiOptions({ apiKey: live.key, baseUrl: live.tap, sessionId: "s-stock-ts", metadata: { tier: "gold" } });
  const c = new OpenAI({ ...opts, maxRetries: 0 });
  process.env = saved;
  return { c, opts };
}

describeStock("stock openai-node through openaiOptions()", () => {
  it("sends the gateway key and drops OpenAI-Organization / OpenAI-Project", async () => {
    const saved = { ...process.env };
    Object.assign(process.env, { OPENAI_API_KEY: "openai-key-that-must-not-be-sent", OPENAI_ORG_ID: "org-live-stock", OPENAI_PROJECT_ID: "proj-live-stock" });
    try {
      const opts = openaiOptions({ apiKey: live.key, baseUrl: live.tap, sessionId: "s-stock-ts", metadata: { tier: "gold" } });
      const c = new OpenAI({ ...opts, maxRetries: 0 });
      const m = marker();
      const { data, response } = await c.chat.completions.create({ model: MODEL, messages: user(`stock-ts ${m}`) }).withResponse();
      const [sent] = await tapRecords(m);
      record("stock_ts_headers", {
        openai_version: require("openai/version").VERSION,
        sent_header_names: Object.keys(sent.headers).sort(),
        authorization: sent.headers.authorization,
        "openai-organization": sent.headers["openai-organization"] ?? null,
        "openai-project": sent.headers["openai-project"] ?? null,
        x_agentcc: Object.fromEntries(Object.entries(sent.headers).filter(([k]) => k.startsWith("x-agentcc"))),
        response_provider: response.headers.get("x-agentcc-provider"),
        content: data.choices[0].message.content,
      });
      expect(sent.headers.authorization).toBe(`<sha256:${sha12(live.key)}>`);
      expect(sent.headers["openai-organization"]).toBeUndefined();
      expect(sent.headers["openai-project"]).toBeUndefined();
      expect(sent.headers["x-agentcc-session-id"]).toBe("s-stock-ts");
      expect(response.headers.get("x-agentcc-provider")).toBe("mock-b");
    } finally {
      process.env = saved;
    }
  });

  it("streams on a warm cache entry (streams bypass the cache at the pin)", async () => {
    const { c } = stock();
    const msgs = user(`stock-ts-cache ${marker()}`);
    await c.chat.completions.create({ model: MODEL, messages: msgs });
    const { response: hit } = await c.chat.completions.create({ model: MODEL, messages: msgs }).withResponse();
    let text = "";
    let chunks = 0;
    for await (const ch of await c.chat.completions.create({ model: MODEL, messages: msgs, stream: true })) {
      chunks += 1;
      text += ch.choices?.[0]?.delta?.content ?? "";
    }
    record("stock_ts_cache_s3", { hit_cache: hit.headers.get("x-agentcc-cache"), chunks, text });
    expect(hit.headers.get("x-agentcc-cache") ?? "").toMatch(/^hit/);
    expect(text).toBe("Hello world");
  });

  it("on the gateway's stream_blocked frame", async () => {
    const { c } = stock();
    let text = "";
    let err: any = null;
    try {
      for await (const ch of await c.chat.completions.create({ model: MODEL, stream: true, messages: user(`[[mock:block-mid]] ${marker()}`) })) {
        text += ch.choices?.[0]?.delta?.content ?? "";
      }
    } catch (e) {
      err = e;
    }
    record("stock_ts_stream_block", { text, error_class: err?.constructor?.name ?? null, error: err ? String(err.message) : null, error_body: err?.error ?? null });
    expect(err).not.toBeNull();
    expect(text).toBe("Hello world");
  });
});
