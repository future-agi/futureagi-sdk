import type { Usage, AgentCCMetadata } from "../shared.js";

export interface FunctionCallDelta {
  name?: string;
  arguments?: string;
}

export interface ToolCallDelta {
  index: number;
  id?: string;
  type?: "function";
  function?: FunctionCallDelta;
}

export interface Delta {
  role?: string;
  content?: string | null;
  tool_calls?: ToolCallDelta[];
  refusal?: string | null;
}

export interface StreamChoice {
  index: number;
  delta: Delta;
  finish_reason: string | null;
  logprobs?: unknown;
}

export interface ChatCompletionChunk {
  id: string;
  object: "chat.completion.chunk";
  created: number;
  model: string;
  choices: StreamChoice[];
  usage?: Usage;
  system_fingerprint?: string;
  /** Gateway metadata — injected by the SDK from response headers. */
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}
