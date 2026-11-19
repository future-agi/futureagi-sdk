import type { Usage, AgentCCMetadata } from "../shared.js";

export interface FunctionCall {
  name: string;
  arguments: string;
}

export interface ToolCall {
  id: string;
  type: "function";
  function: FunctionCall;
}

export interface ChatCompletionMessage {
  role: "system" | "user" | "assistant" | "tool" | "function";
  content: string | null;
  function_call?: FunctionCall;
  tool_calls?: ToolCall[];
  name?: string;
  refusal?: string | null;
}

export interface Choice {
  index: number;
  message: ChatCompletionMessage;
  finish_reason: string | null;
  logprobs?: unknown;
}

export interface ChatCompletion {
  id: string;
  object: "chat.completion";
  created: number;
  model: string;
  choices: Choice[];
  usage?: Usage;
  system_fingerprint?: string;
  service_tier?: string;
  /** Gateway metadata — injected by the SDK. */
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}
