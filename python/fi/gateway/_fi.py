"""`Gateway` / `AsyncGateway`: the AgentCC clients with Future AGI defaults.

The gateway authenticates with its own virtual keys (``sk-agentcc-*``), not with
the platform's FI_API_KEY / FI_SECRET_KEY pair, so it reads its own variables:

    FI_GATEWAY_API_KEY   (fallback: AGENTCC_API_KEY)
    FI_GATEWAY_URL       (fallback: AGENTCC_BASE_URL, then the hosted gateway)

Managing gateways (keys, providers, logs, analytics) is a platform API and lives
on ``fi.Client().gateway`` (the generated platform client, PR #35); this module is
the data plane only.
"""

from __future__ import annotations

from typing import Any

from fi.gateway._client import AgentCC, AsyncAgentCC
from fi.gateway._env import clean_base_url, env_api_key, env_base_url

DEFAULT_GATEWAY_URL = "https://gateway.futureagi.com"


def _resolve(api_key: str | None, base_url: str | None) -> tuple[str | None, str]:
    return api_key or env_api_key() or None, clean_base_url(base_url or env_base_url() or DEFAULT_GATEWAY_URL)


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
