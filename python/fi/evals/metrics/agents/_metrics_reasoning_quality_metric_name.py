"""ReasoningQuality metric name operations."""
from __future__ import annotations

from fi.evals.metrics.agents.metrics import (AgentTrajectoryInput, Any, Dict)


class _ReasoningQualityMetricNameMethods:
    __slots__ = ()

    @property
    def metric_name(self) -> str:
        return "reasoning_quality"


    def compute_one(self, inputs: AgentTrajectoryInput) -> Dict[str, Any]:
        from fi.evals.metrics.agents.metrics import (AgentTrajectoryInput, Any, Dict)
        if not inputs.trajectory:
            return {
                "output": 0.0,
                "reason": "Empty trajectory — no reasoning to evaluate.",
            }

        # Collect all thought texts
        thoughts = [
            step.thought for step in inputs.trajectory
            if step.thought and step.thought.strip()
        ]

        if not thoughts:
            # Check for implicit reasoning in actions/observations
            has_reasoning = False
            for step in inputs.trajectory:
                text = (step.action or "").lower()
                if any(ind in text for ind in self.REASONING_INDICATORS):
                    has_reasoning = True
                    break

            return {
                "output": 0.5 if has_reasoning else 0.3,
                "reason": "No explicit thoughts in trajectory."
                         + (" Implicit reasoning detected." if has_reasoning else ""),
            }

        # Analyze thought quality
        indicator_count = 0
        total_words = 0

        for thought in thoughts:
            text = thought.lower()
            total_words += len(text.split())
            for indicator in self.REASONING_INDICATORS:
                if indicator in text:
                    indicator_count += 1

        avg_length = total_words / len(thoughts)

        # Length score (prefer medium-length thoughts)
        if avg_length < 5:
            length_score = 0.4
        elif avg_length < 10:
            length_score = 0.7
        elif avg_length < 30:
            length_score = 1.0
        else:
            length_score = 0.8

        # Reasoning indicator density
        indicator_density = min(1.0, indicator_count / (len(thoughts) * 2))

        # Progression (more thoughts suggests structured reasoning)
        progression_score = min(1.0, len(thoughts) / 3)

        score = 0.3 * length_score + 0.4 * indicator_density + 0.3 * progression_score

        return {
            "output": round(score, 4),
            "reason": f"{len(thoughts)} thoughts, avg {avg_length:.0f} words, "
                     f"{indicator_count} reasoning indicators",
            "thought_count": len(thoughts),
            "avg_thought_length": round(avg_length, 1),
            "indicator_count": indicator_count,
        }
