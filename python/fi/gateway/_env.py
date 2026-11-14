"""Where the gateway client reads its settings from.

The gateway authenticates with its own virtual keys (``sk-agentcc-*``), so it has
its own variables; the ``AGENTCC_*`` names still work for existing agentcc users.
"""

from __future__ import annotations

import os


def env_api_key() -> str:
    return os.environ.get("FI_GATEWAY_API_KEY") or os.environ.get("AGENTCC_API_KEY") or ""


def env_base_url() -> str:
    return os.environ.get("FI_GATEWAY_URL") or os.environ.get("AGENTCC_BASE_URL") or ""


def clean_base_url(url: str) -> str:
    """Resources add ``/v1/...`` themselves, so an OpenAI-style ``.../v1`` base URL
    (the control plane and the agentcc README both show one) would call ``/v1/v1/...``."""
    url = (url or "").rstrip("/")
    return url[: -len("/v1")] if url.endswith("/v1") else url
