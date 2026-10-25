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

Tests are in `tests/gateway/` (upstream `sdk/python/tests`, same rewrite). `test_gateway_live.py` runs
against a real gateway when `FI_GATEWAY_URL` / `FI_GATEWAY_API_KEY` are set (see its docstring).
