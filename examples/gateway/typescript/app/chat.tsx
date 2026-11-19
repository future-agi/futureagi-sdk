"use client";

import React from "react";
import { useAgentCCChat } from "@future-agi/sdk/gateway/react";

/** Route mode keeps the gateway credential on the server; no client provider is needed. */
export default function Chat() {
  const { messages, setMessages, input, setInput, handleSubmit, isLoading, error, stop } = useAgentCCChat({
    api: "/api/chat",
    model: "server-selected",
  });
  React.useEffect(() => {
    if (isLoading) return;
    // The hook can leave an empty optimistic reply after a failure or early stop.
    // Remove it only once streaming has ended; keep users and non-empty replies.
    const history = messages.filter((message) => message.role !== "assistant" || message.content.trim().length > 0);
    if (history.length !== messages.length) setMessages(history);
  }, [isLoading, messages, setMessages]);
  return (
    <main>
      <h1>Gateway chat example</h1>
      <p>This local demo sends chat through a server route.</p>
      <ol aria-live="polite">
        {messages.map((message, index) => <li key={message.id ?? index}>{message.role}: {message.content}</li>)}
      </ol>
      <form onSubmit={handleSubmit}>
        <label htmlFor="prompt">Message</label>
        <input id="prompt" value={input} onChange={(event) => setInput(event.target.value)} maxLength={4000} />
        <button type="submit" disabled={isLoading || !input.trim()}>Send</button>
        {isLoading && <button type="button" onClick={stop}>Stop</button>}
      </form>
      {error && <p role="alert">Unable to complete the request. Please try again.</p>}
    </main>
  );
}
