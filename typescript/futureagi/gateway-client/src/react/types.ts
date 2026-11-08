// ---------------------------------------------------------------------------
// Shared types for the React hooks (@agentcc/react 1.0 types.ts, plus the
// server-route options)
// ---------------------------------------------------------------------------

export interface ChatMessage {
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  id?: string;
}

/**
 * Where a hook sends its request when no AgentCCProvider is above it: your
 * own server route, which calls the gateway with the key kept on the server
 * (for example @future-agi/sdk/gateway/nextjs `streamResponse`). The hook
 * POSTs `{ model, messages, ...body }` as JSON and reads the server-sent
 * events the route answers with.
 */
export interface RouteOptions {
  /** The route's URL. Default: "/api/chat". */
  api?: string;
  /** Headers for the route request (for example your app's own auth). */
  headers?: Record<string, string>;
  /** The fetch to use. Default: the page's fetch. */
  fetch?: typeof globalThis.fetch;
}

export interface UseAgentCCChatOptions extends RouteOptions {
  /** Model to use (e.g. "gpt-4o"). */
  model: string;
  /** Initial messages to seed the conversation. */
  initialMessages?: ChatMessage[];
  /** Called when an error occurs. */
  onError?: (error: Error) => void;
  /** Called when a response finishes. */
  onFinish?: (message: ChatMessage) => void;
  /** Additional body params for every request. */
  body?: Record<string, unknown>;
}

export interface UseAgentCCChatReturn {
  /** The current conversation messages. */
  messages: ChatMessage[];
  /** The current input value. */
  input: string;
  /** Set the input value. */
  setInput: (value: string) => void;
  /** Submit the current input as a user message. */
  handleSubmit: (e?: { preventDefault?: () => void }) => void;
  /** Whether a response is currently streaming. */
  isLoading: boolean;
  /** The last error, if any. A gateway error frame is a StreamError with its type, code and param. */
  error: Error | null;
  /** Stop the current streaming response. */
  stop: () => void;
  /** Reload (re-send) the last user message. */
  reload: () => void;
  /** Directly append a message. */
  append: (message: ChatMessage) => void;
  /** Replace all messages. */
  setMessages: (messages: ChatMessage[]) => void;
}

export interface UseAgentCCCompletionOptions extends RouteOptions {
  /** Model to use. */
  model: string;
  /** Initial prompt. */
  prompt?: string;
  /** Called when an error occurs. */
  onError?: (error: Error) => void;
}

export interface UseAgentCCCompletionReturn {
  /** The completion text. */
  completion: string;
  /** Whether a request is in progress. */
  isLoading: boolean;
  /** The last error, if any. */
  error: Error | null;
  /** Send a prompt and get a completion. */
  complete: (prompt: string) => Promise<void>;
}

export interface UseAgentCCObjectOptions<T> extends RouteOptions {
  /** Model to use. */
  model: string;
  /** JSON Schema for structured output. */
  schema: Record<string, unknown>;
  /** Schema name for the response_format. */
  schemaName?: string;
  /** Called when an error occurs. */
  onError?: (error: Error) => void;
}

export interface UseAgentCCObjectReturn<T> {
  /** The parsed object (null until a successful response). */
  object: T | null;
  /** Whether a request is in progress. */
  isLoading: boolean;
  /** The last error, if any. */
  error: Error | null;
  /** Submit a prompt and get a structured object. */
  submit: (prompt: string) => Promise<void>;
}
