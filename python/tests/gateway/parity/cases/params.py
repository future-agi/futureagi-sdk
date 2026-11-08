"""Per-request parameters alone and combined; client options; with_options."""

from __future__ import annotations

from typing import Any

from .._fixtures import MSG, ok
from .._runner import Case, exercises

BOTH = ("sync", "async")
CHAT = {"model": "gpt-4o-mini", "messages": MSG}

BODY_PARAMS: dict[str, Any] = {
    "temperature": 0.5,
    "top_p": 0.9,
    "n": 2,
    "stop": ["\n"],
    "max_tokens": 10,
    "max_completion_tokens": 12,
    "presence_penalty": 0.1,
    "frequency_penalty": 0.2,
    "logit_bias": {"50256": -100},
    "logprobs": True,
    "top_logprobs": 2,
    "user": "user-1",
    "seed": 42,
    "tools": [
        {
            "type": "function",
            "function": {"name": "f", "parameters": {"type": "object"}},
        }
    ],
    "tool_choice": "none",
    "response_format": {"type": "json_object"},
    "service_tier": "auto",
    "thinking": {"type": "enabled", "budget_tokens": 64},
    "reasoning_effort": "low",
    "drop_params": True,
    "stream_options": {"include_usage": True},
    "extra_body": {"custom_field": 1},
    "unknown_kwarg": "passes through",
}
GATEWAY_PARAMS: dict[str, Any] = {
    "session_id": "sess-1",
    "trace_id": "trace-1",
    "request_metadata": {"k": "v", "n": 1},
    "request_timeout": 30,
    "cache_ttl": 300,
    "cache_namespace": "ns-1",
    "cache_force_refresh": True,
    "cache_control": "no-cache",
    "guardrail_policy": "strict",
    "properties": {"team": "a", "env": "dev"},
    "user_id": "u-1",
    "request_id": "r-1",
    "extra_headers": {"X-Custom": "1"},
    "timeout": 12.5,
}
NONE_PARAMS = (
    "temperature",
    "session_id",
    "cache_ttl",
    "user_id",
    "properties",
    "extra_headers",
    "timeout",
)


def _create(**extra: Any):
    def fn(ctx):
        return ctx.call(
            ctx.client(max_retries=0), "chat.completions.create", **CHAT, **extra
        )

    return fn


def _alone() -> list[Case]:
    out = []
    for name, value in {**BODY_PARAMS, **GATEWAY_PARAMS}.items():
        out.append(
            Case(
                f"param.chat.{name}",
                "params",
                _create(**{name: value}),
                BOTH,
                replies=[ok("chat_completion")],
            )
        )
    for name in NONE_PARAMS:
        out.append(
            Case(
                f"param.chat.{name}.none",
                "params",
                _create(**{name: None}),
                BOTH,
                replies=[ok("chat_completion")],
            )
        )
    out.append(
        Case(
            "param.chat.combined",
            "params",
            _create(**BODY_PARAMS, **GATEWAY_PARAMS),
            BOTH,
            replies=[ok("chat_completion")],
        )
    )
    return out


def _with_options(**opts: Any):
    @exercises("with_options")
    def fn(ctx):
        base = ctx.client(
            max_retries=0, default_headers={"X-Base": "b"}, session_id="base-sess"
        )
        derived = base.with_options(**opts)
        result = ctx.call(derived, "chat.completions.create", **CHAT)
        return {
            "result": result,
            "base_cost": base.current_cost,
            "derived_cost": derived.current_cost,
        }

    return fn


WITH_OPTIONS: dict[str, Any] = {
    "timeout": 7.5,
    "max_retries": 3,
    "extra_headers": {"X-Derived": "d"},
    "extra_query": {"q": "1"},
    "session_id": "derived-sess",
    "metadata": {"m": "1"},
    "trace_id": "derived-trace",
    "drop_params": True,
}


def _client_option(**opts: Any):
    def fn(ctx):
        client = ctx.client(max_retries=0, **opts)
        return ctx.call(client, "chat.completions.create", **CHAT)

    return fn


class _Hooks:
    """Records every callback hook the SDK calls, by name."""

    NAMES = (
        "on_request_start",
        "on_request_end",
        "on_retry",
        "on_error",
        "on_stream_start",
        "on_stream_chunk",
        "on_stream_end",
        "on_guardrail_warning",
        "on_guardrail_block",
        "on_cache_hit",
        "on_cost_update",
        "on_budget_warning",
        "on_fallback",
        "on_session_start",
        "on_session_end",
    )

    def __init__(self) -> None:
        self.calls: list[list[Any]] = []
        for name in self.NAMES:
            setattr(self, name, self._make(name))

    def _make(self, name: str):
        def hook(*args: Any) -> None:
            self.calls.append([name, [type(a).__qualname__ for a in args]])

        return hook


def _callbacks(replies_kind: str):
    def fn(ctx):
        hooks = _Hooks()
        client = ctx.client(max_retries=1, callbacks=[hooks])
        if replies_kind == "stream":
            stream = ctx.call(client, "chat.completions.create", **CHAT, stream=True)
            ctx.drain(stream)
        else:
            ctx.attempt(lambda: ctx.call(client, "chat.completions.create", **CHAT))
        return hooks.calls

    return fn


def _client_options() -> list[Case]:
    opts: dict[str, dict[str, Any]] = {
        "default_query": {"default_query": {"tenant": "t1"}},
        "default_headers": {"default_headers": {"X-Default": "d"}},
        "session_id": {"session_id": "client-sess"},
        "metadata": {"metadata": {"team": "a", "n": 2}},
        "drop_params": {"drop_params": True},
        "redact_messages": {"redact_messages": True},
        "modify_params": {"modify_params": True},
        "pre_call_rules.allow": {
            "pre_call_rules": [lambda model, messages, kwargs: True]
        },
        "timeout.float": {"timeout": 9.0},
    }
    out = [
        Case(
            f"client_option.{name}",
            "params",
            _client_option(**o),
            BOTH,
            replies=[ok("chat_completion")],
        )
        for name, o in opts.items()
    ]
    out.append(
        Case("client_option.pre_call_rules.block", "params", _blocked_rule, BOTH)
    )
    out.append(
        Case(
            "client_option.modify_params.anthropic",
            "params",
            _modify_anthropic,
            BOTH,
            replies=[ok("chat_completion")],
        )
    )
    out.append(
        Case(
            "client_option.json_schema_validation.ok",
            "params",
            _json_schema("chat_completion_json"),
            BOTH,
            replies=[ok("chat_completion_json")],
        )
    )
    out.append(
        Case(
            "client_option.json_schema_validation.bad",
            "params",
            _json_schema("chat_completion_json_bad"),
            BOTH,
            replies=[ok("chat_completion_json_bad")],
        )
    )
    out.append(
        Case(
            "client_option.callbacks.success",
            "params",
            _callbacks("ok"),
            BOTH,
            replies=[ok("chat_completion")],
        )
    )
    out.append(
        Case(
            "client_option.callbacks.retry_then_error",
            "params",
            _callbacks("ok"),
            BOTH,
            replies=[
                {"status": 500, "json": {"error": {"message": "boom"}}},
                {"status": 400, "json": {"error": {"message": "bad"}}},
            ],
        )
    )
    out.append(
        Case(
            "client_option.callbacks.stream",
            "params",
            _callbacks("stream"),
            BOTH,
            replies=[
                {
                    "status": 200,
                    "sse": [
                        '{"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[]}',
                        "[DONE]",
                    ],
                }
            ],
        )
    )
    out.append(
        Case("client_option.redact_messages.property", "params", _redact_property, BOTH)
    )
    return out


def _blocked_rule(ctx):
    def no_gpt(model, messages, kwargs):
        return not model.startswith("gpt")

    client = ctx.client(max_retries=0, pre_call_rules=[no_gpt])
    return ctx.call(client, "chat.completions.create", **CHAT)


def _modify_anthropic(ctx):
    client = ctx.client(max_retries=0, modify_params=True)
    return ctx.call(
        client,
        "chat.completions.create",
        model="anthropic/claude-3-5-haiku",
        messages=[{"role": "system", "content": "s"}, *MSG],
        temperature=0.3,
    )


def _json_schema(_key: str):
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "p",
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                "required": ["name"],
            },
        },
    }

    def fn(ctx):
        client = ctx.client(max_retries=0, enable_json_schema_validation=True)
        return ctx.call(
            client, "chat.completions.create", **CHAT, response_format=schema
        )

    return fn


def _redact_property(ctx):
    client = ctx.client(redact_messages=False)
    before = client.redact_messages
    client.redact_messages = True
    return [before, client.redact_messages]


def cases() -> list[Case]:
    with_opts = [
        Case(
            f"with_options.{name}",
            "params",
            _with_options(**{name: value}),
            BOTH,
            replies=[ok("chat_completion")],
        )
        for name, value in WITH_OPTIONS.items()
    ]
    with_opts.append(
        Case(
            "with_options.combined",
            "params",
            _with_options(**WITH_OPTIONS),
            BOTH,
            replies=[ok("chat_completion")],
        )
    )
    return _alone() + with_opts + _client_options()
