"""LocalModelBackend classify async operations."""
from __future__ import annotations

from fi.evals.guardrails.backends.local_base import (
    Any, Dict, GuardrailResult, List, Optional, RailType,
)


class _LocalModelBackendClassifyAsyncMethods:
    __slots__ = ()

    async def classify_async(
        self,
        content: str,
        rail_type: RailType,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[GuardrailResult]:
        """
        Async version of classify.

        Uses VLLM async client if available, otherwise falls back to sync.

        Args:
            content: Content to classify
            rail_type: Type of rail
            context: Optional context
            metadata: Optional metadata

        Returns:
            List of GuardrailResult objects
        """
        from fi.evals.guardrails.backends.local_base import (
            Any, Dict, GuardrailResult, List, Optional, RailType, time,
        )
        start_time = time.time()

        # Handle empty content
        if not content or not content.strip():
            return [
                GuardrailResult(
                    passed=True,
                    category="empty",
                    score=0.0,
                    model=self.model_name,
                    reason="Empty or whitespace-only content",
                    action="pass",
                    latency_ms=(time.time() - start_time) * 1000,
                )
            ]

        try:
            # Format prompt
            prompt = self._format_prompt(content, rail_type, context)

            # Generate response
            if self._use_vllm and self._vllm_client:
                vllm_response = await self._vllm_client.chat_async(
                    messages=[{"role": "user", "content": content}],
                    max_tokens=self.MAX_NEW_TOKENS,
                    temperature=self.TEMPERATURE,
                )
                response_text = vllm_response.text
            else:
                # Fall back to sync for transformers
                import asyncio
                response_text = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._generate_with_transformers(prompt)
                )

            elapsed_ms = (time.time() - start_time) * 1000

            # Parse response
            results = self._parse_response(response_text, content, rail_type)

            # Update latency in results
            for result in results:
                result.latency_ms = elapsed_ms

            return results

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return [
                GuardrailResult(
                    passed=False,
                    category="error",
                    score=0.0,
                    model=self.model_name,
                    reason=f"Local model error: {str(e)}",
                    action="block",
                    latency_ms=elapsed_ms,
                )
            ]


    def _infer_categories(self, content: str, response: str) -> List[str]:
        """Infer safety categories from content + response via keyword matching."""
        from fi.evals.guardrails.backends.local_base import (List)
        combined = (content + " " + response).lower()
        categories = [
            cat for cat, keywords in self._CATEGORY_KEYWORDS.items()
            if any(kw in combined for kw in keywords)
        ]
        return categories if categories else ["harmful_content"]


    def is_available(self) -> bool:
        """
        Check if this backend is available.

        Returns:
            True if VLLM server is up or transformers can load the model
        """
        if self._use_vllm:
            return True

        # Check if we can load via transformers
        try:
            import torch
            has_gpu = torch.cuda.is_available() or (
                hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
            )
            return has_gpu or self._device == "cpu"
        except ImportError:
            return False
