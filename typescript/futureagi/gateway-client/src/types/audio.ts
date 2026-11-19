import type { AgentCCMetadata } from "./shared.js";

export interface Transcription {
  text: string;
  task?: string;
  language?: string;
  duration?: number;
  segments?: unknown[];
  words?: unknown[];
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}

export interface Translation {
  text: string;
  task?: string;
  language?: string;
  duration?: number;
  agentcc?: AgentCCMetadata;
  [key: string]: unknown;
}

export interface TranscriptionCreateParams {
  file: Blob | Buffer | ArrayBuffer;
  model: string;
  language?: string;
  prompt?: string;
  response_format?: "json" | "text" | "srt" | "verbose_json" | "vtt";
  temperature?: number;
  timestamp_granularities?: ("word" | "segment")[];
  extra_headers?: Record<string, string>;
  [key: string]: unknown;
}

export interface TranslationCreateParams {
  file: Blob | Buffer | ArrayBuffer;
  model: string;
  prompt?: string;
  response_format?: "json" | "text" | "srt" | "verbose_json" | "vtt";
  temperature?: number;
  extra_headers?: Record<string, string>;
  [key: string]: unknown;
}

export interface SpeechCreateParams {
  input: string;
  model: string;
  voice: "alloy" | "echo" | "fable" | "onyx" | "nova" | "shimmer" | string;
  response_format?: "mp3" | "opus" | "aac" | "flac" | "wav" | "pcm";
  speed?: number;
  extra_headers?: Record<string, string>;
  [key: string]: unknown;
}
