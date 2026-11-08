"""LLMSpanProcessor extract finish reason operations."""
from __future__ import annotations

from fi.evals.otel.processors.llm import (Any, Dict, Optional)


class _LLMSpanProcessorExtractFinishReasonMethods:
    __slots__ = ()

    def _extract_finish_reason(self, attrs: Dict[str, Any]) -> Optional[str]:
        """Extract the finish reason."""
        from fi.evals.otel.processors.llm import (Any, Dict, GenAIAttributes, Optional)
        for key in [
            GenAIAttributes.RESPONSE_FINISH_REASON,
            "llm.finish_reason",
            "finish_reason",
            "stop_reason",
        ]:
            if key in attrs:
                return str(attrs[key])
        return None


    def _extract_prompt(self, attrs: Dict[str, Any]) -> Optional[str]:
        """Extract and process prompt content."""
        from fi.evals.otel.processors.llm import (Any, Dict, GenAIAttributes, Optional, json)
        content = None

        # Try standard format first
        for key in [GenAIAttributes.prompt_content(0), "llm.prompt", "prompt", "input"]:
            if key in attrs:
                content = attrs[key]
                break

        # Try messages format
        if content is None:
            messages = attrs.get("llm.messages") or attrs.get("messages")
            if messages:
                if isinstance(messages, str):
                    try:
                        messages = json.loads(messages)
                    except json.JSONDecodeError:
                        content = messages
                if isinstance(messages, list) and content is None:
                    # Concatenate message contents
                    content = "\n".join(
                        str(m.get("content", ""))
                        for m in messages
                        if isinstance(m, dict)
                    )

        if content is None:
            return None

        content = str(content)
        return self._process_content(content)


    def _extract_completion(self, attrs: Dict[str, Any]) -> Optional[str]:
        """Extract and process completion content."""
        from fi.evals.otel.processors.llm import (Any, Dict, GenAIAttributes, Optional, json)
        content = None

        # Try standard format first
        for key in [
            GenAIAttributes.completion_content(0),
            "llm.completion",
            "completion",
            "output",
            "response",
        ]:
            if key in attrs:
                content = attrs[key]
                break

        # Try choices format
        if content is None:
            choices = attrs.get("llm.choices") or attrs.get("choices")
            if choices:
                if isinstance(choices, str):
                    try:
                        choices = json.loads(choices)
                    except json.JSONDecodeError:
                        content = choices
                if isinstance(choices, list) and content is None:
                    # Get first choice content
                    if choices and isinstance(choices[0], dict):
                        msg = choices[0].get("message", choices[0])
                        if isinstance(msg, dict):
                            content = msg.get("content")
                        else:
                            content = str(msg)

        if content is None:
            return None

        content = str(content)
        return self._process_content(content)


    def _process_content(self, content: str) -> str:
        """Process content: truncate and redact."""
        # Truncate
        if len(content) > self._max_content_length:
            content = content[:self._max_content_length] + "... [truncated]"

        # Redact patterns
        for pattern in self._compiled_patterns:
            content = pattern.sub("[REDACTED]", content)

        return content
