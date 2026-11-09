// ---------------------------------------------------------------------------
// useAgentCCChat — Streaming chat hook (@agentcc/react 1.0 use-chat.ts, with
// the server route as the default transport)
// ---------------------------------------------------------------------------

import React from "react";
import type { AgentCC } from "../client.js";
import type { ChatCompletionChunk } from "../types/chat/chat-completion-chunk.js";
import { AgentCCContext } from "./provider.js";
import { routeStream } from "./route.js";
import type { ChatMessage, UseAgentCCChatOptions, UseAgentCCChatReturn } from "./types.js";

let _idCounter = 0;
function generateId(): string {
  return `msg-${Date.now()}-${++_idCounter}`;
}

function lastUserIndex(messages: ChatMessage[]): number {
  for (let i = messages.length - 1; i >= 0; i--) if (messages[i].role === "user") return i;
  return -1;
}

/**
 * React hook for streaming chat completions.
 *
 * Without an AgentCCProvider above it, the hook POSTs
 * `{ model, messages, ...body }` to your server route (`api`, default
 * "/api/chat"), which calls the gateway with the key kept on the server:
 *
 * ```ts
 * // app/api/chat/route.ts
 * import { createAgentCCClient, streamResponse } from "@future-agi/sdk/gateway/nextjs";
 * export async function POST(req: Request) {
 *   const { messages } = await req.json();
 *   return streamResponse(await createAgentCCClient().chat.completions.stream({ model: "gpt-4o-mini", messages }));
 * }
 * ```
 *
 * Under an AgentCCProvider it calls the gateway with that client instead
 * (direct mode). Either way it manages the conversation, streams the answer
 * token by token, and supports stop and reload. A gateway error frame (a
 * guardrail block) is a StreamError with its type, code and param.
 *
 * @example
 * ```tsx
 * function ChatPage() {
 *   const { messages, input, setInput, handleSubmit, isLoading } = useAgentCCChat({
 *     model: "gpt-4o",
 *   });
 *
 *   return (
 *     <div>
 *       {messages.map((m) => <div key={m.id}>{m.role}: {m.content}</div>)}
 *       <form onSubmit={handleSubmit}>
 *         <input value={input} onChange={(e) => setInput(e.target.value)} />
 *         <button type="submit" disabled={isLoading}>Send</button>
 *       </form>
 *     </div>
 *   );
 * }
 * ```
 */
export function useAgentCCChat(options: UseAgentCCChatOptions): UseAgentCCChatReturn {
  const client = React.useContext(AgentCCContext);
  return useChat(client, options);
}

/**
 * The hook with an explicit client (direct mode), without React context.
 * Exported for testing and for apps that hold the client themselves.
 */
export function useAgentCCChatWithClient(
  client: AgentCC,
  options: UseAgentCCChatOptions,
): UseAgentCCChatReturn {
  return useChat(client, options);
}

function useChat(client: AgentCC | null, options: UseAgentCCChatOptions): UseAgentCCChatReturn {
  const { model, initialMessages = [], onError, onFinish, body, api, headers, fetch } = options;

  const [messages, setMessages] = React.useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);
  const abortRef = React.useRef<AbortController | null>(null);

  const sendMessages = React.useCallback(
    async (msgs: ChatMessage[]) => {
      setIsLoading(true);
      setError(null);

      const controller = new AbortController();
      abortRef.current = controller;

      const assistantMsg: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: "",
      };

      // Optimistically add empty assistant message
      setMessages((prev) => [...prev, assistantMsg]);

      try {
        const request = {
          model,
          messages: msgs.map((m) => ({
            role: m.role as "user" | "assistant" | "system",
            content: m.content,
          })),
          ...body,
        };
        const stream: AsyncIterable<ChatCompletionChunk> = client
          ? await client.chat.completions.stream(request)
          : await routeStream({ api, headers, fetch }, request, controller.signal);

        for await (const chunk of stream) {
          if (controller.signal.aborted) break;
          const delta = chunk.choices?.[0]?.delta;
          if (delta?.content) {
            assistantMsg.content += delta.content;
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = { ...assistantMsg };
              return updated;
            });
          }
        }

        if (onFinish) onFinish(assistantMsg);
      } catch (err) {
        // stop() aborts the request; the read it cuts short is not an error.
        if (controller.signal.aborted || (err as Error).name === "AbortError") return;
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        if (onError) onError(error);
      } finally {
        setIsLoading(false);
        abortRef.current = null;
      }
    },
    [client, model, body, onError, onFinish, api, headers, fetch],
  );

  const handleSubmit = React.useCallback(
    (e?: { preventDefault?: () => void }) => {
      e?.preventDefault?.();
      if (!input.trim() || isLoading) return;

      const userMsg: ChatMessage = {
        id: generateId(),
        role: "user",
        content: input.trim(),
      };

      const newMessages = [...messages, userMsg];
      setMessages(newMessages);
      setInput("");
      sendMessages(newMessages);
    },
    [input, isLoading, messages, sendMessages],
  );

  const stop = React.useCallback(() => {
    abortRef.current?.abort();
    setIsLoading(false);
  }, []);

  const reload = React.useCallback(() => {
    // Find the last user message and re-send up to that point
    const lastUserIdx = lastUserIndex(messages);
    if (lastUserIdx === -1) return;

    const msgsUpToUser = messages.slice(0, lastUserIdx + 1);
    setMessages(msgsUpToUser);
    sendMessages(msgsUpToUser);
  }, [messages, sendMessages]);

  const append = React.useCallback(
    (message: ChatMessage) => {
      const msg = { ...message, id: message.id ?? generateId() };
      const newMessages = [...messages, msg];
      setMessages(newMessages);
      if (msg.role === "user") {
        sendMessages(newMessages);
      }
    },
    [messages, sendMessages],
  );

  return {
    messages,
    input,
    setInput,
    handleSubmit,
    isLoading,
    error,
    stop,
    reload,
    append,
    setMessages,
  };
}
