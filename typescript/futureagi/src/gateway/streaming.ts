import { StreamError } from "./errors";
import type { ChatCompletionChunk } from "./types/chat/chat-completion-chunk";
import type { ChatCompletion, ChatCompletionMessage } from "./types/chat/chat-completion";
import type { AgentCCMetadata } from "./types/shared";
import { parseAgentCCMetadata } from "./types/shared";
import type { StreamEvent } from "./stream-events";

// ---------------------------------------------------------------------------
// SSE parser
// ---------------------------------------------------------------------------

interface SSEEvent {
  data: string | null;
  event: string | null;
  id: string | null;
  retry: number | null;
}

/**
 * Parse an SSE byte stream into individual events.
 * Works with any `ReadableStream<Uint8Array>`.
 */
export async function* parseSSE(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<SSEEvent> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finished = false;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      // SSE lines may end in CRLF; a CR split from its LF by a chunk boundary is joined on the
      // next read, because the replace runs over the whole buffer.
      buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n/g, "\n");

      // Split on double newline (SSE event boundary)
      const parts = buffer.split("\n\n");
      // Keep the last partial part in the buffer
      buffer = parts.pop()!;

      for (const part of parts) {
        const event = parseSSEBlock(part);
        if (event) yield event;
      }
    }

    // Handle any remaining data
    buffer = (buffer + decoder.decode()).replace(/\r\n?/g, "\n");
    if (buffer.trim()) {
      const event = parseSSEBlock(buffer);
      if (event) yield event;
    }
    finished = true;
  } finally {
    // A consumer that stops early (break, throw, `[DONE]`) must not leave the connection open.
    if (!finished) await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

function parseSSEBlock(block: string): SSEEvent | null {
  let data: string | null = null;
  let event: string | null = null;
  let id: string | null = null;
  let retry: number | null = null;

  for (const line of block.split("\n")) {
    if (line.startsWith(":")) continue; // comment
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;
    const field = line.slice(0, colonIdx);
    const value = line.slice(colonIdx + 1).trimStart();

    switch (field) {
      case "data":
        data = data ? data + "\n" + value : value;
        break;
      case "event":
        event = value;
        break;
      case "id":
        id = value;
        break;
      case "retry":
        retry = parseInt(value, 10) || null;
        break;
    }
  }

  if (data === null && event === null) return null;
  return { data, event, id, retry };
}

// ---------------------------------------------------------------------------
// Stream class — async iterable over ChatCompletionChunk
// ---------------------------------------------------------------------------

/** What a `Stream` reports as it is read; the client turns these into the stream callbacks. */
export interface StreamHooks {
  onStart?: () => void | Promise<void>;
  onChunk?: (chunk: ChatCompletionChunk) => void | Promise<void>;
  onEnd?: (completion: ChatCompletion, chunkCount: number) => void | Promise<void>;
  onError?: (error: Error) => void | Promise<void>;
}

// A cache hit on `stream: true` comes back as one JSON chat completion, not as SSE: give it the
// shape of a chunk (`delta`, indexed tool calls) so `textStream()` and the accumulator read it.
function completionAsChunk(json: Record<string, unknown>): ChatCompletionChunk {
  const choices = (Array.isArray(json.choices) ? json.choices : []) as Array<Record<string, unknown>>;
  return {
    ...json,
    object: "chat.completion.chunk",
    choices: choices.map((choice) => {
      if (choice.delta || !choice.message) return choice;
      const { message, ...rest } = choice;
      const delta = { ...(message as Record<string, unknown>) };
      if (Array.isArray(delta.tool_calls)) {
        delta.tool_calls = (delta.tool_calls as Array<Record<string, unknown>>).map((tc, index) => ({ index, ...tc }));
      }
      return { ...rest, delta };
    }),
  } as unknown as ChatCompletionChunk;
}

export class Stream implements AsyncIterable<ChatCompletionChunk> {
  private _response: Response;
  private _agentcc: AgentCCMetadata;
  private _done = false;
  private _hooks: StreamHooks | undefined;

  constructor(response: Response, hooks?: StreamHooks) {
    this._response = response;
    this._agentcc = parseAgentCCMetadata(response.headers);
    this._hooks = hooks;
  }

  /** Gateway metadata parsed from response headers. */
  get agentcc(): AgentCCMetadata {
    return this._agentcc;
  }

  /** The raw fetch Response. */
  get response(): Response {
    return this._response;
  }

  async *[Symbol.asyncIterator](): AsyncGenerator<ChatCompletionChunk> {
    if (this._done) throw new StreamError("Stream already consumed");
    this._done = true;

    const hooks = this._hooks;
    const accumulator = hooks?.onEnd ? new ChunkAccumulator() : null;
    let chunkCount = 0;
    await hooks?.onStart?.();
    try {
      for await (const chunk of this._chunks()) {
        chunkCount++;
        accumulator?.add(chunk);
        await hooks?.onChunk?.(chunk);
        yield chunk;
      }
    } catch (error) {
      await hooks?.onError?.(error as Error);
      throw error;
    }
    // Reached when the stream ran to its end; a consumer that breaks out early gets no onEnd.
    if (accumulator) await hooks?.onEnd?.(accumulator.getFinalCompletion(), chunkCount);
  }

  private async *_chunks(): AsyncGenerator<ChatCompletionChunk> {
    const body = this._response.body;
    if (!body) throw new StreamError("Response body is null");

    // If content-type is JSON (e.g. cache hit), emit a single synthetic chunk
    const ct = this._response.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const chunk = completionAsChunk((await this._response.json()) as Record<string, unknown>);
      chunk.agentcc = this._agentcc;
      yield chunk;
      return;
    }

    for await (const event of parseSSE(body)) {
      if (!event.data) continue;
      if (event.data === "[DONE]") return;

      let chunk: ChatCompletionChunk;
      try {
        chunk = JSON.parse(event.data);
      } catch {
        throw new StreamError(`Failed to parse SSE data: ${event.data}`);
      }
      chunk.agentcc = this._agentcc;
      yield chunk;
    }
  }

  /** Cancel the stream early. */
  abort(): void {
    this._response.body?.cancel().catch(() => {});
    this._done = true;
  }
}

// ---------------------------------------------------------------------------
// ChunkAccumulator — reassemble a ChatCompletion from chunks
// ---------------------------------------------------------------------------

export class ChunkAccumulator {
  private _chunks: ChatCompletionChunk[] = [];
  private _textParts: string[] = [];
  private _id = "";
  private _model = "";
  private _created = 0;

  add(chunk: ChatCompletionChunk): void {
    this._chunks.push(chunk);
    if (!this._id && chunk.id) this._id = chunk.id;
    if (!this._model && chunk.model) this._model = chunk.model;
    if (!this._created && chunk.created) this._created = chunk.created;

    for (const choice of chunk.choices) {
      if (choice.delta?.content) {
        this._textParts.push(choice.delta.content);
      }
    }
  }

  /** Get the accumulated text content. */
  getText(): string {
    return this._textParts.join("");
  }

  /** Reassemble a full ChatCompletion from all accumulated chunks. */
  getFinalCompletion(): ChatCompletion {
    const lastChunk = this._chunks[this._chunks.length - 1];
    const finishReason =
      lastChunk?.choices?.[0]?.finish_reason ?? "stop";

    const message: ChatCompletionMessage = {
      role: "assistant",
      content: this.getText() || null,
    };

    // Collect tool calls
    const toolCallMap = new Map<number, { id: string; type: "function"; function: { name: string; arguments: string } }>();
    for (const chunk of this._chunks) {
      for (const choice of chunk.choices) {
        if (choice.delta?.tool_calls) {
          for (const tc of choice.delta.tool_calls) {
            if (!toolCallMap.has(tc.index)) {
              toolCallMap.set(tc.index, {
                id: tc.id || "",
                type: "function",
                function: { name: "", arguments: "" },
              });
            }
            const acc = toolCallMap.get(tc.index)!;
            if (tc.id) acc.id = tc.id;
            if (tc.function?.name) acc.function.name += tc.function.name;
            if (tc.function?.arguments) acc.function.arguments += tc.function.arguments;
          }
        }
      }
    }
    if (toolCallMap.size > 0) {
      message.tool_calls = [...toolCallMap.entries()]
        .sort(([a], [b]) => a - b)
        .map(([, tc]) => tc);
    }

    return {
      id: this._id,
      object: "chat.completion",
      created: this._created,
      model: this._model,
      choices: [{ index: 0, message, finish_reason: finishReason }],
      usage: lastChunk?.usage,
      agentcc: lastChunk?.agentcc,
    };
  }
}

// ---------------------------------------------------------------------------
// StreamManager — convenience wrapper with text_stream + final completion
// ---------------------------------------------------------------------------

export class StreamManager implements AsyncIterable<ChatCompletionChunk> {
  private _stream: Stream;
  private _accumulator = new ChunkAccumulator();
  private _consumed = false;

  constructor(stream: Stream) {
    this._stream = stream;
  }

  get agentcc(): AgentCCMetadata {
    return this._stream.agentcc;
  }

  /** Iterate over raw chunks. */
  async *[Symbol.asyncIterator](): AsyncGenerator<ChatCompletionChunk> {
    if (this._consumed) throw new StreamError("StreamManager already consumed");
    this._consumed = true;

    for await (const chunk of this._stream) {
      this._accumulator.add(chunk);
      yield chunk;
    }
  }

  /** Iterate over just the text content deltas. */
  async *textStream(): AsyncGenerator<string> {
    for await (const chunk of this) {
      const content = chunk.choices?.[0]?.delta?.content;
      if (content) yield content;
    }
  }

  /** Get the final reassembled ChatCompletion. Must consume the stream first. */
  getFinalCompletion(): ChatCompletion {
    return this._accumulator.getFinalCompletion();
  }

  /** Get the final text. Must consume the stream first. */
  getFinalText(): string {
    return this._accumulator.getText();
  }

  /** Iterate over typed StreamEvent objects. */
  async *events(): AsyncGenerator<StreamEvent> {
    for await (const chunk of this) {
      // Content deltas
      const content = chunk.choices?.[0]?.delta?.content;
      if (content) {
        yield { type: "content", text: content };
      }

      // Tool call deltas
      const toolCalls = chunk.choices?.[0]?.delta?.tool_calls;
      if (toolCalls) {
        for (const tc of toolCalls) {
          yield {
            type: "tool_call",
            index: tc.index,
            id: tc.id,
            name: tc.function?.name,
            arguments: tc.function?.arguments,
          };
        }
      }

      // Usage
      if (chunk.usage) {
        yield { type: "usage", usage: chunk.usage };
      }

      // Done
      const finishReason = chunk.choices?.[0]?.finish_reason;
      if (finishReason === "stop" || finishReason === "tool_calls") {
        yield { type: "done", completion: this._accumulator.getFinalCompletion() };
      }
    }
  }

  /** Cancel the stream early. */
  abort(): void {
    this._stream.abort();
  }
}
