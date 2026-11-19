import type { Usage, AgentCCMetadata } from "./shared.js";

export interface Embedding {
  object: "embedding";
  index: number;
  embedding: number[] | string;
}

export interface EmbeddingResponse {
  object: "list";
  data: Embedding[];
  model: string;
  usage: Usage;
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}

export interface EmbeddingCreateParams {
  model: string;
  input: string | string[] | number[] | number[][];
  encoding_format?: "float" | "base64";
  dimensions?: number;
  user?: string;
  extra_headers?: Record<string, string>;
  [key: string]: unknown;
}
