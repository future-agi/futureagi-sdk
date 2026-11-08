import { createAgentCCClient, streamResponse } from "@future-agi/sdk/gateway/nextjs";
import { messagesFrom } from "../../../messages.js";
import { settings } from "../../../settings.js";

export const runtime = "nodejs";

/** Local demo route; add your application's session authorization before deployment. */
export async function POST(request: Request): Promise<Response> {
  // Reject browser cross-origin submissions; this is not a replacement for login.
  const origin = request.headers.get("origin");
  const url = new URL(request.url);
  // Next's dev server may normalize request.url to localhost even when the
  // browser connected to 127.0.0.1. Compare with the incoming HTTP Host instead.
  const expectedOrigin = `${url.protocol}//${request.headers.get("host") ?? url.host}`;
  if (origin && origin !== expectedOrigin) {
    return Response.json({ error: "Origin refused" }, { status: 403 });
  }
  let messages;
  try {
    const text = await request.text();
    if (text.length > 96_000) return Response.json({ error: "Request too large" }, { status: 413 });
    messages = messagesFrom(JSON.parse(text));
  } catch {
    return Response.json({ error: "Invalid messages" }, { status: 400 });
  }
  try {
    // The browser cannot choose the gateway URL, API key, model or extra headers.
    const { apiKey, baseUrl, model } = settings();
    const client = createAgentCCClient({ apiKey, baseUrl, maxRetries: 0, timeout: 15_000 });
    const stream = await client.chat.completions.stream({ model, messages, max_tokens: 128 });
    return streamResponse(stream);
  } catch {
    return Response.json({ error: "Gateway request failed" }, { status: 502 });
  }
}
