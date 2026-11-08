"""Pricing for cost."""
from __future__ import annotations

from fi.evals.otel.processors.cost import (Dict, TokenPricing)

DEFAULT_PRICING: Dict[str, TokenPricing] = {
    # OpenAI Models
    "gpt-4o": TokenPricing("gpt-4o", 0.005, 0.015),
    "gpt-4o-mini": TokenPricing("gpt-4o-mini", 0.00015, 0.0006),
    "gpt-4-turbo": TokenPricing("gpt-4-turbo", 0.01, 0.03),
    "gpt-4": TokenPricing("gpt-4", 0.03, 0.06),
    "gpt-4-32k": TokenPricing("gpt-4-32k", 0.06, 0.12),
    "gpt-3.5-turbo": TokenPricing("gpt-3.5-turbo", 0.0005, 0.0015),
    "gpt-3.5-turbo-16k": TokenPricing("gpt-3.5-turbo-16k", 0.003, 0.004),

    # Anthropic Models
    "claude-3-opus-20240229": TokenPricing("claude-3-opus-20240229", 0.015, 0.075),
    "claude-3-sonnet-20240229": TokenPricing("claude-3-sonnet-20240229", 0.003, 0.015),
    "claude-3-haiku-20240307": TokenPricing("claude-3-haiku-20240307", 0.00025, 0.00125),
    "claude-3-5-sonnet-20241022": TokenPricing("claude-3-5-sonnet-20241022", 0.003, 0.015),
    "claude-2.1": TokenPricing("claude-2.1", 0.008, 0.024),
    "claude-2.0": TokenPricing("claude-2.0", 0.008, 0.024),
    "claude-instant-1.2": TokenPricing("claude-instant-1.2", 0.0008, 0.0024),

    # Google Models
    "gemini-1.5-pro": TokenPricing("gemini-1.5-pro", 0.00125, 0.005),
    "gemini-1.5-flash": TokenPricing("gemini-1.5-flash", 0.000075, 0.0003),
    "gemini-pro": TokenPricing("gemini-pro", 0.00025, 0.0005),

    # Mistral Models
    "mistral-large-latest": TokenPricing("mistral-large-latest", 0.004, 0.012),
    "mistral-medium-latest": TokenPricing("mistral-medium-latest", 0.0027, 0.0081),
    "mistral-small-latest": TokenPricing("mistral-small-latest", 0.001, 0.003),
    "open-mixtral-8x7b": TokenPricing("open-mixtral-8x7b", 0.0007, 0.0007),
    "open-mistral-7b": TokenPricing("open-mistral-7b", 0.00025, 0.00025),

    # Cohere Models
    "command-r-plus": TokenPricing("command-r-plus", 0.003, 0.015),
    "command-r": TokenPricing("command-r", 0.0005, 0.0015),
    "command": TokenPricing("command", 0.001, 0.002),
    "command-light": TokenPricing("command-light", 0.0003, 0.0006),

    # Meta/Llama Models (typical cloud pricing)
    "llama-3-70b": TokenPricing("llama-3-70b", 0.0009, 0.0009),
    "llama-3-8b": TokenPricing("llama-3-8b", 0.0002, 0.0002),
    "llama-2-70b": TokenPricing("llama-2-70b", 0.0009, 0.0009),
    "llama-2-13b": TokenPricing("llama-2-13b", 0.0002, 0.0002),

    # Embedding Models
    "text-embedding-3-large": TokenPricing("text-embedding-3-large", 0.00013, 0.0),
    "text-embedding-3-small": TokenPricing("text-embedding-3-small", 0.00002, 0.0),
    "text-embedding-ada-002": TokenPricing("text-embedding-ada-002", 0.0001, 0.0),
}


MODEL_ALIASES: Dict[str, str] = {
    # OpenAI
    "gpt-4-0613": "gpt-4",
    "gpt-4-1106-preview": "gpt-4-turbo",
    "gpt-4-0125-preview": "gpt-4-turbo",
    "gpt-4-turbo-preview": "gpt-4-turbo",
    "gpt-3.5-turbo-0125": "gpt-3.5-turbo",
    "gpt-3.5-turbo-1106": "gpt-3.5-turbo",

    # Anthropic
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-haiku": "claude-3-haiku-20240307",
    "claude-3.5-sonnet": "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",

    # Google
    "gemini-pro-vision": "gemini-pro",
    "gemini-1.0-pro": "gemini-pro",

    # Mistral
    "mistral-large": "mistral-large-latest",
    "mistral-medium": "mistral-medium-latest",
    "mistral-small": "mistral-small-latest",
}
