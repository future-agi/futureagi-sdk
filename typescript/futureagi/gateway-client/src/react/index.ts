// ---------------------------------------------------------------------------
// @future-agi/sdk/gateway/react — React hooks and a provider for the gateway
// (formerly @agentcc/react; same names). Without an AgentCCProvider the hooks
// call your server route (api, default "/api/chat"); with one they call the
// gateway directly with its client.
// ---------------------------------------------------------------------------

export { AgentCCProvider, useAgentCCClient, AgentCCContext } from "./provider.js";
export type { AgentCCProviderProps } from "./provider.js";

export { useAgentCCChat, useAgentCCChatWithClient } from "./use-chat.js";
export { useAgentCCCompletion, useAgentCCCompletionWithClient } from "./use-completion.js";
export { useAgentCCObject, useAgentCCObjectWithClient } from "./use-object.js";

export type {
  ChatMessage,
  RouteOptions,
  UseAgentCCChatOptions,
  UseAgentCCChatReturn,
  UseAgentCCCompletionOptions,
  UseAgentCCCompletionReturn,
  UseAgentCCObjectOptions,
  UseAgentCCObjectReturn,
} from "./types.js";
