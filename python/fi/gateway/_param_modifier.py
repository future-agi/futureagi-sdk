"""Provider-specific parameter adaptation for modify_params mode.

When ``modify_params=True`` is set on the client, request parameters are
automatically adjusted for provider compatibility before sending. This
avoids errors when using the same code with different providers.
"""

from __future__ import annotations

from typing import Any

# Model prefixes that identify each provider family.
_ANTHROPIC_PREFIXES = ("claude-",)
_GOOGLE_PREFIXES = ("gemini-", "models/gemini-")
_COHERE_PREFIXES = ("command-",)
_MISTRAL_PREFIXES = ("mistral-", "mixtral-", "codestral-", "open-mistral-", "open-mixtral-")

# Parameters that specific providers do NOT support.
_ANTHROPIC_UNSUPPORTED = frozenset({
    "logit_bias",
    "logprobs",
    "top_logprobs",
    "n",
    "best_of",
    "suffix",
    "echo",
    "functions",
    "function_call",
    "service_tier",
})

_GOOGLE_UNSUPPORTED = frozenset({
    "logit_bias",
    "n",
    "best_of",
    "suffix",
    "echo",
    "functions",
    "function_call",
    "service_tier",
})

_COHERE_UNSUPPORTED = frozenset({
    "logit_bias",
    "logprobs",
    "top_logprobs",
    "n",
    "best_of",
    "suffix",
    "echo",
    "functions",
    "function_call",
    "presence_penalty",
    "frequency_penalty",
    "service_tier",
})


def _is_provider(model: str, prefixes: tuple[str, ...]) -> bool:
    model_lower = model.lower()
    return any(model_lower.startswith(p) for p in prefixes)


def modify_params_for_provider(model: str, body: dict[str, Any]) -> dict[str, Any]:
    """Modify request body params for provider compatibility.

    This function removes unsupported parameters and converts formats
    as needed for the target provider, based on the model name.

    Args:
        model: The model identifier (e.g. "claude-3-5-sonnet-20241022").
        body: The request body dict (mutated in place and returned).

    Returns:
        The modified body dict.
    """
    if _is_provider(model, _ANTHROPIC_PREFIXES):
        _adapt_for_anthropic(model, body)
    elif _is_provider(model, _GOOGLE_PREFIXES):
        _adapt_for_google(model, body)
    elif _is_provider(model, _COHERE_PREFIXES):
        _adapt_for_cohere(model, body)

    return body


def _adapt_for_anthropic(model: str, body: dict[str, Any]) -> None:
    """Remove unsupported params and convert formats for Claude models."""
    for key in _ANTHROPIC_UNSUPPORTED:
        body.pop(key, None)

    # Convert tool_choice string format: OpenAI uses "auto"/"none"/"required",
    # Anthropic uses {"type": "auto"} / {"type": "any"} / {"type": "tool", "name": "..."}
    tool_choice = body.get("tool_choice")
    if isinstance(tool_choice, str):
        if tool_choice == "none":
            # Anthropic doesn't have "none" — just remove tools
            body.pop("tool_choice", None)
            body.pop("tools", None)
        elif tool_choice == "required":
            body["tool_choice"] = {"type": "any"}
        elif tool_choice == "auto":
            body["tool_choice"] = {"type": "auto"}

    # max_tokens is required for Claude — if only max_completion_tokens set, copy it
    if "max_tokens" not in body and "max_completion_tokens" in body:
        body["max_tokens"] = body.pop("max_completion_tokens")


def _adapt_for_google(model: str, body: dict[str, Any]) -> None:
    """Remove unsupported params for Gemini models."""
    for key in _GOOGLE_UNSUPPORTED:
        body.pop(key, None)

    # Gemini uses max_output_tokens instead of max_tokens
    if "max_tokens" in body and "max_output_tokens" not in body:
        body["max_output_tokens"] = body.pop("max_tokens")


def _adapt_for_cohere(model: str, body: dict[str, Any]) -> None:
    """Remove unsupported params for Command models."""
    for key in _COHERE_UNSUPPORTED:
        body.pop(key, None)
