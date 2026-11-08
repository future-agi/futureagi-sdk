"""Registry for health."""
from __future__ import annotations

from fi.evals.framework.resilience.health import (
    Dict, EventCallback, HealthCheckConfig, HealthCheckFunc, HealthCheckResult, HealthChecker,
    HealthStatus, List, Optional, threading,
)

class HealthRegistry:
    """
    Registry for managing multiple health checkers.

    Example:
        registry = HealthRegistry()
        registry.register("api", lambda: api.ping())
        registry.register("db", lambda: db.is_connected())

        registry.start_all()

        # Get overall health
        overall = registry.get_overall_status()

        registry.stop_all()
    """

    def __init__(
        self,
        default_config: Optional[HealthCheckConfig] = None,
        event_callback: Optional[EventCallback] = None,
    ):
        """
        Initialize health registry.

        Args:
            default_config: Default config for registered checkers
            event_callback: Callback for all health events
        """
        self.default_config = default_config or HealthCheckConfig()
        self.event_callback = event_callback

        self._checkers: Dict[str, HealthChecker] = {}
        self._lock = threading.RLock()  # RLock for reentrant locking

    def register(
        self,
        name: str,
        check_func: HealthCheckFunc,
        config: Optional[HealthCheckConfig] = None,
    ) -> HealthChecker:
        """
        Register a new health checker.

        Args:
            name: Name for the health checker
            check_func: Function that returns True if healthy
            config: Optional config override

        Returns:
            The registered HealthChecker
        """
        with self._lock:
            if name in self._checkers:
                raise ValueError(f"Health checker '{name}' already registered")

            checker = HealthChecker(
                name=name,
                check_func=check_func,
                config=config or self.default_config,
                event_callback=self.event_callback,
            )
            self._checkers[name] = checker
            return checker

    def unregister(self, name: str) -> None:
        """Unregister a health checker."""
        with self._lock:
            if name in self._checkers:
                self._checkers[name].stop()
                del self._checkers[name]

    def get(self, name: str) -> Optional[HealthChecker]:
        """Get a health checker by name."""
        with self._lock:
            return self._checkers.get(name)

    def start_all(self) -> None:
        """Start all registered health checkers."""
        with self._lock:
            for checker in self._checkers.values():
                checker.start()

    def stop_all(self, timeout: float = 5.0) -> None:
        """Stop all registered health checkers."""
        with self._lock:
            for checker in self._checkers.values():
                checker.stop(timeout)

    def check_all_now(self) -> Dict[str, HealthCheckResult]:
        """Perform immediate health check on all registered checkers."""
        results = {}
        with self._lock:
            for name, checker in self._checkers.items():
                results[name] = checker.check_now()
        return results

    def get_overall_status(self) -> HealthStatus:
        """
        Get overall health status.

        Returns:
            HEALTHY if all healthy
            DEGRADED if any degraded but none unhealthy
            UNHEALTHY if any unhealthy
            UNKNOWN if no checkers or all unknown
        """
        with self._lock:
            if not self._checkers:
                return HealthStatus.UNKNOWN

            statuses = [c.status for c in self._checkers.values()]

            if all(s == HealthStatus.UNKNOWN for s in statuses):
                return HealthStatus.UNKNOWN

            if any(s == HealthStatus.UNHEALTHY for s in statuses):
                return HealthStatus.UNHEALTHY

            if any(s == HealthStatus.DEGRADED for s in statuses):
                return HealthStatus.DEGRADED

            if all(s == HealthStatus.HEALTHY for s in statuses):
                return HealthStatus.HEALTHY

            return HealthStatus.DEGRADED

    def get_all_stats(self) -> Dict[str, dict]:
        """Get statistics for all health checkers."""
        with self._lock:
            return {name: checker.get_stats() for name, checker in self._checkers.items()}

    def get_summary(self) -> dict:
        """Get summary of all health checkers."""
        with self._lock:
            return {
                "overall_status": self.get_overall_status().value,
                "checker_count": len(self._checkers),
                "healthy_count": sum(
                    1 for c in self._checkers.values() if c.status == HealthStatus.HEALTHY
                ),
                "unhealthy_count": sum(
                    1 for c in self._checkers.values() if c.status == HealthStatus.UNHEALTHY
                ),
                "degraded_count": sum(
                    1 for c in self._checkers.values() if c.status == HealthStatus.DEGRADED
                ),
                "checkers": {
                    name: checker.status.value for name, checker in self._checkers.items()
                },
            }

    @property
    def names(self) -> List[str]:
        """Get names of all registered health checkers."""
        with self._lock:
            return list(self._checkers.keys())

    def __len__(self) -> int:
        """Get number of registered health checkers."""
        with self._lock:
            return len(self._checkers)

    def __contains__(self, name: str) -> bool:
        """Check if a health checker is registered."""
        with self._lock:
            return name in self._checkers
