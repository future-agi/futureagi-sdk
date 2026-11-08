"""Destination validation shared by gateway clients and direct HTTP helpers."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

from fi.gateway._exceptions import AgentCCError


def _origin(url: str) -> tuple[str, str, int]:
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.fragment or "\\" in url or any(ord(c) < 32 for c in url)
        ):
            raise ValueError
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "https" else 80
        return parsed.scheme, parsed.hostname.lower(), port
    except ValueError:
        raise AgentCCError("Gateway URL must be an absolute HTTP(S) URL without userinfo or fragment.") from None


def validate_destination(base_url: str, url: str) -> None:
    """Reject cross-origin requests and cleartext credentials outside loopback.

    Never resolves a hostname or reads a response to choose a destination.
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
    if not loopback:
        raise AgentCCError("Gateway credentials require HTTPS except on a loopback host.")
