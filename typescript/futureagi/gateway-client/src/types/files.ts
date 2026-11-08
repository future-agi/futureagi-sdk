import type { AgentCCMetadata } from "./shared.js";

export interface FileObject {
  id: string;
  object: "file";
  bytes: number;
  created_at: number;
  filename: string;
  purpose: string;
  status?: string;
  status_details?: string;
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}

export interface FileList {
  object: "list";
  data: FileObject[];
}

export interface FileUploadParams {
  file: Blob | Buffer | ArrayBuffer;
  purpose: string;
  extra_headers?: Record<string, string>;
  [key: string]: unknown;
}
