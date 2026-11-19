"""
ResilientBackend wrapper for adding resilience to any backend.

Combines circuit breaker, rate limiting, retry, and fallback capabilities.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

from fi.evals.framework.backends.base import (
    Backend,
    BackendConfig,
    TaskHandle,
    TaskStatus,
)
from .circuit_breaker import CircuitBreaker
from .degradation import FallbackChain
from .health import HealthChecker, HealthRegistry
from .rate_limiter import TokenBucketRateLimiter
from .retry import RetryHandler
from .types import (
    CircuitBreakerConfig,
    CircuitOpenError,
    DegradationConfig,
    EventCallback,
    HealthCheckConfig,
    RateLimitConfig,
    RateLimitExceededError,
    ResilienceConfig,
    ResilienceEvent,
    ResilienceEventType,
    RetryConfig,
    RetryExhaustedError,
)

T = TypeVar("T")
logger = logging.getLogger(__name__)


@dataclass
class ResilientBackendConfig(BackendConfig):
    """Configuration for ResilientBackend wrapper."""

    resilience: ResilienceConfig = field(default_factory=ResilienceConfig)


from ._wrapper_resilient_backend_setup_components import _ResilientBackendSetupComponentsMethods
from ._wrapper_resilient_backend_reset import _ResilientBackendResetMethods

class ResilientBackend(
    _ResilientBackendSetupComponentsMethods,
    _ResilientBackendResetMethods,
    Backend,
):
    """
    Wraps any backend with resilience features.

    Applies the following protections in order:
    1. Rate limiting - prevent overwhelming the backend
    2. Circuit breaker - fail fast if backend is unhealthy
    3. Retry - retry transient failures
    4. Fallback - use alternative if all else fails

    Example:
        from fi.evals.framework.backends import ThreadPoolBackend
        from fi.evals.framework.resilience import (
            ResilientBackend,
            CircuitBreakerConfig,
            RateLimitConfig,
            ResilienceConfig,
        )

        config = ResilienceConfig(
            circuit_breaker=CircuitBreakerConfig(failure_threshold=5),
            rate_limit=RateLimitConfig(requests_per_second=10),
        )

        underlying = ThreadPoolBackend()
        backend = ResilientBackend(underlying, config)

        # Use normally - resilience is transparent
        handle = backend.submit(my_func, args=(1, 2))
        result = backend.get_result(handle)
    """

    name: str = "resilient"

    def __init__(
        self,
        underlying: Backend,
        config: Optional[ResilienceConfig] = None,
        fallback_backend: Optional[Backend] = None,
        event_callback: Optional[EventCallback] = None,
    ):
        """
        Initialize ResilientBackend wrapper.

        Args:
            underlying: The backend to wrap
            config: Resilience configuration
            fallback_backend: Optional fallback backend
            event_callback: Callback for resilience events
        """
        self.underlying = underlying
        self.config = config or ResilienceConfig()
        self.fallback_backend = fallback_backend
        self.event_callback = event_callback
        self.name = f"resilient({underlying.name})"

        # Initialize components based on config
        self._rate_limiter: Optional[TokenBucketRateLimiter] = None
        self._circuit_breaker: Optional[CircuitBreaker] = None
        self._retry_handler: Optional[RetryHandler] = None
        self._fallback_chain: Optional[FallbackChain] = None
        self._health_checker: Optional[HealthChecker] = None

        self._setup_components()


    # === Component access for testing/monitoring ===


def wrap_backend(
    backend: Backend,
    circuit_breaker: Optional[CircuitBreakerConfig] = None,
    rate_limit: Optional[RateLimitConfig] = None,
    retry: Optional[RetryConfig] = None,
    degradation: Optional[DegradationConfig] = None,
    health_check: Optional[HealthCheckConfig] = None,
    fallback_backend: Optional[Backend] = None,
    event_callback: Optional[EventCallback] = None,
) -> ResilientBackend:
    """
    Convenience function to wrap a backend with resilience.

    Example:
        backend = wrap_backend(
            ThreadPoolBackend(),
            circuit_breaker=CircuitBreakerConfig(failure_threshold=5),
            rate_limit=RateLimitConfig(requests_per_second=10),
        )

    Args:
        backend: The backend to wrap
        circuit_breaker: Circuit breaker configuration
        rate_limit: Rate limit configuration
        retry: Retry configuration
        degradation: Degradation configuration
        health_check: Health check configuration
        fallback_backend: Optional fallback backend
        event_callback: Callback for events

    Returns:
        ResilientBackend wrapping the original
    """
    config = ResilienceConfig(
        circuit_breaker=circuit_breaker,
        rate_limit=rate_limit,
        retry=retry,
        degradation=degradation,
        health_check=health_check,
    )

    return ResilientBackend(
        underlying=backend,
        config=config,
        fallback_backend=fallback_backend,
        event_callback=event_callback,
    )
