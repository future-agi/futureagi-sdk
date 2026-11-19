// Shared fixture data (tests/fixtures/gateway/*.json) and reply builders, the
// same data the Python recorder reads.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export const FIXTURES = fileURLToPath(new URL("../../../../../../tests/fixtures/gateway/", import.meta.url));
const cache = new Map();

export function load(name) {
  if (!cache.has(name)) cache.set(name, readFileSync(FIXTURES + name, "utf8"));
  return JSON.parse(cache.get(name));
}

const responses = () => load("responses.json");
export const MSG = [{ role: "user", content: "Say hello" }];
export const CHAT = { model: "gpt-4o-mini", messages: MSG };
export const body = (key) => responses().bodies[key];
export const chunks = (key) => responses().chunks[key];
export const responseHeaders = (key) => responses().response_headers[key];
export const envelope = (key) => responses().error_envelopes[key];
export const statuses = () => responses().statuses;
export const streamErrorCases = () => load("stream-error-frames.json").cases;
export const streamExtraCases = () => load("stream-cases-extra.json").cases;

export function ok(key, { status = 200, headers = {} } = {}) {
  const value = body(key);
  if (typeof value === "string") return { status, headers: { "content-type": "application/octet-stream", ...headers }, text: value };
  return { status, headers, json: value };
}

export const sse = (frames, { headers = {}, status = 200 } = {}) => ({ status, headers, sse: frames });

export function errorReply(status, kind, headers = {}) {
  const value = envelope(kind);
  return typeof value === "string" ? { status, headers, text: value } : { status, headers, json: value };
}
