"""TaskCompletion metric name operations."""
from __future__ import annotations

from fi.evals.metrics.agents.metrics import (AgentTrajectoryInput, Any, Dict)


class _TaskCompletionMetricNameMethods:
    __slots__ = ()

    @property
    def metric_name(self) -> str:
        return "task_completion"


    def compute_one(self, inputs: AgentTrajectoryInput) -> Dict[str, Any]:
        from fi.evals.metrics.agents.metrics import (
            AgentTrajectoryInput, Any, Dict, _check_criteria_match, _check_outcome_match,
        )
        if not inputs.trajectory:
            return {
                "output": 0.0,
                "reason": "Empty trajectory - no steps taken."
            }

        score_components = []
        reasons = []

        # Check if trajectory has a final step
        has_final = any(step.is_final for step in inputs.trajectory)
        if has_final:
            score_components.append(0.2)
            reasons.append("Agent reached final step")
        else:
            reasons.append("No final step marked")

        # Check expected result match
        if inputs.expected_result is not None:
            match, match_score = _check_outcome_match(
                inputs.final_result,
                inputs.expected_result
            )
            score_components.append(0.5 * match_score)
            if match:
                reasons.append(f"Result matches expected ({match_score:.0%})")
            else:
                reasons.append(f"Result mismatch (similarity: {match_score:.0%})")
        elif inputs.final_result is not None:
            # Has result but no expected to compare
            score_components.append(0.3)
            reasons.append("Produced result (no expected for comparison)")

        # Check success criteria
        if inputs.task.success_criteria:
            met, total, unmet = _check_criteria_match(
                inputs.final_result,
                inputs.trajectory,
                inputs.task.success_criteria
            )
            criteria_score = met / total if total > 0 else 1.0
            score_components.append(0.3 * criteria_score)
            reasons.append(f"Criteria: {met}/{total} met")
            if unmet:
                reasons.append(f"Unmet: {', '.join(unmet[:2])}")
        else:
            score_components.append(0.2)

        final_score = sum(score_components)

        return {
            "output": round(min(1.0, final_score), 4),
            "reason": ". ".join(reasons),
            "has_final_step": has_final,
            "result_produced": inputs.final_result is not None,
        }
