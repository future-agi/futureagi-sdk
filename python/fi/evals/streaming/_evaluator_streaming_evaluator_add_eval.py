"""StreamingEvaluator add eval operations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict
from fi.evals.streaming.evaluator import (Callable, ChunkResult, EarlyStopPolicy, Optional)

if TYPE_CHECKING:
    from fi.evals.streaming.evaluator import StreamingEvaluator


class _StreamingEvaluatorAddEvalMethods:
    __slots__ = ()

    def add_eval(
        self,
        name: str,
        eval_fn: Callable[[str, str], float],
        threshold: float = 0.7,
        weight: float = 1.0,
        pass_above: bool = True,
    ) -> "StreamingEvaluator":
        """
        Add an evaluation function.

        Args:
            name: Name of the evaluation
            eval_fn: Function that takes (chunk_text, cumulative_text) and returns score
            threshold: Passing threshold
            weight: Weight for final score calculation
            pass_above: If True, scores above threshold pass; if False, below

        Returns:
            Self for chaining
        """
        from fi.evals.streaming.evaluator import (Callable, EvalSpec)
        self._evals.append(
            EvalSpec(
                name=name,
                eval_fn=eval_fn,
                threshold=threshold,
                weight=weight,
                pass_above=pass_above,
            )
        )
        return self


    def set_policy(self, policy: EarlyStopPolicy) -> "StreamingEvaluator":
        """
        Set the early stop policy.

        Args:
            policy: Policy to use for early stopping

        Returns:
            Self for chaining
        """
        from fi.evals.streaming.evaluator import (EarlyStopPolicy)
        self._policy = policy
        return self


    def reset(self) -> None:
        """Reset the evaluator for a new stream."""
        from fi.evals.streaming.evaluator import (EarlyStopReason, StreamingState)
        self._buffer.reset()
        self._policy.reset()
        self._chunk_results = []
        self._state = StreamingState.IDLE
        self._start_time = 0.0
        self._stop_reason = EarlyStopReason.NONE
        self._stopped_at_chunk = None


    def process_token(self, token: str) -> Optional[ChunkResult]:
        """
        Process a single token from the stream.

        Args:
            token: The token text

        Returns:
            ChunkResult if evaluation was triggered, None otherwise
        """
        from fi.evals.streaming.evaluator import (ChunkResult, Optional, StreamingState, time)
        if self._state == StreamingState.IDLE:
            self._state = StreamingState.STREAMING
            self._start_time = time.perf_counter()

        if self._state in (StreamingState.STOPPED, StreamingState.COMPLETED, StreamingState.ERROR):
            return None

        # Add token to buffer
        self._buffer.add(token)

        # Check for limits
        should_stop_limits, limit_reason = self._buffer.should_stop_for_limits()
        if should_stop_limits:
            return self._handle_limit_stop(limit_reason)

        # Check if we should evaluate
        if not self._buffer.should_evaluate():
            return None

        # Run evaluation
        return self._evaluate_chunk()


    async def process_token_async(self, token: str) -> Optional[ChunkResult]:
        """
        Process a single token asynchronously.

        Args:
            token: The token text

        Returns:
            ChunkResult if evaluation was triggered, None otherwise
        """
        from fi.evals.streaming.evaluator import (ChunkResult, Optional, asyncio)
        # For now, wrap sync processing - can be optimized later
        return await asyncio.to_thread(self.process_token, token)


    def process_chunk(self, chunk: str) -> Optional[ChunkResult]:
        """
        Process a larger chunk of text (multiple tokens).

        Args:
            chunk: The chunk text

        Returns:
            ChunkResult if evaluation was triggered, None otherwise
        """
        from fi.evals.streaming.evaluator import (ChunkResult, Optional, StreamingState, time)
        if self._state == StreamingState.IDLE:
            self._state = StreamingState.STREAMING
            self._start_time = time.perf_counter()

        if self._state in (StreamingState.STOPPED, StreamingState.COMPLETED, StreamingState.ERROR):
            return None

        # Add chunk to buffer
        self._buffer.add_chunk(chunk)

        # Check for limits
        should_stop_limits, limit_reason = self._buffer.should_stop_for_limits()
        if should_stop_limits:
            return self._handle_limit_stop(limit_reason)

        # Check if we should evaluate
        if not self._buffer.should_evaluate():
            return None

        # Run evaluation
        return self._evaluate_chunk()


    def _evaluate_chunk(self) -> ChunkResult:
        """Run evaluations on the current chunk."""
        from fi.evals.streaming.evaluator import (
            ChunkResult, EarlyStopReason, StreamingState, time,
        )
        chunk_start = time.perf_counter()

        chunk_text = self._buffer.get_chunk()
        cumulative_text = self._buffer.get_cumulative()
        chunk_index = self._buffer.get_chunk_index()

        scores: Dict[str, float] = {}
        flags: Dict[str, bool] = {}

        # Run all evaluations
        for eval_spec in self._evals:
            try:
                score = eval_spec.eval_fn(chunk_text, cumulative_text)
                scores[eval_spec.name] = score

                # Determine if passed
                if eval_spec.pass_above:
                    flags[eval_spec.name] = score >= eval_spec.threshold
                else:
                    flags[eval_spec.name] = score <= eval_spec.threshold
            except Exception as e:
                # Handle eval errors gracefully
                scores[eval_spec.name] = 0.0
                flags[eval_spec.name] = False

        latency_ms = (time.perf_counter() - chunk_start) * 1000

        # Create chunk result
        chunk_result = ChunkResult(
            chunk_index=chunk_index,
            chunk_text=chunk_text,
            cumulative_text=cumulative_text,
            scores=scores,
            flags=flags,
            latency_ms=latency_ms,
        )

        # Check policy for early stop
        if self.config.enable_early_stop:
            should_stop, stop_reason = self._policy.check(chunk_result)

            if should_stop:
                chunk_result.should_stop = True
                chunk_result.stop_reason = stop_reason
                self._state = StreamingState.STOPPED
                self._stop_reason = stop_reason
                self._stopped_at_chunk = chunk_index

                # Trigger callback if configured
                if self.config.on_stop_callback:
                    self.config.on_stop_callback(stop_reason, cumulative_text)

            # Check stop on first failure
            elif self.config.stop_on_first_failure and not chunk_result.all_passed:
                chunk_result.should_stop = True
                chunk_result.stop_reason = EarlyStopReason.THRESHOLD
                self._state = StreamingState.STOPPED
                self._stop_reason = EarlyStopReason.THRESHOLD
                self._stopped_at_chunk = chunk_index

                # Trigger callback if configured
                if self.config.on_stop_callback:
                    self.config.on_stop_callback(EarlyStopReason.THRESHOLD, cumulative_text)

        # Store result
        self._chunk_results.append(chunk_result)

        # Mark as evaluated
        self._buffer.mark_evaluated()

        # Trigger chunk callback if configured
        if self.config.on_chunk_callback:
            self.config.on_chunk_callback(chunk_result)

        return chunk_result


    def _handle_limit_stop(self, reason: str) -> ChunkResult:
        """Handle stopping due to limits."""
        from fi.evals.streaming.evaluator import (ChunkResult, EarlyStopReason, StreamingState)
        # Evaluate any remaining content first
        if self._buffer.has_pending:
            chunk_result = self._evaluate_chunk()
        else:
            # Create a minimal result for the stop
            chunk_result = ChunkResult(
                chunk_index=self._buffer.get_chunk_index(),
                chunk_text="",
                cumulative_text=self._buffer.get_cumulative(),
                scores={},
                flags={},
            )

        # Map limit reason to stop reason
        if reason == "max_tokens":
            stop_reason = EarlyStopReason.MAX_TOKENS
        elif reason == "max_chars":
            stop_reason = EarlyStopReason.MAX_CHARS
        elif reason == "timeout":
            stop_reason = EarlyStopReason.TIMEOUT
        else:
            stop_reason = EarlyStopReason.ERROR

        chunk_result.should_stop = True
        chunk_result.stop_reason = stop_reason
        self._state = StreamingState.STOPPED
        self._stop_reason = stop_reason
        self._stopped_at_chunk = chunk_result.chunk_index

        return chunk_result
