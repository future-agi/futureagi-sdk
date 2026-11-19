"""Local LLM integration for running LLM-as-judge evaluations without cloud API.

This module provides support for local LLM inference via Ollama, enabling
offline LLM-based evaluations for air-gapped environments or faster iteration.

Example:
    >>> from fi.evals.local.llm import OllamaLLM, LocalLLMConfig
    >>>
    >>> # Initialize with default model
    >>> llm = OllamaLLM()
    >>>
    >>> # Generate completion
    >>> response = llm.generate("What is 2+2?")
    >>>
    >>> # Use as LLM judge
    >>> result = llm.judge(
    ...     query="What is the capital of France?",
    ...     response="The capital of France is Paris.",
    ...     criteria="Evaluate if the response correctly answers the question."
    ... )
    >>> print(result["score"])
    0.9
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import json
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class LocalLLMConfig:
    """Configuration for local LLM.

    Attributes:
        model: The model name to use (e.g., "llama3.2", "mistral", "phi3").
        base_url: The Ollama API base URL.
        temperature: Sampling temperature (0.0 for deterministic).
        max_tokens: Maximum tokens to generate.
        timeout: Request timeout in seconds.
    """

    model: str = "llama3.2"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.0
    max_tokens: int = 1024
    timeout: int = 120


from ._llm_ollama_l_l_m_check_availability import _OllamaLLMCheckAvailabilityMethods
from ._llm_ollama_l_l_m_parse_judge_response import _OllamaLLMParseJudgeResponseMethods

class OllamaLLM(_OllamaLLMCheckAvailabilityMethods, _OllamaLLMParseJudgeResponseMethods):
    """Interface to Ollama for local LLM inference.

    This class provides methods for text generation and LLM-as-judge
    evaluations using locally running Ollama models.

    Example:
        >>> llm = OllamaLLM()
        >>> llm.is_available()
        True
        >>> response = llm.generate("Hello, how are you?")
        "I'm doing well, thank you for asking!"
    """

    def __init__(
        self,
        config: Optional[LocalLLMConfig] = None,
        auto_check: bool = True,
    ) -> None:
        """Initialize the Ollama LLM interface.

        Args:
            config: Configuration for the LLM.
            auto_check: If True, check Ollama availability on init.
        """
        self.config = config or LocalLLMConfig()
        self._available: Optional[bool] = None
        self._models: Optional[List[str]] = None

        if auto_check:
            self._check_availability()


class LocalLLMFactory:
    """Factory for creating local LLM instances.

    This factory provides a unified interface for creating different
    types of local LLM backends.
    """

    _backends = {
        "ollama": OllamaLLM,
    }

    @classmethod
    def create(
        cls,
        backend: str = "ollama",
        **kwargs,
    ) -> OllamaLLM:
        """Create a local LLM instance.

        Args:
            backend: The LLM backend to use (currently only "ollama").
            **kwargs: Additional arguments passed to the LLM constructor.

        Returns:
            An initialized LLM instance.

        Raises:
            ValueError: If backend is not supported.
        """
        if backend not in cls._backends:
            raise ValueError(
                f"Unsupported LLM backend: {backend}. "
                f"Supported backends: {list(cls._backends.keys())}"
            )

        return cls._backends[backend](**kwargs)

    @classmethod
    def from_string(cls, spec: str) -> OllamaLLM:
        """Create a local LLM from a string specification.

        Args:
            spec: String specification in format "backend/model"
                  (e.g., "ollama/llama3.2").

        Returns:
            An initialized LLM instance.
        """
        parts = spec.split("/", 1)
        backend = parts[0].lower()
        model = parts[1] if len(parts) > 1 else None

        config = LocalLLMConfig()
        if model:
            config.model = model

        return cls.create(backend, config=config)
