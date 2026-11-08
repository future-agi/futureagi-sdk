"""Streaming Evaluator for real-time LLM output evaluation.

Evaluates LLM outputs in real-time as tokens stream in, with support for
early stopping based on configurable policies.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
)

from .types import (
    ChunkResult,
    EarlyStopReason,
    StreamingConfig,
    StreamingEvalResult,
    StreamingState,
)
from .buffer import ChunkBuffer
from .policy import EarlyStopPolicy


@dataclass
class EvalSpec:
    """Specification for a streaming evaluation."""

    name: str
    eval_fn: Callable[[str, str], float]  # (chunk, cumulative) -> score
    threshold: float = 0.7
    weight: float = 1.0
    pass_above: bool = True  # True if higher scores are better


from fi.evals._extracted import bind_owner as _bind_owner
from ._evaluator_streaming_evaluator_add_eval import _StreamingEvaluatorAddEvalMethods
from ._evaluator_streaming_evaluator_finalize import _StreamingEvaluatorFinalizeMethods

class StreamingEvaluator(_StreamingEvaluatorAddEvalMethods, _StreamingEvaluatorFinalizeMethods):
    """
    Evaluates LLM outputs in real-time as tokens stream in.

    Supports early stopping based on configurable policies and provides
    detailed per-chunk and aggregate evaluation results.

    Example:
        evaluator = StreamingEvaluator(config)
        evaluator.add_eval("toxicity", toxicity_scorer, threshold=0.7, pass_above=False)
        evaluator.set_policy(EarlyStopPolicy.default())

        # Synchronous iteration
        for token in stream:
            result = evaluator.process_token(token)
            if result and result.should_stop:
                break

        final_result = evaluator.finalize()

        # Or async iteration
        async for token in async_stream:
            result = await evaluator.process_token_async(token)
            if result and result.should_stop:
                break
    """

    def __init__(
        self,
        config: Optional[StreamingConfig] = None,
        policy: Optional[EarlyStopPolicy] = None,
    ):
        """
        Initialize the streaming evaluator.

        Args:
            config: Streaming configuration (uses defaults if None)
            policy: Early stop policy (uses default if None)
        """
        self.config = config or StreamingConfig()
        self._policy = policy or EarlyStopPolicy.default()
        self._buffer = ChunkBuffer(self.config)
        self._evals: List[EvalSpec] = []
        self._chunk_results: List[ChunkResult] = []
        self._state = StreamingState.IDLE
        self._start_time: float = 0.0
        self._stop_reason = EarlyStopReason.NONE
        self._stopped_at_chunk: Optional[int] = None


_bind_owner(StreamingEvaluator)
