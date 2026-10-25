"""Token counting and cost estimation utilities."""

from __future__ import annotations

import json
from typing import Any

from fi.gateway._models_info import get_model_info


def encode(model: str, text: str) -> list[int]:
    """Encode text into token IDs using tiktoken.

    Args:
        model: Model name (used to select the tokenizer).
        text: Text to encode.

    Returns:
        List of token IDs.

    Raises:
        ImportError: If ``tiktoken`` is not installed.
    """
    try:
        import tiktoken
    except ImportError:
        raise ImportError(
            "tiktoken is required for encode(). "
            "Install it with: pip install tiktoken"
        ) from None

    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    return enc.encode(text)


def decode(model: str, tokens: list[int]) -> str:
    """Decode token IDs back to text using tiktoken.

    Args:
        model: Model name (used to select the tokenizer).
        tokens: List of token IDs to decode.

    Returns:
        Decoded text string.

    Raises:
        ImportError: If ``tiktoken`` is not installed.
    """
    try:
        import tiktoken
    except ImportError:
        raise ImportError(
            "tiktoken is required for decode(). "
            "Install it with: pip install tiktoken"
        ) from None

    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")

    return enc.decode(tokens)


def trim_messages(
    messages: list[dict[str, Any]],
    model: str,
    trim_ratio: float = 0.75,
    max_tokens: int | None = None,
) -> list[dict[str, Any]]:
    """Trim messages to fit within the model's context window.

    Keeps system messages and removes oldest user/assistant messages first
    until the total token count is within ``trim_ratio * max_tokens``.
    If *max_tokens* is provided, use that instead of model lookup.

    Args:
        messages: List of chat messages.
        model: Model name (used for tokenizer and context window lookup).
        trim_ratio: Fraction of the context window to use (default ``0.75``).
        max_tokens: Override context window size. If ``None``, looks up
            the model's max tokens from the model info database.

    Returns:
        Trimmed list of messages that fits within the token budget.

    Raises:
        ValueError: If the model is unknown and *max_tokens* is not provided.
    """
    if max_tokens is None:
        info = get_model_info(model)
        if info is None:
            raise ValueError(
                f"Unknown model {model!r}. "
                "Provide max_tokens explicitly or register the model first."
            )
        max_tokens = info.max_tokens

    budget = int(max_tokens * trim_ratio)

    # Check if messages already fit
    total = token_counter(model, messages=messages)
    if total <= budget:
        return list(messages)

    # Separate system messages from the rest
    system_msgs: list[dict[str, Any]] = []
    non_system_msgs: list[dict[str, Any]] = []
    for msg in messages:
        if msg.get("role") == "system":
            system_msgs.append(msg)
        else:
            non_system_msgs.append(msg)

    # Start with system messages (always kept)
    result = list(system_msgs)
    system_tokens = token_counter(model, messages=system_msgs) if system_msgs else 0
    remaining_budget = budget - system_tokens

    # Add non-system messages from newest to oldest until budget is exhausted
    kept: list[dict[str, Any]] = []
    running_tokens = 0
    for msg in reversed(non_system_msgs):
        msg_tokens = token_counter(model, messages=[msg])
        if running_tokens + msg_tokens <= remaining_budget:
            kept.append(msg)
            running_tokens += msg_tokens
        else:
            break

    # Reverse to restore chronological order and append after system messages
    kept.reverse()
    result.extend(kept)
    return result


def token_counter(
    model: str,
    text: str | None = None,
    messages: list[dict[str, Any]] | None = None,
) -> int:
    """Count tokens for text or messages.

    Uses ``tiktoken`` if installed, otherwise falls back to a character-based
    estimate (~4 chars per token for English text).

    Args:
        model: Model name (used to select the tokenizer).
        text: Raw text to count tokens for.
        messages: Chat messages list to count tokens for.

    Returns:
        Estimated token count.
    """
    if text is None and messages is None:
        return 0

    content = ""
    overhead = 0
    if text is not None:
        content = text
    elif messages is not None:
        # Serialize messages to estimate total tokens
        parts: list[str] = []
        for msg in messages:
            parts.append(msg.get("role", ""))
            msg_content = msg.get("content", "")
            if isinstance(msg_content, str):
                parts.append(msg_content)
            elif isinstance(msg_content, list):
                for part in msg_content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        parts.append(part.get("text", ""))
            # Tool calls
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                parts.append(json.dumps(tool_calls))
        content = "\n".join(parts)
        # Add overhead per message (~4 tokens per message for chat format)
        overhead = len(messages) * 4 + 2  # 2 for priming

    try:
        import tiktoken

        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")

        count = len(enc.encode(content))
        if messages is not None:
            count += overhead
        return count
    except ImportError:
        # Fallback: ~4 characters per token for English
        count = len(content) // 4
        if messages is not None:
            count += overhead
        return max(count, 1)


def get_max_tokens(model: str) -> int | None:
    """Return the context window size for a model.

    Returns:
        Max input tokens, or ``None`` if model is unknown.
    """
    info = get_model_info(model)
    return info.max_tokens if info else None


def get_max_output_tokens(model: str) -> int | None:
    """Return the max output tokens for a model."""
    info = get_model_info(model)
    return info.max_output_tokens if info else None


def completion_cost(
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> float | None:
    """Estimate the cost of a completion.

    Args:
        model: Model name.
        prompt_tokens: Number of input tokens.
        completion_tokens: Number of output tokens.

    Returns:
        Estimated cost in USD, or ``None`` if model is unknown.
    """
    info = get_model_info(model)
    if info is None:
        return None
    return (prompt_tokens * info.input_cost_per_token) + (completion_tokens * info.output_cost_per_token)


# --- Context window fallbacks ---

CONTEXT_WINDOW_FALLBACKS: dict[str, str] = {
    "gpt-4": "gpt-4-turbo",
    "gpt-4-turbo": "gpt-4o",
    "gpt-3.5-turbo": "gpt-4o-mini",
    "claude-3-haiku-20240307": "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229": "claude-sonnet-4-20250514",
}


def get_context_window_fallback(model: str) -> str | None:
    """Return a model with a larger context window, or ``None``."""
    return CONTEXT_WINDOW_FALLBACKS.get(model)


# --- Content policy fallbacks ---

CONTENT_POLICY_FALLBACKS: dict[str, str] = {
    "gpt-4o": "gpt-4-turbo",
    "gpt-4o-mini": "gpt-3.5-turbo",
}


def get_content_policy_fallback(model: str) -> str | None:
    """Return a less restrictive model for content policy errors, or ``None``."""
    return CONTENT_POLICY_FALLBACKS.get(model)


def is_prompt_caching_valid(model: str, messages: list[dict[str, Any]]) -> tuple[bool, str]:
    """Check if a prompt qualifies for provider-side caching.

    Inspects the model name and message structure to determine whether
    prompt caching can be leveraged.

    Args:
        model: The model name (e.g. ``'claude-3-5-sonnet-20241022'``, ``'gpt-4o'``).
        messages: Chat messages list.

    Returns:
        Tuple of (is_eligible, reason_string).
    """
    # Check for Anthropic models with cache_control
    if "claude" in model.lower():
        for msg in messages:
            if "cache_control" in msg:
                return (True, "Anthropic cache_control detected")
            # Also check content parts for cache_control
            content = msg.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and "cache_control" in part:
                        return (True, "Anthropic cache_control detected")

    # Check for OpenAI models with long system prompts
    if any(prefix in model.lower() for prefix in ("gpt-", "o1", "o3")):
        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content", "")
                if isinstance(system_content, str):
                    system_tokens = token_counter(model, text=system_content)
                    if system_tokens >= 1024:
                        return (True, "System prompt eligible for OpenAI automatic caching")

    return (False, "No caching indicators found")


def completion_cost_from_response(response: Any) -> float | None:
    """Estimate cost from a ChatCompletion response object.

    First checks ``response.agentcc.cost`` (actual cost from gateway),
    falling back to local estimation if not available.
    """
    # Try gateway-reported cost first
    agentcc = getattr(response, "agentcc", None)
    if agentcc and getattr(agentcc, "cost", None) is not None:
        return agentcc.cost  # type: ignore[no-any-return]

    # Fall back to estimation
    usage = getattr(response, "usage", None)
    model = getattr(response, "model", None)
    if usage and model:
        return completion_cost(
            model=model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0),
            completion_tokens=getattr(usage, "completion_tokens", 0),
        )
    return None
