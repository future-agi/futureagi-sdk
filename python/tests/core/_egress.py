"""The no-egress guard for the platform test packages.

``FI_BASE_URL`` defaults to production, so a stray test would otherwise reach it. Every test in
``tests/core`` and ``tests/platform`` runs with ``FI_BASE_URL`` and ``FI_PLATFORM_BASE_URL`` set to
``http://127.0.0.1:9`` (nothing listens there), no keys in the environment, a login file that does
not exist, and sockets that refuse any address but loopback. A refused attempt raises at once and is
counted, so a test that tried to leave the machine fails even if it caught the error.
"""

from __future__ import annotations

import ipaddress
import socket
from typing import Any

import pytest

LOOPBACK_NAMES = {"localhost", "127.0.0.1", "::1"}
ATTEMPTS: list[str] = []


def _loopback(host: Any) -> bool:
    if not isinstance(host, str):
        return False
    if host in LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host.split("%")[0]).is_loopback
    except ValueError:
        return False


def install(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    for name in (
        "FI_API_KEY",
        "FI_SECRET_KEY",
        "FI_PLATFORM_TOKEN",
        "FI_WORKSPACE_ID",
        "FI_ORGANIZATION_ID",
        "FI_ALLOW_CUSTOM_PLATFORM_URL",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "ALL_PROXY",
        "https_proxy",
        "http_proxy",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("FI_PLATFORM_BASE_URL", "http://127.0.0.1:9/omega/api")
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "no-login.json"))
    real_connect = socket.socket.connect
    real_getaddrinfo = socket.getaddrinfo

    def connect(self: socket.socket, address: Any) -> Any:
        host = address[0] if isinstance(address, tuple) else address
        if self.family in (socket.AF_INET, socket.AF_INET6) and not _loopback(host):
            ATTEMPTS.append(str(host))
            raise ConnectionRefusedError(f"no-egress guard: refused a connection to {host}")
        return real_connect(self, address)

    def getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        name = host.decode() if isinstance(host, bytes) else host
        if name is not None and not _loopback(name):
            ATTEMPTS.append(str(name))
            raise socket.gaierror(f"no-egress guard: refused to resolve {name}")
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)


def assert_no_attempts() -> None:
    attempts = list(ATTEMPTS)
    ATTEMPTS.clear()
    assert not attempts, f"a test tried to leave the machine: {attempts}"
