"""The 7-level header merge: one case per collision between two levels.

Levels (agentcc 1.0 _base_client._build_headers): 1 SDK auto headers, 2 auth,
3 client default_headers, 4 client session_id / metadata, 5 config headers,
6 per-request gateway params, 7 per-request extra_headers. A session context
and ``properties`` / ``user_id`` / ``request_id`` feed level 7.
"""

from __future__ import annotations

from typing import Any

from .._fixtures import MSG, ok
from .._runner import Case, exercises

BOTH = ("sync", "async")
CHAT = {"model": "gpt-4o-mini", "messages": MSG}


def _collide(
    client_opts: dict[str, Any],
    call_opts: dict[str, Any],
    config: dict[str, Any] | None = None,
):
    def fn(ctx):
        opts = dict(client_opts)
        if config is not None:
            g = ctx.T
            opts["config"] = g.GatewayConfig(cache=g.CacheConfig(**config))
        client = ctx.client(max_retries=0, **opts)
        return ctx.call(client, "chat.completions.create", **CHAT, **call_opts)

    return fn


@exercises("session")
def _session_vs_extra(ctx):
    client = ctx.client(max_retries=0, session_id="client-sess")
    with client.session(
        session_id="ctx-sess", name="flow", metadata={"k": "v"}
    ) as sess:
        sess.step("one")
        a = ctx.call(client, "chat.completions.create", **CHAT)
        b = ctx.call(
            client,
            "chat.completions.create",
            **CHAT,
            extra_headers={"x-agentcc-session-id": "explicit"},
            session_id="param-sess",
        )
    after = ctx.call(client, "chat.completions.create", **CHAT)
    return {"a": a.id, "b": b.id, "after": after.id}


COLLISIONS: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]] = {
    "l3_over_l1": (
        {
            "default_headers": {
                "User-Agent": "custom-ua",
                "Content-Type": "text/plain",
                "x-agentcc-sdk-version": "9",
            }
        },
        {},
        None,
    ),
    "l3_over_l2": (
        {"default_headers": {"Authorization": "Bearer from-default"}},
        {},
        None,
    ),
    "l3_case_variant_l2": (
        {"default_headers": {"authorization": "Bearer lower-case"}},
        {},
        None,
    ),
    "l4_over_l3": (
        {
            "default_headers": {
                "x-agentcc-session-id": "from-default",
                "x-agentcc-metadata": "{}",
            },
            "session_id": "from-client",
            "metadata": {"a": 1},
        },
        {},
        None,
    ),
    "l5_over_l3": ({"default_headers": {"x-agentcc-cache-ttl": "1"}}, {}, {"ttl": 300}),
    "l5_over_l4": ({"session_id": "s"}, {}, {"ttl": 300, "namespace": "cfg"}),
    "l6_over_l4": (
        {"session_id": "from-client", "metadata": {"a": 1}},
        {"session_id": "from-param", "request_metadata": {"b": 2}},
        None,
    ),
    "l6_over_l5": (
        {},
        {"cache_ttl": 5, "cache_namespace": "param"},
        {"ttl": 300, "namespace": "cfg", "force_refresh": True},
    ),
    "l7_over_l6": (
        {},
        {
            "session_id": "from-param",
            "extra_headers": {"x-agentcc-session-id": "from-extra"},
        },
        None,
    ),
    "l7_over_l5": ({}, {"extra_headers": {"x-agentcc-cache-ttl": "9"}}, {"ttl": 300}),
    "l7_over_l3": (
        {"default_headers": {"X-Dup": "default"}},
        {"extra_headers": {"X-Dup": "extra"}},
        None,
    ),
    "l7_over_l2": ({}, {"extra_headers": {"Authorization": "Bearer from-extra"}}, None),
    "l7_over_l1": (
        {},
        {
            "extra_headers": {
                "User-Agent": "extra-ua",
                "Content-Type": "application/x-test",
            }
        },
        None,
    ),
    "l7_case_variant_l3": (
        {"default_headers": {"X-Case": "upper"}},
        {"extra_headers": {"x-case": "lower"}},
        None,
    ),
    "properties_over_extra": (
        {},
        {
            "properties": {"team": "prop"},
            "extra_headers": {"x-agentcc-property-team": "extra"},
        },
        None,
    ),
    "user_id_over_extra": (
        {},
        {"user_id": "param", "extra_headers": {"x-agentcc-user-id": "extra"}},
        None,
    ),
    "request_id_over_extra": (
        {},
        {"request_id": "param", "extra_headers": {"x-agentcc-request-id": "extra"}},
        None,
    ),
    "guardrail_policy_param_vs_extra": (
        {},
        {"guardrail_policy": "param", "extra_headers": {"X-Guardrail-Policy": "extra"}},
        None,
    ),
}


@exercises("with_options")
def _with_options_vs_default(ctx):
    base = ctx.client(
        max_retries=0, default_headers={"X-Dup": "default", "X-Keep": "k"}
    )
    derived = base.with_options(
        extra_headers={"X-Dup": "with-options"}, session_id="wo"
    )
    return ctx.call(
        derived, "chat.completions.create", **CHAT, extra_headers={"X-Late": "l"}
    )


def cases() -> list[Case]:
    out = [
        Case(
            f"header_merge.{name}",
            "header_merge",
            _collide(*spec),
            BOTH,
            replies=[ok("chat_completion")],
        )
        for name, spec in COLLISIONS.items()
    ]
    out.append(
        Case(
            "header_merge.session_ctx",
            "header_merge",
            _session_vs_extra,
            BOTH,
            replies=[ok("chat_completion")] * 3,
        )
    )
    out.append(
        Case(
            "header_merge.with_options_vs_default",
            "header_merge",
            _with_options_vs_default,
            BOTH,
            replies=[ok("chat_completion")],
        )
    )
    return out
