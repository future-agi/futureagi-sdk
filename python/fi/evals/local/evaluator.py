"""Local evaluator for running metrics without API calls.

This module provides the LocalEvaluator class which can run heuristic
metrics locally, enabling offline evaluation and faster feedback loops.

It also provides the HybridEvaluator which can intelligently route
evaluations between local execution, local LLM, and cloud APIs.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
import time
import logging

from ..types import BatchRunResult, EvalResult
from .execution_mode import RoutingMode, can_run_locally, select_routing_mode
from .registry import get_registry, LocalMetricRegistry

if TYPE_CHECKING:
    from .llm import OllamaLLM

logger = logging.getLogger(__name__)


@dataclass
class LocalEvaluatorConfig:
    """Configuration for the local evaluator.

    Attributes:
        execution_mode: The default execution mode.
        fail_on_unsupported: If True, raise an error when a metric can't run locally.
        parallel_workers: Number of parallel workers (for future use).
        timeout: Timeout in seconds for individual evaluations.
    """

    execution_mode: RoutingMode = RoutingMode.HYBRID
    fail_on_unsupported: bool = False
    parallel_workers: int = 4
    timeout: int = 60


@dataclass
class LocalEvaluationResult:
    """Result of a local evaluation operation.

    Attributes:
        results: The batch run results.
        executed_locally: Set of metric names that ran locally.
        skipped: Set of metric names that were skipped (not local-capable).
        errors: Dictionary mapping metric names to error messages.
    """

    results: BatchRunResult
    executed_locally: set = field(default_factory=set)
    skipped: set = field(default_factory=set)
    errors: Dict[str, str] = field(default_factory=dict)


from ._evaluator_local_evaluator_can_run_locally import _LocalEvaluatorCanRunLocallyMethods

class LocalEvaluator(_LocalEvaluatorCanRunLocallyMethods):
    """Evaluator that runs metrics locally without API calls.

    This evaluator can run heuristic metrics locally, providing fast feedback
    without requiring network access or API credentials.

    Example:
        >>> evaluator = LocalEvaluator()
        >>> result = evaluator.evaluate(
        ...     metric_name="contains",
        ...     inputs=[{"response": "Hello world", "keyword": "world"}],
        ...     config={"keyword": "world"}
        ... )
        >>> print(result.results.eval_results[0].output)
        1.0
    """

    def __init__(
        self,
        config: Optional[LocalEvaluatorConfig] = None,
        registry: Optional[LocalMetricRegistry] = None,
    ) -> None:
        """Initialize the local evaluator.

        Args:
            config: Configuration for the evaluator.
            registry: Optional metric registry (uses global if not provided).
        """
        self.config = config or LocalEvaluatorConfig()
        self.registry = registry or get_registry()


from ._evaluator_hybrid_evaluator_set_local_llm import _HybridEvaluatorSetLocalLlmMethods
from ._evaluator_hybrid_evaluator_evaluate_batch import _HybridEvaluatorEvaluateBatchMethods

class HybridEvaluator(_HybridEvaluatorSetLocalLlmMethods, _HybridEvaluatorEvaluateBatchMethods):
    """Evaluator that routes metrics between local and cloud execution.

    This evaluator analyzes each metric and automatically routes it to
    either local heuristics, local LLM, or cloud execution based on the
    metric type and configuration.

    Example:
        >>> # Basic usage with automatic routing
        >>> evaluator = HybridEvaluator()
        >>> partitions = evaluator.partition_evaluations([
        ...     {"metric_name": "contains", "inputs": [{"response": "test"}]},
        ...     {"metric_name": "groundedness", "inputs": [{"response": "test"}]},
        ... ])
        >>> local_results = evaluator.evaluate_local_partition(partitions[RoutingMode.LOCAL])

        >>> # With local LLM for LLM-based evaluations
        >>> from fi.evals.local.llm import OllamaLLM
        >>> evaluator = HybridEvaluator(local_llm=OllamaLLM())
        >>> result = evaluator.evaluate(
        ...     template="custom_llm_judge",
        ...     inputs=[{"query": "What is AI?", "response": "AI is..."}]
        ... )
    """

    # LLM-based metrics that can use local LLM instead of cloud
    LLM_BASED_METRICS = {
        "groundedness",
        "hallucination",
        "relevance",
        "coherence",
        "context_relevance",
        "answer_relevance",
        "custom_llm_judge",
        "tone",
        "safety",
        "pii",
        "bias",
    }

    def __init__(
        self,
        config: Optional[LocalEvaluatorConfig] = None,
        local_evaluator: Optional[LocalEvaluator] = None,
        local_llm: Optional["OllamaLLM"] = None,
        cloud_evaluator: Optional[Any] = None,
        prefer_local: bool = True,
        fallback_to_cloud: bool = True,
        offline_mode: bool = False,
    ) -> None:
        """Initialize the hybrid evaluator.

        Args:
            config: Configuration for the evaluator.
            local_evaluator: Optional local evaluator instance for heuristic metrics.
            local_llm: Optional local LLM instance for LLM-based metrics.
            cloud_evaluator: Optional cloud evaluator instance (Evaluator).
            prefer_local: If True, prefer local execution when possible.
            fallback_to_cloud: If True, fall back to cloud when local fails.
            offline_mode: If True, never use cloud (raise error if metric requires it).
        """
        self.config = config or LocalEvaluatorConfig(execution_mode=RoutingMode.HYBRID)
        self.local_evaluator = local_evaluator or LocalEvaluator(self.config)
        self.local_llm = local_llm
        self.cloud_evaluator = cloud_evaluator
        self.prefer_local = prefer_local
        self.fallback_to_cloud = fallback_to_cloud
        self.offline_mode = offline_mode
