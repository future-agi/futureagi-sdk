export type { Usage, AgentCCMetadata, RateLimitInfo } from "./shared";
export { parseAgentCCMetadata } from "./shared";

// Chat
export type {
  ChatCompletion,
  Choice,
  ChatCompletionMessage,
  ToolCall,
  FunctionCall,
  ChatCompletionChunk,
  StreamChoice,
  Delta,
  ToolCallDelta,
  FunctionCallDelta,
  ChatCompletionCreateParams,
  ChatCompletionMessageParam,
  ContentPart,
  ToolDefinition,
  FunctionDefinition,
  ResponseFormat,
} from "./chat/index";

// Embeddings
export type { Embedding, EmbeddingResponse, EmbeddingCreateParams } from "./embedding";

// Images
export type { ImageData, ImageResponse, ImageGenerateParams } from "./image";

// Audio
export type {
  Transcription,
  Translation,
  TranscriptionCreateParams,
  TranslationCreateParams,
  SpeechCreateParams,
} from "./audio";

// Models
export type { Model, ModelList } from "./model";

// Moderations
export type {
  ModerationResult,
  ModerationResponse,
  ModerationCreateParams,
} from "./moderation";

// Legacy completions
export type { Completion, CompletionChoice, CompletionCreateParams } from "./completion";

// Batches
export type { Batch, BatchList, BatchCreateParams } from "./batch";

// Files
export type { FileObject, FileList, FileUploadParams } from "./files";

// Rerank
export type { RerankResult, RerankResponse, RerankParams } from "./rerank";
