"""ResilientBackend reset operations."""
from __future__ import annotations


class _ResilientBackendResetMethods:
    __slots__ = ()

    def reset(self) -> None:
        """Reset all resilience components."""
        if self._rate_limiter:
            self._rate_limiter.reset()

        if self._circuit_breaker:
            self._circuit_breaker.reset()

        if self._health_checker:
            self._health_checker.reset()
