// ---------------------------------------------------------------------------
// What a streaming answer's payloads mean: a gateway error frame, or a JSON
// answer to a stream request.
// ---------------------------------------------------------------------------

import { streamFrameError } from "./errors.js";
import type { ErrorBody, StreamError } from "./errors.js";
import type { GatewayEvidence } from "./gateway-evidence.js";
import type { ChatCompletionChunk, StreamChoice, ToolCallDelta } from "./types/chat/chat-completion-chunk.js";

// --- Gateway error frames (moved verbatim from streaming.ts, 1.0.1) ---


function stringOrNull(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

/**
 * The StreamError for a parsed SSE payload that carries a non-null `error`
 * (the gateway's `{"error": {"message", "type", "param", "code"}}`), or null
 * for an ordinary chunk.
 */
export function streamErrorFromEvent(data: object, gatewayEvidence?: GatewayEvidence): StreamError | null {
  if (Array.isArray(data) || !("error" in data)) return null;
  const error = (data as { error: unknown }).error;
  if (error === null || error === undefined) return null;

  if (typeof error === "string") {
    return streamFrameError(error || "Stream error", { body: error, gatewayEvidence });
  }
  if (typeof error === "object" && !Array.isArray(error)) {
    const e = error as ErrorBody;
    const message =
      typeof e.message === "string" && e.message
        ? e.message
        : `Stream error: ${JSON.stringify(error)}`;
    return streamFrameError(message, {
      gatewayEvidence,
      type: stringOrNull(e.type),
      code: stringOrNull(e.code),
      param: stringOrNull(e.param),
      body: e,
    });
  }
  // Neither an object nor a string: the message carries the value.
  return streamFrameError(`Stream error: ${JSON.stringify(error)}`, { gatewayEvidence });
}

// --- A JSON answer to a stream request ---

type Json = Record<string, unknown>;

function isObject(value: unknown): value is Json {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function toolCallDeltas(toolCalls: unknown): ToolCallDelta[] | undefined {
  if (!Array.isArray(toolCalls) || toolCalls.length === 0) return undefined;
  return toolCalls.map((call, index) => {
    const tc = isObject(call) ? call : {};
    const fn = isObject(tc.function) ? tc.function : undefined;
    const delta: ToolCallDelta = { index };
    if (typeof tc.id === "string") delta.id = tc.id;
    if (tc.type === "function") delta.type = "function";
    if (fn) {
      delta.function = {};
      if (typeof fn.name === "string") delta.function.name = fn.name;
      if (typeof fn.arguments === "string") delta.function.arguments = fn.arguments;
    }
    return delta;
  });
}

/**
 * One chunk carrying a whole chat completion. The gateway answers a
 * `stream: true` request with plain JSON when it short-circuits (a cache hit;
 * chat_stream.go:211-214 at the recorded source). @agentcc/client 1.x yielded that
 * body as if it were a chunk (`object: "chat.completion"`, `message` instead
 * of `delta`), so stream consumers read no text from it. Each choice's
 * message becomes its delta (role, content, tool calls with their index), and
 * finish_reason and usage are kept, as fi.gateway (Python) does.
 */
export function chunkFromCompletion(body: Json): ChatCompletionChunk {
  const choices: StreamChoice[] = (Array.isArray(body.choices) ? body.choices : []).map((raw, i) => {
    const choice = isObject(raw) ? raw : {};
    const message = isObject(choice.message) ? choice.message : {};
    const delta: StreamChoice["delta"] = {};
    if (typeof message.role === "string") delta.role = message.role;
    if (typeof message.content === "string" || message.content === null) delta.content = message.content as string | null;
    const toolCalls = toolCallDeltas(message.tool_calls);
    if (toolCalls) delta.tool_calls = toolCalls;
    if (typeof message.refusal === "string") delta.refusal = message.refusal;
    return {
      index: typeof choice.index === "number" ? choice.index : i,
      delta,
      finish_reason: typeof choice.finish_reason === "string" ? choice.finish_reason : null,
    };
  });
  const chunk: ChatCompletionChunk = {
    id: typeof body.id === "string" ? body.id : "",
    object: "chat.completion.chunk",
    created: typeof body.created === "number" ? body.created : 0,
    model: typeof body.model === "string" ? body.model : "",
    choices,
  };
  if (isObject(body.usage)) chunk.usage = body.usage as unknown as ChatCompletionChunk["usage"];
  if (typeof body.system_fingerprint === "string") chunk.system_fingerprint = body.system_fingerprint;
  return chunk;
}
