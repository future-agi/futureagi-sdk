"""
Dual-Judge System for AI Code Security.

Combines pattern-based and LLM-based detection with configurable
consensus modes for optimal precision/recall tradeoffs.
"""

import time
from typing import List, Dict, Any, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from .base import BaseJudge, JudgeResult, JudgeFinding, ConsensusMode
from .pattern_judge import PatternJudge
from .llm_judge import LLMJudge
from ..types import Severity


from fi.evals._extracted import bind_owner as _bind_owner
from ._dual_judge_dual_judge_judge import _DualJudgeJudgeMethods
from ._dual_judge_dual_judge_combine_cascade import _DualJudgeCombineCascadeMethods

class DualJudge(_DualJudgeJudgeMethods, _DualJudgeCombineCascadeMethods, BaseJudge):
    """
    Dual-judge system combining pattern and LLM analysis.

    Provides multiple consensus modes to balance precision and recall:

    - ANY: Flag if either judge flags (high recall, may have false positives)
    - BOTH: Flag only if both agree (high precision, may miss some)
    - WEIGHTED: Weighted combination of confidences (balanced)
    - CASCADE: Pattern first, LLM only for uncertain cases (efficient)

    Architecture:
        ┌─────────────────────────────────────────┐
        │           Dual-Judge System             │
        ├─────────────────────────────────────────┤
        │  ┌─────────────┐    ┌─────────────┐    │
        │  │   Pattern   │    │     LLM     │    │
        │  │    Judge    │    │    Judge    │    │
        │  │  (< 10ms)   │    │  (accurate) │    │
        │  └─────────────┘    └─────────────┘    │
        │          ↓                ↓             │
        │      ┌───────────────────────┐         │
        │      │   Consensus Engine    │         │
        │      │  • any: high recall   │         │
        │      │  • both: high prec.   │         │
        │      │  • weighted: balanced │         │
        │      │  • cascade: efficient │         │
        │      └───────────────────────┘         │
        └─────────────────────────────────────────┘

    Usage:
        # Default dual judge
        judge = DualJudge()
        result = judge.judge(code, "python")

        # High precision mode
        judge = DualJudge(consensus_mode=ConsensusMode.BOTH)

        # High recall mode
        judge = DualJudge(consensus_mode=ConsensusMode.ANY)

        # Efficient cascade mode
        judge = DualJudge(consensus_mode=ConsensusMode.CASCADE)

        # Custom judges
        judge = DualJudge(
            pattern_judge=PatternJudge.with_strict_rules(),
            llm_judge=LLMJudge.with_gpt4(),
            consensus_mode=ConsensusMode.WEIGHTED,
        )
    """

    judge_type = "dual"

    def __init__(
        self,
        pattern_judge: Optional[PatternJudge] = None,
        llm_judge: Optional[LLMJudge] = None,
        consensus_mode: ConsensusMode = ConsensusMode.WEIGHTED,
        severity_threshold: Severity = Severity.HIGH,
        min_confidence: float = 0.7,
        pattern_weight: float = 0.4,
        llm_weight: float = 0.6,
        cascade_threshold: float = 0.6,
        parallel: bool = True,
        llm_timeout: float = 30.0,
    ):
        """
        Initialize the dual judge.

        Args:
            pattern_judge: Pattern-based judge (default: PatternJudge())
            llm_judge: LLM-based judge (default: None, pattern-only)
            consensus_mode: How to combine judge results
            severity_threshold: Minimum severity to flag as insecure
            min_confidence: Minimum confidence to include findings
            pattern_weight: Weight for pattern judge in WEIGHTED mode
            llm_weight: Weight for LLM judge in WEIGHTED mode
            cascade_threshold: Confidence threshold for CASCADE mode
            parallel: Run judges in parallel
            llm_timeout: Timeout for LLM judge
        """
        super().__init__(severity_threshold, min_confidence)

        self.pattern_judge = pattern_judge or PatternJudge(
            severity_threshold=severity_threshold,
            min_confidence=min_confidence,
        )
        self.llm_judge = llm_judge
        self.consensus_mode = consensus_mode
        self.pattern_weight = pattern_weight
        self.llm_weight = llm_weight
        self.cascade_threshold = cascade_threshold
        self.parallel = parallel
        self.llm_timeout = llm_timeout


_bind_owner(DualJudge)
