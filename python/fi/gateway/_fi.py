"""`Gateway` / `AsyncGateway`: the AgentCC clients with Future AGI defaults.

The gateway authenticates with its own virtual keys (``sk-agentcc-*``), not with
the platform's FI_API_KEY / FI_SECRET_KEY pair, so it reads its own variables:

    FI_GATEWAY_API_KEY   (fallback: AGENTCC_API_KEY)
    FI_GATEWAY_URL       (fallback: AGENTCC_BASE_URL, then the hosted gateway)

Managing gateways (keys, providers, logs, analytics) is a platform API and lives
on ``fi.Client().gateway``; this module is the data plane only.
"""

from __future__ import annotations

import os
from typing import Any

from fi.gateway._client import AgentCC, AsyncAgentCC

DEFAULT_GATEWAY_URL = "https://gateway.futureagi.com"


def _resolve(api_key: str | None, base_url: str | None) -> tuple[str | None, str]:
    api_key = api_key or os.environ.get("FI_GATEWAY_API_KEY") or os.environ.get("AGENTCC_API_KEY")
    base_url = (
        base_url
        or os.environ.get("FI_GATEWAY_URL")
        or os.environ.get("AGENTCC_BASE_URL")
        or DEFAULT_GATEWAY_URL
    ).rstrip("/")
    # Resources already add /v1/...; accept the OpenAI-style ".../v1" URL too,
    # which the agentcc README shows and would otherwise call /v1/v1/...
    if base_url.endswith("/v1"):
        base_url = base_url[: -len("/v1")]
    return api_key, base_url


class Gateway(AgentCC):
    """OpenAI-compatible client for the Future AGI gateway (Agent Command Center).

    Usage::

        from fi.gateway import Gateway

        gw = Gateway()  # FI_GATEWAY_API_KEY, FI_GATEWAY_URL
        reply = gw.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
        )
    """

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, **kwargs: Any) -> None:
        api_key, base_url = _resolve(api_key, base_url)
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)


class AsyncGateway(AsyncAgentCC):
    """Async version of :class:`Gateway`."""

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, **kwargs: Any) -> None:
        api_key, base_url = _resolve(api_key, base_url)
        super().__init__(api_key=api_key, base_url=base_url, **kwargs)
