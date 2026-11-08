"""Arguments for a stock OpenAI SDK client pointed at the gateway: ``openai_kwargs()``.

Nothing here imports ``openai``. The result always holds an explicit ``api_key``: the
OpenAI SDK falls back to ``OPENAI_API_KEY`` when none is passed, which would send the
user's OpenAI key to the gateway (critique B1).
"""

from __future__ import annotations

from typing import Any

from fi.gateway._env import resolve_api_key, resolve_base_url
from fi.gateway._gateway_config import GatewayConfig, create_headers


def openai_kwargs(
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    config: GatewayConfig | None = None,
    trace_id: str | None = None,
    session_id: str | None = None,
    session_name: str | None = None,
    session_path: str | None = None,
    metadata: dict[str, Any] | None = None,
    user_id: str | None = None,
    request_id: str | None = None,
    cache_ttl: int | None = None,
    cache_namespace: str | None = None,
    cache_force_refresh: bool | None = None,
    guardrail_policy: str | None = None,
    properties: dict[str, str] | None = None,
) -> dict[str, Any]:
    """``api_key``, ``base_url`` and ``default_headers`` for ``openai.OpenAI(**...)``.

    The key and base URL resolve as :class:`fi.gateway.AgentCC`'s do (argument, then
    ``FI_GATEWAY_*``, then ``AGENTCC_*``; the FI key pair is refused; a missing value
    raises ``AgentCCError``). ``base_url`` is the gateway origin plus ``/v1``, where the
    OpenAI SDK expects it. The other arguments become ``x-agentcc-*`` headers, as
    :func:`fi.gateway.create_headers` builds them. LangChain takes the same values::

        from openai import OpenAI
        from fi.gateway import openai_kwargs

        client = OpenAI(**openai_kwargs(session_id="s1"))
        chat = ChatOpenAI(model="gpt-4o-mini", **openai_kwargs())  # langchain_openai

    A gateway cache hit answers a ``stream=True`` request with one JSON body, which the
    OpenAI SDK's stream does not read; :class:`fi.gateway.AgentCC` handles it.

    The OpenAI SDK still reads its own ``OPENAI_ORG_ID`` and ``OPENAI_PROJECT_ID`` and
    sends them as ``OpenAI-Organization`` / ``OpenAI-Project``; unset them if those
    identifiers should not reach the gateway. ``OPENAI_API_KEY`` and ``OPENAI_BASE_URL``
    are never used, since both values are passed explicitly.
    """
    key = resolve_api_key(api_key)
    origin = resolve_base_url(base_url)
    from fi.gateway._http_security import validate_destination

    validate_destination(origin, origin)
    headers = create_headers(
        config=config,
        trace_id=trace_id,
        session_id=session_id,
        session_name=session_name,
        session_path=session_path,
        metadata=metadata,
        user_id=user_id,
        request_id=request_id,
        cache_ttl=cache_ttl,
        cache_namespace=cache_namespace,
        cache_force_refresh=cache_force_refresh,
        guardrail_policy=guardrail_policy,
        properties=properties,
    )
    return {"api_key": key, "base_url": f"{origin}/v1", "default_headers": headers}
