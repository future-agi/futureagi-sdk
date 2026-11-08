// @agentcc/client: pure utilities (S bucket), ./testing mocks, ./express and
// ./nextjs, the env matrix, and the runtime surface of classes and errors.
import { CHAT, MSG, chunks, ok, sse } from "./fixtures.mjs";
import { KEY, OMIT } from "../harness/runner.mjs";

const URL_ = "https://gateway.example.test";
const LONG = [{ role: "system", content: "rules ".repeat(50) }, ...Array.from({ length: 12 }, (_, i) => ({ role: "user", content: `turn ${i} `.repeat(40) }))];
const MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4", "claude-3-5-haiku-20241022", "claude-sonnet-4-20250514", "gemini-2.0-flash", "o1", "text-embedding-3-small", "unknown-model", "openai/gpt-4o", ""];

const ERROR_CTORS = {
  AgentCCError: ["base message"],
  APIConnectionError: ["connection refused"],
  APITimeoutError: [],
  StreamError: ["stream broke", { type: "guardrail_error", code: "stream_blocked", param: null, body: { error: { message: "m" } } }],
};

async function utilities(ctx) {
  const m = ctx.mod;
  const perModel = {};
  for (const model of MODELS) {
    perModel[model] = await ctx.attempt(() => ({
      info: m.getModelInfo(model), maxTokens: m.getMaxTokens(model), maxOutput: m.getMaxOutputTokens(model),
      cost: m.completionCost(model, 1000, 1000), vision: m.supportsVision(model), functions: m.supportsFunctionCalling(model),
      json: m.supportsJsonMode(model), schema: m.supportsResponseSchema(model), contextFallback: m.getContextWindowFallback(model),
      contentFallback: m.getContentPolicyFallback(model), caching: m.isPromptCachingValid(model, LONG.slice(0, 2)),
      encoding: m.getEncodingForModel(model),
    }));
  }
  return {
    perModel,
    valid: m.getValidModels(),
    alias: m.modelAliasMap,
    tokens: await ctx.attempt(() => [m.tokenCounter("gpt-4o", { text: "hello world" }), m.tokenCounter("gpt-4o", { messages: MSG })]),
    encode: await ctx.attempt(() => m.encode("gpt-4o", "hello world")),
    trim: await ctx.attempt(() => [m.trimMessages(LONG, "gpt-4o"), m.trimMessages(LONG, "gpt-4", { maxTokens: 50 })]),
    costFromResponse: await ctx.attempt(() => m.completionCostFromResponse({ model: "gpt-4o", usage: { prompt_tokens: 10, completion_tokens: 5 } })),
    validateEnvironment: m.validateEnvironment(),
    trace: { parse: m.parseTraceparent("00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"), bad: m.parseTraceparent("nope"), id: m.generateTraceId(), span: m.generateSpanId() },
    structured: { validate: m.validateJsonResponse('{"name":"Ada"}', { type: "object", properties: { name: { type: "string" } }, required: ["name"] }), missing: m.validateJsonResponse("{}", { type: "object", required: ["name"] }), isZod: m.isZodSchema({}) },
    functionToTool: await ctx.attempt(() => m.functionToTool(function getWeather(city) { return city; }, { description: "w", parameters: { type: "object" } })),
    rules: { allow: m.evaluatePreCallRules?.([m.allowModels(["gpt-4o"])], { model: "gpt-4o", path: "/v1/chat/completions", body: null }) ?? "<absent>" },
  };
}

async function budget(ctx) {
  const b = new ctx.mod.BudgetManager({ maxBudget: 1, window: "1d" });
  const steps = [];
  const step = async (fn) => steps.push(await ctx.attempt(fn));
  await step(() => b.checkBudget()); b.updateCost(0.4); b.updateCost(0.4, "u1");
  await step(() => [b.getCurrentSpend(), b.getRemainingBudget(), b.projectedCost(1)]);
  b.setUserBudget("u1", 0.5);
  await step(() => [b.isValidUser("u1"), b.isValidUser("nobody")]);
  b.updateCost(0.5);
  await step(() => b.checkBudget(0.1));
  b.reset();
  await step(() => b.getCurrentSpend());
  return steps;
}

async function mocks(ctx) {
  const t = (await ctx.sub("./testing")).module;
  const mock = new t.MockAgentCC();
  mock.chat.completions.respondWith(t.mockCompletion({ content: "first" }));
  const first = await mock.chat.completions.create(CHAT);
  const second = await ctx.attempt(() => mock.chat.completions.create(CHAT));
  const checks = {};
  for (const [name, fn] of Object.entries({
    valid: () => t.assertCompletionValid(first), content: () => t.assertCompletionHasContent(first, "first"), contentFail: () => t.assertCompletionHasContent(first, "nope"),
    usage: () => t.assertUsageValid(t.mockUsage()), meta: () => t.assertAgentCCMetadata(first, { provider: "openai" }), cost: () => t.assertCostTracked(first),
  })) checks[name] = await ctx.attempt(fn);
  return { first, second, calls: mock.chat.completions.calls ?? "<absent>", values: { completion: t.mockCompletion(), meta: t.mockAgentCCMetadata(), usage: t.mockUsage() }, checks };
}

async function express(ctx) {
  const e = (await ctx.sub("./express")).module;
  const mw = e.agentccMiddleware({ apiKey: KEY, baseUrl: URL_, clientOptions: { maxRetries: 0 } });
  const req = { headers: { "x-request-id": "rid-1", traceparent: "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01" }, method: "POST", path: "/chat" };
  let nextCalled = false;
  mw(req, {}, () => { nextCalled = true; });
  const result = await req.agentcc.chat.completions.create(CHAT);
  const bare = { headers: {}, method: "GET", path: "/x" };
  mw(bare, {}, () => {});
  return { nextCalled, result, sessionId: req.agentccSession.sessionId, bareSession: bare.agentccSession.sessionId };
}

async function nextjs(ctx) {
  const n = (await ctx.sub("./nextjs")).module;
  const a = n.createAgentCCClient({ apiKey: KEY, baseUrl: URL_, maxRetries: 0 });
  const same = n.createAgentCCClient({ apiKey: "other" }) === a;
  const m = await a.chat.completions.stream(CHAT);
  const res = n.streamResponse(m, { headers: { "X-Extra": "1" } });
  const text = await res.text();
  n.resetAgentCCClient();
  return { same, status: res.status, headers: [...res.headers.entries()].sort(), text, fresh: n.createAgentCCClient({ apiKey: KEY, baseUrl: URL_ }) !== a };
}

async function nextjsError(ctx) {
  const n = (await ctx.sub("./nextjs")).module;
  n.resetAgentCCClient();
  const a = n.createAgentCCClient({ apiKey: KEY, baseUrl: URL_, maxRetries: 0 });
  const res = n.streamResponse(await a.chat.completions.stream(CHAT));
  n.resetAgentCCClient();
  return res.text();
}

function surface(ctx) {
  const m = ctx.mod;
  const classes = {};
  for (const key of Object.keys(m).sort()) {
    const v = m[key];
    if (typeof v === "function" && /^class\s/.test(Function.prototype.toString.call(v))) {
      classes[key] = { proto: Object.getOwnPropertyNames(v.prototype).sort(), statics: Object.getOwnPropertyNames(v).filter((n) => !["length", "name", "prototype"].includes(n)).sort(), parent: Object.getPrototypeOf(v)?.name ?? null };
    }
  }
  const errors = {};
  for (const key of Object.keys(m).sort()) {
    const v = m[key];
    if (typeof v === "function" && v.prototype instanceof Error) {
      const args = ERROR_CTORS[key] ?? [`${key} message`, 418, { error: { message: "m", type: "t", code: "c", param: "p" } }, new Headers({ "x-agentcc-request-id": "req-1" })];
      try { errors[key] = new v(...args); } catch (err) { errors[key] = { construct_error: err.name, message: err.message }; }
    }
  }
  const client = ctx.client();
  const tree = {};
  for (const key of Object.keys(client).filter((k) => !k.startsWith("_")).sort()) tree[key] = { type: client[key]?.constructor?.name, methods: Object.getOwnPropertyNames(Object.getPrototypeOf(client[key]) ?? {}).sort() };
  const values = {};
  for (const key of ["VERSION", "AGENTCC_GATEWAY_URL"]) values[key] = m[key];
  values.NOT_GIVEN = String(m.NOT_GIVEN);
  return { classes, errors, tree, clientMethods: Object.getOwnPropertyNames(Object.getPrototypeOf(client)).sort(), values };
}

const env = (opts, envVars) => ({ fn: async (ctx) => ctx.client({ maxRetries: 0, ...opts }).models.list(), env: envVars, replies: [ok("models_list")] });

// The env matrix, with the ids and values of its Python twin (cases/envmatrix.py);
// test_parity_twins.py fails if the two languages record different env.* ids.
const KEY_SOURCES = {
  none: [{ apiKey: OMIT }, {}],
  arg: [{ apiKey: "key-from-arg" }, {}],
  agentcc_env: [{ apiKey: OMIT }, { AGENTCC_API_KEY: "key-from-agentcc-env" }],
  fi_gateway_env: [{ apiKey: OMIT }, { FI_GATEWAY_API_KEY: "key-from-fi-gateway-env" }],
  both_env_differ: [{ apiKey: OMIT }, { AGENTCC_API_KEY: "key-agentcc", FI_GATEWAY_API_KEY: "key-fi-gateway" }],
  arg_over_env: [{ apiKey: "key-from-arg" }, { AGENTCC_API_KEY: "key-env", FI_GATEWAY_API_KEY: "key-fi-env" }],
  empty_arg_env: [{ apiKey: "" }, { AGENTCC_API_KEY: "key-from-agentcc-env" }],
};
const URL_SOURCES = {
  none: [{ baseUrl: OMIT }, {}],
  arg: [{ baseUrl: URL_ }, {}],
  agentcc_env: [{ baseUrl: OMIT }, { AGENTCC_BASE_URL: "https://agentcc-env.example.test" }],
  fi_gateway_env: [{ baseUrl: OMIT }, { FI_GATEWAY_BASE_URL: "https://fi-env.example.test" }],
  both_env_differ: [{ baseUrl: OMIT }, { AGENTCC_BASE_URL: "https://agentcc-env.example.test", FI_GATEWAY_BASE_URL: "https://fi-env.example.test" }],
  arg_over_env: [{ baseUrl: URL_ }, { AGENTCC_BASE_URL: "https://agentcc-env.example.test" }],
  gateway_url_env: [{ baseUrl: OMIT }, { AGENTCC_GATEWAY_URL: "https://gateway-url-env.example.test" }],
  empty_arg_env: [{ baseUrl: "" }, { AGENTCC_BASE_URL: "https://agentcc-env.example.test" }],
};
const URL_SHAPES = {
  trailing_slash: `${URL_}/`,
  v1: `${URL_}/v1`,
  v1_slash: `${URL_}/v1/`,
  v1_twice: `${URL_}/v1/v1`,
  prefix: `${URL_}/gw`,
  prefix_v1: `${URL_}/gw/v1`,
  port: "http://127.0.0.1:8090",
  localhost: "http://localhost:8090",
  uppercase_v1: `${URL_}/V1`,
};
const ISOLATION_ENV = {
  FI_API_KEY: "fi-api-key-value",
  FI_SECRET_KEY: "fi-secret-key-value",
  FI_BASE_URL: "https://platform.example.test",
  FI_PLATFORM_TOKEN: "fi-platform-token-value",
  FI_WORKSPACE_ID: "ws-1",
  FI_ORGANIZATION_ID: "org-1",
  OPENAI_API_KEY: "openai-key-value",
  OPENAI_ORG_ID: "org-openai",
  OPENAI_PROJECT_ID: "proj-openai",
  OPENAI_BASE_URL: "https://openai-env.example.test/v1",
};
const GATEWAY_URL_CONSTANT = {
  unset: {},
  agentcc_base_url: { AGENTCC_BASE_URL: "https://from-env.example.test" },
  agentcc_gateway_url: { AGENTCC_GATEWAY_URL: "https://gateway-url-env.example.test" },
  both: { AGENTCC_GATEWAY_URL: "https://gateway-url-env.example.test", AGENTCC_BASE_URL: "https://from-env.example.test" },
};
const chat = (opts = {}) => async (ctx) => ctx.client({ maxRetries: 0, ...opts }).chat.completions.create(CHAT);

function envCases() {
  const out = [];
  for (const [kn, [ko, ke]] of Object.entries(KEY_SOURCES)) for (const [un, [uo, ue]] of Object.entries(URL_SOURCES)) out.push({ id: `env.key_${kn}.url_${un}`, area: "env_matrix", ...env({ ...ko, ...uo }, { ...ke, ...ue }) });
  for (const [name, url] of Object.entries(URL_SHAPES)) out.push({ id: `env.base_url.${name}`, area: "env_matrix", ...env({ baseUrl: url }, {}) });
  out.push({ id: "env.isolation.all_fi_openai_set", area: "env_matrix", ...env({}, ISOLATION_ENV) });
  out.push({ id: "env.isolation.chat", area: "env_matrix", fn: chat(), env: ISOLATION_ENV, replies: [ok("chat_completion")] });
  for (const name of ["FI_API_KEY", "FI_SECRET_KEY"]) {
    out.push({ id: `env.${name.toLowerCase()}_reused_as_gateway_key`, area: "env_matrix", fn: chat({ apiKey: OMIT }), env: { [name]: KEY, AGENTCC_API_KEY: KEY }, replies: [ok("chat_completion")] });
  }
  // The exported AGENTCC_GATEWAY_URL is read once, when the module loads, so each
  // case loads the package in a fresh process with only its own variables set.
  for (const [name, vars] of Object.entries(GATEWAY_URL_CONSTANT)) out.push({ id: `env.gateway_url_constant.${name}`, area: "env_matrix", env: vars, fn: (ctx) => ctx.importTime("AGENTCC_GATEWAY_URL") });
  return out;
}

export function cases() {
  const out = [
    { id: "utility.all", area: "utilities", fn: utilities },
    { id: "utility.budget_manager", area: "utilities", fn: budget },
    { id: "utility.batch_completion", area: "utilities", fn: async (ctx) => ctx.mod.batchCompletion(ctx.client({ maxRetries: 0 }), { model: "gpt-4o-mini", messages: [MSG, [{ role: "user", content: "again" }]], maxConcurrency: 1, returnExceptions: true }), replies: [ok("chat_completion"), { status: 400, json: { error: { message: "bad" } } }] },
    { id: "utility.batch_completion_models", area: "utilities", fn: async (ctx) => ctx.mod.batchCompletionModels(ctx.client({ maxRetries: 0 }), { models: ["gpt-4o-mini", "claude-3-5-haiku"], messages: MSG, maxConcurrency: 1 }), replies: [{ status: 400, json: { error: { message: "bad" } } }, ok("chat_completion")] },
    { id: "utility.patch_openai", area: "utilities", fn: async (ctx) => ctx.attempt(() => ctx.mod.patchOpenAI({ apiKey: KEY, baseUrl: URL_ })) },
    { id: "utility.middleware_use", area: "utilities", fn: async (ctx) => { const seen = []; const c = ctx.client({ maxRetries: 0 }); c.use(ctx.mod.createMiddleware({ name: "m", onRequest: (x) => { seen.push("req"); return x; } })); return { result: await c.chat.completions.create(CHAT), seen }; }, replies: [ok("chat_completion")] },
    { id: "utility.builtin_callbacks", area: "utilities", fn: async (ctx) => { const metrics = new ctx.mod.MetricsCallback(); const c = ctx.client({ maxRetries: 0, callbacks: [metrics, new ctx.mod.LoggingCallback(), new ctx.mod.JSONLoggingCallback()] }); await c.chat.completions.create(CHAT); return metrics.getMetrics?.() ?? metrics; }, replies: [ok("chat_completion", { headers: { "x-agentcc-cost": "0.2" } })] },
    { id: "mock.testing", area: "mocks", fn: mocks },
    { id: "integration.express", area: "express_nextjs", fn: express, replies: [ok("chat_completion")] },
    { id: "integration.nextjs.stream", area: "express_nextjs", fn: nextjs, replies: [sse(chunks("content"))] },
    { id: "integration.nextjs.stream_error", area: "express_nextjs", fn: nextjsError, replies: [sse(['{"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"Hi"},"finish_reason":null}]}', '{"error":{"message":"Content blocked by streaming guardrail","type":"guardrail_error","param":null,"code":"stream_blocked"}}'])] },
    { id: "surface.runtime", area: "surface", fn: surface },
  ];
  return [...out, ...envCases()];
}
