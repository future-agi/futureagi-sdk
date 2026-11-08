// The four integration packages at 1.0.0: @agentcc/langchain, @agentcc/llamaindex,
// @agentcc/vercel and @agentcc/react, each driven through the scripted fetch.
import { CHAT, chunks, ok, sse } from "./fixtures.mjs";
import { BASE_URL, KEY } from "../harness/runner.mjs";

const LC_MSGS = [{ _getType: () => "system", content: "be brief" }, { _getType: () => "human", content: "Say hello" }];
const pkg = async (ctx, name, sub = ".") => (await ctx.target.loadPackage(name, sub)).module;

async function langchain(ctx) {
  const lc = await pkg(ctx, "@agentcc/langchain");
  const model = new lc.ChatAgentCC({ agentccApiKey: KEY, agentccBaseUrl: BASE_URL, model: "gpt-4o-mini", temperature: 0.2, maxTokens: 9, clientOptions: { maxRetries: 0 } });
  const generate = await ctx.attempt(() => model.generate(LC_MSGS, { stop: ["\n"] }));
  const invoke = await ctx.attempt(() => model.invoke(LC_MSGS));
  const stream = await ctx.drain(model.stream(LC_MSGS));
  const emb = new lc.AgentCCEmbeddings({ agentccApiKey: KEY, agentccBaseUrl: BASE_URL, model: "text-embedding-3-small", clientOptions: { maxRetries: 0 } });
  const embedQuery = await ctx.attempt(() => emb.embedQuery("hi"));
  const embedDocuments = await ctx.attempt(() => emb.embedDocuments(["a", "b"]));
  const seen = [];
  const handler = new lc.AgentCCCallbackHandler({ callbacks: [{ onRequestStart: (...a) => seen.push(["start", a.length]), onRequestEnd: (...a) => seen.push(["end", a.length]), onError: (...a) => seen.push(["error", a.length]), onStreamChunk: (...a) => seen.push(["chunk", a.length]) }] });
  await ctx.attempt(() => handler.handleLLMStart({ id: ["x"] }, ["p"], "run-1", undefined, { invocation_params: { model: "gpt-4o" } }));
  await ctx.attempt(() => handler.handleLLMNewToken("tok", undefined, "run-1"));
  await ctx.attempt(() => handler.handleLLMEnd({ generations: [[{ text: "t" }]], llmOutput: { tokenUsage: { totalTokens: 3 } } }, "run-1"));
  await ctx.attempt(() => handler.handleLLMError(new Error("boom"), "run-2"));
  return { lcName: lc.ChatAgentCC.lc_name(), namespace: model.lc_namespace, modelName: model.modelName, generate, invoke, stream, embedQuery, embedDocuments, handler: { name: handler.name, seen } };
}

async function llamaindex(ctx) {
  const li = await pkg(ctx, "@agentcc/llamaindex");
  const llm = new li.AgentCCLLM({ agentccApiKey: KEY, agentccBaseUrl: BASE_URL, model: "gpt-4o-mini", temperature: 0.1, clientOptions: { maxRetries: 0 } });
  const messages = [{ role: "user", content: "Say hello" }];
  const chat = await ctx.attempt(() => llm.chat({ messages }));
  const chatStream = await ctx.drain(llm.chatStream({ messages }));
  const complete = await ctx.attempt(() => llm.complete({ prompt: "Say hello" }));
  const completeStream = await ctx.drain(llm.completeStream({ prompt: "Say hello" }));
  const emb = new li.AgentCCEmbedding({ agentccApiKey: KEY, agentccBaseUrl: BASE_URL, clientOptions: { maxRetries: 0 } });
  const text = await ctx.attempt(() => emb.getTextEmbedding("a"));
  const texts = await ctx.attempt(() => emb.getTextEmbeddings(["a", "b"]));
  const query = await ctx.attempt(() => emb.getQueryEmbedding("q"));
  return { metadata: llm.metadata, chat, chatStream, complete, completeStream, text, texts, query };
}

async function vercel(ctx, settings) {
  const v = await pkg(ctx, "@agentcc/vercel");
  const provider = v.createAgentCC(settings);
  const model = provider("gpt-4o-mini");
  const config = model.config ?? {};
  const generate = await ctx.attempt(() => model.doGenerate({ inputFormat: "messages", mode: { type: "regular" }, prompt: [{ role: "user", content: [{ type: "text", text: "Say hello" }] }] }));
  return {
    provider: model.provider,
    modelId: model.modelId,
    url: await ctx.attempt(() => config.url?.({ modelId: "gpt-4o-mini", path: "/chat/completions" })),
    headers: await ctx.attempt(() => config.headers?.()),
    generate,
  };
}

async function react(ctx, kind) {
  const reactModule = await pkg(ctx, "react");
  const React = reactModule.default ?? reactModule;
  const renderer = await pkg(ctx, "react-test-renderer");
  const r = await pkg(ctx, "@agentcc/react");
  const client = new (await pkg(ctx, "@agentcc/client")).AgentCC({ apiKey: KEY, baseUrl: BASE_URL, maxRetries: 0 });
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  let hook;
  const hooks = {
    chat: () => r.useAgentCCChat({ model: "gpt-4o-mini", body: { temperature: 0 } }),
    completion: () => r.useAgentCCCompletion({ model: "gpt-4o-mini" }),
    object: () => r.useAgentCCObject({ model: "gpt-4o-mini", schema: { type: "object", properties: { name: { type: "string" } } } }),
  };
  function Probe() {
    hook = hooks[kind]();
    return null;
  }
  const tree = React.createElement(r.AgentCCProvider, { client }, React.createElement(Probe));
  const create = renderer.default?.create ?? renderer.create;
  const act = renderer.default?.act ?? renderer.act;
  let root;
  await act(async () => { root = create(tree); });
  const initial = { keys: Object.keys(hook).sort(), state: Object.fromEntries(Object.entries(hook).filter(([, v]) => typeof v !== "function")) };
  const fire = { chat: () => hook.append?.({ role: "user", content: "Say hello" }), completion: () => hook.complete?.("Say hello"), object: () => hook.submit?.("Give a name") };
  const action = await ctx.attempt(async () => { await act(async () => { await fire[kind](); }); });
  const after = Object.fromEntries(Object.entries(hook).filter(([, v]) => typeof v !== "function"));
  await act(async () => root.unmount());
  const outside = await ctx.attempt(async () => { function Bare() { r.useAgentCCClient(); return null; } await act(async () => { create(React.createElement(Bare)); }); });
  return { initial, action, after, outside };
}

export function cases() {
  const replyChat = [ok("chat_completion")];
  return [
    { id: "integration.langchain", area: "integrations", fn: langchain, replies: [ok("chat_completion"), ok("chat_completion"), sse(chunks("content")), ok("embedding"), ok("embedding")] },
    { id: "integration.llamaindex", area: "integrations", fn: llamaindex, replies: [ok("chat_completion"), sse(chunks("content")), ok("chat_completion"), sse(chunks("content")), ok("embedding"), ok("embedding"), ok("embedding")] },
    { id: "integration.vercel.explicit", area: "integrations", fn: (ctx) => vercel(ctx, { apiKey: KEY, baseURL: `${BASE_URL}/v1`, cache: true, guardrailPolicy: "strict", sessionId: "s", traceId: "t", metadata: { k: "v" } }), replies: replyChat },
    { id: "integration.vercel.defaults", area: "integrations", fn: (ctx) => vercel(ctx, {}), replies: replyChat },
    { id: "integration.vercel.env", area: "integrations", fn: (ctx) => vercel(ctx, {}), env: { AGENTCC_API_KEY: "key-from-env", AGENTCC_BASE_URL: "https://agentcc-env.example.test/v1" }, replies: replyChat },
    { id: "integration.vercel.key_env_only", area: "integrations", fn: (ctx) => vercel(ctx, {}), env: { AGENTCC_API_KEY: "key-from-env" }, replies: replyChat },
    { id: "integration.react.chat", area: "integrations", fn: (ctx) => react(ctx, "chat"), replies: [sse(chunks("content")), ok("chat_completion")] },
    { id: "integration.react.completion", area: "integrations", fn: (ctx) => react(ctx, "completion"), replies: [ok("chat_completion"), sse(chunks("content"))] },
    { id: "integration.react.object", area: "integrations", fn: (ctx) => react(ctx, "object"), replies: [ok("chat_completion_json"), sse(chunks("content"))] },
    { id: "integration.react.context", area: "integrations", fn: async (ctx) => { const c = (await pkg(ctx, "@agentcc/react")).AgentCCContext; return { type: String(c?.$$typeof), provider: typeof c?.Provider, consumer: typeof c?.Consumer, defaultValue: c?._currentValue ?? null }; } },
    { id: "integration.chat_via_client", area: "integrations", fn: async (ctx) => new (await pkg(ctx, "@agentcc/client")).AgentCC({ apiKey: KEY, baseUrl: BASE_URL, maxRetries: 0 }).chat.completions.create(CHAT), replies: replyChat },
  ];
}
