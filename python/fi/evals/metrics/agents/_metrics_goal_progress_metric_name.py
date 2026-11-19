"""GoalProgress metric name operations."""
from __future__ import annotations

from fi.evals.metrics.agents.metrics import (AgentTrajectoryInput, Any, Dict)


class _GoalProgressMetricNameMethods:
    __slots__ = ()

    @property
    def metric_name(self) -> str:
        return "goal_progress"


    def compute_one(self, inputs: AgentTrajectoryInput) -> Dict[str, Any]:
        from fi.evals.metrics.agents.metrics import (
            AgentTrajectoryInput, Any, Dict, _extract_keywords,
        )
        if not inputs.trajectory:
            return {
                "output": 0.0,
                "reason": "Empty trajectory - no progress."
            }

        # Extract goal keywords from task description
        goal_keywords = _extract_keywords(inputs.task.description)
        if inputs.task.expected_outcome:
            goal_keywords |= _extract_keywords(inputs.task.expected_outcome)

        if not goal_keywords:
            return {
                "output": 0.5,
                "reason": "Could not extract goal keywords for progress tracking."
            }

        # Track progress through trajectory (cumulative — never decreases)
        progress_scores = []
        prev_score = 0.0
        for step in inputs.trajectory:
            step_text = " ".join(filter(None, [
                step.thought,
                step.action,
                step.observation,
                " ".join(tc.name for tc in step.tool_calls)
            ]))
            step_keywords = _extract_keywords(step_text)

            if step_keywords:
                overlap = len(step_keywords & goal_keywords) / len(goal_keywords)
                cumulative = max(overlap, prev_score)
                progress_scores.append(cumulative)
                prev_score = cumulative

        if not progress_scores:
            return {
                "output": 0.2,
                "reason": "No meaningful progress detected."
            }

        # Calculate overall progress
        avg_progress = sum(progress_scores) / len(progress_scores)
        final_progress = progress_scores[-1] if progress_scores else 0.0
        max_progress = max(progress_scores)

        # Weight final progress more heavily
        overall = 0.3 * avg_progress + 0.5 * final_progress + 0.2 * max_progress

        return {
            "output": round(overall, 4),
            "reason": f"Progress: avg={avg_progress:.2f}, final={final_progress:.2f}, max={max_progress:.2f}",
            "progress_by_step": [round(p, 3) for p in progress_scores],
            "final_progress": round(final_progress, 4),
        }
