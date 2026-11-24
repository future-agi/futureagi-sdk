import type { AgentCCMetadata } from "./shared";

export interface Batch {
  id: string;
  object: "batch";
  endpoint: string;
  input_file_id: string;
  completion_window: string;
  status: string;
  output_file_id?: string;
  error_file_id?: string;
  created_at: number;
  in_progress_at?: number;
  expires_at?: number;
  finalizing_at?: number;
  completed_at?: number;
  failed_at?: number;
  expired_at?: number;
  cancelling_at?: number;
  cancelled_at?: number;
  request_counts?: { total: number; completed: number; failed: number };
  metadata?: Record<string, string>;
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}

export interface BatchList {
  object: "list";
  data: Batch[];
  has_more: boolean;
  first_id?: string;
  last_id?: string;
}

export interface BatchCreateParams {
  input_file_id: string;
  endpoint: string;
  completion_window: string;
  metadata?: Record<string, string>;
  extra_headers?: Record<string, string>;
  [key: string]: unknown;
}
