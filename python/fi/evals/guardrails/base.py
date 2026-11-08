"""
Main Guardrails Class.

Provides the primary interface for content screening with support for:
- Multiple models (Turing, local models, third-party APIs)
- Input, output, and retrieval rails
- Ensemble mode with configurable aggregation
- Async and sync APIs
- Fast scanner pipeline for quick threat detection
"""

import asyncio
import functools
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, List, Optional, Type

from fi.evals.guardrails.config import (
    GuardrailsConfig,
    GuardrailModel,
    RailType,
    AggregationStrategy,
)
from fi.evals.guardrails.types import GuardrailResult, GuardrailsResponse
from fi.evals.guardrails.backends.base import BaseBackend
from fi.evals.guardrails.scanners import ScannerPipeline, create_default_pipeline

logger = logging.getLogger(__name__)


def _trace_guardrail(fn):
    """Decorator that wraps guardrail screen methods with OTEL spans."""
    @functools.wraps(fn)
    def wrapper(self, content, *args, **kwargs):
        try:
            from fi.evals.otel.enrichment import is_auto_enrichment_enabled
            if not is_auto_enrichment_enabled():
                raise ImportError
            from fi.evals.otel.conventions import (
                GenAIAttributes,
                GuardrailAttributes,
            )
            from opentelemetry import trace as _trace
        except ImportError:
            return fn(self, content, *args, **kwargs)

        tracer = _trace.get_tracer("fi.evals.guardrails")
        rail_type = args[0] if args else kwargs.get("rail_type", RailType.INPUT)
        span_name = f"guardrail.screen_{rail_type.value}"

        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute(GenAIAttributes.SPAN_KIND, "GUARDRAIL")
            span.set_attribute(GuardrailAttributes.GEN_AI_NAME, span_name)
            span.set_attribute(GuardrailAttributes.GEN_AI_TYPE, rail_type.value)
            span.set_attribute(GenAIAttributes.INPUT_MESSAGES, content)

            response = fn(self, content, *args, **kwargs)

            result_str = "allow" if response.passed else "block"
            span.set_attribute(GuardrailAttributes.GEN_AI_RESULT, result_str)
            if response.blocked_categories:
                span.set_attribute(
                    GuardrailAttributes.GEN_AI_CATEGORIES,
                    str(response.blocked_categories),
                )
            if response.total_latency_ms:
                span.set_attribute(GuardrailAttributes.LATENCY_MS, response.total_latency_ms)

            return response
    return wrapper


from ._base_guardrails_discover_backends import _GuardrailsDiscoverBackendsMethods
from ._base_guardrails_screen_retrieval_async import _GuardrailsScreenRetrievalAsyncMethods
from ._base_guardrails_screen_async import _GuardrailsScreenAsyncMethods

class Guardrails(
    _GuardrailsDiscoverBackendsMethods,
    _GuardrailsScreenRetrievalAsyncMethods,
    _GuardrailsScreenAsyncMethods,
):
    """
    Comprehensive guardrails system supporting multiple backends.

    Extends the existing Protect system with:
    - Local model support (Qwen3Guard, Granite Guardian, etc.)
    - Turing model integration
    - Ensemble mode with configurable aggregation
    - Input, output, and retrieval rails
    - Async and sync APIs

    Usage:
        # Quick start with defaults (uses Turing Flash)
        guardrails = Guardrails()
        result = guardrails.screen_input("user message")

        # Advanced: Ensemble with multiple models
        guardrails = Guardrails(
            config=GuardrailsConfig(
                models=[
                    GuardrailModel.TURING_FLASH,
                    GuardrailModel.QWEN3GUARD_8B,
                ],
                aggregation=AggregationStrategy.MAJORITY,
            )
        )
    """

    def __init__(
        self,
        config: Optional[GuardrailsConfig] = None,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
    ):
        """
        Initialize the Guardrails system.

        Args:
            config: Configuration for the guardrails system
            fi_api_key: FutureAGI API key (for Turing models)
            fi_secret_key: FutureAGI secret key
            fi_base_url: Base URL for FutureAGI API
        """
        self.config = config or GuardrailsConfig()
        self._fi_api_key = fi_api_key
        self._fi_secret_key = fi_secret_key
        self._fi_base_url = fi_base_url
        self.backends: Dict[GuardrailModel, BaseBackend] = {}
        self.scanner_pipeline: Optional[ScannerPipeline] = None

        self._load_backends()
        self._load_scanners()
