"""GuardrailsGateway with openai operations."""
from __future__ import annotations

from typing import TYPE_CHECKING
from fi.evals.guardrails.gateway import (
    AggregationStrategy, AsyncIterator, AsyncScreeningSession, GuardrailModel, GuardrailsResponse,
    Iterator, List, Optional, ScreeningSession, asynccontextmanager, contextmanager,
)

if TYPE_CHECKING:
    from fi.evals.guardrails.gateway import GuardrailsGateway


class _GuardrailsGatewayWithOpenaiMethods:
    __slots__ = ()

    @classmethod
    def with_openai(cls, api_key: Optional[str] = None) -> "GuardrailsGateway":
        """Create a gateway using OpenAI Moderation (FREE).

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.

        Returns:
            GuardrailsGateway configured for OpenAI.
        """
        from fi.evals.guardrails.gateway import (GuardrailModel, GuardrailsConfig, Optional)
        import os
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        config = GuardrailsConfig(
            models=[GuardrailModel.OPENAI_MODERATION],
            timeout_ms=30000,
        )
        return cls(config=config)


    @classmethod
    def with_azure(
        cls,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> "GuardrailsGateway":
        """Create a gateway using Azure Content Safety.

        Args:
            endpoint: Azure endpoint URL. If None, uses env var.
            api_key: Azure API key. If None, uses env var.

        Returns:
            GuardrailsGateway configured for Azure.
        """
        from fi.evals.guardrails.gateway import (GuardrailModel, GuardrailsConfig, Optional)
        import os
        if endpoint:
            os.environ["AZURE_CONTENT_SAFETY_ENDPOINT"] = endpoint
        if api_key:
            os.environ["AZURE_CONTENT_SAFETY_KEY"] = api_key

        config = GuardrailsConfig(
            models=[GuardrailModel.AZURE_CONTENT_SAFETY],
            timeout_ms=30000,
        )
        return cls(config=config)


    @classmethod
    def with_local_model(
        cls,
        model: GuardrailModel,
        vllm_url: Optional[str] = None,
    ) -> "GuardrailsGateway":
        """Create a gateway using a local model via VLLM.

        Args:
            model: The local model to use (e.g., GuardrailModel.WILDGUARD_7B).
            vllm_url: VLLM server URL. If None, uses env var.

        Returns:
            GuardrailsGateway configured for the local model.
        """
        from fi.evals.guardrails.gateway import (GuardrailModel, GuardrailsConfig, Optional)
        import os
        if vllm_url:
            os.environ["VLLM_SERVER_URL"] = vllm_url

        config = GuardrailsConfig(
            models=[model],
            timeout_ms=60000,  # Local models may be slower
        )
        return cls(config=config)


    @classmethod
    def with_ensemble(
        cls,
        models: List[GuardrailModel],
        aggregation: AggregationStrategy = AggregationStrategy.ANY,
        parallel: bool = True,
    ) -> "GuardrailsGateway":
        """Create a gateway with ensemble of multiple backends.

        Args:
            models: List of models to use.
            aggregation: How to combine results (ANY, ALL, MAJORITY).
            parallel: Whether to run backends in parallel.

        Returns:
            GuardrailsGateway configured for ensemble mode.
        """
        from fi.evals.guardrails.gateway import (
            AggregationStrategy, GuardrailModel, GuardrailsConfig, List,
        )
        config = GuardrailsConfig(
            models=models,
            aggregation=aggregation,
            parallel=parallel,
            timeout_ms=60000,
        )
        return cls(config=config)


    @classmethod
    def auto(cls) -> "GuardrailsGateway":
        """Create a gateway that auto-discovers available backends.

        Returns:
            GuardrailsGateway with the best available backend.

        Raises:
            ValueError: If no backends are available.
        """
        return cls(auto_discover=True)


    def screen(self, content: str, metadata: Optional[dict] = None) -> GuardrailsResponse:
        """Quick screen content (alias for screen_input).

        Args:
            content: Content to screen.
            metadata: Optional metadata.

        Returns:
            GuardrailsResponse with results.
        """
        from fi.evals.guardrails.gateway import (GuardrailsResponse, Optional)
        return self._guardrails.screen_input(content, metadata=metadata)


    async def screen_async(self, content: str, metadata: Optional[dict] = None) -> GuardrailsResponse:
        """Quick screen content asynchronously.

        Args:
            content: Content to screen.
            metadata: Optional metadata.

        Returns:
            GuardrailsResponse with results.
        """
        from fi.evals.guardrails.gateway import (GuardrailsResponse, Optional)
        return await self._guardrails.screen_input_async(content, metadata=metadata)


    @contextmanager
    def screening(self) -> Iterator[ScreeningSession]:
        """Create a synchronous screening session.

        Yields:
            ScreeningSession for screening operations.

        Example:
            with gateway.screening() as session:
                input_result = session.input("user message")
                if input_result.passed:
                    response = generate_response()
                    output_result = session.output(response)
        """
        from fi.evals.guardrails.gateway import (Iterator, ScreeningSession, contextmanager)
        session = ScreeningSession(self._guardrails)
        yield session


    @asynccontextmanager
    async def screening_async(self) -> AsyncIterator[AsyncScreeningSession]:
        """Create an async screening session.

        Yields:
            AsyncScreeningSession for async screening operations.

        Example:
            async with gateway.screening_async() as session:
                input_result = await session.input("user message")
                if input_result.passed:
                    response = await generate_response()
                    output_result = await session.output(response)
        """
        from fi.evals.guardrails.gateway import (
            AsyncIterator, AsyncScreeningSession, asynccontextmanager,
        )
        session = AsyncScreeningSession(self._guardrails)
        yield session


    @property
    def available_backends(self) -> List[GuardrailModel]:
        """Get list of available backends."""
        from fi.evals.guardrails.gateway import (GuardrailModel, List, discover_backends)
        return discover_backends()


    @property
    def configured_models(self) -> List[GuardrailModel]:
        """Get list of configured models."""
        from fi.evals.guardrails.gateway import (GuardrailModel, List)
        return self._config.models


    @staticmethod
    def discover() -> List[GuardrailModel]:
        """Discover available backends.

        Returns:
            List of available GuardrailModel values.
        """
        from fi.evals.guardrails.gateway import (GuardrailModel, List, discover_backends)
        return discover_backends()


    @staticmethod
    def get_details() -> dict:
        """Get detailed backend availability info.

        Returns:
            Dict mapping model names to availability details.
        """
        from fi.evals.guardrails.gateway import (get_backend_details)
        return get_backend_details()
