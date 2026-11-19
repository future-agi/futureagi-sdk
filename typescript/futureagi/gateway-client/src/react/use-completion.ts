// ---------------------------------------------------------------------------
// useAgentCCCompletion — Single completion hook (@agentcc/react 1.0, with the
// server route as the default transport)
// ---------------------------------------------------------------------------

import React from "react";
import type { AgentCC } from "../client.js";
import { AgentCCContext } from "./provider.js";
import { routeText } from "./route.js";
import type {
  UseAgentCCCompletionOptions,
  UseAgentCCCompletionReturn,
} from "./types.js";

/**
 * React hook for a single chat completion.
 *
 * Without an AgentCCProvider above it, the hook POSTs
 * `{ model, messages: [{ role: "user", content: prompt }] }` to your server
 * route (`api`, default "/api/chat") and joins the text it streams back.
 * Under an AgentCCProvider it calls the gateway with that client (one
 * non-streaming request, as in 1.0).
 *
 * @example
 * ```tsx
 * function TranslatePage() {
 *   const { completion, isLoading, complete } = useAgentCCCompletion({
 *     model: "gpt-4o",
 *   });
 *
 *   return (
 *     <div>
 *       <button onClick={() => complete("Translate 'hello' to French")}>
 *         Translate
 *       </button>
 *       {isLoading && <p>Loading...</p>}
 *       {completion && <p>{completion}</p>}
 *     </div>
 *   );
 * }
 * ```
 */
export function useAgentCCCompletion(
  options: UseAgentCCCompletionOptions,
): UseAgentCCCompletionReturn {
  const client = React.useContext(AgentCCContext);
  return useCompletion(client, options);
}

export function useAgentCCCompletionWithClient(
  client: AgentCC,
  options: UseAgentCCCompletionOptions,
): UseAgentCCCompletionReturn {
  return useCompletion(client, options);
}

function useCompletion(client: AgentCC | null, options: UseAgentCCCompletionOptions): UseAgentCCCompletionReturn {
  const { model, onError, api, headers, fetch } = options;

  const [completion, setCompletion] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const complete = React.useCallback(
    async (prompt: string) => {
      setIsLoading(true);
      setError(null);
      setCompletion("");

      try {
        const messages = [{ role: "user" as const, content: prompt }];
        let text: string;
        if (client) {
          const response = await client.chat.completions.create({ model, messages });
          text = response.choices?.[0]?.message?.content ?? "";
        } else {
          text = await routeText({ api, headers, fetch }, { model, messages });
        }
        setCompletion(text);
      } catch (err) {
        const e = err instanceof Error ? err : new Error(String(err));
        setError(e);
        if (onError) onError(e);
      } finally {
        setIsLoading(false);
      }
    },
    [client, model, onError, api, headers, fetch],
  );

  return { completion, isLoading, error, complete };
}
