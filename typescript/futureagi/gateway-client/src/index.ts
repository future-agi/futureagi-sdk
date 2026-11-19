// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
export { AgentCC } from "./client.js";
export type { ClientOptions, WithResponseResult } from "./base-client.js";

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------
export {
  AgentCCError,
  APIConnectionError,
  APITimeoutError,
  ResponseBodyError,
  APIStatusError,
  BadRequestError,
  AuthenticationError,
  PermissionDeniedError,
  FutureAGICreditsOffError,
  NotFoundError,
  UnprocessableEntityError,
  RateLimitError,
  InsufficientCreditsError,
  AgentBudgetExhaustedError,
  BudgetExceededError,
  InternalServerError,
  BadGatewayError,
  ServiceUnavailableError,
  GatewayTimeoutError,
  GuardrailBlockedError,
  GuardrailWarning,
  StreamError,
} from "./errors.js";
export type { ErrorBody, StreamErrorOptions } from "./errors.js";
export type { RefusalCategory } from "./refusal-policy.js";
export { MAX_RETRY_AFTER_SECONDS } from "./refusal-policy.js";
export type { GatewayErrorMetadata, ManagedModelUnpricedMetadata, ManagedModelAmbiguousMetadata } from "./refusal-metadata.js";
export { parseGatewayEvidence, getGatewayEvidence } from "./gateway-evidence.js";
export type { DispatchState, GatewayEvidence, GatewayEvidenceOptions, GatewayEvidenceHeaders } from "./gateway-evidence.js";

// ---------------------------------------------------------------------------
// Gateway Configuration
// ---------------------------------------------------------------------------
export type { GatewayConfig, CacheConfig, CreateHeadersOptions } from "./gateway-config.js";
export { createHeaders } from "./gateway-config.js";

// ---------------------------------------------------------------------------
// Stock SDKs pointed at the gateway (OpenAI, LangChain, LlamaIndex, Vercel AI SDK)
// ---------------------------------------------------------------------------
export { openaiOptions, aiSdkProviderSettings } from "./stock-sdk.js";
export type { OpenAIOptionsInput, OpenAIClientOptions, AgentCCProviderSettings, AiSdkProviderSettings } from "./stock-sdk.js";

// ---------------------------------------------------------------------------
// Streaming
// ---------------------------------------------------------------------------
export { Stream, StreamManager, ChunkAccumulator } from "./streaming.js";
export type { StreamEvent } from "./stream-events.js";

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------
export { Session } from "./session.js";
export type { SessionOptions } from "./session.js";

// ---------------------------------------------------------------------------
// Callbacks
// ---------------------------------------------------------------------------
export { CallbackHandler, invokeCallbacks } from "./callbacks.js";
export type { CallbackRequest, CallbackResponse } from "./callbacks.js";
export {
  LoggingCallback,
  MetricsCallback,
  JSONLoggingCallback,
} from "./callbacks-builtin.js";

// ---------------------------------------------------------------------------
// Retry Policy
// ---------------------------------------------------------------------------
export { RetryPolicy } from "./retry-policy.js";
export type { RetryPolicyOptions } from "./retry-policy.js";

// ---------------------------------------------------------------------------
// Redaction
// ---------------------------------------------------------------------------
export { redactCallbackRequest } from "./redact.js";

// ---------------------------------------------------------------------------
// Constants & Utilities
// ---------------------------------------------------------------------------
export { VERSION, NOT_GIVEN } from "./constants.js";
export type { NotGiven } from "./constants.js";

// ---------------------------------------------------------------------------
// Trace Context (W3C)
// ---------------------------------------------------------------------------
export {
  TraceContextManager,
  generateTraceId,
  generateSpanId,
  parseTraceparent,
  formatTraceparent,
} from "./trace-context.js";
export type {
  TraceContext,
  TraceContextManagerOptions,
} from "./trace-context.js";

// ---------------------------------------------------------------------------
// OpenTelemetry Callback
// ---------------------------------------------------------------------------
export { OTelCallback } from "./otel-callback.js";
export type {
  OTelCallbackOptions,
  OTelTracer,
  OTelSpan,
  OTelMeter,
  OTelCounter,
  OTelHistogram,
} from "./otel-callback.js";

// ---------------------------------------------------------------------------
// Structured Output & Zod
// ---------------------------------------------------------------------------
export { zodToJsonSchema, isZodSchema } from "./structured-output.js";

// ---------------------------------------------------------------------------
// Function → Tool Definition
// ---------------------------------------------------------------------------
export { functionToTool } from "./function-to-tool.js";
export type { FunctionToToolOptions } from "./function-to-tool.js";

// ---------------------------------------------------------------------------
// Pagination
// ---------------------------------------------------------------------------
export { PaginatedList } from "./pagination.js";

// ---------------------------------------------------------------------------
// Tool Execution Loop
// ---------------------------------------------------------------------------
export { RunToolsRunner } from "./run-tools.js";
export type {
  ToolWithExecute,
  ToolStep,
  RunToolsResult,
  RunToolsParams,
} from "./run-tools.js";

// ---------------------------------------------------------------------------
// Response Validation
// ---------------------------------------------------------------------------
export { validateJsonResponse, toResponseFormat } from "./validate-response.js";
export type { ValidationResult } from "./validate-response.js";

// ---------------------------------------------------------------------------
// Dry Run
// ---------------------------------------------------------------------------
export type { DryRunResult } from "./dry-run.js";

// ---------------------------------------------------------------------------
// Health Check
// ---------------------------------------------------------------------------
export { checkValidKey, healthCheck } from "./health-check.js";
export type {
  CheckValidKeyOptions,
  CheckValidKeyResult,
  HealthCheckOptions,
  HealthCheckResult as HealthCheckResponse,
} from "./health-check.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export type {
  // Shared
  Usage,
  AgentCCMetadata,
  RateLimitInfo,
  // Chat
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
  // Embeddings
  Embedding,
  EmbeddingResponse,
  EmbeddingCreateParams,
  // Images
  ImageData,
  ImageResponse,
  ImageGenerateParams,
  // Audio
  Transcription,
  Translation,
  TranscriptionCreateParams,
  TranslationCreateParams,
  SpeechCreateParams,
  // Models
  Model,
  ModelList,
  // Legacy completions
  Completion,
  CompletionChoice,
  CompletionCreateParams,
  // Files
  FileObject,
  FileList,
  FileUploadParams,
  // Rerank
  RerankResult,
  RerankResponse,
  RerankParams,
} from "./types/index.js";
