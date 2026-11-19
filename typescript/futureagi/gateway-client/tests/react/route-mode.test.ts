/**
 * @jest-environment ./tests/jsdom-with-fetch.environment.cjs
 */
/**
 * @future-agi/sdk/gateway/react: without an
 * AgentCCProvider the hooks call the app's own server route (default
 * "/api/chat"), so the gateway key stays on the server; under a provider
 * they call the gateway with its client (direct mode, as @agentcc/react 1.0).
 *
 * The route answers are made end to end: canned gateway frames, read by a
 * server-side AgentCC, written by @future-agi/sdk/gateway/nextjs
 * streamResponse. A gateway error frame reaches the
 * page as a typed StreamError with its type, code and param.
 */
import { describe, it, expect, jest, beforeEach, afterEach } from "@jest/globals";
import React from "react";
import type { ReactNode } from "react";
import { renderHook, act, waitFor } from "@testing-library/react";
import { AgentCC, RateLimitError, StreamError } from "../../src/index.js";
import { streamResponse } from "../../src/nextjs.js";
import {
  AgentCCProvider,
  useAgentCCChat,
  useAgentCCClient,
  useAgentCCCompletion,
  useAgentCCObject,
} from "../../src/react/index.js";

type Fetch = typeof globalThis.fetch;

const chunk = (content: string, finish: string | null = null) =>
  JSON.stringify({ id: "c", object: "chat.completion.chunk", created: 1, model: "m", choices: [{ index: 0, delta: { content }, finish_reason: finish }] });
const OK_FRAMES = [chunk("Hello"), chunk(" world", "stop"), "[DONE]"];
const BLOCK = JSON.stringify({ error: { message: "Content blocked by streaming guardrail", type: "guardrail_error", param: null, code: "stream_blocked" } });

function gatewayFetch(frames: string[]) {
  return jest.fn<Fetch>(async () => new Response(frames.map((f) => `data: ${f}\n\n`).join(""), { status: 200, headers: { "content-type": "text/event-stream" } }));
}

/** What the app's route answers: its server code streams the gateway's answer with streamResponse. */
async function routeAnswer(frames: string[]): Promise<Response> {
  // The route's server code; dangerouslyAllowBrowser only because this test runs in a page.
  const server = new AgentCC({ apiKey: "server-key", baseUrl: "http://gw.test", fetch: gatewayFetch(frames), dangerouslyAllowBrowser: true });
  return streamResponse(await server.chat.completions.stream({ model: "m", messages: [] }));
}

let pageFetch: ReturnType<typeof jest.fn<Fetch>>;
let realFetch: Fetch;
beforeEach(() => {
  realFetch = globalThis.fetch;
  pageFetch = jest.fn<Fetch>(async () => routeAnswer(OK_FRAMES));
  globalThis.fetch = pageFetch;
});
afterEach(() => {
  globalThis.fetch = realFetch;
});

function sentTo(fetch: ReturnType<typeof jest.fn<Fetch>>, call = 0) {
  const [url, init] = fetch.mock.calls[call] as [string, RequestInit];
  return { url, init, headers: init.headers as Record<string, string>, body: JSON.parse(String(init.body)) as Record<string, unknown> };
}

describe("useAgentCCChat without a provider: the server route", () => {
  it("POSTs { model, messages, ...body } to /api/chat and streams the route's answer into the assistant message", async () => {
    const { result } = renderHook(() => useAgentCCChat({ model: "gpt-4o-mini", body: { temperature: 0 } }));
    act(() => result.current.append({ role: "user", content: "hi" }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBeNull();
    expect(result.current.messages.map((m) => [m.role, m.content])).toEqual([
      ["user", "hi"],
      ["assistant", "Hello world"],
    ]);
    const { url, init, headers, body } = sentTo(pageFetch);
    expect(url).toBe("/api/chat");
    expect(init.method).toBe("POST");
    expect(headers["Content-Type"]).toBe("application/json");
    expect(body).toEqual({ model: "gpt-4o-mini", messages: [{ role: "user", content: "hi" }], temperature: 0 });
    expect(Object.keys(headers).map((h) => h.toLowerCase())).not.toContain("authorization");
  });

  it("a gateway guardrail block reaches the page as a typed StreamError, after the text before it", async () => {
    pageFetch.mockImplementation(async () => routeAnswer([chunk("Hel"), BLOCK, "[DONE]"]));
    const onError = jest.fn<(e: Error) => void>();
    const onFinish = jest.fn();
    const { result } = renderHook(() => useAgentCCChat({ model: "m", onError, onFinish }));
    act(() => result.current.append({ role: "user", content: "hi" }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    const error = result.current.error as StreamError;
    expect(error).toBeInstanceOf(StreamError);
    expect(error.message).toBe("Content blocked by streaming guardrail");
    expect(error.type).toBe("guardrail_error");
    expect(error.code).toBe("stream_blocked");
    expect(onError).toHaveBeenCalledWith(error);
    expect(onFinish).not.toHaveBeenCalled();
    expect(result.current.messages[1].content).toBe("Hel");
  });

  it("api, headers and fetch options are used for the route request", async () => {
    const own = jest.fn<Fetch>(async () => routeAnswer(OK_FRAMES));
    const { result } = renderHook(() => useAgentCCChat({ model: "m", api: "/api/assistant", headers: { "x-app-session": "abc" }, fetch: own }));
    act(() => result.current.append({ role: "user", content: "hi" }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(pageFetch).not.toHaveBeenCalled();
    const { url, headers } = sentTo(own);
    expect(url).toBe("/api/assistant");
    expect(headers["x-app-session"]).toBe("abc");
    expect(result.current.messages[1].content).toBe("Hello world");
  });

  it("a route error status is the APIStatusError for it, with the route's message", async () => {
    pageFetch.mockImplementation(async () => new Response(JSON.stringify({ error: { message: "slow down" } }), { status: 429, headers: { "content-type": "application/json" } }));
    const { result } = renderHook(() => useAgentCCChat({ model: "m" }));
    act(() => result.current.append({ role: "user", content: "hi" }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBeInstanceOf(RateLimitError);
    expect(result.current.error?.message).toBe("slow down");
  });

  it("a JSON answer from the route (a cache hit passed through) is read as one chunk", async () => {
    pageFetch.mockImplementation(
      async () =>
        new Response(JSON.stringify({ id: "x", object: "chat.completion", created: 1, model: "m", choices: [{ index: 0, message: { role: "assistant", content: "Cached hello" }, finish_reason: "stop" }] }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
    );
    const { result } = renderHook(() => useAgentCCChat({ model: "m" }));
    act(() => result.current.append({ role: "user", content: "hi" }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.messages[1].content).toBe("Cached hello");
  });

  it("stop() aborts the route request and is not an error", async () => {
    let signal: AbortSignal | undefined;
    pageFetch.mockImplementation(
      (_url, init) =>
        new Promise<Response>((_resolve, reject) => {
          signal = init?.signal ?? undefined;
          signal?.addEventListener("abort", () => reject(Object.assign(new Error("aborted"), { name: "AbortError" })));
        }),
    );
    const { result } = renderHook(() => useAgentCCChat({ model: "m" }));
    act(() => result.current.append({ role: "user", content: "hi" }));
    await waitFor(() => expect(result.current.isLoading).toBe(true));
    act(() => result.current.stop());
    await waitFor(() => expect(signal?.aborted).toBe(true));
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });
});

describe("useAgentCCCompletion and useAgentCCObject without a provider", () => {
  it("useAgentCCCompletion joins the text the route streams", async () => {
    const { result } = renderHook(() => useAgentCCCompletion({ model: "m" }));
    await act(() => result.current.complete("Say hello"));
    expect(result.current.completion).toBe("Hello world");
    expect(sentTo(pageFetch).body).toEqual({ model: "m", messages: [{ role: "user", content: "Say hello" }] });
  });

  it("useAgentCCObject sends response_format to the route and parses the streamed JSON", async () => {
    pageFetch.mockImplementation(async () => routeAnswer([chunk("{\"temp\":"), chunk("72}", "stop"), "[DONE]"]));
    const schema = { type: "object", properties: { temp: { type: "number" } } };
    const { result } = renderHook(() => useAgentCCObject<{ temp: number }>({ model: "m", schema, schemaName: "weather" }));
    await act(() => result.current.submit("Weather?"));
    expect(result.current.error).toBeNull();
    expect(result.current.object).toEqual({ temp: 72 });
    expect(sentTo(pageFetch).body.response_format).toEqual({ type: "json_schema", json_schema: { name: "weather", strict: true, schema } });
  });

  it("an error frame on the completion route is a typed StreamError", async () => {
    pageFetch.mockImplementation(async () => routeAnswer([BLOCK]));
    const { result } = renderHook(() => useAgentCCCompletion({ model: "m" }));
    await act(() => result.current.complete("x"));
    expect(result.current.error).toBeInstanceOf(StreamError);
    expect((result.current.error as StreamError).code).toBe("stream_blocked");
  });
});

describe("under an AgentCCProvider: direct mode", () => {
  it("the hooks call the gateway with the provider's client, never the route", async () => {
    const gateway = gatewayFetch(OK_FRAMES);
    const client = new AgentCC({ apiKey: "public-key", baseUrl: "http://gw.test", fetch: gateway, dangerouslyAllowBrowser: true });
    const wrapper = ({ children }: { children?: ReactNode }) => React.createElement(AgentCCProvider, { client }, children);
    const { result } = renderHook(() => ({ chat: useAgentCCChat({ model: "m" }), client: useAgentCCClient() }), { wrapper });
    expect(result.current.client).toBe(client);
    act(() => result.current.chat.append({ role: "user", content: "hi" }));
    await waitFor(() => expect(result.current.chat.isLoading).toBe(false));
    expect(result.current.chat.messages[1].content).toBe("Hello world");
    expect(pageFetch).not.toHaveBeenCalled();
    expect(gateway.mock.calls[0][0]).toBe("http://gw.test/v1/chat/completions");
  });

  it("useAgentCCClient still throws outside a provider, while the hooks fall back to the route", () => {
    const quiet = jest.spyOn(console, "error").mockImplementation(() => {});
    try {
      expect(() => renderHook(() => useAgentCCClient())).toThrow(/AgentCCProvider/);
      expect(() => renderHook(() => useAgentCCChat({ model: "m" }))).not.toThrow();
    } finally {
      quiet.mockRestore();
    }
  });
});
