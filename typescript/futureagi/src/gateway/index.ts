// The gateway (Agent Command Center) client: an OpenAI-compatible data-plane client.
//
//     import { Gateway } from "@future-agi/sdk/gateway";
//     const gw = new Gateway();               // FI_GATEWAY_API_KEY / FI_GATEWAY_URL
//     const reply = await gw.chat.completions.create({ model: "gpt-4o-mini", messages: [...] });
//
// Vendored from the agentcc TypeScript client; see ./VENDORED.md for the source commit and the changes.

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------
export { AgentCC } from "./client";
export type { ClientOptions, WithResponseResult } from "./base-client";
// The same client with Future AGI defaults (FI_GATEWAY_API_KEY / FI_GATEWAY_URL, hosted gateway).
export { Gateway, DEFAULT_GATEWAY_URL } from "./fi";

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------
export {
  AgentCCError,
  APIConnectionError,
  APITimeoutError,
  APIStatusError,
  BadRequestError,
  AuthenticationError,
  PermissionDeniedError,
  NotFoundError,
  UnprocessableEntityError,
  RateLimitError,
  InternalServerError,
  BadGatewayError,
  ServiceUnavailableError,
  GatewayTimeoutError,
  GuardrailBlockedError,
  GuardrailWarning,
  StreamError,
} from "./errors";

// ---------------------------------------------------------------------------
// Gateway Configuration
// ---------------------------------------------------------------------------
export type {
  GatewayConfig,
  FallbackConfig,
  FallbackTarget,
  LoadBalanceConfig,
  LoadBalanceTarget,
  CacheConfig,
  GuardrailConfig,
  GuardrailCheck,
  ConditionalRoutingConfig,
  RoutingCondition,
  TrafficMirrorConfig,
  RetryConfig,
  TimeoutConfig,
  CreateHeadersOptions,
} from "./gateway-config";
export { createHeaders } from "./gateway-config";

// ---------------------------------------------------------------------------
// Streaming
// ---------------------------------------------------------------------------
export { Stream, StreamManager, ChunkAccumulator } from "./streaming";
export type { StreamEvent } from "./stream-events";
export type { StreamHooks } from "./streaming";

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------
export { Session } from "./session";
export type { SessionOptions } from "./session";

// ---------------------------------------------------------------------------
// Callbacks
// ---------------------------------------------------------------------------
export { CallbackHandler, invokeCallbacks } from "./callbacks";
export type {
  CallbackRequest,
  CallbackResponse,
  StreamInfo,
  SessionSummary,
} from "./callbacks";
export {
  LoggingCallback,
  MetricsCallback,
  JSONLoggingCallback,
} from "./callbacks-builtin";

// ---------------------------------------------------------------------------
// Retry Policy
// ---------------------------------------------------------------------------
export { RetryPolicy } from "./retry-policy";
export type { RetryPolicyOptions } from "./retry-policy";

// ---------------------------------------------------------------------------
// Redaction
// ---------------------------------------------------------------------------
export { redactCallbackRequest } from "./redact";

// ---------------------------------------------------------------------------
// Constants & Utilities
// ---------------------------------------------------------------------------
export { VERSION, NOT_GIVEN, AGENTCC_GATEWAY_URL } from "./constants";
export type { NotGiven } from "./constants";

// ---------------------------------------------------------------------------
// Model Info & Token Utilities
// ---------------------------------------------------------------------------
export type { ModelInfo } from "./models-info";
export {
  getModelInfo,
  getValidModels,
  registerModel,
  modelAliasMap,
  supportsVision,
  supportsFunctionCalling,
  supportsJsonMode,
  supportsResponseSchema,
  validateEnvironment,
} from "./models-info";
export {
  tokenCounter,
  getMaxTokens,
  getMaxOutputTokens,
  completionCost,
  completionCostFromResponse,
  trimMessages,
  getContextWindowFallback,
  getContentPolicyFallback,
  isPromptCachingValid,
} from "./tokens";
export type { ChatMessage } from "./tokens";

// ---------------------------------------------------------------------------
// Budget Management
// ---------------------------------------------------------------------------
export { BudgetManager } from "./budget";
export type { BudgetManagerOptions } from "./budget";

// ---------------------------------------------------------------------------
// Trace Context (W3C)
// ---------------------------------------------------------------------------
export {
  TraceContextManager,
  generateTraceId,
  generateSpanId,
  parseTraceparent,
  formatTraceparent,
} from "./trace-context";
export type {
  TraceContext,
  TraceContextManagerOptions,
} from "./trace-context";

// ---------------------------------------------------------------------------
// OpenTelemetry Callback
// ---------------------------------------------------------------------------
export { OTelCallback } from "./otel-callback";
export type {
  OTelCallbackOptions,
  OTelTracer,
  OTelSpan,
  OTelMeter,
  OTelCounter,
  OTelHistogram,
} from "./otel-callback";

// ---------------------------------------------------------------------------
// Middleware
// ---------------------------------------------------------------------------
export { createMiddleware, composeMiddlewares } from "./middleware";
export type {
  Middleware,
  MiddlewareContext,
  MiddlewareResult,
  NextFn,
} from "./middleware";

// ---------------------------------------------------------------------------
// Structured Output & Zod
// ---------------------------------------------------------------------------
export { zodToJsonSchema, isZodSchema } from "./structured-output";

// ---------------------------------------------------------------------------
// Function → Tool Definition
// ---------------------------------------------------------------------------
export { functionToTool } from "./function-to-tool";
export type { FunctionToToolOptions } from "./function-to-tool";

// ---------------------------------------------------------------------------
// Pagination
// ---------------------------------------------------------------------------
export { PaginatedList } from "./pagination";

// ---------------------------------------------------------------------------
// Batch Execution
// ---------------------------------------------------------------------------
export { batchCompletion, batchCompletionModels } from "./batch";
export type {
  BatchCompletionParams,
  BatchCompletionModelsParams,
  ModelCompletionResult,
} from "./batch";

// ---------------------------------------------------------------------------
// Tool Execution Loop
// ---------------------------------------------------------------------------
export { RunToolsRunner } from "./run-tools";
export type {
  ToolWithExecute,
  ToolStep,
  RunToolsResult,
  RunToolsParams,
} from "./run-tools";

// ---------------------------------------------------------------------------
// Migration Helpers
// ---------------------------------------------------------------------------
export { patchOpenAI } from "./patch-openai";

// ---------------------------------------------------------------------------
// Response Validation
// ---------------------------------------------------------------------------
export { validateJsonResponse, toResponseFormat } from "./validate-response";
export type { ValidationResult } from "./validate-response";

// ---------------------------------------------------------------------------
// Pre-Call Rules
// ---------------------------------------------------------------------------
export {
  evaluatePreCallRules,
  allowModels,
  blockModels,
  requireSessionId,
} from "./pre-call-rules";
export type {
  PreCallRule,
  PreCallRuleInput,
  PreCallRuleResult,
} from "./pre-call-rules";

// ---------------------------------------------------------------------------
// Dry Run
// ---------------------------------------------------------------------------
export type { DryRunResult } from "./dry-run";

// ---------------------------------------------------------------------------
// Token Encoding
// ---------------------------------------------------------------------------
export { encode, decode, getEncodingForModel } from "./token-encoding";

// ---------------------------------------------------------------------------
// Health Check
// ---------------------------------------------------------------------------
export { checkValidKey, healthCheck } from "./health-check";
export type {
  CheckValidKeyOptions,
  CheckValidKeyResult,
  HealthCheckOptions,
  HealthCheckResult as HealthCheckResponse,
} from "./health-check";

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
  // Moderations
  ModerationResult,
  ModerationResponse,
  ModerationCreateParams,
  // Legacy completions
  Completion,
  CompletionChoice,
  CompletionCreateParams,
  // Batches
  Batch,
  BatchList,
  BatchCreateParams,
  // Files
  FileObject,
  FileList,
  FileUploadParams,
  // Rerank
  RerankResult,
  RerankResponse,
  RerankParams,
} from "./types/index";
