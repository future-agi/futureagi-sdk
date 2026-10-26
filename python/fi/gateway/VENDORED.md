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

Tests are in `tests/gateway/` (upstream `sdk/python/tests`, same rewrite). `test_gateway_live.py` runs
against a real gateway when `FI_GATEWAY_URL` / `FI_GATEWAY_API_KEY` are set (see its docstring).
