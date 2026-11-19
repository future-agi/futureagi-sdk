"""Plain-HTTP policy, independent of credential resolution and retry routing."""
from __future__ import annotations

import ipaddress
import os
import sys
import threading
from typing import Mapping, Optional

import httpx

from fi.errors import ConfigurationError

ALLOW_INSECURE_HTTP_ENV = "FI_ALLOW_INSECURE_HTTP"
_warned: set[tuple[str, str, int]] = set()
_lock = threading.Lock()


def _loopback(host: str) -> bool:
    """localhost, any 127.0.0.0/8 address or ::1 (the origin guard keeps its own narrower list)."""
    host = host.strip("[]").lower()  # ascii_host already removes the single trailing DNS dot
    if host == "localhost":
        return True
    try:
        address = ipaddress.ip_address(host)
        return address.is_loopback if address.version == 4 else address == ipaddress.IPv6Address("::1")
    except ValueError:
        return False


def is_insecure_http(url: httpx.URL) -> bool:
    """Plain HTTP to anything other than loopback (TypeScript's ``isInsecureHttp``)."""
    from fi._core.origins import ascii_host

    return url.scheme == "http" and not _loopback(ascii_host(url))


def check_http_security(
    url: httpx.URL,
    mode: str,
    *,
    allow_insecure_http: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> None:
    """Refuse bearer cleartext unless explicitly allowed; warn once per origin.

    Keys retain their existing host/provenance policy. This check never grants a
    host exemption or changes the destination.
    Paths and credentials are never included in warnings. Explicit False wins
    over the environment, just as it does for the separate custom-host option.
    """
    from fi._core.origins import ascii_host, display_host

    if not is_insecure_http(url):
        return
    if mode == "bearer":
        env = os.environ if environ is None else environ
        allowed = (bool(allow_insecure_http) if allow_insecure_http is not None else
                   env.get(ALLOW_INSECURE_HTTP_ENV, "").strip().lower() in ("1", "true", "yes"))
        if not allowed:
            raise ConfigurationError(
                "Refusing to send a Bearer token over nonloopback HTTP. Use HTTPS, or explicitly set "
                f"allow_insecure_http=True / {ALLOW_INSECURE_HTTP_ENV}=1 to allow cleartext credentials",
                code="insecure_http_origin",
            )
    # One notice for both modes, as in TypeScript: the per-origin budget is shared, so a bearer
    # warning must still carry the keys deprecation for later keys-mode calls to that origin.
    notice = ("credentials (API keys or a Bearer token) may be sent in cleartext. Plain-HTTP keys-mode "
              "origins are deprecated and will be refused in a future minor release; Bearer HTTP requires "
              f"allow_insecure_http / {ALLOW_INSECURE_HTTP_ENV}")
    key = (url.scheme, ascii_host(url), 80 if url.port is None else url.port)
    with _lock:
        if key in _warned:
            return
        _warned.add(key)
    sys.stderr.write(f"futureagi: insecure HTTP to {display_host(url)}: {notice}.\n")
