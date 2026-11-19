// @agentcc/client: every resource method, per-request parameters alone and
// combined, the header merge levels, GatewayConfig / createHeaders / Session,
// and every response header.
import { CHAT, MSG, chunks, ok, responseHeaders, sse } from "./fixtures.mjs";
import { BASE_URL, KEY } from "../harness/runner.mjs";

const at = (obj, path) => path.split(".").reduce((o, p) => o[p], obj);
const callOn = (path, ...args) => async (ctx) => {
  const client = ctx.client({ maxRetries: 0 });
  const parts = path.split(".");
  return at(client, parts.slice(0, -1).join("."))[parts.at(-1)](...args);
};
const streamed = (params) => async (ctx) => {
  const stream = await ctx.client({ maxRetries: 0 }).chat.completions.create({ ...params, stream: true });
  return { ...(await ctx.drain(stream)), agentcc: stream.agentcc };
};
const manager = (params) => async (ctx) => {
  const m = await ctx.client({ maxRetries: 0 }).chat.completions.stream(params);
  const events = await ctx.drain(m.events());
  return { events, final: await ctx.attempt(() => m.getFinalCompletion()), text: await ctx.attempt(() => m.getFinalText()) };
};
const readText = (path, ...args) => async (ctx) => {
  const res = await callOn(path, ...args)(ctx);
  return { status: res.status, text: await res.text() };
};

function form() {
  return new File([new TextEncoder().encode("RIFF-parity")], "a.wav", { type: "audio/wav" });
}

const GW = { session_id: "sess-r", trace_id: "trace-r", cache_ttl: 60, request_metadata: { team: "a" } };
const RESOURCES = [
  ["chat.create", callOn("chat.completions.create", CHAT), [ok("chat_completion")]],
  ["chat.create.gateway_params", callOn("chat.completions.create", { ...CHAT, ...GW }), [ok("chat_completion")]],
  ["chat.create.tools", callOn("chat.completions.create", { ...CHAT, tools: [{ type: "function", function: { name: "get_weather", parameters: { type: "object" } } }], tool_choice: "auto" }), [ok("chat_completion_tools")]],
  ["chat.create.stream", streamed(CHAT), [sse(chunks("content"))]],
  ["chat.create.stream_tools", streamed(CHAT), [sse(chunks("tool_calls"))]],
  ["chat.stream", manager(CHAT), [sse(chunks("content"))]],
  ["chat.stream.tools", manager(CHAT), [sse(chunks("tool_calls"))]],
  ["chat.dryRun", async (ctx) => ctx.client({ defaultHeaders: { "X-D": "1" } }).chat.completions.dryRun({ ...CHAT, ...GW }), []],
  ["chat.runTools", async (ctx) => ctx.client({ maxRetries: 0 }).chat.completions.runTools({ ...CHAT, maxSteps: 3, tools: [{ type: "function", function: { name: "get_weather", parameters: { type: "object", properties: { city: { type: "string" } } }, execute: async (args) => ({ temp: 21, args }) } }] }), [ok("chat_completion_tools"), ok("chat_completion")]],
  ["chat.createParsed", async (ctx) => ctx.client({ maxRetries: 0 }).chat.completions.createParsed({ ...CHAT, response_format: { type: "json_schema", json_schema: { name: "p", schema: { type: "object", properties: { name: { type: "string" } }, required: ["name"] } } } }), [ok("chat_completion_json")]],
  ["completions.create", callOn("completions.create", { model: "gpt-3.5-turbo-instruct", prompt: "Hello", max_tokens: 5 }), [ok("completion")]],
  ["completions.create.gateway_params", callOn("completions.create", { model: "gpt-3.5-turbo-instruct", prompt: ["a", "b"], ...GW }), [ok("completion")]],
  ["embeddings.create", callOn("embeddings.create", { model: "text-embedding-3-small", input: "hi", dimensions: 3, encoding_format: "float" }), [ok("embedding")]],
  ["embeddings.create.list", callOn("embeddings.create", { model: "text-embedding-3-small", input: ["a", "b"], extra_body: { x: 1 } }), [ok("embedding")]],
  ["images.generate", callOn("images.generate", { prompt: "a cat", model: "dall-e-3", size: "1024x1024", n: 1 }), [ok("image")]],
  ["audio.transcriptions.file", async (ctx) => ctx.client({ maxRetries: 0 }).audio.transcriptions.create({ file: form(), model: "whisper-1", language: "en", ...GW }), [ok("transcription")]],
  ["audio.translations.file", async (ctx) => ctx.client({ maxRetries: 0 }).audio.translations.create({ file: form(), model: "whisper-1" }), [ok("translation")]],
  ["audio.speech", readText("audio.speech.create", { model: "tts-1", input: "hello", voice: "alloy" }), [ok("speech_bytes")]],
  ["audio.speech.options", readText("audio.speech.create", { model: "tts-1", input: "hello", voice: "alloy", response_format: "wav", speed: 1.25, session_id: "s" }), [ok("speech_bytes")]],
  ["models.list", callOn("models.list"), [ok("models_list")]],
  ["models.retrieve", callOn("models.retrieve", "gpt-4o-mini"), [ok("model")]],
  ["models.retrieve.slash", callOn("models.retrieve", "openai/gpt-4o mini"), [ok("model")]],
  ["files.create", async (ctx) => ctx.client({ maxRetries: 0 }).files.create({ file: new File(['{"a":1}\n'], "data.jsonl", { type: "application/jsonl" }), purpose: "batch" }), [ok("file_object")]],
  ["files.list", callOn("files.list"), [ok("file_list")]],
  ["files.retrieve", callOn("files.retrieve", "file-parity"), [ok("file_object")]],
  ["files.content", readText("files.content", "file-parity"), [ok("file_content")]],
  ["files.delete", callOn("files.delete", "file-parity"), [ok("file_deleted")]],
  ["rerank.rank", callOn("rerank.rank", { model: "rerank-v1", query: "q", documents: ["alpha", "beta"], top_n: 2, return_documents: true }), [ok("rerank")]],
  ["batches.create", callOn("batches.create", { requests: [{ model: "gpt-4o-mini", messages: MSG }], max_concurrency: 2 }), [ok("batch")]],
  ["batches.list", callOn("batches.list", { after: "b0", limit: 5 }), [{ status: 200, json: { object: "list", data: [] } }]],
  ["batches.retrieve", callOn("batches.retrieve", "batch-parity"), [ok("batch")]],
  ["batches.cancel", callOn("batches.cancel", "batch-parity"), [ok("batch")]],
  ["moderations.create", callOn("moderations.create", { input: "hello", model: "omni-moderation-latest" }), [ok("moderation")]],
  ["healthCheck.method", async (ctx) => ctx.client({ maxRetries: 0 }).healthCheck(), [ok("health")]],
  ["healthCheck.method.error", async (ctx) => ctx.client({ maxRetries: 0 }).healthCheck(), [{ status: 404, text: "404 page not found" }]],
  ["healthCheck.function", async (ctx) => ctx.mod.healthCheck({ model: "gpt-4o-mini", apiKey: KEY, baseUrl: BASE_URL }), [ok("chat_completion", { headers: { "x-agentcc-provider": "openai" } })]],
  ["healthCheck.function.error", async (ctx) => ctx.mod.healthCheck({ model: "gpt-4o-mini", apiKey: KEY, baseUrl: BASE_URL }), [{ status: 401, json: { error: { message: "bad key" } } }]],
  ["checkValidKey", async (ctx) => ctx.mod.checkValidKey({ apiKey: KEY, baseUrl: BASE_URL }), [ok("models_list")]],
  ["checkValidKey.401", async (ctx) => ctx.mod.checkValidKey({ apiKey: KEY, baseUrl: BASE_URL }), [{ status: 401, json: { error: { message: "bad key" } } }]],
  ["withResponse", async (ctx) => ctx.client({ maxRetries: 0 }).requestWithResponse({ method: "GET", path: "/v1/models" }), [ok("models_list", { headers: { "x-agentcc-request-id": "r1" } })]],
  ["injected_fetch", async (ctx) => {
    const seen = [];
    const client = ctx.client({ maxRetries: 0, fetch: (u, i) => { seen.push(String(u)); return globalThis.fetch(u, i); } });
    return { result: await client.chat.completions.create(CHAT), seen };
  }, [ok("chat_completion")]],
];

const BODY_PARAMS = {
  temperature: 0.5, top_p: 0.9, n: 2, stop: ["\n"], max_tokens: 10, max_completion_tokens: 12, presence_penalty: 0.1,
  frequency_penalty: 0.2, logit_bias: { 50256: -100 }, logprobs: true, top_logprobs: 2, user: "user-1", seed: 42,
  tools: [{ type: "function", function: { name: "f", parameters: { type: "object" } } }], tool_choice: "none",
  response_format: { type: "json_object" }, stream_options: { include_usage: true }, extra_body: { custom_field: 1 }, unknown_kwarg: "passes through",
};
const GATEWAY_PARAMS = {
  session_id: "sess-1", trace_id: "trace-1", request_metadata: { k: "v", n: 1 }, request_timeout: 30, cache_ttl: 300,
  cache_namespace: "ns-1", cache_force_refresh: true, cache_control: "no-cache", guardrail_policy: "strict",
  extra_headers: { "X-Custom": "1" }, properties: { team: "a" }, user_id: "u-1", request_id: "r-1",
};
const NULLS = ["temperature", "session_id", "cache_ttl", "cache_force_refresh", "extra_headers"];
const CLIENT_OPTIONS = {
  defaultQuery: { defaultQuery: { tenant: "t1" } },
  defaultHeaders: { defaultHeaders: { "X-Default": "d" } },
  sessionId: { sessionId: "client-sess" },
  metadata: { metadata: { team: "a", n: 2 } },
  dropParams: { dropParams: true },
  "dropParams.unknown_model": { dropParams: true, __model: "unknown-model" },
  modifyParams: { modifyParams: (p) => ({ ...p, injected: true }) },
  redactMessages: { redactMessages: true },
  traceContext: { traceContext: true },
  traceparent: { traceparent: "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01" },
  timeout: { timeout: 9000 },
  "preCallRules.allow": { preCallRules: [() => ({ allowed: true })] },
  "preCallRules.block": { preCallRules: [() => ({ allowed: false, reason: "no" })] },
  "jsonSchemaValidation.bad": { enableJsonSchemaValidation: true, __rf: true, __reply: "chat_completion_json_bad" },
  "jsonSchemaValidation.ok": { enableJsonSchemaValidation: true, __rf: true, __reply: "chat_completion_json" },
};
const RF = { type: "json_schema", json_schema: { name: "p", schema: { type: "object", properties: { name: { type: "string" }, age: { type: "integer" } }, required: ["name"] } } };
const WITH_OPTIONS = { timeout: 7500, maxRetries: 3, defaultHeaders: { "X-Derived": "d" }, defaultQuery: { q: "1" }, sessionId: "derived-sess", metadata: { m: "1" } };

const COLLISIONS = {
  l3_over_l1: [{ defaultHeaders: { "User-Agent": "custom-ua", "Content-Type": "text/plain", "x-agentcc-sdk-version": "9", Accept: "*/*" } }, {}],
  l3_over_l2: [{ defaultHeaders: { Authorization: "Bearer from-default" } }, {}],
  l3_case_variant_l2: [{ defaultHeaders: { authorization: "Bearer lower-case" } }, {}],
  l4_over_l3: [{ defaultHeaders: { "x-agentcc-session-id": "from-default" }, sessionId: "from-client", metadata: { a: 1 } }, {}],
  l5_over_l4: [{ sessionId: "s", config: { cache: { ttl: 300, namespace: "cfg" } } }, {}],
  l6_over_l5: [{ config: { cache: { ttl: 300, namespace: "cfg", forceRefresh: true } } }, { cache_ttl: 5, cache_namespace: "param" }],
  l6_over_l4: [{ sessionId: "from-client", metadata: { a: 1 } }, { session_id: "from-param", request_metadata: { b: 2 } }],
  l7_over_l6: [{}, { session_id: "from-param", extra_headers: { "x-agentcc-session-id": "from-extra" } }],
  l7_over_l2: [{}, { extra_headers: { Authorization: "Bearer from-extra" } }],
  l7_over_l1: [{}, { extra_headers: { "User-Agent": "extra-ua" } }],
  l7_case_variant_l3: [{ defaultHeaders: { "X-Case": "upper" } }, { extra_headers: { "x-case": "lower" } }],
  trace_over_default: [{ traceparent: "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01", defaultHeaders: { traceparent: "from-default" } }, {}],
};

const CONFIG_SECTIONS = {
  fallback: { fallback: { targets: [{ model: "gpt-4o-mini", provider: "openai" }] } },
  loadBalance: { loadBalance: { strategy: "weighted", targets: [{ model: "a", weight: 2 }] } },
  cache: { cache: { ttl: 300, namespace: "prod", forceRefresh: true } },
  guardrails: { guardrails: { inputGuardrails: ["pii"], outputGuardrails: ["toxicity"] } },
  routing: { routing: { conditions: [{ field: "metadata.tier", operator: "$eq", value: "gold", target: "gpt-4o" }] } },
  mirror: { mirror: { targetModel: "shadow", sampleRate: 0.25 } },
  retry: { retry: { maxRetries: 3 } },
  timeout: { timeout: { total: 10 } },
};

function chatWith(clientOpts, params) {
  return async (ctx) => {
    const { __model, __rf, __reply, ...opts } = clientOpts;
    const client = ctx.client({ maxRetries: 0, ...opts });
    return client.chat.completions.create({ ...CHAT, ...(__model ? { model: __model } : {}), ...(__rf ? { response_format: RF } : {}), ...params });
  };
}

export function cases() {
  const out = RESOURCES.map(([name, fn, replies]) => ({ id: `resource.${name}`, area: "resources", fn, replies }));
  for (const [name, value] of Object.entries({ ...BODY_PARAMS, ...GATEWAY_PARAMS })) out.push({ id: `param.chat.${name}`, area: "params", fn: chatWith({}, { [name]: value }), replies: [ok("chat_completion")] });
  for (const name of NULLS) out.push({ id: `param.chat.${name}.null`, area: "params", fn: chatWith({}, { [name]: null }), replies: [ok("chat_completion")] });
  out.push({ id: "param.chat.combined", area: "params", fn: chatWith({}, { ...BODY_PARAMS, ...GATEWAY_PARAMS }), replies: [ok("chat_completion")] });
  for (const [name, opts] of Object.entries(CLIENT_OPTIONS)) {
    out.push({ id: `client_option.${name}`, area: "params", fn: chatWith(opts, {}), replies: [ok(opts.__reply ?? "chat_completion")] });
  }
  for (const [name, value] of Object.entries(WITH_OPTIONS)) {
    out.push({ id: `with_options.${name}`, area: "params", fn: async (ctx) => {
      const base = ctx.client({ maxRetries: 0, defaultHeaders: { "X-Base": "b" }, sessionId: "base-sess" });
      const derived = base.withOptions({ [name]: value });
      return { result: await derived.chat.completions.create(CHAT), base: base.currentCost, derived: derived.currentCost };
    }, replies: [ok("chat_completion")] });
  }
  for (const [name, [clientOpts, params]] of Object.entries(COLLISIONS)) out.push({ id: `header_merge.${name}`, area: "header_merge", fn: chatWith(clientOpts, params), replies: [ok("chat_completion")] });
  out.push({ id: "header_merge.session", area: "header_merge", fn: async (ctx) => {
    const { client, session } = ctx.client({ maxRetries: 0, sessionId: "client-sess" }).session({ sessionId: "ctx-sess", name: "flow", metadata: { k: "v" } });
    session.step("one");
    const a = await client.chat.completions.create(CHAT);
    const b = await client.chat.completions.create({ ...CHAT, session_id: "param-sess", extra_headers: { "x-agentcc-session-id": "explicit" } });
    return { a: a.id, b: b.id, cost: session.totalCost, count: session.requestCount, path: session.path };
  }, replies: [ok("chat_completion", { headers: { "x-agentcc-cost": "0.5" } }), ok("chat_completion")] });
  for (const [name, section] of Object.entries(CONFIG_SECTIONS)) {
    out.push({ id: `config.section.${name}`, area: "config", fn: async (ctx) => ({ headers: ctx.mod.createHeaders({ config: section }), raw: ctx.mod.gatewayConfigToHeaders?.(section) ?? "<not exported>" }) });
    out.push({ id: `config.wire.${name}`, area: "config", fn: chatWith({ config: section }, {}), replies: [ok("chat_completion")] });
  }
  const CH = { apiKey: KEY, traceId: "t", sessionId: "s", sessionName: "flow", sessionPath: "/a/b", metadata: { k: "v" }, userId: "u", requestId: "r", cacheTtl: 60, cacheNamespace: "ns", cacheForceRefresh: true, guardrailPolicy: "strict", properties: { team: "a" } };
  for (const [name, value] of Object.entries(CH)) out.push({ id: `create_headers.${name}`, area: "config", fn: async (ctx) => ctx.mod.createHeaders({ [name]: value }) });
  out.push({ id: "create_headers.combined", area: "config", fn: async (ctx) => ctx.mod.createHeaders(CH) });
  out.push({ id: "create_headers.none", area: "config", fn: async (ctx) => ctx.mod.createHeaders({}) });
  out.push({ id: "session.pure", area: "config", fn: async (ctx) => {
    const s = new ctx.mod.Session({ name: "flow", metadata: { k: "v" } });
    const states = [s.toHeaders()];
    s.step("search"); s.step("summarize"); states.push(s.toHeaders());
    s.trackRequest(0.25, 10); s.trackRequest(0.5, 0);
    const totals = [s.totalCost, s.requestCount, s.totalTokens];
    s.resetPath(); states.push(s.toHeaders());
    return { states, totals, autoId: new ctx.mod.Session().sessionId };
  } });
  const all = responseHeaders("all");
  const meta = async (ctx) => (await ctx.client({ maxRetries: 0 }).chat.completions.create(CHAT)).agentcc;
  out.push({ id: "response_header.none", area: "response_headers", fn: meta, replies: [ok("chat_completion")] });
  out.push({ id: "response_header.all", area: "response_headers", fn: meta, replies: [ok("chat_completion", { headers: all })] });
  out.push({ id: "response_header.malformed", area: "response_headers", fn: meta, replies: [ok("chat_completion", { headers: responseHeaders("malformed") })] });
  out.push({ id: "response_header.stream_all", area: "response_headers", fn: async (ctx) => { const s = await ctx.client({ maxRetries: 0 }).chat.completions.create({ ...CHAT, stream: true }); await ctx.drain(s); return s.agentcc; }, replies: [sse(chunks("content"), { headers: all })] });
  out.push({ id: "response_header.current_cost", area: "response_headers", fn: async (ctx) => { const c = ctx.client({ maxRetries: 0 }); await c.chat.completions.create(CHAT); await c.chat.completions.create(CHAT); const before = c.currentCost; c.resetCost(); return [before, c.currentCost]; }, replies: [ok("chat_completion", { headers: { "x-agentcc-cost": "0.25" } }), ok("chat_completion", { headers: { "x-agentcc-cost": "0.25" } })] });
  for (const [name, value] of Object.entries(all)) out.push({ id: `response_header.alone.${name}`, area: "response_headers", fn: meta, replies: [ok("chat_completion", { headers: { [name]: value } })] });
  return out;
}
