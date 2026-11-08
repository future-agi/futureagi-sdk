// @agentcc/client: statuses x envelopes, retries (attempts, Retry-After,
// recorded timers), timeouts and transport failures.
import { CHAT, body, errorReply, ok, statuses } from "./fixtures.mjs";

const ENVELOPES = ["error_object", "error_object_minimal", "top_level_message", "non_json", "empty"];
const GUARD = {
  "x-agentcc-request-id": "req-err-1",
  "x-agentcc-guardrail-name": "pii",
  "x-agentcc-guardrail-action": "block",
  "x-agentcc-guardrail-confidence": "0.97",
  "x-agentcc-guardrail-message": "PII found",
  "x-ratelimit-limit-requests": "10",
  "x-ratelimit-remaining-requests": "0",
  "x-ratelimit-reset-requests": "30",
};
const RETRYABLE = [408, 429, 500, 502, 503, 504];
const NOT_RETRIED = [400, 401, 403, 404, 413, 422, 446];
const RETRY_AFTER = { zero: "0", one: "1", fraction: "2.5", above_cap: "90", negative: "-1", text: "soon", http_date: "Wed, 21 Oct 2026 07:28:00 GMT" };
const TRANSPORT = ["connect", "read_timeout", "remote_protocol"];

const create = (opts = {}) => async (ctx) => ctx.client(opts).chat.completions.create(CHAT);
const stream = (opts = {}) => async (ctx) => ctx.drain(await ctx.client(opts).chat.completions.create({ ...CHAT, stream: true }));
const repeat = (n, reply) => Array.from({ length: n }, () => reply);

export function cases() {
  const out = [];
  for (const status of statuses()) {
    for (const env of ENVELOPES) out.push({ id: `status.${status}.${env}`, area: "statuses", fn: create({ maxRetries: 0 }), replies: [errorReply(status, env)] });
    out.push({ id: `status.${status}.headers`, area: "statuses", fn: create({ maxRetries: 0 }), replies: [errorReply(status, "error_object", GUARD)] });
  }
  for (const status of [400, 401, 429, 446, 500, 503]) out.push({ id: `status.stream.${status}`, area: "statuses", fn: stream({ maxRetries: 0 }), replies: [errorReply(status, "error_object", GUARD)] });
  out.push({ id: "status.stream.246", area: "statuses", fn: stream({ maxRetries: 0 }), replies: [{ status: 246, headers: GUARD, json: body("chat_completion") }] });
  out.push({ id: "status.246.on_guardrail_warning", area: "statuses", fn: async (ctx) => {
    const seen = [];
    const client = ctx.client({ maxRetries: 0, callbacks: [{ onGuardrailWarning: (...a) => seen.push(a.length) }] });
    return { result: await ctx.attempt(() => client.chat.completions.create(CHAT)), seen };
  }, replies: [{ status: 246, headers: GUARD, json: body("chat_completion") }] });
  out.push({ id: "status.embeddings.429", area: "statuses", fn: async (ctx) => ctx.client({ maxRetries: 0 }).embeddings.create({ model: "e", input: "x" }), replies: [errorReply(429, "error_object", GUARD)] });
  out.push({ id: "status.speech.500", area: "statuses", fn: async (ctx) => ctx.client({ maxRetries: 0 }).audio.speech.create({ model: "tts-1", input: "x", voice: "alloy" }), replies: [errorReply(500, "non_json")] });
  out.push({ id: "status.418_unmapped", area: "statuses", fn: create({ maxRetries: 0 }), replies: [errorReply(418, "error_object")] });
  out.push({ id: "status.599_unmapped", area: "statuses", fn: create({ maxRetries: 0 }), replies: [errorReply(599, "empty")] });
  out.push({ id: "status.200_non_json", area: "statuses", fn: create({ maxRetries: 0 }), replies: [{ status: 200, text: "not json" }] });
  out.push({ id: "status.200_wrong_shape", area: "statuses", fn: create({ maxRetries: 0 }), replies: [{ status: 200, json: { unexpected: true } }] });
  out.push({ id: "status.201_ok", area: "statuses", fn: create({ maxRetries: 0 }), replies: [{ status: 201, json: body("chat_completion") }] });

  for (const status of RETRYABLE) {
    out.push({ id: `retry.${status}.exhausted`, area: "retry", fn: create(), replies: repeat(4, errorReply(status, "error_object")) });
    out.push({ id: `retry.${status}.then_ok`, area: "retry", fn: create(), replies: [errorReply(status, "error_object"), ok("chat_completion")] });
  }
  for (const status of NOT_RETRIED) out.push({ id: `retry.${status}.not_retried`, area: "retry", fn: create({ maxRetries: 3 }), replies: [errorReply(status, "error_object"), ok("chat_completion")] });
  for (const [name, value] of Object.entries(RETRY_AFTER)) out.push({ id: `retry.retry_after.${name}`, area: "retry", fn: create({ maxRetries: 1 }), replies: [errorReply(429, "error_object", { "retry-after": value }), ok("chat_completion")] });
  out.push({ id: "retry.retry_after_ms", area: "retry", fn: create({ maxRetries: 1 }), replies: [errorReply(503, "error_object", { "retry-after-ms": "1500" }), ok("chat_completion")] });
  for (const n of [0, 1, 3, 5]) out.push({ id: `retry.max_retries.${n}`, area: "retry", fn: create({ maxRetries: n }), replies: repeat(n + 1, errorReply(500, "empty")) });
  for (const kind of TRANSPORT) {
    out.push({ id: `retry.transport.${kind}`, area: "retry", fn: create({ maxRetries: 1 }), replies: [{ raise: kind }, ok("chat_completion")] });
    out.push({ id: `retry.transport.${kind}.exhausted`, area: "retry", fn: create({ maxRetries: 1 }), replies: [{ raise: kind }, { raise: kind }] });
  }
  out.push({ id: "retry.stream.500", area: "retry", fn: stream(), replies: [errorReply(500, "error_object"), ok("chat_completion")] });
  out.push({ id: "retry.stream.connect", area: "retry", fn: stream(), replies: [{ raise: "connect" }, ok("chat_completion")] });
  const policy = (fields) => async (ctx) => ctx.client({ retryPolicy: new ctx.mod.RetryPolicy(fields) }).chat.completions.create(CHAT);
  out.push({ id: "retry.policy.ratelimit", area: "retry", fn: policy({ rateLimitRetries: 3 }), replies: repeat(4, errorReply(429, "error_object")) });
  out.push({ id: "retry.policy.no_5xx", area: "retry", fn: policy({ internalServerErrorRetries: 0 }), replies: [errorReply(500, "error_object"), ok("chat_completion")] });
  out.push({ id: "retry.policy.408", area: "retry", fn: policy({}), replies: [errorReply(408, "error_object"), ok("chat_completion")] });
  out.push({ id: "retry.policy.timeout", area: "retry", fn: policy({ timeoutRetries: 1, connectionErrorRetries: 0 }), replies: [{ raise: "read_timeout" }, { raise: "connect" }, ok("chat_completion")] });
  out.push({ id: "retry.policy.defaults", area: "retry", fn: async (ctx) => new ctx.mod.RetryPolicy() });
  out.push({ id: "retry.callbacks", area: "retry", fn: async (ctx) => {
    const seen = [];
    const hook = (name) => (...args) => seen.push([name, args.length]);
    const names = ["onRequestStart", "onRequestEnd", "onRetry", "onError", "onStreamStart", "onStreamChunk", "onStreamEnd", "onCacheHit", "onCostUpdate", "onFallback", "onGuardrailWarning", "onGuardrailBlock"];
    const cb = Object.fromEntries(names.map((n) => [n, hook(n)]));
    const client = ctx.client({ maxRetries: 1, callbacks: [cb] });
    return { result: await ctx.attempt(() => client.chat.completions.create(CHAT)), seen };
  }, replies: [errorReply(500, "error_object"), ok("chat_completion", { headers: { "x-agentcc-cost": "0.1", "x-agentcc-cache": "hit", "x-agentcc-fallback-used": "true" } })] });

  const timeout = (clientOpts, params = {}) => async (ctx) => ctx.client({ maxRetries: 0, ...clientOpts }).chat.completions.create({ ...CHAT, ...params });
  out.push({ id: "timeout.client.default", area: "timeouts", fn: timeout({}), replies: [ok("chat_completion")] });
  out.push({ id: "timeout.client.ms", area: "timeouts", fn: timeout({ timeout: 5000 }), replies: [ok("chat_completion")] });
  out.push({ id: "timeout.with_options", area: "timeouts", fn: async (ctx) => ctx.client({ maxRetries: 0, timeout: 3000 }).withOptions({ timeout: 6000 }).chat.completions.create(CHAT), replies: [ok("chat_completion")] });
  out.push({ id: "timeout.request_timeout_header", area: "timeouts", fn: timeout({}, { request_timeout: 2500 }), replies: [ok("chat_completion")] });
  out.push({ id: "timeout.read_raises", area: "timeouts", fn: timeout({}), replies: [{ raise: "read_timeout" }] });
  out.push({ id: "timeout.stream_read_raises", area: "timeouts", fn: stream({ maxRetries: 0 }), replies: [{ raise: "read_timeout" }] });
  out.push({ id: "timeout.stream_drop_mid_body", area: "timeouts", fn: stream({ maxRetries: 0 }), replies: [{ status: 200, sse: ['{"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"Part"},"finish_reason":null}]}'], drop_after: true }] });
  return out;
}
