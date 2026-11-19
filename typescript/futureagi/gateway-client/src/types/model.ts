import type { AgentCCMetadata } from "./shared.js";

export interface Model {
  id: string;
  object: "model";
  created: number;
  owned_by: string;
  [key: string]: unknown;
}

export interface ModelList {
  object: "list";
  data: Model[];
  agentcc?: AgentCCMetadata;
}
