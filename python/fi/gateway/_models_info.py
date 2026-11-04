"""Model information database -- pricing, context windows, capabilities."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelInfo:
    """Metadata about an LLM model."""

    max_tokens: int
    max_output_tokens: int | None = None
    input_cost_per_token: float = 0.0  # USD
    output_cost_per_token: float = 0.0  # USD
    supports_vision: bool = False
    supports_function_calling: bool = False
    supports_json_mode: bool = False


# Pricing as of Feb 2026 -- update periodically
MODEL_INFO: dict[str, ModelInfo] = {
    # OpenAI
    "gpt-4o": ModelInfo(
        max_tokens=128000,
        max_output_tokens=16384,
        input_cost_per_token=2.5e-6,
        output_cost_per_token=10e-6,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "gpt-4o-mini": ModelInfo(
        max_tokens=128000,
        max_output_tokens=16384,
        input_cost_per_token=0.15e-6,
        output_cost_per_token=0.6e-6,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "gpt-4-turbo": ModelInfo(
        max_tokens=128000,
        max_output_tokens=4096,
        input_cost_per_token=10e-6,
        output_cost_per_token=30e-6,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "gpt-4": ModelInfo(
        max_tokens=8192,
        max_output_tokens=8192,
        input_cost_per_token=30e-6,
        output_cost_per_token=60e-6,
        supports_function_calling=True,
    ),
    "gpt-3.5-turbo": ModelInfo(
        max_tokens=16385,
        max_output_tokens=4096,
        input_cost_per_token=0.5e-6,
        output_cost_per_token=1.5e-6,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "o1": ModelInfo(
        max_tokens=200000,
        max_output_tokens=100000,
        input_cost_per_token=15e-6,
        output_cost_per_token=60e-6,
        supports_vision=True,
        supports_function_calling=True,
    ),
    "o1-mini": ModelInfo(
        max_tokens=128000,
        max_output_tokens=65536,
        input_cost_per_token=3e-6,
        output_cost_per_token=12e-6,
        supports_function_calling=True,
    ),
    "o3-mini": ModelInfo(
        max_tokens=200000,
        max_output_tokens=100000,
        input_cost_per_token=1.1e-6,
        output_cost_per_token=4.4e-6,
        supports_function_calling=True,
    ),
    # OpenAI Embeddings
    "text-embedding-3-small": ModelInfo(
        max_tokens=8191,
        input_cost_per_token=0.02e-6,
    ),
    "text-embedding-3-large": ModelInfo(
        max_tokens=8191,
        input_cost_per_token=0.13e-6,
    ),
    "text-embedding-ada-002": ModelInfo(
        max_tokens=8191,
        input_cost_per_token=0.1e-6,
    ),
    # Anthropic
    "claude-sonnet-4-20250514": ModelInfo(
        max_tokens=200000,
        max_output_tokens=64000,
        input_cost_per_token=3e-6,
        output_cost_per_token=15e-6,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "claude-3-5-sonnet-20241022": ModelInfo(
        max_tokens=200000,
        max_output_tokens=8192,
        input_cost_per_token=3e-6,
        output_cost_per_token=15e-6,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "claude-3-5-haiku-20241022": ModelInfo(
        max_tokens=200000,
        max_output_tokens=8192,
        input_cost_per_token=0.8e-6,
        output_cost_per_token=4e-6,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "claude-3-opus-20240229": ModelInfo(
        max_tokens=200000,
        max_output_tokens=4096,
        input_cost_per_token=15e-6,
        output_cost_per_token=75e-6,
        supports_vision=True,
        supports_function_calling=True,
    ),
    "claude-3-haiku-20240307": ModelInfo(
        max_tokens=200000,
        max_output_tokens=4096,
        input_cost_per_token=0.25e-6,
        output_cost_per_token=1.25e-6,
        supports_vision=True,
        supports_function_calling=True,
    ),
    # Google
    "gemini-2.0-flash": ModelInfo(
        max_tokens=1048576,
        max_output_tokens=8192,
        input_cost_per_token=0.1e-6,
        output_cost_per_token=0.4e-6,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "gemini-1.5-pro": ModelInfo(
        max_tokens=2097152,
        max_output_tokens=8192,
        input_cost_per_token=1.25e-6,
        output_cost_per_token=5e-6,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "gemini-1.5-flash": ModelInfo(
        max_tokens=1048576,
        max_output_tokens=8192,
        input_cost_per_token=0.075e-6,
        output_cost_per_token=0.3e-6,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    # Meta
    "llama-3.1-70b": ModelInfo(
        max_tokens=128000,
        max_output_tokens=4096,
        input_cost_per_token=0.88e-6,
        output_cost_per_token=0.88e-6,
        supports_function_calling=True,
    ),
    "llama-3.1-8b": ModelInfo(
        max_tokens=128000,
        max_output_tokens=4096,
        input_cost_per_token=0.18e-6,
        output_cost_per_token=0.18e-6,
    ),
    # Mistral
    "mistral-large-latest": ModelInfo(
        max_tokens=128000,
        max_output_tokens=4096,
        input_cost_per_token=2e-6,
        output_cost_per_token=6e-6,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "mistral-small-latest": ModelInfo(
        max_tokens=128000,
        max_output_tokens=4096,
        input_cost_per_token=0.2e-6,
        output_cost_per_token=0.6e-6,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
}

model_alias_map: dict[str, str] = {}
"""Map short names to full model names. E.g. ``{"gpt4": "gpt-4o"}``"""

# --- Required environment variables ---

_REQUIRED_ENV_VARS: list[str] = ["AGENTCC_API_KEY", "AGENTCC_BASE_URL"]


def get_model_info(model: str) -> ModelInfo | None:
    """Look up model info by name.

    Resolution order:

    1. Exact match in ``MODEL_INFO``.
    2. Alias lookup via ``model_alias_map``, then exact match.
    3. Prefix match (e.g., ``"gpt-4o-2024-08-06"`` -> ``"gpt-4o"``).
    """
    # 1. Exact match
    if model in MODEL_INFO:
        return MODEL_INFO[model]

    # 2. Alias resolution
    resolved = model_alias_map.get(model)
    if resolved is not None and resolved in MODEL_INFO:
        return MODEL_INFO[resolved]

    # 3. Prefix match (longest match first)
    for known_model in sorted(MODEL_INFO.keys(), key=len, reverse=True):
        if model.startswith(known_model):
            return MODEL_INFO[known_model]
    return None


def get_valid_models() -> list[str]:
    """Return all known model names from the model info database."""
    return list(MODEL_INFO.keys())


def register_model(model_name: str, model_info: ModelInfo) -> None:
    """Register or update a model in the info database.

    Args:
        model_name: The model identifier (e.g. ``"my-custom-model"``).
        model_info: A :class:`ModelInfo` instance with the model's metadata.
    """
    MODEL_INFO[model_name] = model_info


def supports_vision(model: str) -> bool:
    """Check if *model* supports vision/image inputs."""
    info = get_model_info(model)
    return info.supports_vision if info else False


def supports_function_calling(model: str) -> bool:
    """Check if *model* supports function/tool calling."""
    info = get_model_info(model)
    return info.supports_function_calling if info else False


def supports_json_mode(model: str) -> bool:
    """Check if *model* supports JSON mode / structured output."""
    info = get_model_info(model)
    return info.supports_json_mode if info else False


def supports_response_schema(model: str) -> bool:
    """Alias for :func:`supports_json_mode`."""
    return supports_json_mode(model)


def validate_environment() -> dict[str, Any]:
    """Check if required environment variables are set.

    Returns:
        A dict with:
            - ``keys_set``: list of env var names that are set.
            - ``keys_missing``: list of env var names that are missing.
            - ``ready``: ``True`` if all required vars are set.
    """
    keys_set: list[str] = []
    keys_missing: list[str] = []

    for var in _REQUIRED_ENV_VARS:
        if os.environ.get(var):
            keys_set.append(var)
        else:
            keys_missing.append(var)

    return {
        "keys_set": keys_set,
        "keys_missing": keys_missing,
        "ready": len(keys_missing) == 0,
    }
