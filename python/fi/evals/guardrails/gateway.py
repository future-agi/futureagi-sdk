"""
Guardrails Gateway - High-level API for content screening.

Provides a simple, ergonomic interface for screening content
with automatic backend management and context managers.
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator, List, Optional, Union

from fi.evals.guardrails.base import Guardrails
from fi.evals.guardrails.config import GuardrailModel, GuardrailsConfig, AggregationStrategy
from fi.evals.guardrails.types import GuardrailsResponse
from fi.evals.guardrails.discovery import BackendDiscovery, discover_backends, get_backend_details


from ._gateway_screening_session_input import _ScreeningSessionInputMethods

class ScreeningSession(_ScreeningSessionInputMethods):
    """A screening session for synchronous operations."""

    def __init__(self, guardrails: Guardrails):
        self._guardrails = guardrails
        self._history: List[GuardrailsResponse] = []


from ._gateway_async_screening_session_input import _AsyncScreeningSessionInputMethods

class AsyncScreeningSession(_AsyncScreeningSessionInputMethods):
    """A screening session for async operations."""

    def __init__(self, guardrails: Guardrails):
        self._guardrails = guardrails
        self._history: List[GuardrailsResponse] = []


from fi.evals._extracted import bind_owner as _bind_owner
from ._gateway_guardrails_gateway_with_openai import _GuardrailsGatewayWithOpenaiMethods

class GuardrailsGateway(_GuardrailsGatewayWithOpenaiMethods):
    """High-level gateway for content screening.

    Provides convenient methods for creating screening sessions
    and managing guardrails configuration.

    Example:
        # Simple usage
        gateway = GuardrailsGateway()
        result = gateway.screen("Hello world")

        # With context manager
        with gateway.screening() as session:
            input_result = session.input("user message")
            if input_result.passed:
                response = call_llm("user message")
                output_result = session.output(response)

        # Async context manager
        async with gateway.screening_async() as session:
            input_result = await session.input("user message")
            output_result = await session.output(response)
    """

    def __init__(
        self,
        models: Optional[List[GuardrailModel]] = None,
        config: Optional[GuardrailsConfig] = None,
        auto_discover: bool = False,
    ):
        """Initialize the gateway.

        Args:
            models: List of models to use. If None, uses default.
            config: Full configuration object. Takes precedence over models.
            auto_discover: If True and no models specified, auto-discover available backends.
        """
        if config:
            self._config = config
        elif models:
            self._config = GuardrailsConfig(models=models)
        elif auto_discover:
            available = discover_backends()
            if not available:
                raise ValueError("No backends available. Set API keys or start VLLM server.")
            self._config = GuardrailsConfig(models=available[:1])  # Use first available
        else:
            self._config = GuardrailsConfig()

        self._guardrails = Guardrails(config=self._config)


_bind_owner(GuardrailsGateway)


# Convenience alias
Gateway = GuardrailsGateway


__all__ = [
    "GuardrailsGateway",
    "Gateway",
    "ScreeningSession",
    "AsyncScreeningSession",
    "discover_backends",
    "get_backend_details",
]
