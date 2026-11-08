"""The egress guard for the Python runner: the same rule as classify.mjs.

    guard = EgressGuard(allow=["rig-host"])
    client = httpx.Client(transport=guard.transport())          # wraps httpx's own transport
    aclient = httpx.AsyncClient(transport=guard.async_transport())
    exporter = guard.wrap_exporter(span_exporter, endpoint)

The first request to a host that is not allowed trips the guard: it is refused before the inner
transport sees it (so no socket and no DNS lookup), recorded, and ``assert_not_tripped()`` fails
the run. Hosts in the Future AGI production zone are refused even when listed.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import urlsplit

PRODUCTION_ZONE = "futureagi.com"
NAMED_PRODUCTION_HOSTS = (
    "api.futureagi.com",
    "app.futureagi.com",
    "gateway.futureagi.com",
)
_LOOPBACK_V4 = re.compile(r"^(::ffff:)?127(\.\d{1,3}){3}$")


class EgressBlockedError(Exception):
    def __init__(self, host: str, reason: str) -> None:
        super().__init__(f"egress guard: refused {host or '(no host)'} ({reason})")
        self.host = host
        self.reason = reason


def normalize_host(host: Any) -> str:
    value = str(host or "").strip().lower()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    if value.endswith("."):
        value = value[:-1]
    return value


def is_production_host(host: Any) -> bool:
    value = normalize_host(host)
    return value == PRODUCTION_ZONE or value.endswith("." + PRODUCTION_ZONE)


def is_loopback_host(host: Any) -> bool:
    value = normalize_host(host)
    if value in ("localhost", "::1", "0:0:0:0:0:0:0:1") or value.endswith(".localhost"):
        return True
    return bool(_LOOPBACK_V4.match(value))


def host_of(url: Any) -> str:
    try:
        return normalize_host(urlsplit(str(url)).hostname or "")
    except ValueError:
        return ""


def classify_host(host: Any, allowlist: Iterable[str] = ()) -> tuple[bool, str]:
    value = normalize_host(host)
    if not value:
        return False, "no host"
    if is_production_host(value):
        return False, "production Future AGI host"
    if is_loopback_host(value):
        return True, "loopback"
    if value in {normalize_host(item) for item in allowlist}:
        return True, "allowlisted"
    return False, "not on the run's allowlist"


def require_endpoints(
    endpoints: dict[str, str | None], allow: Iterable[str] = ()
) -> list[str]:
    """Refuse to start when any endpoint is unset or names a refused host."""
    problems = []
    for name, url in endpoints.items():
        if not url:
            problems.append(f"{name} is unset")
            continue
        allowed, reason = classify_host(host_of(url), allow)
        if not allowed:
            problems.append(f"{name} names {host_of(url) or url} ({reason})")
    if problems:
        raise RuntimeError("refusing to start: " + "; ".join(problems))
    return [host_of(url) for url in endpoints.values() if url]


class EgressGuard:
    def __init__(self, allow: Iterable[str] = ()) -> None:
        self.allow = list(allow)
        self.trips: list[dict[str, str]] = []
        self.reached: list[str] = []

    def check(self, host: str, via: str) -> None:
        allowed, reason = classify_host(host, self.allow)
        if not allowed:
            self.trips.append(
                {
                    "host": host,
                    "reason": reason,
                    "via": via,
                    "at": datetime.now(timezone.utc).isoformat(),
                }
            )
            raise EgressBlockedError(host, reason)
        if host not in self.reached:
            self.reached.append(host)

    @property
    def tripped(self) -> bool:
        return bool(self.trips)

    def assert_not_tripped(self) -> None:
        if self.trips:
            raise EgressBlockedError(
                self.trips[0]["host"], f"{len(self.trips)} refused request(s)"
            )

    def transport(self, inner: Any = None) -> Any:
        import httpx

        guard = self
        base = inner if inner is not None else httpx.HTTPTransport()

        class GuardedTransport(httpx.BaseTransport):
            def handle_request(self, request: "httpx.Request") -> "httpx.Response":
                guard.check(normalize_host(request.url.host), "httpx")
                return base.handle_request(request)

            def close(self) -> None:
                base.close()

        return GuardedTransport()

    def async_transport(self, inner: Any = None) -> Any:
        import httpx

        guard = self
        base = inner if inner is not None else httpx.AsyncHTTPTransport()

        class AsyncGuardedTransport(httpx.AsyncBaseTransport):
            async def handle_async_request(
                self, request: "httpx.Request"
            ) -> "httpx.Response":
                guard.check(normalize_host(request.url.host), "httpx-async")
                return await base.handle_async_request(request)

            async def aclose(self) -> None:
                await base.aclose()

        return AsyncGuardedTransport()

    def wrap_exporter(self, exporter: Any, endpoint: str) -> Any:
        guard = self
        guard.check(host_of(endpoint), "exporter")

        class GuardedExporter:
            def export(self, spans: Any) -> Any:
                guard.check(host_of(endpoint), "exporter")
                return exporter.export(spans)

            def shutdown(self) -> Any:
                return getattr(exporter, "shutdown", lambda: None)()

        return GuardedExporter()

    def receipt(self) -> dict[str, Any]:
        return {
            "armed": True,
            "allowlist": list(self.allow),
            "reached": list(self.reached),
            "trips": list(self.trips),
        }
