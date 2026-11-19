import type { AgentCCMetadata } from "./shared.js";

export interface RerankResult {
  index: number;
  relevance_score: number;
  document?: { text: string };
}

export interface RerankResponse {
  id?: string;
  results: RerankResult[];
  model: string;
  usage?: { total_tokens: number };
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}

export interface RerankParams {
  model: string;
  query: string;
  documents: string[] | { text: string }[];
  top_n?: number;
  return_documents?: boolean;
  extra_headers?: Record<string, string>;
  [key: string]: unknown;
}
