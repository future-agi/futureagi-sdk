"""
LLM Span Processor.

Enriches LLM spans with standardized GenAI attributes,
normalizes provider names, and extracts token usage.
"""

from typing import Any, Dict, List, Optional, Set
import logging
import json

from .base import BaseSpanProcessor, OTEL_AVAILABLE
from ..conventions import (
    GenAIAttributes,
    normalize_system_name,
    OPERATION_CHAT,
    OPERATION_COMPLETION,
    OPERATION_EMBEDDING,
)

if OTEL_AVAILABLE:
    from opentelemetry.sdk.trace import ReadableSpan
else:
    ReadableSpan = Any

logger = logging.getLogger(__name__)


from ._llm_l_l_m_span_processor_compile_redact_patterns import _LLMSpanProcessorCompileRedactPatternsMethods
from ._llm_l_l_m_span_processor_extract_finish_reason import _LLMSpanProcessorExtractFinishReasonMethods

class LLMSpanProcessor(
    _LLMSpanProcessorCompileRedactPatternsMethods,
    _LLMSpanProcessorExtractFinishReasonMethods,
    BaseSpanProcessor,
):
    """
    Processor that enriches LLM spans with standardized attributes.

    This processor:
    - Normalizes provider/system names
    - Extracts and standardizes token usage
    - Captures request parameters (temperature, max_tokens, etc.)
    - Adds derived attributes (total tokens, etc.)

    Works with spans from any LLM provider, normalizing them
    to the OpenTelemetry GenAI semantic conventions.

    Example:
        processor = LLMSpanProcessor(
            capture_prompts=True,
            capture_completions=True,
            max_content_length=5000,
        )
    """

    # Common span name patterns that indicate LLM operations
    LLM_SPAN_PATTERNS = {
        "llm", "chat", "completion", "generate", "embedding",
        "openai", "anthropic", "cohere", "bedrock", "azure",
        "gemini", "mistral", "ollama", "together", "groq",
    }

    # Attribute keys from various providers that we normalize
    PROVIDER_TOKEN_MAPPINGS = {
        # OpenAI patterns
        "llm.usage.prompt_tokens": "input_tokens",
        "llm.usage.completion_tokens": "output_tokens",
        "llm.usage.total_tokens": "total_tokens",
        # LangChain patterns
        "llm.token_count.prompt": "input_tokens",
        "llm.token_count.completion": "output_tokens",
        # Generic patterns
        "input_tokens": "input_tokens",
        "output_tokens": "output_tokens",
        "prompt_tokens": "input_tokens",
        "completion_tokens": "output_tokens",
        # Anthropic patterns
        "anthropic.usage.input_tokens": "input_tokens",
        "anthropic.usage.output_tokens": "output_tokens",
    }

    def __init__(
        self,
        capture_prompts: bool = True,
        capture_completions: bool = True,
        max_content_length: int = 10000,
        redact_patterns: Optional[List[str]] = None,
        span_filter: Optional[Set[str]] = None,
        enabled: bool = True,
    ):
        """
        Initialize the LLM span processor.

        Args:
            capture_prompts: Whether to capture prompt content
            capture_completions: Whether to capture completion content
            max_content_length: Maximum content length before truncation
            redact_patterns: Regex patterns to redact from content
            span_filter: Only process spans with these names (None = all)
            enabled: Whether processor is active
        """
        super().__init__(enabled=enabled)
        self._capture_prompts = capture_prompts
        self._capture_completions = capture_completions
        self._max_content_length = max_content_length
        self._redact_patterns = redact_patterns or []
        self._span_filter = span_filter
        self._compiled_patterns: List[Any] = []

        self._compile_redact_patterns()


__all__ = ["LLMSpanProcessor"]
