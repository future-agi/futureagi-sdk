"""ResilientBackend setup components operations."""
from __future__ import annotations

from fi.evals.framework.resilience.wrapper import (
    Any, Backend, Callable, CircuitBreaker, Dict, HealthChecker, List, Optional, RetryHandler, T,
    TaskHandle, TaskStatus, TokenBucketRateLimiter,
)


class _ResilientBackendSetupComponentsMethods:
    __slots__ = ()

    def _setup_components(self) -> None:
        """Initialize resilience components based on config."""
        from fi.evals.framework.resilience.wrapper import (
            CircuitBreaker, FallbackChain, HealthChecker, RetryHandler, TokenBucketRateLimiter,
        )
        # Rate limiter
        if self.config.rate_limit:
            self._rate_limiter = TokenBucketRateLimiter(
                name=self.name,
                config=self.config.rate_limit,
                event_callback=self.event_callback,
            )

        # Circuit breaker
        if self.config.circuit_breaker:
            self._circuit_breaker = CircuitBreaker(
                name=self.name,
                config=self.config.circuit_breaker,
                event_callback=self.event_callback,
            )

        # Retry handler
        if self.config.retry:
            self._retry_handler = RetryHandler(
                name=self.name,
                config=self.config.retry,
                event_callback=self.event_callback,
            )

        # Fallback chain (if fallback backend configured)
        if self.fallback_backend and self.config.degradation:
            self._fallback_chain = FallbackChain(
                name=self.name,
                config=self.config.degradation,
                event_callback=self.event_callback,
            )
            self._fallback_chain.add_fallback(
                "fallback_backend",
                lambda: None,  # Placeholder - actual fallback handled in submit
            )

        # Health checker
        if self.config.health_check:
            self._health_checker = HealthChecker(
                name=self.name,
                check_func=self._health_check,
                config=self.config.health_check,
                event_callback=self.event_callback,
            )


    def _health_check(self) -> bool:
        """Health check for the underlying backend."""
        # If circuit breaker exists, check its state
        if self._circuit_breaker:
            return self._circuit_breaker.is_closed

        # Default: assume healthy
        return True


    def submit(
        self,
        fn: Callable[..., T],
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskHandle[T]:
        """
        Submit a task with resilience protections.

        Applies rate limiting, circuit breaker, retry, and fallback.

        Args:
            fn: The function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            context: Trace context

        Returns:
            TaskHandle to track the task

        Raises:
            RateLimitExceededError: If rate limit exceeded and blocking disabled
            CircuitOpenError: If circuit breaker is open
            RetryExhaustedError: If all retries fail
        """
        from fi.evals.framework.resilience.wrapper import (
            Any, Callable, CircuitOpenError, Dict, Optional, RateLimitExceededError,
            RetryExhaustedError, T, TaskHandle,
        )
        kwargs = kwargs or {}

        def do_submit() -> TaskHandle[T]:
            """Perform the actual submission."""
            return self.underlying.submit(fn, args, kwargs, context)

        def submit_with_protections() -> TaskHandle[T]:
            """Apply all resilience protections."""
            # 1. Rate limiting
            if self._rate_limiter:
                if not self._rate_limiter.acquire():
                    raise RateLimitExceededError(
                        self.name,
                        self._rate_limiter.get_wait_time(),
                    )

            # 2. Circuit breaker
            if self._circuit_breaker:
                return self._circuit_breaker.execute(do_submit)

            return do_submit()

        def submit_with_retry() -> TaskHandle[T]:
            """Apply retry logic."""
            if self._retry_handler:
                return self._retry_handler.execute(submit_with_protections)
            return submit_with_protections()

        # 3. Retry + fallback
        try:
            return submit_with_retry()
        except (CircuitOpenError, RateLimitExceededError, RetryExhaustedError):
            # Try fallback if available
            if self.fallback_backend and self.config.degradation:
                if self.config.degradation.fallback_on_circuit_open:
                    self._emit_fallback_event("circuit_open_or_rate_limit")
                    return self.fallback_backend.submit(fn, args, kwargs, context)
            raise


    def get_result(
        self,
        handle: TaskHandle[T],
        timeout: Optional[float] = None,
    ) -> T:
        """
        Get the result of a submitted task.

        Args:
            handle: The task handle from submit()
            timeout: Maximum seconds to wait

        Returns:
            The task result

        Raises:
            TimeoutError: If timeout exceeded
            Exception: If task failed
        """
        from fi.evals.framework.resilience.wrapper import (Optional, T, TaskHandle)
        # Determine which backend to use based on handle metadata
        backend = self._get_backend_for_handle(handle)
        return backend.get_result(handle, timeout)


    def get_status(self, handle: TaskHandle) -> TaskStatus:
        """Get current status of a task."""
        from fi.evals.framework.resilience.wrapper import (TaskHandle, TaskStatus)
        backend = self._get_backend_for_handle(handle)
        return backend.get_status(handle)


    def cancel(self, handle: TaskHandle) -> bool:
        """Attempt to cancel a task."""
        from fi.evals.framework.resilience.wrapper import (TaskHandle)
        backend = self._get_backend_for_handle(handle)
        return backend.cancel(handle)


    def _get_backend_for_handle(self, handle: TaskHandle) -> Backend:
        """Determine which backend handles this task."""
        from fi.evals.framework.resilience.wrapper import (Backend, TaskHandle)
        # Check if handle is from fallback backend
        if (
            self.fallback_backend
            and handle.backend_name == self.fallback_backend.name
        ):
            return self.fallback_backend
        return self.underlying


    def submit_batch(
        self,
        tasks: List[tuple],
    ) -> List[TaskHandle]:
        """Submit multiple tasks with resilience protections."""
        from fi.evals.framework.resilience.wrapper import (List, TaskHandle)
        handles = []
        for fn, args, kwargs, context in tasks:
            handle = self.submit(fn, args, kwargs or {}, context)
            handles.append(handle)
        return handles


    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the backend and all components."""
        # Stop health checker if running
        if self._health_checker and self._health_checker.is_running:
            self._health_checker.stop()

        # Shutdown underlying backend
        self.underlying.shutdown(wait)

        # Shutdown fallback if exists
        if self.fallback_backend:
            self.fallback_backend.shutdown(wait)


    def _emit_fallback_event(self, reason: str) -> None:
        """Emit fallback event."""
        from fi.evals.framework.resilience.wrapper import (ResilienceEvent, ResilienceEventType)
        if not self.event_callback:
            return

        event = ResilienceEvent(
            event_type=ResilienceEventType.FALLBACK_USED,
            backend_name=self.name,
            metadata={
                "reason": reason,
                "fallback_backend": (
                    self.fallback_backend.name if self.fallback_backend else None
                ),
            },
        )

        try:
            self.event_callback(event)
        except Exception:
            pass


    @property
    def rate_limiter(self) -> Optional[TokenBucketRateLimiter]:
        """Get rate limiter component."""
        from fi.evals.framework.resilience.wrapper import (Optional, TokenBucketRateLimiter)
        return self._rate_limiter


    @property
    def circuit_breaker(self) -> Optional[CircuitBreaker]:
        """Get circuit breaker component."""
        from fi.evals.framework.resilience.wrapper import (CircuitBreaker, Optional)
        return self._circuit_breaker


    @property
    def retry_handler(self) -> Optional[RetryHandler]:
        """Get retry handler component."""
        from fi.evals.framework.resilience.wrapper import (Optional, RetryHandler)
        return self._retry_handler


    @property
    def health_checker(self) -> Optional[HealthChecker]:
        """Get health checker component."""
        from fi.evals.framework.resilience.wrapper import (HealthChecker, Optional)
        return self._health_checker


    def get_stats(self) -> dict:
        """Get combined statistics from all components."""
        stats = {
            "backend": self.name,
            "underlying": self.underlying.name,
        }

        if self._rate_limiter:
            stats["rate_limiter"] = self._rate_limiter.get_stats()

        if self._circuit_breaker:
            stats["circuit_breaker"] = self._circuit_breaker.get_stats()

        if self._retry_handler:
            stats["retry"] = self._retry_handler.get_stats()

        if self._health_checker:
            stats["health"] = self._health_checker.get_stats()

        return stats


    def start_health_checks(self) -> None:
        """Start periodic health checking."""
        if self._health_checker:
            self._health_checker.start()


    def stop_health_checks(self) -> None:
        """Stop periodic health checking."""
        if self._health_checker:
            self._health_checker.stop()
