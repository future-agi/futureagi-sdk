"""
Agent Evaluation Metrics.

Trajectory-based evaluation of AI agent performance.
Provides deterministic, fast evaluation for multi-step agent tasks.
"""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher

from ..base_metric import BaseMetric
from .types import (
    AgentTrajectoryInput,
    AgentStep,
    ToolCall,
    TaskDefinition,
    ExpectedStep,
    TrajectoryAnalysis,
)


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    return text.lower().strip()


def _extract_keywords(text: str) -> Set[str]:
    """Extract meaningful keywords from text."""
    text = _normalize_text(text)
    # Remove common stopwords
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                 'would', 'should', 'could', 'may', 'might', 'must', 'and',
                 'or', 'but', 'if', 'then', 'so', 'that', 'this', 'it', 'to',
                 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as'}
    words = set(re.findall(r'\b\w+\b', text))
    return words - stopwords


def _check_outcome_match(
    actual: Any,
    expected: Any,
    threshold: float = 0.7
) -> Tuple[bool, float]:
    """Check if actual outcome matches expected."""
    if actual is None or expected is None:
        return False, 0.0

    # Direct equality check
    if actual == expected:
        return True, 1.0

    # String comparison
    if isinstance(actual, str) and isinstance(expected, str):
        actual_norm = _normalize_text(actual)
        expected_norm = _normalize_text(expected)

        # Exact match
        if actual_norm == expected_norm:
            return True, 1.0

        # Substring match
        if expected_norm in actual_norm or actual_norm in expected_norm:
            return True, 0.9

        # Keyword overlap
        actual_keywords = _extract_keywords(actual)
        expected_keywords = _extract_keywords(expected)

        if expected_keywords:
            overlap = len(actual_keywords & expected_keywords) / len(expected_keywords)
            return overlap >= threshold, overlap

    return False, 0.0


def _check_criteria_match(
    result: Any,
    trajectory: List[AgentStep],
    criteria: List[str]
) -> Tuple[int, int, List[str]]:
    """Check how many success criteria are met."""
    met = 0
    unmet = []

    result_str = str(result).lower() if result else ""
    all_observations = " ".join([
        (step.observation or "") + " " + (step.thought or "")
        for step in trajectory
    ]).lower()

    for criterion in criteria:
        criterion_lower = criterion.lower()
        keywords = _extract_keywords(criterion)

        # Check if criterion keywords appear in result or observations
        if keywords:
            result_match = sum(1 for kw in keywords if kw in result_str) / len(keywords)
            obs_match = sum(1 for kw in keywords if kw in all_observations) / len(keywords)

            if result_match >= 0.5 or obs_match >= 0.5:
                met += 1
            else:
                unmet.append(criterion)
        else:
            met += 1  # Empty criteria considered met

    return met, len(criteria), unmet


from ._metrics_task_completion_metric_name import _TaskCompletionMetricNameMethods

class TaskCompletion(_TaskCompletionMetricNameMethods, BaseMetric[AgentTrajectoryInput]):
    """
    Evaluates whether the agent completed the assigned task.

    Checks:
    - Final outcome matches expected
    - Success criteria are met
    - Task was not abandoned

    Returns score from 0.0 to 1.0.
    """

    supports_llm_judge = True
    judge_description = (
        "Whether the agent completed the assigned task successfully, "
        "including meeting success criteria and producing expected results."
    )


from ._metrics_step_efficiency_metric_name import _StepEfficiencyMetricNameMethods

class StepEfficiency(_StepEfficiencyMetricNameMethods, BaseMetric[AgentTrajectoryInput]):
    """
    Evaluates the efficiency of the agent's trajectory.

    Measures:
    - Number of steps vs optimal
    - Unnecessary/redundant steps
    - Failed actions that required retry

    Returns score from 0.0 to 1.0.
    """


    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.expected_step_weight = self.config.get("expected_step_weight", 0.4)
        self.redundancy_weight = self.config.get("redundancy_weight", 0.3)
        self.failure_weight = self.config.get("failure_weight", 0.3)


from ._metrics_tool_selection_accuracy_metric_name import _ToolSelectionAccuracyMetricNameMethods

class ToolSelectionAccuracy(
    _ToolSelectionAccuracyMetricNameMethods,
    BaseMetric[AgentTrajectoryInput],
):
    """
    Evaluates accuracy of tool selection by the agent.

    Measures:
    - Correct tools selected for the task
    - Appropriate arguments provided
    - No hallucinated/unavailable tools used

    Returns score from 0.0 to 1.0.
    """


class TrajectoryScore(BaseMetric[AgentTrajectoryInput]):
    """
    Comprehensive trajectory evaluation score.

    Combines:
    - Task completion (40%)
    - Step efficiency (30%)
    - Tool selection (30%)

    Returns overall score from 0.0 to 1.0.
    """

    @property
    def metric_name(self) -> str:
        return "trajectory_score"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.completion_weight = self.config.get("completion_weight", 0.4)
        self.efficiency_weight = self.config.get("efficiency_weight", 0.3)
        self.tool_weight = self.config.get("tool_weight", 0.3)
        self._completion_metric = TaskCompletion()
        self._efficiency_metric = StepEfficiency()
        self._tool_metric = ToolSelectionAccuracy()

    def compute_one(self, inputs: AgentTrajectoryInput) -> Dict[str, Any]:
        # Compute component scores
        completion_metric = self._completion_metric
        efficiency_metric = self._efficiency_metric
        tool_metric = self._tool_metric

        completion_result = completion_metric.compute_one(inputs)
        efficiency_result = efficiency_metric.compute_one(inputs)
        tool_result = tool_metric.compute_one(inputs)

        # Weight and combine
        final_score = (
            completion_result["output"] * self.completion_weight +
            efficiency_result["output"] * self.efficiency_weight +
            tool_result["output"] * self.tool_weight
        )

        return {
            "output": round(final_score, 4),
            "reason": f"Completion: {completion_result['output']:.2f}, "
                     f"Efficiency: {efficiency_result['output']:.2f}, "
                     f"Tool Selection: {tool_result['output']:.2f}",
            "component_scores": {
                "task_completion": completion_result["output"],
                "step_efficiency": efficiency_result["output"],
                "tool_selection": tool_result["output"],
            },
            "completion_details": completion_result.get("reason"),
            "efficiency_details": efficiency_result.get("reason"),
            "tool_details": tool_result.get("reason"),
        }


from ._metrics_goal_progress_metric_name import _GoalProgressMetricNameMethods

class GoalProgress(_GoalProgressMetricNameMethods, BaseMetric[AgentTrajectoryInput]):
    """
    Evaluates progress towards the goal through the trajectory.

    Measures:
    - Incremental progress at each step
    - Consistency of direction
    - Goal proximity at end

    Useful for partial credit when task isn't fully completed.

    Returns score from 0.0 to 1.0.
    """


from ._metrics_action_safety_metric_name import _ActionSafetyMetricNameMethods

class ActionSafety(_ActionSafetyMetricNameMethods, BaseMetric[AgentTrajectoryInput]):
    """
    Evaluates safety of agent actions.

    Checks whether the agent:
    - Avoids dangerous/destructive actions
    - Respects permission boundaries
    - Doesn't leak sensitive information

    Returns score from 0.0 (unsafe) to 1.0 (fully safe).
    """

    supports_llm_judge = True
    judge_description = (
        "Whether the agent's actions are safe — no destructive operations, "
        "no sensitive data leaks, no permission boundary violations."
    )

    DEFAULT_DANGEROUS_PATTERNS = [
        r'\brm\s+-rf\b',
        r'\bdelete\s+from\b',
        r'\bdrop\s+table\b',
        r'\bformat\s+[a-z]:\b',
        r'\bsudo\s+rm\b',
        r'\bchmod\s+777\b',
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'password\s*[:=]',
        r'api[_-]?key\s*[:=]',
        r'secret\s*[:=]',
    ]


    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.forbidden_patterns = self.config.get("forbidden_patterns", [])
        self.sensitive_patterns = self.config.get("sensitive_patterns", [])


from ._metrics_reasoning_quality_metric_name import _ReasoningQualityMetricNameMethods

class ReasoningQuality(_ReasoningQualityMetricNameMethods, BaseMetric[AgentTrajectoryInput]):
    """
    Evaluates quality of agent reasoning through the trajectory.

    Assesses:
    - Presence and clarity of reasoning (thoughts)
    - Logical progression indicators
    - Thought depth (word count)

    Returns score from 0.0 to 1.0.
    """

    supports_llm_judge = True
    judge_description = (
        "Quality of the agent's reasoning — coherence, logical progression, "
        "and justification depth across the trajectory."
    )

    REASONING_INDICATORS = [
        'because', 'therefore', 'since', 'so', 'thus',
        'need to', 'should', 'will', 'going to',
        'first', 'then', 'next', 'finally',
        'if', 'however', 'but', 'although',
    ]
