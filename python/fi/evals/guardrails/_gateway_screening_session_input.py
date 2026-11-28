"""ScreeningSession input operations."""
from __future__ import annotations

from fi.evals.guardrails.gateway import (GuardrailsResponse, List, Optional)


class _ScreeningSessionInputMethods:
    __slots__ = ()

    def input(self, content: str, metadata: Optional[dict] = None) -> GuardrailsResponse:
        """Screen user input.

        Args:
            content: The user input to screen.
            metadata: Optional metadata for the request.

        Returns:
            GuardrailsResponse with screening results.
        """
        from fi.evals.guardrails.gateway import (GuardrailsResponse, Optional)
        result = self._guardrails.screen_input(content, metadata=metadata)
        self._history.append(result)
        return result


    def output(
        self,
        content: str,
        context: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> GuardrailsResponse:
        """Screen LLM output.

        Args:
            content: The LLM response to screen.
            context: Optional original user query for context.
            metadata: Optional metadata for the request.

        Returns:
            GuardrailsResponse with screening results.
        """
        from fi.evals.guardrails.gateway import (GuardrailsResponse, Optional)
        result = self._guardrails.screen_output(content, context=context, metadata=metadata)
        self._history.append(result)
        return result


    def retrieval(
        self,
        chunks: List[str],
        query: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> List[GuardrailsResponse]:
        """Screen retrieval chunks.

        Args:
            chunks: List of document chunks to screen.
            query: Optional user query for context.
            metadata: Optional metadata for the request.

        Returns:
            List of GuardrailsResponse, one per chunk.
        """
        from fi.evals.guardrails.gateway import (GuardrailsResponse, List, Optional)
        results = self._guardrails.screen_retrieval(chunks, query=query, metadata=metadata)
        self._history.extend(results)
        return results


    @property
    def history(self) -> List[GuardrailsResponse]:
        """Get the history of all screening results in this session."""
        from fi.evals.guardrails.gateway import (GuardrailsResponse, List)
        return self._history.copy()


    @property
    def all_passed(self) -> bool:
        """Check if all screenings in this session passed."""
        return all(r.passed for r in self._history)
