"""Internal utility functions for the AgentCC SDK."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from typing import Any

import httpx

from fi.gateway._constants import DEFAULT_TIMEOUT


def parse_timeout(timeout: float | Any | None) -> httpx.Timeout:
    """Convert a user-supplied timeout value to an httpx.Timeout.

    Args:
        timeout: A float (applied uniformly), a Timeout dataclass, or None for default.
    """
    if timeout is None:
        return httpx.Timeout(DEFAULT_TIMEOUT)
    if isinstance(timeout, (int, float)):
        return httpx.Timeout(float(timeout))
    # Timeout dataclass from _base_client
    if hasattr(timeout, "connect"):
        return httpx.Timeout(
            connect=timeout.connect,
            read=timeout.read,
            write=timeout.write,
            pool=timeout.pool,
        )
    return httpx.Timeout(DEFAULT_TIMEOUT)


def redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Return a copy of *headers* with the Authorization value redacted."""
    result: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() == "authorization":
            # Show "Bearer sk-...XXXX" pattern
            if len(value) > 14:
                result[key] = value[:10] + "..." + value[-4:]
            else:
                result[key] = "***"
        else:
            result[key] = value
    return result


def serialize_agentcc_param(key: str, value: Any) -> str:
    """Serialize a AgentCC parameter value to a header string."""
    if key == "request_metadata" and isinstance(value, dict):
        return json.dumps(value, separators=(",", ":"))
    if key == "cache_force_refresh" and isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def return_raw_request(
    *,
    model: str,
    messages: list[dict[str, Any]],
    base_url: str = "https://gateway.futureagi.com",
    **kwargs: Any,
) -> dict[str, Any]:
    """Return the raw HTTP request that would be sent, without sending it.

    Useful for debugging and inspecting what the SDK will send.

    Returns:
        Dict with ``method``, ``url``, ``headers`` (redacted), and ``body``.
    """
    from fi.gateway._constants import NOT_GIVEN, __version__

    body: dict[str, Any] = {"model": model, "messages": messages}
    body.update({k: v for k, v in kwargs.items() if v is not NOT_GIVEN})

    return {
        "method": "POST",
        "url": f"{base_url.rstrip('/')}/v1/chat/completions",
        "headers": {
            "Content-Type": "application/json",
            "User-Agent": f"agentcc-python/{__version__}",
            "Authorization": "Bearer [REDACTED]",
        },
        "body": body,
    }


def health_check(
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Quick validation that the gateway/model endpoint is reachable.

    Args:
        model: If provided, send a minimal completion request to verify the model works.
        api_key: API key. Falls back to ``AGENTCC_API_KEY`` env var.
        base_url: Base URL. Falls back to ``AGENTCC_BASE_URL`` env var.
        timeout: Request timeout in seconds (default 10).

    Returns:
        Dict with ``status`` ('ok' or 'error'), ``latency_ms``, and optionally ``error``.
    """
    import os

    resolved_key = api_key or os.environ.get("AGENTCC_API_KEY", "")
    resolved_url = base_url or os.environ.get("AGENTCC_BASE_URL", "")
    if not resolved_url:
        return {"status": "error", "error": "base_url is required"}

    headers: dict[str, str] = {}
    if resolved_key:
        headers["Authorization"] = f"Bearer {resolved_key}"

    try:
        start = time.monotonic()
        if model is None:
            # Just check /health endpoint
            response = httpx.get(
                f"{resolved_url.rstrip('/')}/health",
                headers=headers,
                timeout=timeout,
            )
        else:
            # Send a minimal completion request
            response = httpx.post(
                f"{resolved_url.rstrip('/')}/v1/chat/completions",
                headers={**headers, "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1,
                },
                timeout=timeout,
            )
        elapsed_ms = (time.monotonic() - start) * 1000

        if response.status_code < 400:
            return {"status": "ok", "latency_ms": round(elapsed_ms, 1)}
        else:
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "latency_ms": round(elapsed_ms, 1),
            }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def check_valid_key(api_key: str, base_url: str) -> bool:
    """Check if an API key is valid by hitting the gateway models endpoint.

    Returns ``True`` if the key authenticates successfully, ``False`` otherwise.
    """
    try:
        response = httpx.get(
            f"{base_url.rstrip('/')}/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        return response.status_code == 200
    except Exception:
        return False
