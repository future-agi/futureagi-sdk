# Vendored from agent-command-center-sdk

`fi/gateway` is the `agentcc` Python package from
https://github.com/future-agi/agent-command-center-sdk (`sdk/python/src/agentcc`, commit 988c46e, agentcc 1.0.0),
copied in so the gateway client ships inside `futureagi`.

Changes from upstream:
- imports rewritten from `agentcc` to `fi.gateway` (logger names stay `agentcc` so existing logging config keeps working);
- `_fi.py` adds `Gateway` / `AsyncGateway` (Future AGI env vars, hosted default URL, tolerant of a trailing `/v1`).

Tests are in `tests/gateway/` (upstream `sdk/python/tests`, same rewrite).
