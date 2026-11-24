# Vendored from agent-command-center-sdk

`src/gateway` is the `@agentcc/client` TypeScript package from
https://github.com/future-agi/agent-command-center-sdk (`sdk/typescript/src`, commit 988c46e,
@agentcc/client 1.0.0), copied in so the gateway client ships inside `@future-agi/sdk`, the way
`fi.gateway` ships inside the Python package (`python/fi/gateway/VENDORED.md`).

Entry points: `@future-agi/sdk/gateway` (also `Gateway` and the `gateway` namespace from the
package root), and `@future-agi/sdk/gateway/testing`, `/express`, `/nextjs` for upstream's three
side entry points.

Changes from upstream:
- relative imports lost their `.js` suffix (this package's build adds it), and doc examples import
  from `@future-agi/sdk/gateway`;
- `fi.ts` adds `Gateway` (hosted default URL), and `env.ts` the settings every entry point reads:
  `FI_GATEWAY_API_KEY` / `FI_GATEWAY_URL`, then `AGENTCC_API_KEY` / `AGENTCC_BASE_URL`. A base URL
  may end in `/v1` or not (upstream's own `AGENTCC_GATEWAY_URL` default ends in `/v1`, which made
  every call `/v1/v1/...`).
- bugs fixed while bringing it in (regression tests in `__tests__/fi-gateway.test.ts`):
  - error messages ignored the gateway's `{"error": {"message": ...}}` body, so every failure read
    "Request failed with status N"; `{"error": "text"}` and `{"detail"}` are read too. A non-JSON
    error body (a proxy's HTML 502) lost its text because the body was read twice;
  - `checkValidKey` recognised a rejected key by searching the message for "401"; it checks the
    error class;
  - `client.use(middleware)` stored the middleware and never ran it; middlewares now wrap the
    request (retries included), first added outermost;
  - `onStreamStart` / `onStreamChunk` / `onStreamEnd` were never called; a stream reports to the
    callbacks as it is read (`BaseClient.openStream`, `StreamHooks`), and a stream that fails
    mid-way reports `onError`;
  - `onRequestEnd` got a `null` body for every call a resource parses itself (chat, embeddings,
    completions, models, rerank, audio), so `MetricsCallback.totalTokens` and a session's
    `totalTokens` stayed 0; the JSON body is read from a clone, and a stream adds its usage when
    it ends;
  - a session's headers were copied once when `session()` was called, so `session.step()` never
    changed the path that was sent, and a client-level `sessionId` overrode the session's own id;
    they are read on every request. `session()` also returns `end()`, which fires `onSessionEnd`
    (nothing did);
  - `withOptions()` returned a plain `AgentCC` without the middlewares; it keeps the class, the
    middlewares and the session;
  - the SSE parser split events on `\n\n` only, so a CRLF stream never produced an event; a
    stream that the consumer left early (or that ended with `[DONE]`) kept its connection open;
  - a cache hit on `stream: true` arrives as one JSON completion and was yielded as if it were a
    chunk, so `textStream()` and `getFinalCompletion()` saw no content; it is reshaped into a chunk;
  - redaction left `tool_calls[].function.arguments`, `function_call.arguments` and
    `instructions` in the copy callbacks get.

Tests are in `__tests__/` (upstream `sdk/typescript/tests`, ported from vitest to jest; three
suites needed type fixes vitest never checked). Not brought over: the benchmark suites and
`e2e-real.test.ts` (they need a running gateway; `__tests__/live.test.ts` replaces the latter and
runs when `FI_GATEWAY_URL` / `FI_GATEWAY_API_KEY` are set), and the framework adapters under
`sdk/typescript/packages` (`@agentcc/langchain`, `/llamaindex`, `/react`, `/vercel`), which are
separate packages with their own peer dependencies.
