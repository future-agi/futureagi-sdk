"""ToolSelectionAccuracy metric name operations."""
from __future__ import annotations

from fi.evals.metrics.agents.metrics import (AgentTrajectoryInput, Any, Dict)


class _ToolSelectionAccuracyMetricNameMethods:
    __slots__ = ()

    @property
    def metric_name(self) -> str:
        return "tool_selection_accuracy"


    def compute_one(self, inputs: AgentTrajectoryInput) -> Dict[str, Any]:
        # Collect all tools used
        from fi.evals.metrics.agents.metrics import (AgentTrajectoryInput, Any, Dict)
        tools_used = set()
        all_calls = []
        for step in inputs.trajectory:
            for tc in step.tool_calls:
                tools_used.add(tc.name)
                all_calls.append(tc)

        if not all_calls:
            return {
                "output": 1.0,
                "reason": "No tool calls made."
            }

        reasons = []

        # Determine weights based on what data is available
        w_required = 0.4 if inputs.task.required_tools else 0.0
        w_validity = 0.3 if inputs.available_tools else 0.0
        w_success = 0.3

        # Normalize weights to sum to 1.0
        total_weight = w_required + w_validity + w_success
        if total_weight > 0:
            w_required /= total_weight
            w_validity /= total_weight
            w_success /= total_weight

        score = 0.0

        # Check if required tools were used
        if inputs.task.required_tools:
            required = set(inputs.task.required_tools)
            used_required = tools_used & required
            coverage = len(used_required) / len(required) if required else 1.0
            score += w_required * coverage
            reasons.append(f"Required tools: {len(used_required)}/{len(required)} used")

            unused = required - tools_used
            if unused:
                reasons.append(f"Missing: {', '.join(unused)}")

        # Check for invalid tool usage (tools not in available list)
        if inputs.available_tools:
            available = set(inputs.available_tools)
            invalid_tools = tools_used - available
            if invalid_tools:
                invalid_penalty = len(invalid_tools) / len(tools_used)
                score += w_validity * (1.0 - invalid_penalty)
                reasons.append(f"Invalid tools used: {', '.join(invalid_tools)}")
            else:
                score += w_validity
                reasons.append("All tools valid")

        # Check tool call success rate
        successful = sum(1 for tc in all_calls if tc.success)
        success_rate = successful / len(all_calls)
        score += w_success * success_rate
        reasons.append(f"Success rate: {success_rate:.0%}")

        return {
            "output": round(score, 4),
            "reason": ". ".join(reasons),
            "tools_used": list(tools_used),
            "total_calls": len(all_calls),
            "successful_calls": successful,
        }
