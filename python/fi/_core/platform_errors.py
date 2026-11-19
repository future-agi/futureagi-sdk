"""Response-evidence classification for sync and async platform calls.

Console membership comes from generated operation families, never handwritten URL paths.
The shared HTTP executor also serves FA management, whose gateway family is not Console.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Mapping, Optional

import httpx

from fi._core.errors import api_error, is_platform_error
from fi._core.origins import PlatformOrigin, display_host
from fi._core.policy import OperationSpec
from fi._core.redact import redact_value, scrub_text, scrub_value
from fi._core.transport import MAX_ERROR_BODY
from fi.errors import FutureAGIAPIError

# x-omega-sdk families in the pinned Console contract and connector supplements.
_CONSOLE_FAMILIES = frozenset({"deployments", "platform", "runs", "connectors"})


def platform_status_error(
    op: OperationSpec,
    origin: PlatformOrigin,
    response: httpx.Response,
    raw: bytes,
    *,
    complete: bool,
    secrets: list[str],
    idempotency_key: Optional[str],
    error_scrubber: Optional[Callable[[Any, list[str]], Any]] = None,
) -> FutureAGIAPIError:
    """Map the actual response; only a complete non-envelope Console 404 gets a host hint."""
    text = raw[:MAX_ERROR_BODY].decode("utf-8", "replace")
    platform_error = False
    try:
        # Classify before scrubbing: a secret may equal a wire key or error code.
        decoded = json.loads(text) if text.strip() else None
        platform_error = is_platform_error(decoded)
        body = (error_scrubber or scrub_value)(decoded, secrets)
    except ValueError:
        body = None  # HTML (including FA's default Django 404) is never echoed
    unavailable = None
    headers: Mapping[str, str] = response.headers
    # Without EOF, a missing envelope may simply be a capped or interrupted EE body.
    if response.status_code == 404 and op.family in _CONSOLE_FAMILIES and complete and not platform_error:
        if origin.source == "derived":
            hint = "for self-hosted Enterprise, set FI_PLATFORM_BASE_URL to your Console API origin."
        elif origin.source == "login":
            hint = "for self-hosted Enterprise, check the Console API URL in your saved login."
        else:
            hint = ("for self-hosted Enterprise, check your configured Console API URL "
                    "(FI_PLATFORM_BASE_URL or platform_base_url).")
        unavailable = scrub_text(
            f"The Console API is not available at {display_host(origin.url)}. "
            "Hosted Future AGI does not support Console access through the SDK in this release; " + hint,
            secrets,
        )
        # Prefer over-scrubbed metadata to reflecting even a short credential. Legacy
        # errors retain their existing request IDs; only the new diagnostic is affected.
        headers = {k: scrub_text(v, secrets, min_length=1) for k, v in response.headers.items()}
    return api_error(
        response.status_code,
        redact_value(body),
        headers,
        operation=op.name,
        family=op.family,
        idempotency_key=idempotency_key,
        body=body,
        console_unavailable_message=unavailable,
    )
