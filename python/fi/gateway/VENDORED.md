# Vendored from agent-command-center-sdk

`fi/gateway` is the `agentcc` Python package from
https://github.com/future-agi/agent-command-center-sdk (`sdk/python/src/agentcc`, commit 988c46e, agentcc 1.0.0),
copied in so the gateway client ships inside `futureagi`.

Changes from upstream:
- imports rewritten from `agentcc` to `fi.gateway` (logger names stay `agentcc` so existing logging config keeps working);
- `_fi.py` adds `Gateway` / `AsyncGateway` (Future AGI env vars, hosted default URL, tolerant of a trailing `/v1`).
- bugs fixed after running against a real gateway with real providers (regression tests in
  `tests/gateway/test_live_fixes.py`):
  - `audio.transcriptions` / `audio.translations` sent the file inside a JSON body; they now upload
    `multipart/form-data` (`RequestOptions.files`);
  - `Usage.completion_tokens` was required, so every embeddings response failed to parse;
  - `Session.request_count` / `total_cost` / `total_tokens` stayed 0: nothing called `track_request`.
- bugs found in code review (regression tests in `tests/gateway/test_review_fixes.py`):
  - the SSE parsers split each network chunk on its own, so a line straddling two chunks was torn
    (truncated JSON, or a multibyte character replaced); they now buffer partial lines and decode
    UTF-8 incrementally;
  - a cache hit on `stream=True` called `response.json()` on an unread streamed response;
  - a streamed error response was never closed, leaking a pooled connection; a 246 guardrail
    warning on a stream was not raised;
  - `{"error": "<string>"}` bodies crashed error parsing instead of giving a typed error;
  - `on_request_end` callbacks got the parsed model instead of a `CallbackResponse`, so the built-in
    logging/recording handlers always raised (and were silenced); the JSON logger also read a
    field that does not exist (`cache_hit`);
  - `audio.speech` serialised agentcc params with `str()`, so `request_metadata` was sent as a
    Python repr, not JSON;
  - `files.create` / `files.content` / `responses.delete` bypassed the base client (no retries,
    callbacks, session tracking or error mapping);
  - `with_options()` shared the parent's base client, so timeout, retries, headers, session and
    metadata overrides were ignored once the parent had made a request; `trace_id` was accepted
    and dropped;
  - `FI_GATEWAY_API_KEY` / `FI_GATEWAY_URL` (and the `/v1` fix) now apply to every entry point
    (`AgentCC`, `health_check`, `validate_environment`, `patch_openai`), through `_env.py`.
- bugs found in the security / correctness review of futureagi-sdk#35 (regression tests in
  `tests/gateway/test_security_review_fixes.py`):
  - `redact_messages=True` was stored and never applied: callbacks (and so `RequestRecorder`)
    received the full message body. Callbacks now get a redacted copy (`messages[].content`,
    `prompt`, `input`, `instructions` replaced by `[REDACTED]`); the request to the provider is
    untouched;
  - the active session was one attribute on the client, so two threads or asyncio tasks sharing a
    client overwrote each other's session, a request could be credited to another task's session,
    and leaving a nested session dropped the outer one. It is a `ContextVar` now, restored on exit,
    and a request is credited to the session it started in;
  - `to_response_format()` sent Pydantic's schema with `strict: true`, which OpenAI rejects
    (`additionalProperties`, `required`, `default`). The schema is converted (`strict_schema`):
    every object closed, every property required, defaulted fields made nullable, `$defs` too;
  - `responses.create(stream=True)` and `completions.create(stream=True)` decoded every event as
    a chat chunk and failed on the first one; each endpoint now has its own event model
    (`ResponseStreamEvent` with a string `delta`, `Completion`);
  - a stream that ended normally (or with an error) never closed its HTTP response, holding a
    pooled connection until the caller remembered `close()`; both streams close themselves when
    they end (closing is idempotent);
  - `AsyncStream` built a new parser on every `async for`, so breaking out of a loop and then
    calling `get_final_completion()` hit httpx's `StreamConsumed`; one iterator is shared;
  - `create_mock_client()` returned an ordinary network client that ignored its fixture mapping
    (a reachable gateway would have made billable calls); it now installs an httpx mock transport
    that serves the mapping and answers 404 for anything else;
  - `Embedding.embedding` only accepted `list[float]`, so `encoding_format="base64"` responses
    failed validation; the base64 string is accepted and `decode_base64_embedding()` unpacks it;
  - `close()` / `aclose()` skipped every client made by `with_options()`, so a copy made before
    the parent's first request could never close the pool it owns; closing is delegated to the
    base client, which already knows whether its pool is owned, shared or injected.

Tests are in `tests/gateway/` (upstream `sdk/python/tests`, same rewrite). `test_gateway_live.py` runs
against a real gateway when `FI_GATEWAY_URL` / `FI_GATEWAY_API_KEY` are set (see its docstring).
