"""Factories for evaluator."""
from __future__ import annotations

from fi.evals.framework.evaluator import (
    Any, Backend, BaseEvaluation, Callable, FrameworkEvaluator, Optional,
)

def blocking_evaluator(
    *evaluations: BaseEvaluation,
    auto_enrich_span: bool = True,
    fail_fast: bool = False,
) -> FrameworkEvaluator:
    """
    Create a blocking evaluator.

    Args:
        *evaluations: Evaluations to run
        auto_enrich_span: Whether to enrich OTEL spans
        fail_fast: Stop on first failure

    Returns:
        Configured Evaluator in blocking mode

    Example:
        evaluator = blocking_evaluator(ToxicityEval(), BiasEval())
        result = evaluator.run({"response": "..."})
    """
    from fi.evals.framework.evaluator import (BaseEvaluation, ExecutionMode, FrameworkEvaluator)
    return FrameworkEvaluator(
        evaluations=list(evaluations),
        mode=ExecutionMode.BLOCKING,
        auto_enrich_span=auto_enrich_span,
        fail_fast=fail_fast,
    )


def async_evaluator(
    *evaluations: BaseEvaluation,
    max_workers: int = 4,
    auto_enrich_span: bool = True,
    backend: Optional[Backend] = None,
) -> FrameworkEvaluator:
    """
    Create a non-blocking (async) evaluator.

    Args:
        *evaluations: Evaluations to run
        max_workers: Maximum concurrent evaluations
        auto_enrich_span: Whether to enrich OTEL spans
        backend: Custom execution backend

    Returns:
        Configured Evaluator in non-blocking mode

    Example:
        evaluator = async_evaluator(ToxicityEval(), BiasEval())
        result = evaluator.run({"response": "..."})  # Returns immediately
        batch = result.wait()  # Get results when needed
    """
    from fi.evals.framework.evaluator import (
        Backend, BaseEvaluation, ExecutionMode, FrameworkEvaluator, Optional,
    )
    return FrameworkEvaluator(
        evaluations=list(evaluations),
        mode=ExecutionMode.NON_BLOCKING,
        max_workers=max_workers,
        auto_enrich_span=auto_enrich_span,
        backend=backend,
    )


def distributed_evaluator(
    *evaluations: BaseEvaluation,
    backend: Backend,
    auto_enrich_span: bool = True,
) -> FrameworkEvaluator:
    """
    Create a distributed evaluator with custom backend.

    Args:
        *evaluations: Evaluations to run
        backend: Execution backend (Temporal, Celery, Ray, etc.)
        auto_enrich_span: Whether to enrich OTEL spans

    Returns:
        Configured Evaluator in distributed mode

    Example:
        backend = TemporalBackend(config)
        evaluator = distributed_evaluator(
            ToxicityEval(),
            backend=backend,
        )
        result = evaluator.run({"response": "..."})
    """
    from fi.evals.framework.evaluator import (
        Backend, BaseEvaluation, ExecutionMode, FrameworkEvaluator,
    )
    return FrameworkEvaluator(
        evaluations=list(evaluations),
        mode=ExecutionMode.DISTRIBUTED,
        backend=backend,
        auto_enrich_span=auto_enrich_span,
    )


def resilient_evaluator(
    *evaluations: BaseEvaluation,
    backend: Optional[Backend] = None,
    resilience: Optional[Any] = None,
    fallback_backend: Optional[Backend] = None,
    event_callback: Optional[Callable] = None,
    auto_enrich_span: bool = True,
) -> FrameworkEvaluator:
    """
    Create a distributed evaluator with resilience protections.

    Wraps a backend with circuit breaker, rate limiting, retry, and fallback
    capabilities, then creates an Evaluator in DISTRIBUTED mode.

    Args:
        *evaluations: Evaluations to run
        backend: Execution backend (uses ThreadPoolBackend if None)
        resilience: ResilienceConfig for resilience settings (optional)
        fallback_backend: Optional fallback backend for degradation
        event_callback: Callback for resilience events
        auto_enrich_span: Whether to enrich OTEL spans

    Returns:
        Configured Evaluator in distributed mode with resilience

    Example:
        from fi.evals.framework import resilient_evaluator, ResilienceConfig
        from fi.evals.framework import CircuitBreakerConfig, RateLimitConfig

        evaluator = resilient_evaluator(
            ToxicityEval(),
            BiasEval(),
            resilience=ResilienceConfig(
                circuit_breaker=CircuitBreakerConfig(failure_threshold=5),
                rate_limit=RateLimitConfig(requests_per_second=10),
            ),
        )
        result = evaluator.run({"response": "..."})
    """
    from fi.evals.framework.evaluator import (
        Any, Backend, BaseEvaluation, Callable, ExecutionMode, FrameworkEvaluator, Optional,
        ThreadPoolBackend,
    )
    from .resilience import ResilientBackend, ResilienceConfig

    # Create underlying backend if not provided
    underlying = backend or ThreadPoolBackend()

    # Wrap with resilience
    resilience_config = resilience or ResilienceConfig()
    resilient = ResilientBackend(
        underlying=underlying,
        config=resilience_config,
        fallback_backend=fallback_backend,
        event_callback=event_callback,
    )

    return FrameworkEvaluator(
        evaluations=list(evaluations),
        mode=ExecutionMode.DISTRIBUTED,
        backend=resilient,
        auto_enrich_span=auto_enrich_span,
    )
