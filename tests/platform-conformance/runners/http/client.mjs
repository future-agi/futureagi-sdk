/**
 * The raw HTTP transport of the `http` runner: no SDK, nothing hidden. Redirects are never
 * followed (`redirect: "manual"`), every call has a deadline, and a server-sent-events response
 * is read until a limit (events, time, or a terminal event type) and then aborted.
 *
 * Returns { status, headers, body, text, events, durationMs, location } where body is the parsed
 * JSON (or null) and headers holds only the ids, retry and redirect headers a receipt needs.
 */
const KEPT_HEADERS = [
  "content-type", "location", "retry-after", "x-request-id", "x-upstream-request-id", "x-correlation-id",
  "x-omega-receipt-id", "x-omega-idempotency-key", "x-omega-operation-id", "ratelimit-limit", "ratelimit-remaining", "ratelimit-reset",
];

export function joinUrl(base, path, query) {
  const url = new URL(`${String(base).replace(/\/+$/, "")}${path}`);
  for (const [name, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null) continue;
    for (const item of Array.isArray(value) ? value : [value]) url.searchParams.append(name, String(item));
  }
  return url;
}

/** Parse SSE text incrementally. Returns { events, rest } (rest = an unfinished block). */
export function parseSse(buffer) {
  const events = [];
  const blocks = buffer.split(/\r?\n\r?\n/);
  const rest = blocks.pop() ?? "";
  for (const block of blocks) {
    let event = "message";
    let id;
    const data = [];
    for (const line of block.split(/\r?\n/)) {
      if (line.startsWith(":")) continue;
      const at = line.indexOf(":");
      const field = at === -1 ? line : line.slice(0, at);
      const value = at === -1 ? "" : line.slice(at + 1).replace(/^ /, "");
      if (field === "event") event = value;
      else if (field === "data") data.push(value);
      else if (field === "id") id = value;
    }
    if (data.length === 0 && event === "message") continue;
    const raw = data.join("\n");
    let parsed = null;
    try {
      parsed = raw ? JSON.parse(raw) : null;
    } catch {
      parsed = null;
    }
    const type = parsed && typeof parsed === "object" && typeof parsed.type === "string" ? parsed.type : event;
    events.push({ type, event, id, data: parsed, raw: parsed ? undefined : raw.slice(0, 200) });
  }
  return { events, rest };
}

async function readSse(response, { maxEvents = 200, maxMs = 30_000, until = [] }, controller) {
  const events = [];
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const deadline = setTimeout(() => controller.abort(new Error("sse-limit")), maxMs);
  let ended = "eof";
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parsed = parseSse(buffer);
      buffer = parsed.rest;
      events.push(...parsed.events);
      if (events.length >= maxEvents) {
        ended = "max-events";
        break;
      }
      if (parsed.events.some((e) => until.includes(e.type))) {
        ended = "until";
        break;
      }
    }
  } catch (error) {
    ended = controller.signal.aborted ? "max-ms" : `error:${error.name}`;
  } finally {
    clearTimeout(deadline);
    controller.abort();
  }
  return { events, ended };
}

/**
 * One raw call. `stream` = { maxEvents, maxMs, until } reads an event-stream body.
 * `fetchImpl` is the egress-guarded fetch.
 */
export async function rawCall({ base, method, path, query, headers = {}, body, rawBody, contentType, stream, timeoutMs = 60_000, fetchImpl }) {
  const url = joinUrl(base, path, query);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error("timeout")), stream ? Math.max(timeoutMs, (stream.maxMs ?? 30_000) + 15_000) : timeoutMs);
  const sent = { ...headers };
  let payload;
  if (rawBody !== undefined) {
    payload = rawBody;
    sent["content-type"] = contentType ?? "application/json";
  } else if (body !== undefined) {
    payload = JSON.stringify(body);
    sent["content-type"] = contentType ?? "application/json";
  }
  const started = performance.now();
  let response;
  try {
    response = await fetchImpl(url, { method, headers: sent, body: payload, redirect: "manual", signal: controller.signal });
  } catch (error) {
    clearTimeout(timer);
    return { status: null, transportError: `${error.name}: ${error.message}`.slice(0, 300), headers: {}, body: null, events: [], durationMs: Math.round(performance.now() - started) };
  }
  const kept = {};
  for (const name of KEPT_HEADERS) {
    const value = response.headers.get(name);
    if (value !== null) kept[name] = value;
  }
  let result;
  if ((kept["content-type"] ?? "").startsWith("text/event-stream") && response.status >= 200 && response.status < 300) {
    const { events, ended } = await readSse(response, stream ?? {}, controller);
    result = { body: null, events, streamEnded: ended };
  } else {
    const text = await response.text().catch(() => "");
    let parsed = null;
    try {
      parsed = text ? JSON.parse(text) : null;
    } catch {
      parsed = null;
    }
    result = { body: parsed, events: [], textBytes: text.length, nonJson: parsed === null && text.length > 0 };
  }
  clearTimeout(timer);
  return {
    status: response.status,
    headers: kept,
    ...result,
    durationMs: Math.round(performance.now() - started),
  };
}
