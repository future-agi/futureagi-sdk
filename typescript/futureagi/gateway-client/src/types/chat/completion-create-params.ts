import type { NotGiven } from "../../constants.js";

export interface ChatCompletionMessageParam {
  role: "system" | "user" | "assistant" | "tool" | "function";
  content: string | Array<ContentPart> | null;
  name?: string;
  tool_call_id?: string;
}

export interface ContentPart {
  type: "text" | "image_url";
  text?: string;
  image_url?: { url: string; detail?: "auto" | "low" | "high" };
}

export interface FunctionDefinition {
  name: string;
  description?: string;
  parameters?: Record<string, unknown>;
}

export interface ToolDefinition {
  type: "function";
  function: FunctionDefinition;
}

export interface ResponseFormat {
  type: "text" | "json_object" | "json_schema";
  json_schema?: {
    name: string;
    description?: string;
    schema: Record<string, unknown>;
    strict?: boolean;
  };
}

/**
 * Parameters for `chat.completions.create()`.
 *
 * Standard OpenAI fields plus AgentCC-specific params (which become headers).
 */
export interface ChatCompletionCreateParams {
  // --- Required ---
  model: string;
  messages: ChatCompletionMessageParam[];

  // --- OpenAI optional ---
  temperature?: number | null;
  top_p?: number | null;
  n?: number | null;
  stream?: boolean | null;
  stop?: string | string[] | null;
  max_tokens?: number | null;
  max_completion_tokens?: number | null;
  presence_penalty?: number | null;
  frequency_penalty?: number | null;
  logit_bias?: Record<string, number> | null;
  logprobs?: boolean | null;
  top_logprobs?: number | null;
  user?: string;
  seed?: number | null;
  tools?: ToolDefinition[];
  tool_choice?: "none" | "auto" | "required" | { type: "function"; function: { name: string } };
  response_format?: ResponseFormat;
  service_tier?: string;
  thinking?: { type: string; budget_tokens?: number };
  reasoning_effort?: string;

  // --- AgentCC-specific (extracted to headers) ---
  session_id?: string | NotGiven;
  trace_id?: string | NotGiven;
  request_metadata?: Record<string, unknown> | NotGiven;
  request_timeout?: number | NotGiven;
  cache_ttl?: number | NotGiven;
  cache_namespace?: string | NotGiven;
  cache_force_refresh?: boolean | NotGiven;
  cache_control?: string | NotGiven;
  guardrail_policy?: string | NotGiven;

  // --- Pass-through ---
  extra_headers?: Record<string, string>;
  extra_body?: Record<string, unknown>;

  [key: string]: unknown;
}
