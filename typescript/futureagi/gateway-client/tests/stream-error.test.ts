/**
 * A gateway stream that ends with an error event (a guardrail block, an
 * upstream timeout) must raise StreamError from every public stream surface,
 * carrying the gateway's code and message, the way the Python SDK raises
 * StreamError on the same frames.
 *
 * The frames come from sdk/fixtures/stream-error-frames.json, which the
 * Python SDK's tests/test_stream_error_parity.py reads too. All requests go
 * to a mocked fetch; nothing leaves the process.
 */
import { describe, it, expect, jest } from "@jest/globals";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  AgentCC,
  AgentCCError,
  Stream,
  StreamError,
} from "../src/index.js";
import type {
  ChatCompletionChunk,
  ErrorBody,
  StreamErrorOptions,
  StreamEvent,
} from "../src/index.js";
import { streamResponse } from "../src/nextjs.js";

// ---------------------------------------------------------------------------
// Fixture
// ---------------------------------------------------------------------------

interface ErrorExpect {
  raises: true;
  type: string;
  code: string;
  message: string;
  chunks_before_error: number;
  text_before_error: string;
}

interface OkExpect {
  raises: false;
  chunks: number;
  text: string;
  total_tokens: number | null;
}

interface FixtureCase {
  name: string;
  about: string;
  frames: string[];
  expect: ErrorExpect | OkExpect;
}

// sdk/fixtures/stream-error-frames.json at the recorded revision, copied byte for byte into tests/fixtures/gateway.
const FIXTURE_PATH = join(__dirname, "../../../../tests/fixtures/gateway/stream-error-frames.json");
const fixture = JSON.parse(readFileSync(FIXTURE_PATH, "utf8")) as {
  cases: FixtureCase[];
};

// Vitest prints a `$name` string the way chai's inspect does: single-quoted,
// cut to 37 characters and "…" when longer than 38. jest prints it bare, so
// the port passes 1.0.1's title as `$title` and every test name stays equal.
const titled = <T extends { name: string }>(c: T): T & { title: string } => ({
  ...c,
  title: `'${c.name.length > 38 ? `${c.name.slice(0, 37)}…` : c.name}'`,
});

const errorCases = fixture.cases.filter(
  (c): c is FixtureCase & { expect: ErrorExpect } => c.expect.raises,
);
const okCases = fixture.cases.filter(
  (c): c is FixtureCase & { expect: OkExpect } => !c.expect.raises,
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * One SSE frame per read, pulled on demand (highWaterMark 0), the way the
 * gateway flushes each frame. `onCancel` sees the SDK cancel the body.
 */
function sseBody(frames: string[], onCancel?: () => void): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  let i = 0;
  return new ReadableStream<Uint8Array>(
    {
      pull(controller) {
        if (i < frames.length) {
          controller.enqueue(enc.encode(`data: ${frames[i++]}\n\n`));
        } else {
          controller.close();
        }
      },
      cancel() {
        onCancel?.();
      },
    },
    { highWaterMark: 0 },
  );
}

function sseResponse(frames: string[], onCancel?: () => void): Response {
  return new Response(sseBody(frames, onCancel), {
    status: 200,
    headers: {
      "content-type": "text/event-stream",
      "x-agentcc-request-id": "req-sdk101",
    },
  });
}

function clientFor(frames: string[]) {
  const fetch = jest.fn<any>(async () => sseResponse(frames));
  const client = new AgentCC({
    apiKey: "sk-test",
    baseUrl: "http://127.0.0.1:8090",
    fetch,
    maxRetries: 0,
  });
  return { client, fetch };
}

const PARAMS = {
  model: "gpt-4o-mini",
  messages: [{ role: "user" as const, content: "Say hello" }],
};

async function drain<T>(
  iterable: AsyncIterable<T>,
): Promise<{ items: T[]; error: unknown }> {
  const items: T[] = [];
  try {
    for await (const item of iterable) items.push(item);
    return { items, error: null };
  } catch (error) {
    return { items, error };
  }
}

function textOf(chunks: ChatCompletionChunk[]): string {
  return chunks.map((c) => c.choices?.[0]?.delta?.content ?? "").join("");
}

function expectGatewayStreamError(error: unknown, exp: ErrorExpect): void {
  expect(error).toBeInstanceOf(StreamError);
  expect(error).toBeInstanceOf(AgentCCError);
  const err = error as StreamError;
  expect(err.name).toBe("StreamError");
  expect(err.code).toBe(exp.code);
  expect(err.type).toBe(exp.type);
  expect(err.message).toBe(exp.message);
  expect(err.param).toBeNull();
  // The gateway's error object, typed as sent: its param is null.
  const sent: ErrorBody = {
    message: exp.message,
    type: exp.type,
    param: null,
    code: exp.code,
  };
  const body: ErrorBody | string | null = err.body;
  expect(body).toEqual(sent);
}

/** The data payloads of an SSE body, in order. */
function dataFrames(body: string): string[] {
  return body
    .split("\n\n")
    .map((block) => block.trim())
    .filter((block) => block.startsWith("data:"))
    .map((block) => block.slice("data:".length).trim());
}

// ---------------------------------------------------------------------------
// Error frames raise StreamError
// ---------------------------------------------------------------------------

describe.each(errorCases.map(titled))("gateway stream error: $title", ({ frames, expect: exp }) => {
  it("chat.completions.create({ stream: true }) iteration throws StreamError with the code and message", async () => {
    const { client } = clientFor(frames);
    const stream = await client.chat.completions.create({ ...PARAMS, stream: true });
    const { items, error } = await drain(stream);
    expectGatewayStreamError(error, exp);
    expect(items).toHaveLength(exp.chunks_before_error);
    expect(textOf(items)).toBe(exp.text_before_error);
    for (const chunk of items) expect(chunk).not.toHaveProperty("error");
  });

  it("new Stream(response) iteration throws StreamError", async () => {
    const stream = new Stream(sseResponse(frames));
    const { items, error } = await drain(stream);
    expectGatewayStreamError(error, exp);
    expect(items).toHaveLength(exp.chunks_before_error);
  });

  it("StreamManager iteration throws StreamError and keeps the text before it", async () => {
    const { client } = clientFor(frames);
    const manager = await client.chat.completions.stream(PARAMS);
    const { items, error } = await drain(manager);
    expectGatewayStreamError(error, exp);
    expect(items).toHaveLength(exp.chunks_before_error);
    expect(manager.getFinalText()).toBe(exp.text_before_error);
  });

  it("StreamManager.textStream() throws StreamError after the text before it", async () => {
    const { client } = clientFor(frames);
    const manager = await client.chat.completions.stream(PARAMS);
    const { items, error } = await drain(manager.textStream());
    expectGatewayStreamError(error, exp);
    expect(items.join("")).toBe(exp.text_before_error);
  });

  it("StreamManager.events() throws StreamError", async () => {
    const { client } = clientFor(frames);
    const manager = await client.chat.completions.stream(PARAMS);
    const { items, error } = await drain<StreamEvent>(manager.events());
    expectGatewayStreamError(error, exp);
    const text = items
      .map((e) => (e.type === "content" ? e.text : ""))
      .join("");
    expect(text).toBe(exp.text_before_error);
  });

  it("nextjs streamResponse() forwards the gateway's error code and message", async () => {
    const { client } = clientFor(frames);
    const manager = await client.chat.completions.stream(PARAMS);
    const body = await streamResponse(manager).text();
    const out = dataFrames(body);
    expect(out).toHaveLength(exp.chunks_before_error + 1);
    expect(out).not.toContain("[DONE]");
    const last = JSON.parse(out[out.length - 1]) as {
      error?: { message?: string; type?: string; code?: string };
    };
    expect(last.error).toEqual({
      message: exp.message,
      type: exp.type,
      code: exp.code,
    });
  });

  it("cancels the response body once the error frame is read", async () => {
    const onCancel = jest.fn<any>();
    const stream = new Stream(sseResponse(frames, onCancel));
    const { error } = await drain(stream);
    expect(error).toBeInstanceOf(StreamError);
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});

// ---------------------------------------------------------------------------
// Streams without an error still iterate
// ---------------------------------------------------------------------------

describe.each(okCases.map(titled))("gateway stream without error: $title", ({ frames, expect: exp }) => {
  it("Stream iteration yields every chunk", async () => {
    const { client } = clientFor(frames);
    const stream = await client.chat.completions.create({ ...PARAMS, stream: true });
    const { items, error } = await drain(stream);
    expect(error).toBeNull();
    expect(items).toHaveLength(exp.chunks);
    expect(textOf(items)).toBe(exp.text);
    if (exp.total_tokens !== null) {
      const last = items[items.length - 1];
      expect(last.choices).toEqual([]);
      expect(last.usage?.total_tokens).toBe(exp.total_tokens);
    }
  });

  it("StreamManager, textStream() and events() complete", async () => {
    const a = clientFor(frames);
    const manager = await a.client.chat.completions.stream(PARAMS);
    const iterated = await drain(manager);
    expect(iterated.error).toBeNull();
    expect(iterated.items).toHaveLength(exp.chunks);
    expect(manager.getFinalText()).toBe(exp.text);
    if (exp.total_tokens !== null) {
      expect(manager.getFinalCompletion().usage?.total_tokens).toBe(exp.total_tokens);
    }

    const b = clientFor(frames);
    const texts = await drain((await b.client.chat.completions.stream(PARAMS)).textStream());
    expect(texts.error).toBeNull();
    expect(texts.items.join("")).toBe(exp.text);

    const c = clientFor(frames);
    const events = await drain<StreamEvent>((await c.client.chat.completions.stream(PARAMS)).events());
    expect(events.error).toBeNull();
    const usage = events.items.filter((e) => e.type === "usage");
    expect(usage).toHaveLength(exp.total_tokens === null ? 0 : 1);
  });

  it("nextjs streamResponse() ends with [DONE] and no error frame", async () => {
    const { client } = clientFor(frames);
    const manager = await client.chat.completions.stream(PARAMS);
    const out = dataFrames(await streamResponse(manager).text());
    expect(out[out.length - 1]).toBe("[DONE]");
    expect(out).toHaveLength(exp.chunks + 1);
    for (const frame of out.slice(0, -1)) {
      expect(JSON.parse(frame)).not.toHaveProperty("error");
    }
  });
});

// ---------------------------------------------------------------------------
// StreamError shape (TypeScript-only edges)
// ---------------------------------------------------------------------------

describe("StreamError fields", () => {
  it("an SDK-raised StreamError has null gateway fields", () => {
    const err = new StreamError("Stream already consumed");
    expect(err.message).toBe("Stream already consumed");
    expect(err.code).toBeNull();
    expect(err.type).toBeNull();
    expect(err.param).toBeNull();
    expect(err.body).toBeNull();
  });

  it("takes the gateway's fields as options", () => {
    const body: ErrorBody = {
      message: "m",
      type: "guardrail_error",
      param: null,
      code: "stream_blocked",
    };
    const options: StreamErrorOptions = {
      type: "guardrail_error",
      code: "stream_blocked",
      param: null,
      body,
    };
    const err = new StreamError("m", options);
    expect(err.code).toBe("stream_blocked");
    expect(err.type).toBe("guardrail_error");
    const typed: ErrorBody | string | null = err.body;
    expect(typed).toEqual(body);
  });

  it("an error frame whose error is a string raises StreamError with that message", async () => {
    const stream = new Stream(sseResponse(['{"error":"upstream closed the stream"}']));
    const { error } = await drain(stream);
    expect(error).toBeInstanceOf(StreamError);
    expect((error as StreamError).message).toBe("upstream closed the stream");
    expect((error as StreamError).code).toBeNull();
    expect((error as StreamError).body).toBe("upstream closed the stream");
  });

  it.each(["42", "true", '["blocked"]'])(
    "an error frame whose error is %s (neither an object nor a string) raises StreamError with a null body",
    async (value) => {
      const stream = new Stream(sseResponse([`{"error":${value}}`]));
      const { error } = await drain(stream);
      expect(error).toBeInstanceOf(StreamError);
      const err = error as StreamError;
      expect(err.message).toBe(`Stream error: ${value}`);
      expect(err.code).toBeNull();
      expect(err.type).toBeNull();
      expect(err.body).toBeNull();
    },
  );

  it("a chunk with error: null is an ordinary chunk", async () => {
    const chunk =
      '{"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"ok"},"finish_reason":null}],"error":null}';
    const { items, error } = await drain(new Stream(sseResponse([chunk, "[DONE]"])));
    expect(error).toBeNull();
    expect(textOf(items)).toBe("ok");
  });

  it("malformed JSON still raises the parse StreamError", async () => {
    const { error } = await drain(new Stream(sseResponse(["{not json"])));
    expect(error).toBeInstanceOf(StreamError);
    expect((error as StreamError).message).toBe("Failed to parse SSE data: {not json");
  });
});
