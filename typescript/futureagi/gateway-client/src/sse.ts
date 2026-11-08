// ---------------------------------------------------------------------------
// Server-sent events: the byte stream of a streaming answer, split into events.
// Moved verbatim from streaming.ts (@agentcc/client 1.0.1) to keep each module
// under 400 lines.
// ---------------------------------------------------------------------------

/** One server-sent event. */
export interface SSEEvent {
  data: string | null;
  event: string | null;
  id: string | null;
  retry: number | null;
}

/**
 * Parse an SSE byte stream into individual events.
 * Works with any `ReadableStream<Uint8Array>`.
 */
export async function* parseSSE(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<SSEEvent> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Split on double newline (SSE event boundary)
      const parts = buffer.split("\n\n");
      // Keep the last partial part in the buffer
      buffer = parts.pop()!;

      for (const part of parts) {
        const event = parseSSEBlock(part);
        if (event) yield event;
      }
    }

    // Handle any remaining data
    if (buffer.trim()) {
      const event = parseSSEBlock(buffer);
      if (event) yield event;
    }
  } finally {
    reader.releaseLock();
  }
}

function parseSSEBlock(block: string): SSEEvent | null {
  let data: string | null = null;
  let event: string | null = null;
  let id: string | null = null;
  let retry: number | null = null;

  for (const line of block.split("\n")) {
    if (line.startsWith(":")) continue; // comment
    const colonIdx = line.indexOf(":");
    if (colonIdx === -1) continue;
    const field = line.slice(0, colonIdx);
    const value = line.slice(colonIdx + 1).trimStart();

    switch (field) {
      case "data":
        data = data ? data + "\n" + value : value;
        break;
      case "event":
        event = value;
        break;
      case "id":
        id = value;
        break;
      case "retry":
        retry = parseInt(value, 10) || null;
        break;
    }
  }

  if (data === null && event === null) return null;
  return { data, event, id, retry };
}
