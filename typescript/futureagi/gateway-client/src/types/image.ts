import type { AgentCCMetadata } from "./shared.js";

export interface ImageData {
  url?: string;
  b64_json?: string;
  revised_prompt?: string;
}

export interface ImageResponse {
  created: number;
  data: ImageData[];
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}

export interface ImageGenerateParams {
  prompt: string;
  model?: string;
  n?: number;
  quality?: "standard" | "hd";
  response_format?: "url" | "b64_json";
  size?: "256x256" | "512x512" | "1024x1024" | "1792x1024" | "1024x1792";
  style?: "vivid" | "natural";
  user?: string;
  extra_headers?: Record<string, string>;
  [key: string]: unknown;
}
