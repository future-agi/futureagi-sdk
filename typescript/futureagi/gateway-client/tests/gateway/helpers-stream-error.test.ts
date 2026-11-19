/**
 * Stream error frames through the server helpers: a gateway error frame on a
 * 200 stream raises a typed StreamError (type, code, param) through the
 * client ./gateway/express attaches to each request, and ./gateway/nextjs
 * streamResponse forwards those fields to the page (the 1.0.1 tests in
 * tests/stream-error.test.ts cover streamResponse frame by frame; the React
 * hooks read them back in tests/react/route-mode.test.ts).
 */
import { describe, it, expect, jest } from "@jest/globals";
import { StreamError } from "../../src/index.js";
import { agentccMiddleware } from "../../src/express.js";
import { createAgentCCClient, resetAgentCCClient, streamResponse } from "../../src/nextjs.js";

const BLOCK = { error: { message: "Content blocked by streaming guardrail", type: "guardrail_error", param: "messages", code: "stream_blocked" } };
const CONTENT = { id: "c", object: "chat.completion.chunk", created: 1, model: "m", choices: [{ index: 0, delta: { content: "Hel" }, finish_reason: null }] };

function gateway() {
  return jest.fn<typeof globalThis.fetch>(
    async () =>
      new Response([CONTENT, BLOCK].map((f) => `data: ${JSON.stringify(f)}\n\n`).join("") + "data: [DONE]\n\n", {
        status: 200,
        headers: { "content-type": "text/event-stream" },
      }),
  );
}

describe("server helpers keep the gateway's stream error typed", () => {
  it("express: the client agentccMiddleware attaches raises StreamError with type, code and param", async () => {
    const mw = agentccMiddleware({ apiKey: "k", baseUrl: "http://gw.test", clientOptions: { fetch: gateway() } });
    const req: { method: string; path: string; headers: Record<string, string>; agentcc?: import("../../src/client.js").AgentCC } = { method: "POST", path: "/chat", headers: {} };
    await new Promise<void>((resolve) => mw(req, { on() {} }, () => resolve()));
    const stream = await req.agentcc!.chat.completions.create({ model: "m", messages: [{ role: "user", content: "hi" }], stream: true });
    const text: string[] = [];
    let caught: unknown = null;
    try {
      for await (const chunk of stream) text.push(chunk.choices[0]?.delta?.content ?? "");
    } catch (e) {
      caught = e;
    }
    expect(text.join("")).toBe("Hel");
    expect(caught).toBeInstanceOf(StreamError);
    expect(caught).toMatchObject({ message: BLOCK.error.message, type: "guardrail_error", code: "stream_blocked", param: "messages" });
  });

  it("nextjs: createAgentCCClient + streamResponse forward type, code and param and end without [DONE]", async () => {
    resetAgentCCClient();
    try {
      const client = createAgentCCClient({ apiKey: "k", baseUrl: "http://gw.test", fetch: gateway() });
      const body = await streamResponse(await client.chat.completions.stream({ model: "m", messages: [] })).text();
      const frames = body.split("\n\n").filter(Boolean).map((f) => f.replace(/^data: /, ""));
      expect(frames).toHaveLength(2);
      expect(JSON.parse(frames[1])).toEqual({ error: { message: BLOCK.error.message, type: "guardrail_error", code: "stream_blocked", param: "messages" } });
    } finally {
      resetAgentCCClient();
    }
  });
});
