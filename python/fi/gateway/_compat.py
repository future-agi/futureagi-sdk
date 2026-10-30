"""OpenAI compatibility layer.

Since AgentCC already exposes the same ``client.chat.completions.create()``
API surface as the OpenAI SDK, "patching" is simply creating a new AgentCC
client.  This function exists for discoverability and migration guides.
"""

from __future__ import annotations

from typing import Any


def patch_openai(
    client: Any = None,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    **kwargs: Any,
) -> Any:
    """Create a AgentCC client that is a drop-in replacement for OpenAI.

    Args:
        client: Ignored. Accepted for API compatibility with migration guides.
        api_key: AgentCC API key (or set ``AGENTCC_API_KEY`` env var).
        base_url: AgentCC gateway URL (or set ``AGENTCC_BASE_URL`` env var).
        **kwargs: Passed to ``AgentCC()``.

    Returns:
        A ``AgentCC`` client instance.

    Example::

        from fi.gateway import patch_openai

        client = patch_openai(api_key="sk-agentcc-xxx", base_url="https://gw.example.com")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )
    """
    from fi.gateway._client import AgentCC

    return AgentCC(api_key=api_key, base_url=base_url, **kwargs)
