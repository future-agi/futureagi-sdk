// ---------------------------------------------------------------------------
// The server-route transport of the React hooks: the
// hooks' default when no AgentCCProvider is above them, so the gateway key
// stays on the server.
// ---------------------------------------------------------------------------

import { APIStatusError } from "../errors.js";
import { Stream } from "../streaming.js";
import { acceptStreamAdapterResponse } from "../stream-adapter.js";
import { markScrubbedResponse, scrubCredentialHeaders } from "../redact.js";
import type { RouteOptions } from "./types.js";

/** The route a hook calls without an AgentCCProvider. */
export const DEFAULT_API = "/api/chat";

async function errorBody(response: Response): Promise<unknown> {
  const text = await response.text().catch(() => "");
  try {
    return JSON.parse(text);
  } catch {
    return { message: text || `Request failed with status ${response.status}` };
  }
}

/**
 * POST `body` to the route and read its answer as a stream of chunks: the
 * server-sent events @future-agi/sdk/gateway/nextjs `streamResponse` writes
 * (a gateway error frame raises a typed StreamError with its type, code and
 * param), or one JSON completion. A route that answers an error status
 * raises the APIStatusError for it (a 429 is a RateLimitError).
 */
export async function routeStream(route: RouteOptions, body: Record<string, unknown>, signal?: AbortSignal): Promise<Stream> {
  const api = route.api ?? DEFAULT_API;
  const doFetch = route.fetch ?? ((input: string, init?: RequestInit) => globalThis.fetch(input, init));
  const headers = { "Content-Type": "application/json", Accept: "text/event-stream", ...route.headers };
  let response: Response;
  try {
    response = await doFetch(api, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal,
    });
  } finally {
    scrubCredentialHeaders(headers);
  }
  markScrubbedResponse(response);
  if (!response.ok) throw APIStatusError.from(response.status, await errorBody(response), response.headers);
  return new Stream(acceptStreamAdapterResponse(response));
}

/** The text a route streams for `body`, joined. */
export async function routeText(route: RouteOptions, body: Record<string, unknown>, signal?: AbortSignal): Promise<string> {
  let text = "";
  for await (const chunk of await routeStream(route, body, signal)) {
    text += chunk.choices?.[0]?.delta?.content ?? "";
  }
  return text;
}
