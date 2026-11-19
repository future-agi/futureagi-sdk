import type { Usage, AgentCCMetadata } from "./shared.js";

export interface CompletionChoice {
  index: number;
  text: string;
  finish_reason: string | null;
  logprobs?: unknown;
}

export interface Completion {
  id: string;
  object: "text_completion";
  created: number;
  model: string;
  choices: CompletionChoice[];
  usage?: Usage;
  system_fingerprint?: string;
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}

export interface CompletionCreateParams {
  model: string;
  prompt: string | string[] | number[] | number[][];
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
  n?: number;
  stream?: boolean;
  logprobs?: number | null;
  echo?: boolean;
  stop?: string | string[] | null;
  presence_penalty?: number;
  frequency_penalty?: number;
  best_of?: number;
  logit_bias?: Record<string, number>;
  user?: string;
  suffix?: string;
  seed?: number;
  extra_headers?: Record<string, string>;
  [key: string]: unknown;
}
