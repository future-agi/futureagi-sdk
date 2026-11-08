"""Destination validation shared by gateway clients and direct HTTP helpers."""

from __future__ import annotations

import ipaddress
import warnings
from urllib.parse import parse_qsl, urlsplit

from fi.gateway._deprecation import AgentCCDeprecationWarning
from fi.gateway._exceptions import AgentCCError

_CREDENTIAL_QUERY_NAMES = frozenset({"key", "api_key", "token", "access_token"})


def _origin(url: str) -> tuple[str, str, int]:
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.fragment or "\\" in url or any(ord(c) < 32 for c in url)
        ):
            raise ValueError
        if any(
            name.lower() in _CREDENTIAL_QUERY_NAMES
            for name, _ in parse_qsl(parsed.query, keep_blank_values=True)
        ):
            raise AgentCCError("Gateway URL must not contain credential query parameters.")
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "https" else 80
        return parsed.scheme, parsed.hostname.lower(), port
    except ValueError:
        raise AgentCCError("Gateway URL must be an absolute HTTP(S) URL without userinfo or fragment.") from None


def validate_destination(
    base_url: str, url: str, *,
    warned_origins: set[tuple[str, str, int]] | None = None,
    warn_cleartext: bool = True,
) -> None:
    """Reject cross-origin requests; warn about cleartext outside loopback.

    Never resolves a hostname or reads a response to choose a destination.
    A client supplies its own warning set, independent of Python's warning filter.
    Settings-only validation can defer the warning until credentials are used.
    """
    origin = _origin(base_url)
    target = _origin(url)
    if target != origin:
        raise AgentCCError("Gateway requests must use the explicitly configured origin.")
    scheme, host, _ = target
    if scheme == "https":
        return
    loopback = host == "localhost"
    try:
        loopback = loopback or ipaddress.ip_address(host).is_loopback
    except ValueError:
        pass
    if not loopback and warn_cleartext and (warned_origins is None or target not in warned_origins):
        _, host, port = target
        authority = f"[{host}]" if ":" in host else host
        if port != 80:
            authority += f":{port}"
        warnings.warn(
            "futureagi: sending gateway credentials in cleartext over HTTP to "
            f"http://{authority}. Use HTTPS; plain HTTP outside loopback will be "
            "rejected in a future major release.",
            AgentCCDeprecationWarning,
            stacklevel=3,
        )
        if warned_origins is not None:
            warned_origins.add(target)
