"""Guardrails discover backends operations."""
from __future__ import annotations

from fi.evals.guardrails.base import (
    Any, BaseBackend, Dict, GuardrailModel, GuardrailsResponse, List, Optional,
)


class _GuardrailsDiscoverBackendsMethods:
    __slots__ = ()

    @classmethod
    def discover_backends(cls) -> List[GuardrailModel]:
        """
        Discover available backends based on environment.

        Checks for API keys, VLLM servers, and GPU availability.

        Returns:
            List of available GuardrailModel values

        Usage:
            available = Guardrails.discover_backends()
            print(f"Available: {[m.value for m in available]}")
        """
        from fi.evals.guardrails.base import (GuardrailModel, List)
        from fi.evals.guardrails.discovery import discover_backends
        return discover_backends()


    @classmethod
    def get_backend_details(cls) -> Dict[str, Dict]:
        """
        Get detailed information about all backends.

        Returns:
            Dict mapping model names to availability details

        Usage:
            details = Guardrails.get_backend_details()
            for model, info in details.items():
                print(f"{model}: {info['status']} - {info['reason']}")
        """
        from fi.evals.guardrails.base import (Dict)
        from fi.evals.guardrails.discovery import get_backend_details
        return get_backend_details()


    def _load_backends(self):
        """Initialize model backends based on configuration."""
        for model in self.config.models:
            self.backends[model] = self._create_backend(model)


    def _load_scanners(self):
        """Initialize scanner pipeline based on configuration."""
        from fi.evals.guardrails.base import (ScannerPipeline)
        scanner_config = self.config.scanners
        if scanner_config is None or not scanner_config.enabled:
            self.scanner_pipeline = None
            return

        # Build scanner pipeline from config
        from fi.evals.guardrails.scanners import (
            JailbreakScanner,
            CodeInjectionScanner,
            SecretsScanner,
            MaliciousURLScanner,
            InvisibleCharScanner,
            LanguageScanner,
            TopicRestrictionScanner,
            RegexScanner,
            RegexPattern,
        )

        scanners = []

        if scanner_config.jailbreak:
            scanners.append(JailbreakScanner(
                threshold=scanner_config.jailbreak_threshold
            ))

        if scanner_config.code_injection:
            scanners.append(CodeInjectionScanner(
                threshold=scanner_config.code_injection_threshold
            ))

        if scanner_config.secrets:
            scanners.append(SecretsScanner(
                threshold=scanner_config.secrets_threshold
            ))

        if scanner_config.urls:
            scanners.append(MaliciousURLScanner(
                threshold=scanner_config.urls_threshold
            ))

        if scanner_config.invisible_chars:
            scanners.append(InvisibleCharScanner())

        if scanner_config.language:
            scanners.append(LanguageScanner(
                allowed_languages=scanner_config.language.allowed,
                blocked_languages=scanner_config.language.blocked,
                allowed_scripts=scanner_config.language.allowed_scripts,
            ))

        if scanner_config.topics:
            scanners.append(TopicRestrictionScanner(
                allowed_topics=scanner_config.topics.allowed,
                denied_topics=scanner_config.topics.denied,
                custom_topics=scanner_config.topics.custom_topics,
                min_keyword_matches=scanner_config.topics.min_keyword_matches,
            ))

        if scanner_config.regex_patterns or scanner_config.predefined_patterns:
            custom_patterns = []
            for pattern_config in scanner_config.regex_patterns:
                custom_patterns.append(RegexPattern(
                    name=pattern_config.name,
                    pattern=pattern_config.pattern,
                    confidence=pattern_config.confidence,
                    description=pattern_config.description,
                ))
            scanners.append(RegexScanner(
                patterns=scanner_config.predefined_patterns,
                custom_patterns=custom_patterns if custom_patterns else None,
            ))

        if scanners:
            self.scanner_pipeline = ScannerPipeline(
                scanners=scanners,
                parallel=scanner_config.parallel,
                fail_fast=scanner_config.fail_fast,
            )


    def _create_backend(self, model: GuardrailModel) -> BaseBackend:
        """
        Create a backend for the specified model.

        Uses the model registry to find and instantiate the correct backend.

        Args:
            model: The model to create a backend for

        Returns:
            Backend instance

        Raises:
            ValueError: If model not found in registry
            RuntimeError: If backend cannot be instantiated
        """
        from fi.evals.guardrails.base import (BaseBackend, GuardrailModel, os)
        from fi.evals.guardrails.registry import get_model_info, get_backend_class

        info = get_model_info(model)
        if not info:
            raise ValueError(f"Model {model.value} not found in registry")

        try:
            backend_class = get_backend_class(model)
        except ImportError as e:
            raise RuntimeError(
                f"Failed to import backend for {model.value}: {e}. "
                "Make sure required dependencies are installed."
            )

        # Build kwargs based on model type
        kwargs = {"model": model}

        if info.model_type == "api":
            if model.value.startswith("turing"):
                kwargs.update({
                    "fi_api_key": self._fi_api_key,
                    "fi_secret_key": self._fi_secret_key,
                    "fi_base_url": self._fi_base_url,
                })
            elif model.value == "openai-moderation":
                kwargs["api_key"] = os.environ.get("OPENAI_API_KEY")
            elif model.value == "azure-content-safety":
                kwargs["endpoint"] = os.environ.get("AZURE_CONTENT_SAFETY_ENDPOINT")
                kwargs["api_key"] = os.environ.get("AZURE_CONTENT_SAFETY_KEY")

        elif info.model_type == "local":
            # Check for VLLM server URL
            env_var = f"VLLM_{model.value.upper().replace('-', '_')}_URL"
            vllm_url = os.environ.get(env_var) or os.environ.get("VLLM_SERVER_URL")
            if vllm_url:
                kwargs["vllm_url"] = vllm_url

            # HuggingFace token for gated models
            hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
            if hf_token:
                kwargs["hf_token"] = hf_token

        try:
            return backend_class(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Failed to create backend for {model.value}: {e}")


    def screen_input(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GuardrailsResponse:
        """
        Screen user input BEFORE sending to LLM.

        Args:
            content: User input to screen
            metadata: Optional context (user_id, session_id, etc.)

        Returns:
            GuardrailsResponse with pass/fail and details
        """
        from fi.evals.guardrails.base import (Any, Dict, GuardrailsResponse, Optional, RailType)
        return self._screen_sync(content, RailType.INPUT, metadata=metadata)


    async def screen_input_async(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GuardrailsResponse:
        """
        Async version of screen_input.

        Args:
            content: User input to screen
            metadata: Optional context

        Returns:
            GuardrailsResponse with pass/fail and details
        """
        from fi.evals.guardrails.base import (Any, Dict, GuardrailsResponse, Optional, RailType)
        return await self._screen_async(content, RailType.INPUT, metadata=metadata)


    def screen_output(
        self,
        content: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GuardrailsResponse:
        """
        Screen LLM output BEFORE sending to user.

        Args:
            content: LLM response to screen
            context: Optional context (for hallucination check)
            metadata: Optional metadata
        """
        from fi.evals.guardrails.base import (Any, Dict, GuardrailsResponse, Optional, RailType)
        return self._screen_sync(content, RailType.OUTPUT, context=context, metadata=metadata)


    async def screen_output_async(
        self,
        content: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GuardrailsResponse:
        """Async version of screen_output."""
        from fi.evals.guardrails.base import (Any, Dict, GuardrailsResponse, Optional, RailType)
        return await self._screen_async(content, RailType.OUTPUT, context=context, metadata=metadata)


    def screen_retrieval(
        self,
        chunks: List[str],
        query: Optional[str] = None,
    ) -> List[GuardrailsResponse]:
        """
        Screen retrieved chunks in RAG pipeline.

        Args:
            chunks: Retrieved document chunks
            query: Original user query

        Returns:
            List of responses, one per chunk
        """
        from fi.evals.guardrails.base import (GuardrailsResponse, List, Optional, RailType)
        results = []
        for chunk in chunks:
            result = self._screen_sync(
                chunk,
                RailType.RETRIEVAL,
                metadata={"query": query} if query else None,
            )
            results.append(result)
        return results
