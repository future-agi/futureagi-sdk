"""LLMSpanProcessor compile redact patterns operations."""
from __future__ import annotations

from fi.evals.otel.processors.llm import (Any, Dict, Optional, ReadableSpan)


class _LLMSpanProcessorCompileRedactPatternsMethods:
    __slots__ = ()

    def _compile_redact_patterns(self) -> None:
        """Compile redaction regex patterns."""
        from fi.evals.otel.processors.llm import (logger)
        import re
        self._compiled_patterns = []
        for pattern in self._redact_patterns:
            try:
                self._compiled_patterns.append(re.compile(pattern))
            except Exception as e:
                logger.warning(f"Invalid redact pattern '{pattern}': {e}")


    def should_process(self, span: ReadableSpan) -> bool:
        """Check if this span should be processed as an LLM span."""
        from fi.evals.otel.processors.llm import (ReadableSpan)
        if not self.enabled:
            return False

        span_name = self._get_span_name(span).lower()

        # If filter is set, only process matching spans
        if self._span_filter:
            return any(f.lower() in span_name for f in self._span_filter)

        # Otherwise, detect LLM spans by name patterns
        return any(pattern in span_name for pattern in self.LLM_SPAN_PATTERNS)


    def _get_span_name(self, span: ReadableSpan) -> str:
        """Get span name safely."""
        from fi.evals.otel.processors.llm import (ReadableSpan)
        try:
            return span.name or ""
        except Exception:
            return ""


    def _get_attributes(self, span: ReadableSpan) -> Dict[str, Any]:
        """Get span attributes safely."""
        from fi.evals.otel.processors.llm import (Any, Dict, ReadableSpan)
        try:
            return dict(span.attributes or {})
        except Exception:
            return {}


    def on_end(self, span: ReadableSpan) -> None:
        """
        Process and enrich an LLM span.

        Note: In OpenTelemetry, spans are immutable after ending.
        This processor extracts data for logging/metrics but cannot
        modify the span. For mutation, use on_start or custom exporters.
        """
        from fi.evals.otel.processors.llm import (ReadableSpan, logger)
        if not self.should_process(span):
            return

        try:
            attrs = self._get_attributes(span)
            enriched = self._extract_llm_attributes(attrs)

            # Log enriched attributes (actual modification requires exporter)
            if enriched:
                logger.debug(f"LLM span enrichment: {enriched}")

        except Exception as e:
            logger.warning(f"LLM span processing error: {e}")


    def _extract_llm_attributes(
        self,
        attrs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extract and normalize LLM attributes.

        Args:
            attrs: Raw span attributes

        Returns:
            Normalized GenAI attributes
        """
        from fi.evals.otel.processors.llm import (Any, Dict, GenAIAttributes)
        enriched: Dict[str, Any] = {}

        # Set span kind
        enriched[GenAIAttributes.SPAN_KIND] = "LLM"

        # Extract system/provider
        system = self._extract_system(attrs)
        if system:
            enriched[GenAIAttributes.PROVIDER_NAME] = system

        # Extract operation type
        operation = self._extract_operation(attrs)
        if operation:
            enriched[GenAIAttributes.OPERATION_NAME] = operation

        # Extract model
        model = self._extract_model(attrs)
        if model:
            enriched[GenAIAttributes.REQUEST_MODEL] = model

        # Extract token usage
        tokens = self._extract_token_usage(attrs)
        if tokens.get("input_tokens") is not None:
            enriched[GenAIAttributes.USAGE_INPUT_TOKENS] = tokens["input_tokens"]
        if tokens.get("output_tokens") is not None:
            enriched[GenAIAttributes.USAGE_OUTPUT_TOKENS] = tokens["output_tokens"]
        if tokens.get("input_tokens") is not None and tokens.get("output_tokens") is not None:
            enriched[GenAIAttributes.USAGE_TOTAL_TOKENS] = (
                tokens["input_tokens"] + tokens["output_tokens"]
            )

        # Extract request parameters
        params = self._extract_request_params(attrs)
        if params.get("temperature") is not None:
            enriched[GenAIAttributes.REQUEST_TEMPERATURE] = params["temperature"]
        if params.get("max_tokens") is not None:
            enriched[GenAIAttributes.REQUEST_MAX_TOKENS] = params["max_tokens"]
        if params.get("top_p") is not None:
            enriched[GenAIAttributes.REQUEST_TOP_P] = params["top_p"]

        # Extract finish reason
        finish_reason = self._extract_finish_reason(attrs)
        if finish_reason:
            enriched[GenAIAttributes.RESPONSE_FINISH_REASON] = finish_reason

        # Extract content (with redaction)
        if self._capture_prompts:
            prompt = self._extract_prompt(attrs)
            if prompt:
                enriched[GenAIAttributes.INPUT_MESSAGES] = prompt

        if self._capture_completions:
            completion = self._extract_completion(attrs)
            if completion:
                enriched[GenAIAttributes.OUTPUT_MESSAGES] = completion

        return enriched


    def _extract_system(self, attrs: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize the LLM system/provider."""
        from fi.evals.otel.processors.llm import (
            Any, Dict, GenAIAttributes, Optional, normalize_system_name,
        )
        # Check standard attribute first
        system = attrs.get(GenAIAttributes.SYSTEM)
        if system:
            return normalize_system_name(str(system))

        # Try common alternatives
        for key in ["llm.provider", "llm.system", "provider", "vendor"]:
            if key in attrs:
                return normalize_system_name(str(attrs[key]))

        # Try to infer from model name
        model = self._extract_model(attrs)
        if model:
            model_lower = model.lower()
            if "gpt" in model_lower or "davinci" in model_lower:
                return "openai"
            if "claude" in model_lower:
                return "anthropic"
            if "gemini" in model_lower or "palm" in model_lower:
                return "google"
            if "mistral" in model_lower or "mixtral" in model_lower:
                return "mistral"
            if "llama" in model_lower:
                return "meta"
            if "command" in model_lower:
                return "cohere"

        return None


    def _extract_operation(self, attrs: Dict[str, Any]) -> Optional[str]:
        """Extract the operation type."""
        from fi.evals.otel.processors.llm import (
            Any, Dict, GenAIAttributes, OPERATION_CHAT, OPERATION_COMPLETION, OPERATION_EMBEDDING,
            Optional,
        )
        # Check standard attribute
        operation = attrs.get(GenAIAttributes.OPERATION_NAME)
        if operation:
            return str(operation)

        # Try alternatives
        for key in ["llm.operation", "operation_name", "llm.request_type"]:
            if key in attrs:
                return str(attrs[key])

        # Infer from context
        if attrs.get("llm.is_embedding") or attrs.get("is_embedding"):
            return OPERATION_EMBEDDING
        if any("chat" in str(v).lower() for v in attrs.values()):
            return OPERATION_CHAT

        return OPERATION_COMPLETION


    def _extract_model(self, attrs: Dict[str, Any]) -> Optional[str]:
        """Extract the model name."""
        from fi.evals.otel.processors.llm import (Any, Dict, GenAIAttributes, Optional)
        for key in [
            GenAIAttributes.REQUEST_MODEL,
            GenAIAttributes.RESPONSE_MODEL,
            "llm.model",
            "model",
            "model_name",
            "llm.request.model",
        ]:
            if key in attrs:
                return str(attrs[key])
        return None


    def _extract_token_usage(self, attrs: Dict[str, Any]) -> Dict[str, Optional[int]]:
        """Extract token usage from various attribute formats."""
        from fi.evals.otel.processors.llm import (Any, Dict, GenAIAttributes, Optional)
        result: Dict[str, Optional[int]] = {
            "input_tokens": None,
            "output_tokens": None,
        }

        # Check standard attributes first
        if GenAIAttributes.USAGE_INPUT_TOKENS in attrs:
            try:
                result["input_tokens"] = int(attrs[GenAIAttributes.USAGE_INPUT_TOKENS])
            except (ValueError, TypeError):
                pass
        if GenAIAttributes.USAGE_OUTPUT_TOKENS in attrs:
            try:
                result["output_tokens"] = int(attrs[GenAIAttributes.USAGE_OUTPUT_TOKENS])
            except (ValueError, TypeError):
                pass

        # Check provider-specific mappings
        for raw_key, normalized_key in self.PROVIDER_TOKEN_MAPPINGS.items():
            if raw_key in attrs and result.get(normalized_key) is None:
                try:
                    result[normalized_key] = int(attrs[raw_key])
                except (ValueError, TypeError):
                    pass

        return result


    def _extract_request_params(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract request parameters."""
        from fi.evals.otel.processors.llm import (Any, Dict, GenAIAttributes)
        params: Dict[str, Any] = {}

        # Temperature
        for key in [GenAIAttributes.REQUEST_TEMPERATURE, "llm.temperature", "temperature"]:
            if key in attrs:
                try:
                    params["temperature"] = float(attrs[key])
                    break
                except (ValueError, TypeError):
                    pass

        # Max tokens
        for key in [GenAIAttributes.REQUEST_MAX_TOKENS, "llm.max_tokens", "max_tokens"]:
            if key in attrs:
                try:
                    params["max_tokens"] = int(attrs[key])
                    break
                except (ValueError, TypeError):
                    pass

        # Top P
        for key in [GenAIAttributes.REQUEST_TOP_P, "llm.top_p", "top_p"]:
            if key in attrs:
                try:
                    params["top_p"] = float(attrs[key])
                    break
                except (ValueError, TypeError):
                    pass

        return params
