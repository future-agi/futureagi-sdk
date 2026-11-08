export type { Usage, AgentCCMetadata, RateLimitInfo } from "./shared.js";
export { parseAgentCCMetadata } from "./shared.js";

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
} from "./chat/index.js";

// Embeddings
export type { Embedding, EmbeddingResponse, EmbeddingCreateParams } from "./embedding.js";

// Images
export type { ImageData, ImageResponse, ImageGenerateParams } from "./image.js";

// Audio
export type {
  Transcription,
  Translation,
  TranscriptionCreateParams,
  TranslationCreateParams,
  SpeechCreateParams,
} from "./audio.js";

// Models
export type { Model, ModelList } from "./model.js";

// Legacy completions
export type { Completion, CompletionChoice, CompletionCreateParams } from "./completion.js";

// Files
export type { FileObject, FileList, FileUploadParams } from "./files.js";

// Rerank
export type { RerankResult, RerankResponse, RerankParams } from "./rerank.js";
