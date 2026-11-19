"""The legacy pydantic ``agentcc.config`` package (S bucket: shim-only after 2.0).

1.0 keeps these models beside the dataclass ``GatewayConfig`` for the older
``config/`` submodule API. Their ``to_headers()`` differs from the dataclass
one (it sends ``x-agentcc-cache-enabled: false``, keeps ``ttl`` a string and
puts every section in one ``x-agentcc-config``), and the client accepts any
object with ``to_headers()`` as ``config=``, so the wire case records what such
a config sends.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .._fixtures import MSG, ok
from .._runner import Case

BOTH = ("sync", "async")
MODELS = (
    "Target",
    "LoadBalanceStrategy",
    "FallbackStrategy",
    "RetryConfig",
    "CacheConfig",
    "GuardrailRule",
    "GuardrailConfig",
    "RouteCondition",
    "ConditionalRoute",
    "GatewayConfig",
)
SUBMODULES = ("caching", "fallback", "guardrails", "retry", "routing")


def _gpt(c: Any) -> Any:
    return c.Target(provider="openai", model="gpt-4o")


# name -> builder of a legacy GatewayConfig from the agentcc.config module
CONFIGS: dict[str, Callable[[Any], Any]] = {
    "empty": lambda c: c.GatewayConfig(),
    "cache.defaults": lambda c: c.GatewayConfig(cache=c.CacheConfig()),
    "cache.disabled": lambda c: c.GatewayConfig(cache=c.CacheConfig(enabled=False)),
    "cache.custom": lambda c: c.GatewayConfig(
        cache=c.CacheConfig(
            mode="semantic",
            ttl="5m",
            namespace="prod",
            semantic_threshold=0.5,
            force_refresh=True,
        )
    ),
    "routing": lambda c: c.GatewayConfig(
        routing=c.LoadBalanceStrategy(mode="round-robin", targets=[_gpt(c)])
    ),
    "routing.weighted": lambda c: c.GatewayConfig(
        routing=c.LoadBalanceStrategy(
            mode="weighted",
            targets=[
                c.Target(provider="openai", weight=0.5, virtual_key="vk-a"),
                c.Target(provider="anthropic", weight=0.5),
            ],
        )
    ),
    "fallback": lambda c: c.GatewayConfig(
        fallback=c.FallbackStrategy(targets=[c.Target(provider="anthropic")])
    ),
    "retry": lambda c: c.GatewayConfig(retry=c.RetryConfig(max_retries=3)),
    "guardrails": lambda c: c.GatewayConfig(
        guardrails=c.GuardrailConfig(
            pre=[c.GuardrailRule(name="pii")],
            post=[c.GuardrailRule(name="toxicity", action="warn", threshold=0.5)],
        )
    ),
    "conditional_routes": lambda c: c.GatewayConfig(
        conditional_routes=[
            c.ConditionalRoute(
                condition=c.RouteCondition(
                    field="metadata.tier", operator="$eq", value="gold"
                ),
                target=_gpt(c),
            )
        ]
    ),
    "conditional_routes.empty": lambda c: c.GatewayConfig(conditional_routes=[]),
}


def _legacy_pure(name: str):
    def fn(ctx):
        config = CONFIGS[name](ctx.mod("config"))
        return {
            "to_headers": config.to_headers(),
            "to_json": config.to_json(),
            "repr": repr(config),
        }

    return fn


def _legacy_invalid(ctx):
    c = ctx.mod("config")
    attempts = {
        "weights_do_not_sum": lambda: c.LoadBalanceStrategy(
            mode="weighted", targets=[c.Target(provider="a", weight=0.3)]
        ),
        "weight_missing": lambda: c.LoadBalanceStrategy(
            mode="weighted", targets=[c.Target(provider="a")]
        ),
        "no_targets": lambda: c.LoadBalanceStrategy(mode="round-robin", targets=[]),
        "fallback_no_targets": lambda: c.FallbackStrategy(targets=[]),
        "retry_too_many": lambda: c.RetryConfig(max_retries=11),
        "threshold_out_of_range": lambda: c.CacheConfig(semantic_threshold=2),
        "unknown_action": lambda: c.GuardrailRule(name="x", action="drop"),
        "unknown_operator": lambda: c.RouteCondition(field="f", operator="eq", value=1),
    }
    return {name: ctx.attempt(fn) for name, fn in attempts.items()}


def _legacy_schemas(ctx):
    c = ctx.mod("config")
    return {name: getattr(c, name).model_json_schema() for name in MODELS}


def _legacy_submodules(ctx):
    c = ctx.mod("config")
    out = {}
    for name in SUBMODULES:
        sub = ctx.mod(f"config.{name}")
        names = sorted(getattr(sub, "__all__", []))
        out[name] = {
            "all": names,
            "same_objects": all(getattr(sub, n) is getattr(c, n) for n in names),
        }
    return {"config_all": sorted(c.__all__), "submodules": out}


def _legacy_wire(ctx):
    c = ctx.mod("config")
    config = c.GatewayConfig(
        cache=c.CacheConfig(enabled=False, ttl="10m"),
        routing=c.LoadBalanceStrategy(
            mode="round-robin", targets=[c.Target(provider="openai")]
        ),
    )
    client = ctx.client(max_retries=0, config=config)
    return ctx.call(
        client, "chat.completions.create", model="gpt-4o-mini", messages=MSG
    )


def cases() -> list[Case]:
    out = [
        Case(f"config.legacy_pydantic.{n}", "config", _legacy_pure(n)) for n in CONFIGS
    ]
    out.append(Case("config.legacy_pydantic.invalid", "config", _legacy_invalid))
    out.append(Case("config.legacy_pydantic.schemas", "config", _legacy_schemas))
    out.append(Case("config.legacy_pydantic.submodules", "config", _legacy_submodules))
    out.append(
        Case(
            "config.legacy_pydantic.wire",
            "config",
            _legacy_wire,
            BOTH,
            replies=[ok("chat_completion")],
        )
    )
    return out
