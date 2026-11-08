"""Retries (attempt counts, Retry-After, recorded sleeps) and timeouts."""

from __future__ import annotations

from typing import Any

from .._fixtures import MSG, error_reply, ok
from .._runner import Case

BOTH = ("sync", "async")
CHAT = {"model": "gpt-4o-mini", "messages": MSG}
RETRYABLE = (408, 429, 500, 502, 503, 504)
NOT_RETRIED = (400, 401, 403, 404, 413, 422, 446)
RETRY_AFTER = {
    "zero": "0",
    "one": "1",
    "fraction": "2.5",
    "above_cap": "30",
    "negative": "-1",
    "text": "soon",
    "http_date": "Wed, 21 Oct 2026 07:28:00 GMT",
}
TRANSPORT = (
    "connect",
    "connect_timeout",
    "read_timeout",
    "write_timeout",
    "pool_timeout",
    "remote_protocol",
)


def _create(**client_opts: Any):
    def fn(ctx):
        return ctx.call(ctx.client(**client_opts), "chat.completions.create", **CHAT)

    return fn


def _stream(**client_opts: Any):
    def fn(ctx):
        stream = ctx.call(
            ctx.client(**client_opts), "chat.completions.create", **CHAT, stream=True
        )
        return ctx.drain(stream)

    return fn


def _policy(**fields: Any):
    def fn(ctx):
        client = ctx.client(retry_policy=ctx.T.RetryPolicy(**fields))
        return ctx.call(client, "chat.completions.create", **CHAT)

    return fn


def _per_request_timeout(timeout: Any):
    def fn(ctx):
        client = ctx.client(max_retries=0)
        return ctx.call(
            client,
            "chat.completions.create",
            **CHAT,
            timeout=timeout(ctx) if callable(timeout) else timeout,
        )

    return fn


def _client_timeout(timeout: Any):
    def fn(ctx):
        value = timeout(ctx) if callable(timeout) else timeout
        client = ctx.client(max_retries=0, timeout=value)
        a = ctx.call(client, "chat.completions.create", **CHAT)
        b = ctx.call(client, "models.list")
        return [a.id, type(b).__qualname__]

    return fn


def _with_options_timeout(ctx):
    client = ctx.client(max_retries=0, timeout=3.0).with_options(timeout=6.0)
    return ctx.call(client, "chat.completions.create", **CHAT)


def _retry_cases() -> list[Case]:
    out = []
    for status in RETRYABLE:
        out.append(
            Case(
                f"retry.{status}.exhausted",
                "retry",
                _create(),
                BOTH,
                replies=[error_reply(status, "error_object")] * 3,
            )
        )
        out.append(
            Case(
                f"retry.{status}.then_ok",
                "retry",
                _create(),
                BOTH,
                replies=[error_reply(status, "error_object"), ok("chat_completion")],
            )
        )
    for status in NOT_RETRIED:
        out.append(
            Case(
                f"retry.{status}.not_retried",
                "retry",
                _create(max_retries=3),
                BOTH,
                replies=[error_reply(status, "error_object"), ok("chat_completion")],
            )
        )
    for name, value in RETRY_AFTER.items():
        reply = error_reply(429, "error_object", {"retry-after": value})
        out.append(
            Case(
                f"retry.retry_after.{name}",
                "retry",
                _create(max_retries=1),
                BOTH,
                replies=[reply, ok("chat_completion")],
            )
        )
    out.append(
        Case(
            "retry.retry_after_ms",
            "retry",
            _create(max_retries=1),
            BOTH,
            replies=[
                error_reply(503, "error_object", {"retry-after-ms": "1500"}),
                ok("chat_completion"),
            ],
        )
    )
    for n in (0, 1, 3, 5):
        out.append(
            Case(
                f"retry.max_retries.{n}",
                "retry",
                _create(max_retries=n),
                BOTH,
                replies=[error_reply(500, "empty")] * (n + 1),
            )
        )
    for kind in TRANSPORT:
        out.append(
            Case(
                f"retry.transport.{kind}",
                "retry",
                _create(max_retries=1),
                BOTH,
                replies=[{"raise": kind}, ok("chat_completion")],
            )
        )
        out.append(
            Case(
                f"retry.transport.{kind}.exhausted",
                "retry",
                _create(max_retries=1),
                BOTH,
                replies=[{"raise": kind}] * 2,
            )
        )
    out.append(
        Case(
            "retry.stream.500",
            "retry",
            _stream(),
            BOTH,
            replies=[error_reply(500, "error_object"), ok("chat_completion")],
        )
    )
    out.append(
        Case(
            "retry.stream.connect",
            "retry",
            _stream(),
            BOTH,
            replies=[{"raise": "connect"}, ok("chat_completion")],
        )
    )
    out.append(
        Case(
            "retry.policy.ratelimit",
            "retry",
            _policy(RateLimitErrorRetries=3),
            BOTH,
            replies=[error_reply(429, "error_object")] * 4,
        )
    )
    out.append(
        Case(
            "retry.policy.no_5xx",
            "retry",
            _policy(InternalServerErrorRetries=0),
            BOTH,
            replies=[error_reply(500, "error_object"), ok("chat_completion")],
        )
    )
    out.append(
        Case(
            "retry.policy.408",
            "retry",
            _policy(),
            BOTH,
            replies=[error_reply(408, "error_object"), ok("chat_completion")],
        )
    )
    out.append(
        Case(
            "retry.policy.timeout",
            "retry",
            _policy(TimeoutRetries=1, ConnectionErrorRetries=0),
            BOTH,
            replies=[
                {"raise": "read_timeout"},
                {"raise": "connect"},
                ok("chat_completion"),
            ],
        )
    )
    out.append(Case("retry.policy.defaults", "retry", lambda c: c.T.RetryPolicy()))
    return out


def _timeout_cases() -> list[Case]:
    def http_timeout(ctx):
        import httpx

        return httpx.Timeout(3.0, connect=1.0)

    def dataclass_timeout(ctx):
        return ctx.T.Timeout(connect=1.0, read=2.0)

    out = [
        Case(
            "timeout.client.default",
            "timeouts",
            _client_timeout(None),
            BOTH,
            replies=[ok("chat_completion"), ok("models_list")],
        ),
        Case(
            "timeout.client.float",
            "timeouts",
            _client_timeout(5),
            BOTH,
            replies=[ok("chat_completion"), ok("models_list")],
        ),
        Case(
            "timeout.client.dataclass",
            "timeouts",
            _client_timeout(dataclass_timeout),
            BOTH,
            replies=[ok("chat_completion"), ok("models_list")],
        ),
        Case(
            "timeout.client.httpx",
            "timeouts",
            _client_timeout(http_timeout),
            BOTH,
            replies=[ok("chat_completion"), ok("models_list")],
        ),
        Case(
            "timeout.request.float",
            "timeouts",
            _per_request_timeout(4),
            BOTH,
            replies=[ok("chat_completion")],
        ),
        Case(
            "timeout.request.dataclass",
            "timeouts",
            _per_request_timeout(dataclass_timeout),
            BOTH,
            replies=[ok("chat_completion")],
        ),
        Case(
            "timeout.request.none",
            "timeouts",
            _per_request_timeout(None),
            BOTH,
            replies=[ok("chat_completion")],
        ),
        Case(
            "timeout.with_options",
            "timeouts",
            _with_options_timeout,
            BOTH,
            replies=[ok("chat_completion")],
        ),
        Case(
            "timeout.request_timeout_header",
            "timeouts",
            lambda c: c.call(
                c.client(max_retries=0),
                "chat.completions.create",
                **CHAT,
                request_timeout=2.5,
            ),
            BOTH,
            replies=[ok("chat_completion")],
        ),
        Case(
            "timeout.read_raises",
            "timeouts",
            _create(max_retries=0),
            BOTH,
            replies=[{"raise": "read_timeout"}],
        ),
        Case(
            "timeout.stream_read_raises",
            "timeouts",
            _stream(max_retries=0),
            BOTH,
            replies=[{"raise": "read_timeout"}],
        ),
        Case(
            "timeout.stream_drop_mid_body",
            "timeouts",
            _stream(max_retries=0),
            BOTH,
            replies=[
                {
                    "status": 200,
                    "sse": [
                        '{"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[{"index":0,"delta":{"content":"Part"},"finish_reason":null}]}'
                    ],
                    "drop_after": True,
                }
            ],
        ),
    ]
    return out


def cases() -> list[Case]:
    return _retry_cases() + _timeout_cases()
