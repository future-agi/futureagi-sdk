"""StreamingEvaluator finalize operations."""
from __future__ import annotations

from typing import TYPE_CHECKING
from fi.evals.streaming.evaluator import (
    AsyncIterator, Dict, Iterator, StreamingEvalResult, StreamingState,
)

if TYPE_CHECKING:
    from fi.evals.streaming.evaluator import StreamingEvaluator


class _StreamingEvaluatorFinalizeMethods:
    __slots__ = ()

    def finalize(self) -> StreamingEvalResult:
        """
        Finalize evaluation and return results.

        Should be called after stream completes or after early stop.

        Returns:
            StreamingEvalResult with all evaluation data
        """
        from fi.evals.streaming.evaluator import (StreamingEvalResult, StreamingState, time)
        # Evaluate any remaining pending content
        if self._buffer.has_pending and self._state == StreamingState.STREAMING:
            self._evaluate_chunk()

        # Mark as completed if not already stopped
        if self._state == StreamingState.STREAMING:
            self._state = StreamingState.COMPLETED

        # Calculate final scores (weighted average across chunks)
        final_scores = self._calculate_final_scores()

        # Determine overall pass/fail
        passed = self._determine_passed(final_scores)

        # Calculate total latency
        total_latency_ms = (time.perf_counter() - self._start_time) * 1000 if self._start_time else 0.0

        return StreamingEvalResult(
            passed=passed,
            final_text=self._buffer.get_cumulative(),
            total_chunks=len(self._chunk_results),
            chunk_results=self._chunk_results,
            final_scores=final_scores,
            early_stopped=self._state == StreamingState.STOPPED,
            stop_reason=self._stop_reason,
            stopped_at_chunk=self._stopped_at_chunk,
            total_latency_ms=total_latency_ms,
            state=self._state,
            metadata={
                "buffer_stats": self._buffer.get_stats(),
                "policy_stats": self._policy.get_stats(),
            },
        )


    def _calculate_final_scores(self) -> Dict[str, float]:
        """Calculate final weighted average scores."""
        from fi.evals.streaming.evaluator import (Dict)
        if not self._chunk_results:
            return {}

        # Build weight lookup from eval specs
        weights: Dict[str, float] = {e.name: e.weight for e in self._evals}

        final_scores: Dict[str, float] = {}
        weighted_sums: Dict[str, float] = {}
        weight_totals: Dict[str, float] = {}

        for chunk_result in self._chunk_results:
            for name, score in chunk_result.scores.items():
                w = weights.get(name, 1.0)
                if name not in weighted_sums:
                    weighted_sums[name] = 0.0
                    weight_totals[name] = 0.0
                weighted_sums[name] += score * w
                weight_totals[name] += w

        for name in weighted_sums:
            if weight_totals[name] > 0:
                final_scores[name] = weighted_sums[name] / weight_totals[name]
            else:
                final_scores[name] = 0.0

        return final_scores


    def _determine_passed(self, final_scores: Dict[str, float]) -> bool:
        """Determine if evaluation passed overall."""
        from fi.evals.streaming.evaluator import (Dict, EarlyStopReason, StreamingState)
        if self._state == StreamingState.STOPPED:
            # If stopped early due to safety/toxicity, fail
            if self._stop_reason in (
                EarlyStopReason.TOXICITY,
                EarlyStopReason.SAFETY,
                EarlyStopReason.PII,
                EarlyStopReason.JAILBREAK,
            ):
                return False

        # Check final scores against thresholds
        for eval_spec in self._evals:
            if eval_spec.name in final_scores:
                score = final_scores[eval_spec.name]
                if eval_spec.pass_above:
                    if score < eval_spec.threshold:
                        return False
                else:
                    if score > eval_spec.threshold:
                        return False

        return True


    @property
    def state(self) -> StreamingState:
        """Get current evaluation state."""
        from fi.evals.streaming.evaluator import (StreamingState)
        return self._state


    @property
    def is_stopped(self) -> bool:
        """Check if evaluation has stopped."""
        from fi.evals.streaming.evaluator import (StreamingState)
        return self._state in (StreamingState.STOPPED, StreamingState.COMPLETED, StreamingState.ERROR)


    @property
    def chunk_count(self) -> int:
        """Get number of chunks evaluated."""
        return len(self._chunk_results)


    def evaluate_stream(
        self,
        stream: Iterator[str],
    ) -> StreamingEvalResult:
        """
        Evaluate an entire stream synchronously.

        Args:
            stream: Iterator yielding tokens/chunks

        Returns:
            StreamingEvalResult after processing complete stream
        """
        from fi.evals.streaming.evaluator import (Iterator, StreamingEvalResult)
        self.reset()

        for token in stream:
            result = self.process_token(token)
            if result and result.should_stop:
                break

        return self.finalize()


    async def evaluate_stream_async(
        self,
        stream: AsyncIterator[str],
    ) -> StreamingEvalResult:
        """
        Evaluate an entire stream asynchronously.

        Args:
            stream: Async iterator yielding tokens/chunks

        Returns:
            StreamingEvalResult after processing complete stream
        """
        from fi.evals.streaming.evaluator import (AsyncIterator, StreamingEvalResult)
        self.reset()

        async for token in stream:
            result = await self.process_token_async(token)
            if result and result.should_stop:
                break

        return self.finalize()


    @classmethod
    def with_defaults(cls) -> "StreamingEvaluator":
        """
        Create an evaluator with default configuration.

        Returns:
            StreamingEvaluator with default settings
        """
        from fi.evals.streaming.evaluator import (EarlyStopPolicy, StreamingConfig)
        return cls(
            config=StreamingConfig(),
            policy=EarlyStopPolicy.default(),
        )


    @classmethod
    def for_safety(
        cls,
        toxicity_threshold: float = 0.5,
        safety_threshold: float = 0.5,
    ) -> "StreamingEvaluator":
        """
        Create an evaluator optimized for safety monitoring.

        Args:
            toxicity_threshold: Threshold for toxicity (stop if above)
            safety_threshold: Threshold for safety (stop if below)

        Returns:
            StreamingEvaluator configured for safety
        """
        from fi.evals.streaming.evaluator import (EarlyStopPolicy, StreamingConfig)
        config = StreamingConfig(
            enable_early_stop=True,
            stop_on_first_failure=True,
            toxicity_threshold=toxicity_threshold,
            safety_threshold=safety_threshold,
        )
        policy = EarlyStopPolicy.strict()
        return cls(config=config, policy=policy)


    @classmethod
    def for_quality(
        cls,
        min_chunk_size: int = 50,
        eval_interval_ms: int = 500,
    ) -> "StreamingEvaluator":
        """
        Create an evaluator optimized for quality assessment.

        Args:
            min_chunk_size: Minimum characters before evaluation
            eval_interval_ms: Milliseconds between evaluations

        Returns:
            StreamingEvaluator configured for quality
        """
        from fi.evals.streaming.evaluator import (EarlyStopPolicy, StreamingConfig)
        config = StreamingConfig(
            min_chunk_size=min_chunk_size,
            max_chunk_size=200,
            eval_interval_ms=eval_interval_ms,
            enable_early_stop=False,  # Don't stop early for quality
            eval_on_sentence_end=True,
        )
        policy = EarlyStopPolicy.permissive()
        return cls(config=config, policy=policy)
