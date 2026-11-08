"""`Gateway` / `AsyncGateway`: the AgentCC clients with Future AGI defaults.

The gateway authenticates with its own virtual keys (``sk-agentcc-*``), not with
the platform's FI_API_KEY / FI_SECRET_KEY pair, so it reads its own variables:

    FI_GATEWAY_API_KEY   (fallback: AGENTCC_API_KEY)
    FI_GATEWAY_BASE_URL  (fallback: FI_GATEWAY_URL, AGENTCC_BASE_URL, hosted gateway)

Managing gateways (keys, providers, logs, analytics) is a platform API and lives
on ``fi.Client().gateway`` (the generated platform client, PR #35); this module is
the data plane only.
"""

from __future__ import annotations

from typing import Any

from fi.gateway._client import AgentCC, AsyncAgentCC
from fi.gateway._env import resolve_wrapper_settings

DEFAULT_GATEWAY_URL = "https://gateway.futureagi.com"


def _resolve(api_key: str | None, base_url: str | None) -> tuple[str | None, str]:
    import warnings

    try:
        warnings.warn(
            "Gateway and AsyncGateway are deprecated released compatibility adapters; "
            "AgentCC and AsyncAgentCC require an explicit gateway origin.",
            DeprecationWarning, stacklevel=3,
        )
        return resolve_wrapper_settings(api_key, base_url)
    finally:
        api_key = None


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
        try:
            api_key, base_url = _resolve(api_key, base_url)
            super().__init__(api_key=api_key, base_url=base_url, **kwargs)
        finally:
            api_key, kwargs = None, {}


class AsyncGateway(AsyncAgentCC):
    """Async version of :class:`Gateway`."""

    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, **kwargs: Any) -> None:
        try:
            api_key, base_url = _resolve(api_key, base_url)
            super().__init__(api_key=api_key, base_url=base_url, **kwargs)
        finally:
            api_key, kwargs = None, {}
