// What this repository adds to or changes in the vendored client (see ../VENDORED.md): the
// `Gateway` class and its settings, and the fixes made while bringing the client in. No network:
// every client here gets a fake `fetch`.

import { AgentCC, CallbackHandler, Gateway, MetricsCallback, checkValidKey, createMiddleware, redactCallbackRequest } from "../index";
import type { CallbackRequest, CallbackResponse, SessionSummary, StreamInfo } from "../index";
import type { ChatCompletion, ChatCompletionChunk } from "../index";
import { Session } from "../session";
import { Stream, StreamManager, parseSSE } from "../streaming";

type Call = { url: string; init: RequestInit };

const COMPLETION = {
  id: "chatcmpl-1",
  object: "chat.completion",
  created: 1,
  model: "gpt-4o-mini",
  choices: [{ index: 0, message: { role: "assistant", content: "Hello there" }, finish_reason: "stop" }],
  usage: { prompt_tokens: 3, completion_tokens: 4, total_tokens: 7 },
};

const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...headers } });

function fakeFetch(respond: (call: Call) => Response): { fetch: typeof globalThis.fetch; calls: Call[] } {
  const calls: Call[] = [];
  const fetch = (async (url: unknown, init?: RequestInit) => {
    const call = { url: String(url), init: init ?? {} };
    calls.push(call);
    return respond(call);
  }) as typeof globalThis.fetch;
  return { fetch, calls };
}

const header = (call: Call, name: string) => (call.init.headers as Record<string, string>)[name];

/** An SSE body delivered in the given byte chunks; `cancelled` records an early close. */
function sseBody(parts: Array<string | Uint8Array>): { body: ReadableStream<Uint8Array>; state: { cancelled: boolean } } {
  const state = { cancelled: false };
  const queue = parts.map((p) => (typeof p === "string" ? new TextEncoder().encode(p) : p));
  const body = new ReadableStream<Uint8Array>({
    pull(controller) {
      const next = queue.shift();
      if (next) controller.enqueue(next);
      else controller.close();
    },
    cancel() {
      state.cancelled = true;
    },
  });
  return { body, state };
}

const chunk = (content: string, extra: Record<string, unknown> = {}) =>
  `data: ${JSON.stringify({ id: "c1", object: "chat.completion.chunk", created: 1, model: "gpt-4o-mini", choices: [{ index: 0, delta: { content }, finish_reason: null }], ...extra })}\n\n`;

const sse = (parts: Array<string | Uint8Array>) => {
  const { body, state } = sseBody(parts);
  return { response: new Response(body, { status: 200, headers: { "content-type": "text/event-stream" } }), state };
};

const ENV = ["FI_GATEWAY_API_KEY", "FI_GATEWAY_URL", "AGENTCC_API_KEY", "AGENTCC_BASE_URL"];

describe("Gateway settings", () => {
  const saved: Record<string, string | undefined> = {};
  beforeEach(() => {
    for (const name of ENV) {
      saved[name] = process.env[name];
      delete process.env[name];
    }
  });
  afterEach(() => {
    for (const name of ENV) {
      if (saved[name] === undefined) delete process.env[name];
      else process.env[name] = saved[name];
    }
  });

  const urlAndKey = async (client: AgentCC, calls: Call[]) => {
    await client.models.list();
    return { url: calls[calls.length - 1].url, auth: header(calls[calls.length - 1], "Authorization") };
  };

  it("defaults to the hosted gateway and reads FI_GATEWAY_* before AGENTCC_*", async () => {
    const { fetch, calls } = fakeFetch(() => json({ object: "list", data: [] }));
    expect((await urlAndKey(new Gateway({ apiKey: "k", fetch }), calls)).url).toBe("https://gateway.futureagi.com/v1/models");

    process.env.AGENTCC_API_KEY = "sk-agentcc-old";
    process.env.AGENTCC_BASE_URL = "http://old.test";
    expect(await urlAndKey(new Gateway({ fetch }), calls)).toEqual({ url: "http://old.test/v1/models", auth: "Bearer sk-agentcc-old" });

    process.env.FI_GATEWAY_API_KEY = "sk-agentcc-new";
    process.env.FI_GATEWAY_URL = "http://new.test";
    expect(await urlAndKey(new Gateway({ fetch }), calls)).toEqual({ url: "http://new.test/v1/models", auth: "Bearer sk-agentcc-new" });
    // The plain AgentCC client reads the same variables.
    expect(await urlAndKey(new AgentCC({ fetch }), calls)).toEqual({ url: "http://new.test/v1/models", auth: "Bearer sk-agentcc-new" });
    // Explicit options win.
    expect(await urlAndKey(new Gateway({ apiKey: "mine", baseUrl: "http://mine.test", fetch }), calls)).toEqual({ url: "http://mine.test/v1/models", auth: "Bearer mine" });
  });

  it("accepts a base URL that ends in /v1", async () => {
    const { fetch, calls } = fakeFetch(() => json({ object: "list", data: [] }));
    for (const baseUrl of ["http://gw.test/v1", "http://gw.test/v1/", "http://gw.test/"]) {
      expect((await urlAndKey(new Gateway({ apiKey: "k", baseUrl, fetch }), calls)).url).toBe("http://gw.test/v1/models");
    }
    process.env.FI_GATEWAY_URL = "http://env.test/v1";
    expect((await urlAndKey(new AgentCC({ apiKey: "k", fetch }), calls)).url).toBe("http://env.test/v1/models");
  });

  it("withOptions and session keep the Gateway class, URL and middlewares", async () => {
    const { fetch, calls } = fakeFetch(() => json({ object: "list", data: [] }));
    const seen: string[] = [];
    const gw = new Gateway({ apiKey: "k", baseUrl: "http://gw.test", fetch });
    gw.use(createMiddleware({ name: "seen", onRequest: (ctx, next) => (seen.push(ctx.path), next(ctx)) }));
    const copy = gw.withOptions({ timeout: 1000 });
    expect(copy).toBeInstanceOf(Gateway);
    expect((await urlAndKey(copy, calls)).url).toBe("http://gw.test/v1/models");
    expect(gw.session().client).toBeInstanceOf(Gateway);
    expect(seen).toEqual(["/v1/models"]);
  });
});

describe("errors", () => {
  const failing = (response: () => Response) => new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", maxRetries: 0, fetch: fakeFetch(response).fetch });

  it("takes the message from OpenAI-style, string and detail error bodies", async () => {
    await expect(failing(() => json({ error: { message: "model not found", type: "invalid_request_error" } }, 404)).models.list()).rejects.toThrow("model not found");
    await expect(failing(() => json({ error: "bad key" }, 401)).models.list()).rejects.toThrow("bad key");
    await expect(failing(() => json({ detail: "no access" }, 403)).models.list()).rejects.toThrow("no access");
    await expect(failing(() => json({ message: "plain" }, 400)).models.list()).rejects.toThrow("plain");
  });

  it("keeps the text of an error body that is not JSON", async () => {
    const html = () => new Response("<html>502 Bad Gateway</html>", { status: 502, headers: { "content-type": "text/html" } });
    await expect(failing(html).models.list()).rejects.toThrow("<html>502 Bad Gateway</html>");
  });

  it("checkValidKey reports a rejected key whatever the server's message says", async () => {
    const original = globalThis.fetch;
    globalThis.fetch = fakeFetch(() => json({ error: { message: "nope" } }, 401)).fetch;
    try {
      expect(await checkValidKey({ apiKey: "sk-bad", baseUrl: "http://gw.test" })).toEqual({ valid: false, error: "Invalid or unauthorized API key" });
    } finally {
      globalThis.fetch = original;
    }
  });
});

class Recorder extends CallbackHandler {
  events: string[] = [];
  ended: CallbackResponse[] = [];
  chunks: ChatCompletionChunk[] = [];
  streamEnd: { info: StreamInfo; completion: ChatCompletion } | null = null;
  errors: Error[] = [];
  summary: SessionSummary | null = null;
  requests: CallbackRequest[] = [];

  override onRequestStart(request: CallbackRequest): void {
    this.events.push("request_start");
    this.requests.push(request);
  }
  override onRequestEnd(_request: CallbackRequest, response: CallbackResponse): void {
    this.events.push("request_end");
    this.ended.push(response);
  }
  override onStreamStart(): void {
    this.events.push("stream_start");
  }
  override onStreamChunk(_request: CallbackRequest, c: ChatCompletionChunk): void {
    this.chunks.push(c);
  }
  override onStreamEnd(_request: CallbackRequest, info: StreamInfo, completion: ChatCompletion): void {
    this.events.push("stream_end");
    this.streamEnd = { info, completion };
  }
  override onError(_request: CallbackRequest, error: Error): void {
    this.errors.push(error);
  }
  override onSessionEnd(_session: Session, summary: SessionSummary): void {
    this.summary = summary;
  }
}

const ASK = { model: "gpt-4o-mini", messages: [{ role: "user" as const, content: "hi" }] };

describe("callbacks and sessions", () => {
  it("onRequestEnd gets the response body of a call the resource parses itself", async () => {
    const recorder = new Recorder();
    const metrics = new MetricsCallback();
    const { fetch } = fakeFetch(() => json(COMPLETION, 200, { "x-agentcc-cost": "0.002" }));
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, callbacks: [recorder, metrics] });
    const reply = await client.chat.completions.create(ASK);
    expect(reply.choices[0].message.content).toBe("Hello there"); // the clone left the body readable
    expect((recorder.ended[0].body as typeof COMPLETION).usage.total_tokens).toBe(7);
    expect(metrics.getMetrics()).toMatchObject({ requestCount: 1, totalTokens: 7, totalCost: 0.002 });
  });

  it("a binary response is not read for the callbacks", async () => {
    const recorder = new Recorder();
    const { fetch } = fakeFetch(() => new Response(new Uint8Array([1, 2, 3]), { status: 200, headers: { "content-type": "audio/mpeg" } }));
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, callbacks: [recorder] });
    const audio = await client.audio.speech.create({ model: "tts-1", input: "hi", voice: "alloy" });
    expect(new Uint8Array(await audio.arrayBuffer())).toEqual(new Uint8Array([1, 2, 3]));
    expect(recorder.ended[0].body).toBeNull();
  });

  it("a session counts tokens, sends the path set by step(), and reports its totals on end()", async () => {
    const recorder = new Recorder();
    const { fetch, calls } = fakeFetch(() => json(COMPLETION, 200, { "x-agentcc-cost": "0.5" }));
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, callbacks: [recorder] });
    const scoped = client.session({ name: "research" });

    await scoped.client.chat.completions.create(ASK);
    expect(header(calls[0], "x-agentcc-session-id")).toBe(scoped.session.sessionId);
    expect(header(calls[0], "x-agentcc-session-path")).toBeUndefined();

    scoped.session.step("summarize");
    await scoped.client.withOptions({ timeout: 5000 }).chat.completions.create(ASK);
    expect(header(calls[1], "x-agentcc-session-path")).toBe("/summarize");
    expect(header(calls[1], "x-agentcc-session-id")).toBe(scoped.session.sessionId);

    expect(scoped.session.requestCount).toBe(2);
    expect(scoped.session.totalTokens).toBe(14);
    expect(scoped.session.totalCost).toBe(1);
    await scoped.end();
    expect(recorder.summary).toEqual({ totalCost: 1, requestCount: 2, totalTokens: 14 });
    // The parent client is not in the session.
    await client.chat.completions.create(ASK);
    expect(header(calls[2], "x-agentcc-session-id")).toBeUndefined();
  });

  it("callbacks get tool-call arguments and instructions redacted", () => {
    const redacted = redactCallbackRequest({
      method: "POST",
      url: "http://gw.test/v1/chat/completions",
      headers: {},
      body: {
        instructions: "secret system prompt",
        messages: [
          { role: "assistant", content: null, tool_calls: [{ id: "t1", type: "function", function: { name: "lookup", arguments: '{"ssn":"123"}' } }] },
          { role: "assistant", content: null, function_call: { name: "old", arguments: '{"card":"4111"}' } },
        ],
      },
    });
    const text = JSON.stringify(redacted.body);
    expect(text).not.toMatch(/123|4111|secret/);
    expect(text).toContain('"name":"lookup"');
  });
});

describe("streams", () => {
  it("reports start, chunks and the final completion to the callbacks, and tokens to the session", async () => {
    const recorder = new Recorder();
    const usage = { prompt_tokens: 2, completion_tokens: 2, total_tokens: 4 };
    const { fetch } = fakeFetch(() => sse([chunk("Hel"), chunk("lo", { usage }), "data: [DONE]\n\n"]).response);
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, callbacks: [recorder] });
    const scoped = client.session();

    const manager = await scoped.client.chat.completions.stream(ASK);
    const text: string[] = [];
    for await (const piece of manager.textStream()) text.push(piece);

    expect(text.join("")).toBe("Hello");
    expect(recorder.events).toEqual(["request_start", "request_end", "stream_start", "stream_end"]);
    expect(recorder.chunks).toHaveLength(2);
    expect(recorder.streamEnd?.info.chunkCount).toBe(2);
    expect(recorder.streamEnd?.completion.choices[0].message.content).toBe("Hello");
    expect(scoped.session.requestCount).toBe(1);
    expect(scoped.session.totalTokens).toBe(4);
  });

  it("a stream that breaks mid-way is reported as an error, not as an end", async () => {
    const recorder = new Recorder();
    const { fetch } = fakeFetch(() => sse([chunk("ok"), "data: {not json\n\n"]).response);
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch, callbacks: [recorder] });
    const stream = await client.chat.completions.create({ ...ASK, stream: true });
    await expect((async () => { for await (const _ of stream) void _; })()).rejects.toThrow("Failed to parse SSE data");
    expect(recorder.errors).toHaveLength(1);
    expect(recorder.events).not.toContain("stream_end");
  });

  it("parses CRLF events and events split across network chunks", async () => {
    const event = `data: ${JSON.stringify({ n: "é" })}`;
    const bytes = new TextEncoder().encode(`${event}\r\n\r\n${event}\r\n\r\n`);
    // Cut inside the multibyte character, and between a CR and its LF.
    const cuts = [bytes.indexOf(0xc3) + 1, bytes.indexOf(0x0d) + 1];
    const parts = [bytes.slice(0, cuts[0]), bytes.slice(cuts[0], cuts[1]), bytes.slice(cuts[1])];
    const seen: string[] = [];
    for await (const e of parseSSE(sseBody(parts).body)) seen.push(e.data ?? "");
    expect(seen).toEqual(['{"n":"é"}', '{"n":"é"}']);
  });

  it("closes the connection when the consumer stops early or the stream says [DONE]", async () => {
    const early = sse([chunk("a"), chunk("b"), chunk("c")]);
    for await (const _ of new Stream(early.response)) {
      void _;
      break;
    }
    expect(early.state.cancelled).toBe(true);

    const done = sse(["data: [DONE]\n\n", chunk("never")]);
    for await (const _ of new Stream(done.response)) void _;
    expect(done.state.cancelled).toBe(true);
  });

  it("a cached JSON answer to a streaming call is read as a chunk", async () => {
    const cached = { ...COMPLETION, choices: [{ index: 0, message: { role: "assistant", content: "cached", tool_calls: [{ id: "t1", type: "function", function: { name: "f", arguments: "{}" } }] }, finish_reason: "stop" }] };
    const manager = new StreamManager(new Stream(json(cached, 200, { "x-agentcc-cache": "hit" })));
    const text: string[] = [];
    for await (const piece of manager.textStream()) text.push(piece);
    expect(text).toEqual(["cached"]);
    const final = manager.getFinalCompletion();
    expect(final.choices[0].message.content).toBe("cached");
    expect(final.choices[0].message.tool_calls?.[0].function.name).toBe("f");
  });
});

describe("middleware", () => {
  it("client.use() runs middlewares around the request, first added outermost", async () => {
    const { fetch, calls } = fakeFetch(() => json(COMPLETION));
    const order: string[] = [];
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch });
    client.use(createMiddleware({
      name: "outer",
      async onRequest(ctx, next) {
        order.push("outer:in");
        const result = await next({ ...ctx, headers: { ...ctx.headers, "x-tenant": "acme" } });
        order.push(`outer:out:${result.statusCode}`);
        return result;
      },
    }));
    client.use(createMiddleware({
      name: "inner",
      async onRequest(ctx, next) {
        order.push(`inner:${ctx.model}`);
        return next({ ...ctx, body: { ...ctx.body, temperature: 0 } });
      },
    }));

    const reply = await client.chat.completions.create(ASK);
    expect(reply.choices[0].message.content).toBe("Hello there");
    expect(order).toEqual(["outer:in", "inner:gpt-4o-mini", "outer:out:200"]);
    expect(header(calls[0], "x-tenant")).toBe("acme");
    expect(JSON.parse(calls[0].init.body as string).temperature).toBe(0);
  });

  it("a middleware leaves a multipart upload intact", async () => {
    const { fetch, calls } = fakeFetch(() => json({ id: "file-1", object: "file" }));
    const client = new AgentCC({ apiKey: "k", baseUrl: "http://gw.test", fetch });
    client.use(createMiddleware({ name: "pass", onRequest: (ctx, next) => next(ctx) }));
    await client.files.create({ file: new Blob(["x"]), purpose: "batch" });
    expect(calls[0].init.body).toBeInstanceOf(FormData);
  });
});
