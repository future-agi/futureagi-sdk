"""Gateway settings and the guard on the platform FI key pair.

Keys: argument, FI_GATEWAY_API_KEY, AGENTCC_API_KEY.
Origins: argument, FI_GATEWAY_BASE_URL, FI_GATEWAY_URL, AGENTCC_BASE_URL.
AgentCC has no implicit origin; only Gateway/AsyncGateway use the hosted default.
Conflicting environment values log variable names, never values.
"""

from __future__ import annotations

import logging
import os

from fi.gateway._exceptions import AgentCCError

logger = logging.getLogger("fi.gateway")
KEY_ENV = ("FI_GATEWAY_API_KEY", "AGENTCC_API_KEY")
URL_ENV = ("FI_GATEWAY_BASE_URL", "FI_GATEWAY_URL", "AGENTCC_BASE_URL")
FI_KEY_PAIR = ("FI_API_KEY", "FI_SECRET_KEY")
_KEY_PAGE = "the Keys page of the Agent Command Center in the Future AGI Console"


def from_env(names: tuple[str, ...]) -> str:
    """Return the first nonempty variable, logging names on conflicts."""
    present = [(name, os.environ.get(name) or "") for name in names]
    present = [(name, value) for name, value in present if value]
    if not present:
        return ""
    if len({value for _, value in present}) > 1:
        logger.warning(
            "%s are set to different values; using %s",
            ", ".join(name for name, _ in present), present[0][0],
        )
    return present[0][1]


def _bare(key: str) -> str:
    key = key.strip()
    if key[:7].lower() == "bearer ":
        key = key[7:].strip()
    return key


def guard_fi_key_pair(api_key: str) -> None:
    """Refuse either platform key, including whitespace/Bearer variants."""
    bare = _bare(api_key)
    for name in FI_KEY_PAIR:
        value = os.environ.get(name)
        if value and _bare(value) and bare == _bare(value):
            raise AgentCCError(
                f"The gateway key equals {name} from the environment. fi.gateway "
                "authenticates with a gateway virtual key and never sends the Future AGI "
                f"API key pair; create a virtual key on {_KEY_PAGE} and pass it as "
                "api_key= or FI_GATEWAY_API_KEY."
            )


def env_api_key() -> str:
    """Released environment lookup (never falls back to platform credentials)."""
    return from_env(KEY_ENV)


def env_base_url() -> str:
    """Released lookup, with FI_GATEWAY_BASE_URL taking highest precedence."""
    return from_env(URL_ENV)


def resolve_wrapper_settings(
    api_key: str | None, base_url: str | None,
) -> tuple[str | None, str]:
    """No-I/O settings for Gateway, AsyncGateway and their raw request helper."""
    from fi.gateway._constants import AGENTCC_GATEWAY_URL
    from fi.gateway._http_security import validate_destination

    origin = clean_base_url(base_url or env_base_url() or AGENTCC_GATEWAY_URL)
    validate_destination(origin, origin, warn_cleartext=False)
    return api_key or env_api_key() or None, origin


def resolve_api_key(api_key: str | None) -> str:
    resolved = api_key or env_api_key()
    if not resolved:
        raise AgentCCError(
            "api_key is required: pass api_key= or set FI_GATEWAY_API_KEY "
            "(AGENTCC_API_KEY is still read). It is a gateway virtual key from "
            f"{_KEY_PAGE}, not your FI_API_KEY."
        )
    guard_fi_key_pair(resolved)
    return resolved


def normalize_base_url(base_url: str) -> str:
    """Drop trailing slashes and one /v1 (resources supply /v1 themselves)."""
    url = base_url.rstrip("/")
    if url.endswith("/v1"):
        url = url[:-len("/v1")].rstrip("/")
    return url


def clean_base_url(url: str) -> str:
    return normalize_base_url(url or "")


def resolve_base_url(base_url: str | None) -> str:
    resolved = base_url or env_base_url()
    if not resolved:
        raise AgentCCError(
            "base_url is required: pass base_url= or set FI_GATEWAY_BASE_URL "
            "(FI_GATEWAY_URL and AGENTCC_BASE_URL are also read) to your gateway's "
            "origin. There is no default, so a key is never sent to a gateway "
            "you did not name."
        )
    return normalize_base_url(resolved)
