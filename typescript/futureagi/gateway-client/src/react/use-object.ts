// ---------------------------------------------------------------------------
// useAgentCCObject — Structured output hook (@agentcc/react 1.0, with the
// server route as the default transport)
// ---------------------------------------------------------------------------

import React from "react";
import type { AgentCC } from "../client.js";
import { AgentCCContext } from "./provider.js";
import { routeText } from "./route.js";
import type {
  UseAgentCCObjectOptions,
  UseAgentCCObjectReturn,
} from "./types.js";

/**
 * React hook for structured output completions.
 * Uses `response_format: { type: "json_schema" }` to get typed JSON.
 *
 * Without an AgentCCProvider above it, the hook POSTs
 * `{ model, messages, response_format }` to your server route (`api`,
 * default "/api/chat") and parses the text it streams back; the route must
 * pass response_format on to the gateway. Under an AgentCCProvider it calls
 * the gateway with that client (as in 1.0).
 *
 * @example
 * ```tsx
 * const schema = {
 *   type: "object",
 *   properties: {
 *     temp: { type: "number" },
 *     condition: { type: "string" },
 *   },
 *   required: ["temp", "condition"],
 * };
 *
 * function WeatherWidget() {
 *   const { object, isLoading, submit } = useAgentCCObject<{ temp: number; condition: string }>({
 *     model: "gpt-4o",
 *     schema,
 *     schemaName: "weather",
 *   });
 *
 *   return (
 *     <div>
 *       <button onClick={() => submit("What's the weather in NYC?")}>Ask</button>
 *       {object && <p>{object.temp}°F, {object.condition}</p>}
 *     </div>
 *   );
 * }
 * ```
 */
export function useAgentCCObject<T = unknown>(
  options: UseAgentCCObjectOptions<T>,
): UseAgentCCObjectReturn<T> {
  const client = React.useContext(AgentCCContext);
  return useObject<T>(client, options);
}

export function useAgentCCObjectWithClient<T = unknown>(
  client: AgentCC,
  options: UseAgentCCObjectOptions<T>,
): UseAgentCCObjectReturn<T> {
  return useObject<T>(client, options);
}

function useObject<T>(client: AgentCC | null, options: UseAgentCCObjectOptions<T>): UseAgentCCObjectReturn<T> {
  const { model, schema, schemaName, onError, api, headers, fetch } = options;

  const [object, setObject] = React.useState<T | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const submit = React.useCallback(
    async (prompt: string) => {
      setIsLoading(true);
      setError(null);
      setObject(null);

      try {
        const messages = [{ role: "user" as const, content: prompt }];
        const response_format = {
          type: "json_schema",
          json_schema: {
            name: schemaName ?? "response",
            strict: true,
            schema,
          },
        };
        let content: string | null | undefined;
        if (client) {
          const response = await client.chat.completions.create({
            model,
            messages,
            response_format: response_format as any,
          });
          content = response.choices?.[0]?.message?.content;
        } else {
          content = await routeText({ api, headers, fetch }, { model, messages, response_format });
        }
        if (!content) {
          throw new Error("No content in response");
        }

        const parsed = JSON.parse(content) as T;
        setObject(parsed);
      } catch (err) {
        const e = err instanceof Error ? err : new Error(String(err));
        setError(e);
        if (onError) onError(e);
      } finally {
        setIsLoading(false);
      }
    },
    [client, model, schema, schemaName, onError, api, headers, fetch],
  );

  return { object, isLoading, error, submit };
}
