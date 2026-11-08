import { StreamError } from "./errors.js";
import type { ChatCompletionChunk } from "./types/chat/chat-completion-chunk.js";
import type { ChatCompletion, ChatCompletionMessage } from "./types/chat/chat-completion.js";
import type { AgentCCMetadata, Usage } from "./types/shared.js";
import { parseAgentCCMetadata } from "./types/shared.js";
import type { StreamEvent } from "./stream-events.js";
import { parseSSE } from "./sse.js";
import { chunkFromCompletion, streamErrorFromEvent } from "./stream-frames.js";

// ---------------------------------------------------------------------------
// Stream class — async iterable over ChatCompletionChunk
// ---------------------------------------------------------------------------

export class Stream implements AsyncIterable<ChatCompletionChunk> {
  private _response: Response;
  private _agentcc: AgentCCMetadata;
  private _done = false;

  constructor(response: Response) {
    this._response = response;
    this._agentcc = parseAgentCCMetadata(response.headers);
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

    const body = this._response.body;
    if (!body) throw new StreamError("Response body is null");

    // A JSON answer to a stream request (a cache hit or another short-circuit)
    // is one whole completion: yield it as one real chunk.
    const ct = this._response.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      yield this._jsonAnswerChunk(await this._response.text());
      return;
    }

    let gatewayError: StreamError | null = null;
    for await (const event of parseSSE(body)) {
      if (!event.data) continue;
      if (event.data === "[DONE]") return;

      let data: unknown;
      try {
        data = JSON.parse(event.data);
      } catch {
        throw new StreamError(`Failed to parse SSE data: ${event.data}`);
      }
      if (typeof data !== "object" || data === null) {
        throw new StreamError(`Failed to parse SSE data: ${event.data}`);
      }

      // The gateway ends a stream it refuses (a guardrail block, an upstream
      // timeout) with {"error": {...}} in a data frame, sometimes followed by
      // a metadata chunk and [DONE]. Stop there: nothing after it is answer.
      gatewayError = streamErrorFromEvent(data);
      if (gatewayError) break;

      const chunk = data as ChatCompletionChunk;
      chunk.agentcc = this._agentcc;
      yield chunk;
    }

    if (gatewayError) {
      // Release the connection: the frames after the error are not read.
      this.abort();
      throw gatewayError;
    }
  }

  /** The one chunk a JSON answer to a stream request stands for. */
  private _jsonAnswerChunk(text: string): ChatCompletionChunk {
    let json: unknown;
    try {
      json = JSON.parse(text);
    } catch {
      throw new StreamError(`Failed to parse JSON answer: ${text.slice(0, 200)}`);
    }
    if (typeof json !== "object" || json === null || Array.isArray(json)) {
      throw new StreamError(`Failed to parse JSON answer: ${text.slice(0, 200)}`);
    }
    const gatewayError = streamErrorFromEvent(json);
    if (gatewayError) throw gatewayError;
    const body = json as Record<string, unknown>;
    const chunk = body.object === "chat.completion.chunk" ? (body as ChatCompletionChunk) : chunkFromCompletion(body);
    chunk.agentcc = this._agentcc;
    return chunk;
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
  private _usage: Usage | undefined;

  add(chunk: ChatCompletionChunk): void {
    this._chunks.push(chunk);
    // The final usage is the last usage the stream carried. The gateway
    // sends it on its own chunk (empty choices) when the upstream does; a chunk
    // after it without usage no longer erases it.
    if (chunk.usage) this._usage = chunk.usage;
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
    // The finish reason is the last chunk that has choices: the gateway ends
    // a stream with a usage chunk whose choices are empty, which must not
    // turn "tool_calls" or "length" into "stop" (1.0.1 read the last chunk).
    let lastWithChoices: ChatCompletionChunk | undefined;
    for (let i = this._chunks.length - 1; i >= 0 && !lastWithChoices; i--) {
      if ((this._chunks[i].choices?.length ?? 0) > 0) lastWithChoices = this._chunks[i];
    }
    const finishReason = lastWithChoices?.choices[0]?.finish_reason ?? "stop";

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
      usage: this._usage,
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
    let usageSeen = false;
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

      // Usage: one event per stream, at the first chunk that carries usage.
      // The gateway sends the usage again on a trailing chunk with empty
      // choices; a consumer that adds up usage events must not count it
      // twice. The final completion's usage is the last one carried.
      if (chunk.usage && !usageSeen) {
        usageSeen = true;
        yield { type: "usage", usage: chunk.usage };
      }
    }

    // Done: only once the body has ended ([DONE] or its end) without
    // an error frame. 1.0.1 yielded done at the chunk with finish_reason
    // "stop" or "tool_calls", so a guardrail error the gateway sends after it
    // reached only consumers that kept reading past done, and a stream that
    // ended on "length" never yielded done.
    yield { type: "done", completion: this._accumulator.getFinalCompletion() };
  }

  /** Cancel the stream early. */
  abort(): void {
    this._stream.abort();
  }
}
