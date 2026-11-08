"""GatewayConfig (every section), create_headers (every argument), Session."""

from __future__ import annotations

from typing import Any

from .._fixtures import MSG, ok
from .._runner import Case, exercises

BOTH = ("sync", "async")
CHAT = {"model": "gpt-4o-mini", "messages": MSG}


def _sections(g: Any) -> dict[str, Any]:
    return {
        "fallback": g.FallbackConfig(
            targets=[
                g.FallbackTarget(
                    model="gpt-4o-mini",
                    provider="openai",
                    override_params={"temperature": 0},
                )
            ]
        ),
        "fallback.default_codes": g.FallbackConfig(),
        "load_balance": g.LoadBalanceConfig(
            strategy="weighted",
            targets=[
                g.LoadBalanceTarget(model="a", weight=2.0, virtual_key="vk-a"),
                g.LoadBalanceTarget(model="b"),
            ],
        ),
        "cache": g.CacheConfig(
            ttl=300,
            namespace="prod",
            force_refresh=True,
            semantic_threshold=0.9,
            ignore_keys=["user"],
        ),
        "cache.defaults": g.CacheConfig(),
        "guardrails.ids": g.GuardrailConfig(
            input_guardrails=["pii"], output_guardrails=["toxicity", "secrets"]
        ),
        "guardrails.checks": g.GuardrailConfig(
            checks=[
                g.GuardrailCheck(
                    name="pii", action="warn", confidence_threshold=0.5, config={"k": 1}
                )
            ],
            pipeline_mode="sequential",
            fail_open=True,
            timeout_ms=250,
        ),
        "routing": g.ConditionalRoutingConfig(
            conditions=[
                g.RoutingCondition(
                    field="metadata.tier", operator="$eq", value="gold", target="gpt-4o"
                )
            ],
            default_target="gpt-4o-mini",
        ),
        "mirror": g.TrafficMirrorConfig(
            target_model="shadow", target_provider="openai", sample_rate=0.25
        ),
        "retry": g.RetryConfig(max_retries=3, on_status_codes=[429]),
        "retry.defaults": g.RetryConfig(),
        "timeout": g.TimeoutConfig(connect=1.0, read=2.5, total=10.0),
        "timeout.total_fraction": g.TimeoutConfig(total=0.0015),
    }


def _config_pure(name: str):
    def fn(ctx):
        g = ctx.T
        section = _sections(g)[name]
        field = name.split(".")[0]
        config = g.GatewayConfig(**{field: section})
        return {
            "to_dict": config.to_dict(),
            "to_headers": config.to_headers(),
            "repr": repr(section),
        }

    return fn


def _config_wire(names: list[str]):
    def fn(ctx):
        g = ctx.T
        sections = _sections(g)
        config = g.GatewayConfig(**{n.split(".")[0]: sections[n] for n in names})
        client = ctx.client(max_retries=0, config=config)
        return ctx.call(client, "chat.completions.create", **CHAT)

    return fn


def _empty_config(ctx):
    g = ctx.T
    return {
        "to_dict": g.GatewayConfig().to_dict(),
        "to_headers": g.GatewayConfig().to_headers(),
    }


CREATE_HEADERS: dict[str, Any] = {
    "api_key": "parity-gateway-key",
    "trace_id": "t",
    "session_id": "s",
    "session_name": "flow",
    "session_path": "/a/b",
    "metadata": {"k": "v", "n": 1},
    "user_id": "u",
    "request_id": "r",
    "cache_ttl": 60,
    "cache_namespace": "ns",
    "cache_force_refresh": True,
    "guardrail_policy": "strict",
    "properties": {"team": "a"},
}


def _create_headers(**kwargs: Any):
    def fn(ctx):
        if "config" in kwargs:
            g = ctx.T
            kwargs_ = {
                **kwargs,
                "config": g.GatewayConfig(
                    cache=g.CacheConfig(ttl=5),
                    guardrails=g.GuardrailConfig(input_guardrails=["pii"]),
                ),
            }
            return ctx.T.create_headers(**kwargs_)
        return ctx.T.create_headers(**kwargs)

    return fn


def _session_pure(ctx):
    s = ctx.T.Session(name="flow", metadata={"k": "v", "n": 2})
    states = [s.to_headers()]
    s.step("search")
    s.step("summarize")
    states.append(s.to_headers())
    s.track_request(cost=0.25, tokens=10)
    s.track_request(cost=0.5)
    totals = [s.total_cost, s.request_count, s.total_tokens]
    s.reset_path()
    states.append(s.to_headers())
    return {
        "states": states,
        "totals": totals,
        "repr": repr(s),
        "auto_id": ctx.T.Session().session_id,
    }


@exercises("session")
def _session_wire(ctx):
    client = ctx.client(max_retries=0)
    with client.session(name="checkout", metadata={"cart": "c1"}) as sess:
        sess.step("pay")
        first = ctx.call(client, "chat.completions.create", **CHAT)
        inner = {"cost": sess.total_cost, "count": sess.request_count}
    return {
        "first_cost": first.agentcc.cost,
        "session_after": inner,
        "session_id": sess.session_id,
    }


def cases() -> list[Case]:
    section_names = [
        "fallback",
        "fallback.default_codes",
        "load_balance",
        "cache",
        "cache.defaults",
        "guardrails.ids",
        "guardrails.checks",
        "routing",
        "mirror",
        "retry",
        "retry.defaults",
        "timeout",
        "timeout.total_fraction",
    ]
    out = [
        Case(f"config.section.{n}", "config", _config_pure(n)) for n in section_names
    ]
    out.append(Case("config.empty", "config", _empty_config))
    for n in ("cache", "guardrails.ids", "timeout", "fallback"):
        out.append(
            Case(
                f"config.wire.{n}",
                "config",
                _config_wire([n]),
                BOTH,
                replies=[ok("chat_completion")],
            )
        )
    out.append(
        Case(
            "config.wire.all",
            "config",
            _config_wire(
                [
                    "fallback",
                    "load_balance",
                    "cache",
                    "guardrails.ids",
                    "routing",
                    "mirror",
                    "retry",
                    "timeout",
                ]
            ),
            BOTH,
            replies=[ok("chat_completion")],
        )
    )
    for name, value in CREATE_HEADERS.items():
        out.append(
            Case(f"create_headers.{name}", "config", _create_headers(**{name: value}))
        )
    out.append(Case("create_headers.none", "config", _create_headers()))
    out.append(
        Case(
            "create_headers.config_overlap",
            "config",
            _create_headers(cache_ttl=60, guardrail_policy="strict", config=True),
        )
    )
    out.append(
        Case("create_headers.combined", "config", _create_headers(**CREATE_HEADERS))
    )
    out.append(Case("session.pure", "config", _session_pure))
    out.append(
        Case(
            "session.wire",
            "config",
            _session_wire,
            BOTH,
            replies=[ok("chat_completion", headers={"x-agentcc-cost": "0.01"})],
        )
    )
    return out
