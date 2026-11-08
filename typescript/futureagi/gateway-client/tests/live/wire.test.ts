/**
 * @future-agi/sdk/gateway against agentcc-gateway the recorded revision: the wire checks
 * with a TypeScript side (D-04, D-07, D-10, D-11, D-12, D-16) and the behaviours
 * only the SDK provides: a gateway error frame raises a typed StreamError
 * (also through nextjs streamResponse and the express middleware's client), the
 * header helpers, the response metadata, usage from the finish chunk.
 */
import { expect, it } from "@jest/globals";
import {
  AgentCC,
  APIStatusError,
  AuthenticationError,
  PermissionDeniedError,
  StreamError,
  createHeaders,
  healthCheck,
} from "../../src/index.js";
import { agentccMiddleware } from "../../src/express.js";
import { streamResponse } from "../../src/nextjs.js";
import { describeLive, live, marker, mockRecords, MODEL, rawStream, record, sha12, tapRecords, user } from "./_live.js";


const client = (opts: Record<string, unknown> = {}) => new AgentCC({ apiKey: live.key, baseUrl: live.base, maxRetries: 0, ...opts });

async function drain(stream: AsyncIterable<any>) {
  const chunks: any[] = [];
  let text = "";
  try {
    for await (const ch of stream) {
      chunks.push(ch);
      text += ch.choices?.[0]?.delta?.content ?? "";
    }
  } catch (err) {
    return { chunks, text, err: err as StreamError };
  }
  return { chunks, text, err: null };
}

describeLive("D-04: APIStatusError.message is the gateway's error.message", () => {
  it("bad key, unknown model and an upstream 500", async () => {
    const seen: Record<string, unknown> = {};
    const cases: [string, AgentCC, string, string][] = [
      ["bad_key", new AgentCC({ apiKey: "not-a-minted-gateway-key", baseUrl: live.base, maxRetries: 0 }), MODEL, "x"],
      ["unknown_model", client(), "no-such-model", "x"],
      ["upstream_500", client(), MODEL, "[[mock:status:500]]"],
    ];
    for (const [name, c, model, prompt] of cases) {
      const err = await c.chat.completions.create({ model, messages: user(`${prompt} ${marker()}`) }).catch((e) => e);
      expect(err).toBeInstanceOf(APIStatusError);
      const body = (err as APIStatusError).body as any;
      seen[name] = { class: err.constructor.name, status: err.statusCode, message: err.message, body };
      expect(body?.error?.message).toBeTruthy();
      expect(err.message).toBe(body.error.message);
      expect(err.message).not.toMatch(/^Request failed with status/);
    }
    record("d04_messages", seen);
    expect((seen.bad_key as any).class).toBe(AuthenticationError.name);
  });
});

describeLive("D-07: base URL forms", () => {
  it.each(["", "/", "/v1", "/v1/"])("baseUrl + %j reaches the gateway", async (suffix) => {
    const r = await new AgentCC({ apiKey: live.key, baseUrl: live.base + suffix, maxRetries: 0 }).chat.completions.create({ model: MODEL, messages: user(`d07 ${marker()}`) });
    expect(r.choices[0].message.content).toBe("PONG from mock");
  });
});

describeLive("D-10: configIgnored and clientRequestId", () => {
  it("are read from the gateway's headers", async () => {
    const cfg = { cache: { ttl: 60, strategy: "semantic" }, fallback: { targets: [{ model: "x" }] } };
    const r = await client().chat.completions.create({
      model: MODEL,
      messages: user(`d10 ${marker()}`),
      extra_headers: { "x-agentcc-config": JSON.stringify(cfg), "x-agentcc-request-id": "ts-cli-req" },
    });
    record("d10_ts", r.agentcc);
    expect(r.agentcc!.configIgnored).toEqual(["cache.strategy", "fallback"]);
    expect(r.agentcc!.clientRequestId).toBe("ts-cli-req");
    expect(r.agentcc!.requestId).not.toBe("ts-cli-req");
  });
});

describeLive("stream error frames raise a typed StreamError", () => {
  it.each([
    ["block-mid", 2, "Hello world"],
    ["block-first", 0, ""],
  ])("%s", async (scenario, before, text) => {
    const r = await drain(await client().chat.completions.create({ model: MODEL, stream: true, messages: user(`[[mock:${scenario}]] ${marker()}`) }));
    record(`ts_stream_${scenario}`, { chunks: r.chunks.length, text: r.text, error: r.err && { name: r.err.name, message: r.err.message, type: r.err.type, code: r.err.code, param: r.err.param, body: r.err.body } });
    expect(r.err).toBeInstanceOf(StreamError);
    expect([r.err!.type, r.err!.code, r.err!.param]).toEqual(["guardrail_error", "stream_blocked", null]);
    expect(r.chunks).toHaveLength(before);
    expect(r.text).toBe(text);
  });

  it("a Finish block raises before the gateway's metadata chunk", async () => {
    const r = await drain(await client().chat.completions.create({ model: MODEL, stream: true, messages: user(`[[mock:block-finish]] ${marker()}`) }));
    expect(r.err?.code).toBe("stream_blocked");
    expect(r.chunks.every((c) => c.choices.length > 0)).toBe(true);
  });

  // The model deadline cuts the stream after "Partial". At the recorded source the gateway usually sends
  // no gateway_timeout frame (python test_live_frames KNOWN_GATEWAY_DIFFERENCES: handleStream's
  // ctx.Done() branch returns without streamCutError), so the client ends with the partial text;
  // when the frame does come, it must raise a typed StreamError. The outcome is recorded.
  it("the deadline cut stops after the partial answer; a gateway_timeout frame raises StreamError", async () => {
    const r = await drain(await client().chat.completions.create({ model: "mock-slow", stream: true, messages: user(`[[mock:stall]] ${marker()}`) }));
    record("ts_stream_deadline_cut", { text: r.text, frame_sent: r.err !== null, error: r.err && { type: r.err.type, code: r.err.code, message: r.err.message } });
    expect(r.text).toBe("Partial");
    if (r.err) expect(r.err.code).toBe("gateway_timeout");
  });

  it("D-16: StreamManager.events() raises before done on a late block", async () => {
    const mgr = await client().chat.completions.stream({ model: MODEL, messages: user(`[[mock:block-finish]] ${marker()}`) });
    const types: string[] = [];
    const err = await (async () => {
      for await (const ev of mgr.events()) types.push(ev.type);
    })().catch((e) => e);
    record("ts_d16_events", { types, code: err?.code });
    expect(err).toBeInstanceOf(StreamError);
    expect(types).not.toContain("done");
  });

  it("nextjs streamResponse forwards type, code and param", async () => {
    const mgr = await client().chat.completions.stream({ model: MODEL, messages: user(`[[mock:block-mid]] ${marker()}`) });
    const body = await streamResponse(mgr).text();
    const frames = body.split("\n").filter((l) => l.startsWith("data: ")).map((l) => l.slice(6));
    const last = JSON.parse(frames[frames.length - 1]);
    record("ts_nextjs_stream_error", { frames });
    expect(last.error).toMatchObject({ type: "guardrail_error", code: "stream_blocked" });
    expect(frames).not.toContain("[DONE]");
  });

  it("the express middleware's client raises the same StreamError, with its session headers", async () => {
    const mw = agentccMiddleware({ apiKey: live.key, baseUrl: live.tap, clientOptions: { maxRetries: 0 } });
    const req: any = { headers: { "x-request-id": "express-sess-1" }, method: "POST", path: "/api/chat" };
    await new Promise<void>((resolve) => mw(req, {} as any, () => resolve()));
    const m = marker();
    const r = await drain(await req.agentcc.chat.completions.create({ model: MODEL, stream: true, messages: user(`[[mock:block-mid]] ${m}`) }));
    const [sent] = await tapRecords(m);
    expect(r.err?.code).toBe("stream_blocked");
    expect(sent.headers["x-agentcc-session-id"]).toBe("express-sess-1");
  });
});

describeLive("D-11: usage from the finish chunk, no stream_options", () => {
  it("events() yields usage and done; the body carries no stream_options", async () => {
    const m = marker();
    const tapped = new AgentCC({ apiKey: live.key, baseUrl: live.tap, maxRetries: 0 });
    const mgr = await tapped.chat.completions.stream({ model: MODEL, messages: user(`usage ${m}`) });
    const evs: any[] = [];
    for await (const ev of mgr.events()) evs.push(ev);
    const done = evs.find((e) => e.type === "done");
    const [sent] = await tapRecords(m);
    record("ts_usage", { events: evs.map((e) => e.type), usage: done?.completion?.usage, sent_body_keys: Object.keys(sent.body as object) });
    expect(Object.keys(sent.body as object)).not.toContain("stream_options");
    // The gateway sends the usage twice (the finish chunk, then its trailing choices-[]
    // chunk); events() yields one usage event per stream.
    expect(evs.filter((e) => e.type === "usage")).toHaveLength(1);
    expect(done.completion.usage.total_tokens).toBeGreaterThan(0);
    expect(done.completion.choices[0].message.content).toBe("Hello world");
  });
});

describeLive("response metadata: timeout, model-used, fallback and routing-strategy readers", () => {
  it("request_timeout is sent in ms, applied and echoed; modelUsed is the upstream's model", async () => {
    const m = marker();
    const r = await new AgentCC({ apiKey: live.key, baseUrl: live.tap, maxRetries: 0 }).chat.completions.create({ model: MODEL, request_timeout: 5000, messages: user(`timeout ${m}`) });
    const [sent] = await tapRecords(m);
    record("ts_request_timeout_model_used", { agentcc: r.agentcc, sent_timeout: sent.headers["x-agentcc-request-timeout"] });
    expect(sent.headers["x-agentcc-request-timeout"]).toBe("5000");
    expect(r.agentcc!.timeoutMs).toBe(5000);
    expect(r.agentcc!.modelUsed).toBe(MODEL);
  });

  async function rawChat(key: string, model: string, text: string) {
    const resp = await fetch(`${live.base}/v1/chat/completions`, {
      method: "POST",
      headers: { authorization: `Bearer ${key}`, "content-type": "application/json" },
      body: JSON.stringify({ model, messages: user(text) }),
    });
    await resp.text();
    const headers = Object.fromEntries([...resp.headers.entries()].filter(([k]) => k.startsWith("x-agentcc-")));
    return { status: resp.status, headers };
  }

  it("a model fallback (the mock answers 503 for mock-fails) sets fallbackUsed and modelUsed", async () => {
    const m = marker();
    const raw = await rawChat(live.fallbackKey, "mock-fails", `fb-raw ${m}`);
    const r = await client({ apiKey: live.fallbackKey }).chat.completions.create({ model: "mock-fails", messages: user(`fb ${m}`) });
    const upstream = (await mockRecords(m)).filter((x) => JSON.stringify(x.body).includes("fb ")).map((x) => (x.body as any).model);
    record("ts_fallback_used_model_used", { raw, agentcc: r.agentcc, upstream_models: upstream });
    expect(raw.status).toBe(200);
    expect(raw.headers["x-agentcc-fallback-used"]).toBe("true");
    expect(raw.headers["x-agentcc-model-used"]).toBe("gpt-4o-mini");
    expect(r.agentcc!.fallbackUsed).toBe(true);
    expect(r.agentcc!.modelUsed).toBe("gpt-4o-mini");
    expect(r.choices[0].message.content).toBe("PONG from mock");
    expect([upstream[0], upstream[upstream.length - 1]]).toEqual(["mock-fails", "gpt-4o-mini"]);
  });

  it("routingStrategy is read for a model with two routing targets; a one-provider model gets null", async () => {
    const m = marker();
    const raw = await rawChat(live.key, "mock-routed", `rs-raw ${m}`);
    const r = await client().chat.completions.create({ model: "mock-routed", messages: user(`rs ${m}`) });
    const single = await client().chat.completions.create({ model: MODEL, messages: user(`rs-single ${m}`) });
    record("ts_routing_strategy", { raw, agentcc: r.agentcc, single_provider_routing_strategy: single.agentcc!.routingStrategy });
    expect(raw.status).toBe(200);
    expect(raw.headers["x-agentcc-routing-strategy"]).toBeTruthy();
    expect(r.agentcc!.routingStrategy).toBe(raw.headers["x-agentcc-routing-strategy"]);
    expect(["mock-a", "mock-b"]).toContain(r.agentcc!.provider);
    expect(single.agentcc!.routingStrategy).toBeNull();
  });
});

describeLive("Embeddings", () => {
  it("embeddings.create parses the gateway's answer (usage without completion_tokens)", async () => {
    const r: any = await client().embeddings.create({ model: "text-embedding-3-small", input: ["a", "b"] } as any);
    record("ts_embeddings", { data: r.data?.length, usage: r.usage, agentcc: r.agentcc });
    expect(r.data).toHaveLength(2);
    expect(r.data[0].embedding).toEqual([0.1, 0.2, 0.3]);
  });
});

describeLive("D-12: stream requests and the cache at the pin", () => {
  it("a warm cache entry never answers stream:true; the stream is SSE from the upstream", async () => {
    const m = marker();
    const c = client();
    await c.chat.completions.create({ model: MODEL, messages: user(`d12 ${m}`) });
    const hit = await c.chat.completions.create({ model: MODEL, messages: user(`d12 ${m}`) });
    const raw = await rawStream("/v1/chat/completions", { model: MODEL, stream: true, messages: user(`d12 ${m}`) });
    const r = await drain(await c.chat.completions.create({ model: MODEL, stream: true, messages: user(`d12 ${m}`) }));
    const up = await mockRecords(m);
    record("ts_d12_cache_stream", { hit_cache: hit.agentcc!.cacheStatus, raw_content_type: raw.headers["content-type"], raw_cache: raw.headers["x-agentcc-cache"], raw_frames: raw.frames, sdk_text: r.text, upstream_calls: up.length });
    expect(hit.agentcc!.cacheStatus).toMatch(/^hit/);
    expect(raw.headers["content-type"]).toMatch(/^text\/event-stream/);
    expect(r.text).toBe("Hello world");
    expect(up).toHaveLength(3);
  });
});

describeLive("Guardrail answers", () => {
  it("a blocked non-stream answer is 403 guardrail_error (PermissionDeniedError; GuardrailBlockedError is keyed to 446)", async () => {
    const err = await client().chat.completions.create({ model: MODEL, messages: user(`[[mock:block-mid]] ${marker()}`) }).catch((e) => e);
    record("ts_nonstream_block", { class: err.constructor.name, status: err.statusCode, body: err.body, message: err.message });
    expect(err).toBeInstanceOf(PermissionDeniedError);
    expect(err.statusCode).toBe(403);
    expect(err.body.error.type).toBe("guardrail_error");
  });

  it("a log-only policy serves the answer with the guardrail outcome headers", async () => {
    const c = new AgentCC({ apiKey: live.overrideKey, baseUrl: live.base, maxRetries: 0 });
    const r = await c.chat.completions.create({ model: MODEL, guardrail_policy: "log-only", messages: user(`[[mock:block-mid]] ${marker()}`) });
    record("ts_guardrail_log_only", { agentcc: r.agentcc, content: r.choices[0].message.content });
    expect(r.choices[0].message.content).toContain(live.blockWord);
    expect(r.agentcc!.guardrailTriggered).toBe(true);
    expect(r.agentcc!.guardrailAction).toBe("log");
  });

  it("guardrailPolicy disabled lets the stream through for a key with allow_policy_override", async () => {
    const c = new AgentCC({ apiKey: live.overrideKey, baseUrl: live.base, maxRetries: 0 });
    const r = await drain(await c.chat.completions.create({ model: MODEL, stream: true, guardrail_policy: "disabled", messages: user(`[[mock:block-mid]] ${marker()}`) }));
    expect(r.err).toBeNull();
    expect(r.text).toContain(live.blockWord);
  });
});

describeLive("Header helpers and isolation", () => {
  it("createHeaders reaches the gateway; the JSON metadata header is read", async () => {
    const hdrs = createHeaders({ traceId: "t-ts", sessionId: "s-ts", sessionName: "checkout", sessionPath: "/a", metadata: { tier: "gold" }, userId: "user 9", requestId: "r-ts", cacheTtl: 60, cacheNamespace: "ns-ts", properties: { env: "prod" } });
    const m = marker();
    const r = await new AgentCC({ apiKey: live.key, baseUrl: live.tap, defaultHeaders: hdrs, maxRetries: 0 }).chat.completions.create({ model: MODEL, messages: user(`helpers ${m}`) });
    const [sent] = await tapRecords(m);
    record("ts_header_helpers", { built: hdrs, received: sent.headers, agentcc: r.agentcc });
    for (const [k, v] of Object.entries(hdrs)) expect(sent.headers[k.toLowerCase()]).toBe(v);
    expect(r.agentcc!.provider).toBe("mock-b");
    expect(r.agentcc!.clientRequestId).toBe("r-ts");
  });

  it("no FI_* or OPENAI_* identity leaves the client; no x-agentcc-sdk-version reader is needed", async () => {
    const saved = { ...process.env };
    Object.assign(process.env, { FI_API_KEY: "fi-key-live", FI_SECRET_KEY: "fi-secret-live", OPENAI_API_KEY: "openai-key-live", OPENAI_ORG_ID: "org-live", OPENAI_PROJECT_ID: "proj-live", FI_GATEWAY_API_KEY: live.key, FI_GATEWAY_BASE_URL: live.tap });
    try {
      const m = marker();
      await new AgentCC({ maxRetries: 0 }).chat.completions.create({ model: MODEL, messages: user(`iso ${m}`) });
      const [sent] = await tapRecords(m);
      record("ts_env_isolation", { header_names: Object.keys(sent.headers).sort() });
      expect(sent.headers.authorization).toBe(`<sha256:${sha12(live.key)}>`);
      for (const h of Object.keys(sent.headers)) expect(h).not.toMatch(/^(x-api-key|x-secret-key|x-organization-id|openai-organization|openai-project|x-workspace-|x-omega-)/);
    } finally {
      process.env = saved;
    }
  });

  it("client.healthCheck() asks /healthz; healthCheck({ model }) sends a completion", async () => {
    expect(await client().healthCheck()).toBe(true);
    expect((await healthCheck({ model: MODEL, apiKey: live.key, baseUrl: live.base })).healthy).toBe(true);
    expect((await fetch(`${live.base}/health`)).status).toBe(404);
    expect((await fetch(`${live.base}/healthz`)).status).toBe(200);
  });
});
