"""Attributes for conventions."""
from __future__ import annotations

from fi.evals.otel.conventions import (Any, Dict, OPERATION_CHAT, Optional)

def normalize_system_name(provider: str) -> str:
    """
    Normalize provider name to standard system name.

    Args:
        provider: Provider name (various formats)

    Returns:
        Normalized system name for gen_ai.provider.name attribute
    """
    from fi.evals.otel.conventions import (
        SYSTEM_ANTHROPIC, SYSTEM_ANYSCALE, SYSTEM_AWS_BEDROCK, SYSTEM_AZURE_OPENAI, SYSTEM_COHERE,
        SYSTEM_CUSTOM, SYSTEM_FIREWORKS, SYSTEM_GOOGLE, SYSTEM_GROQ, SYSTEM_HUGGINGFACE,
        SYSTEM_META, SYSTEM_MISTRAL, SYSTEM_OLLAMA, SYSTEM_OPENAI, SYSTEM_REPLICATE,
        SYSTEM_TOGETHER,
    )
    provider_lower = provider.lower().strip()

    mapping = {
        "openai": SYSTEM_OPENAI,
        "gpt": SYSTEM_OPENAI,
        "chatgpt": SYSTEM_OPENAI,
        "anthropic": SYSTEM_ANTHROPIC,
        "claude": SYSTEM_ANTHROPIC,
        "cohere": SYSTEM_COHERE,
        "command": SYSTEM_COHERE,
        "google": SYSTEM_GOOGLE,
        "gemini": SYSTEM_GOOGLE,
        "palm": SYSTEM_GOOGLE,
        "mistral": SYSTEM_MISTRAL,
        "mixtral": SYSTEM_MISTRAL,
        "meta": SYSTEM_META,
        "llama": SYSTEM_META,
        "bedrock": SYSTEM_AWS_BEDROCK,
        "aws": SYSTEM_AWS_BEDROCK,
        "azure": SYSTEM_AZURE_OPENAI,
        "huggingface": SYSTEM_HUGGINGFACE,
        "hf": SYSTEM_HUGGINGFACE,
        "ollama": SYSTEM_OLLAMA,
        "together": SYSTEM_TOGETHER,
        "anyscale": SYSTEM_ANYSCALE,
        "groq": SYSTEM_GROQ,
        "fireworks": SYSTEM_FIREWORKS,
        "replicate": SYSTEM_REPLICATE,
    }

    for key, value in mapping.items():
        if key in provider_lower:
            return value

    return SYSTEM_CUSTOM


def create_llm_span_attributes(
    system: str,
    model: str,
    operation: str = OPERATION_CHAT,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    finish_reason: Optional[str] = None,
    **extra_attrs
) -> Dict[str, Any]:
    """
    Create a standardized attribute dictionary for an LLM span.

    Args:
        system: Provider system name (will be normalized)
        model: Model name
        operation: Operation type (chat, completion, embedding)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        temperature: Temperature setting
        max_tokens: Max tokens setting
        finish_reason: Finish reason
        **extra_attrs: Additional attributes

    Returns:
        Dictionary of OTEL-compliant attributes
    """
    from fi.evals.otel.conventions import (
        Any, Dict, GenAIAttributes, OPERATION_CHAT, Optional, normalize_system_name,
    )
    normalized = normalize_system_name(system)
    attrs: Dict[str, Any] = {
        GenAIAttributes.SPAN_KIND: "LLM",
        GenAIAttributes.PROVIDER_NAME: normalized,
        GenAIAttributes.OPERATION_NAME: operation,
        GenAIAttributes.REQUEST_MODEL: model,
    }

    if input_tokens is not None:
        attrs[GenAIAttributes.USAGE_INPUT_TOKENS] = input_tokens
    if output_tokens is not None:
        attrs[GenAIAttributes.USAGE_OUTPUT_TOKENS] = output_tokens
    if input_tokens is not None and output_tokens is not None:
        attrs[GenAIAttributes.USAGE_TOTAL_TOKENS] = input_tokens + output_tokens
    if temperature is not None:
        attrs[GenAIAttributes.REQUEST_TEMPERATURE] = temperature
    if max_tokens is not None:
        attrs[GenAIAttributes.REQUEST_MAX_TOKENS] = max_tokens
    if finish_reason is not None:
        attrs[GenAIAttributes.RESPONSE_FINISH_REASON] = finish_reason

    # Add extra attributes
    attrs.update(extra_attrs)

    return attrs


def create_evaluation_attributes(
    metric: str,
    score: float,
    reason: Optional[str] = None,
    latency_ms: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Create attributes for an evaluation result.

    Uses gen_ai.evaluation.* namespace.

    Args:
        metric: Evaluation metric name
        score: Score value (0.0 to 1.0)
        reason: Explanation for the score
        latency_ms: Time taken to evaluate

    Returns:
        Dictionary of evaluation attributes
    """
    from fi.evals.otel.conventions import (Any, Dict, EvaluationAttributes, Optional)
    attrs: Dict[str, Any] = {
        EvaluationAttributes.NAME: metric,
        EvaluationAttributes.SCORE_VALUE: score,
    }

    if reason:
        attrs[EvaluationAttributes.EXPLANATION] = reason
    if latency_ms is not None:
        attrs[EvaluationAttributes.latency(metric)] = latency_ms

    return attrs
