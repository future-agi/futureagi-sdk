// ---------------------------------------------------------------------------
// AgentCCProvider — React context for an AgentCC client (direct mode)
// ---------------------------------------------------------------------------
//
// @agentcc/react 1.0 provider.tsx, written with createElement instead of JSX:
// React 17's react/jsx-runtime has no exports map, so Node's ES module loader
// cannot import it, and this subpath supports React 17, 18 and 19 under both
// import() and require().

import React from "react";
import type { Context, ReactElement, ReactNode } from "react";
import type { AgentCC } from "../client.js";

const AgentCCContext: Context<AgentCC | null> = React.createContext<AgentCC | null>(null);

export interface AgentCCProviderProps {
  /** The AgentCC client instance. */
  client: AgentCC;
  children?: ReactNode;
}

/**
 * Provides an AgentCC client to the hooks below it (direct mode): they call
 * the gateway from the page with that client. In a browser the client needs
 * `dangerouslyAllowBrowser: true`, because every visitor can read its key.
 * Without a provider the hooks use your server route instead (`api`,
 * default "/api/chat"), which keeps the key on the server.
 *
 * @example
 * ```ts
 * import { AgentCC } from "@future-agi/sdk/gateway";
 * import { AgentCCProvider } from "@future-agi/sdk/gateway/react";
 *
 * const client = new AgentCC({ apiKey: shortLivedKey, baseUrl, dangerouslyAllowBrowser: true });
 * // <AgentCCProvider client={client}><ChatPage /></AgentCCProvider>
 * ```
 */
export function AgentCCProvider({ client, children }: AgentCCProviderProps): ReactElement {
  return React.createElement(AgentCCContext.Provider, { value: client }, children);
}

/**
 * Access the AgentCC client from the nearest AgentCCProvider.
 * Throws if used outside a AgentCCProvider.
 */
export function useAgentCCClient(): AgentCC {
  const client = React.useContext(AgentCCContext);
  if (!client) {
    throw new Error(
      "useAgentCCClient must be used within a <AgentCCProvider>. " +
        "Wrap your component tree with <AgentCCProvider client={agentccClient}>.",
    );
  }
  return client;
}

export { AgentCCContext };
