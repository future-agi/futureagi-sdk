import type { AgentCCMetadata } from "./shared";

export interface ModerationCategories {
  hate: boolean;
  "hate/threatening": boolean;
  harassment: boolean;
  "harassment/threatening": boolean;
  "self-harm": boolean;
  "self-harm/intent": boolean;
  "self-harm/instructions": boolean;
  sexual: boolean;
  "sexual/minors": boolean;
  violence: boolean;
  "violence/graphic": boolean;
  [key: string]: boolean;
}

export interface ModerationCategoryScores {
  [key: string]: number;
}

export interface ModerationResult {
  flagged: boolean;
  categories: ModerationCategories;
  category_scores: ModerationCategoryScores;
}

export interface ModerationResponse {
  id: string;
  model: string;
  results: ModerationResult[];
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}

export interface ModerationCreateParams {
  input: string | string[];
  model?: string;
  extra_headers?: Record<string, string>;
  [key: string]: unknown;
}
