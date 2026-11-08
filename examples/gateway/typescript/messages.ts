/** Validate the tiny demo's input before spending a gateway request. */
export function messagesFrom(body: unknown): Array<{ role: "user" | "assistant"; content: string }> {
  if (!body || typeof body !== "object" || !("messages" in body)) {
    throw new Error("Expected messages");
  }
  const messages = body.messages;
  if (!Array.isArray(messages) || messages.length === 0 || messages.length > 20) {
    throw new Error("Send between 1 and 20 messages");
  }
  return messages.map((message: unknown) => {
    if (!message || typeof message !== "object" || !("role" in message) || !("content" in message)
      || (message.role !== "user" && message.role !== "assistant")
      || typeof message.content !== "string" || !message.content.trim() || message.content.length > 4000) {
      throw new Error("Each message needs a user/assistant role and 1-4000 characters");
    }
    return { role: message.role, content: message.content };
  });
}
