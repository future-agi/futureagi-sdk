"""StepEfficiency metric name operations."""
from __future__ import annotations

from typing import Set
from fi.evals.metrics.agents.metrics import (AgentTrajectoryInput, Any, Dict)


class _StepEfficiencyMetricNameMethods:
    __slots__ = ()

    @property
    def metric_name(self) -> str:
        return "step_efficiency"


    def compute_one(self, inputs: AgentTrajectoryInput) -> Dict[str, Any]:
        from fi.evals.metrics.agents.metrics import (AgentTrajectoryInput, Any, Dict, json)
        if not inputs.trajectory:
            return {
                "output": 0.0,
                "reason": "Empty trajectory."
            }

        total_steps = len(inputs.trajectory)
        details = {"total_steps": total_steps}

        # Calculate expected steps
        if inputs.expected_trajectory:
            expected_steps = len(inputs.expected_trajectory)
            step_ratio = min(1.0, expected_steps / total_steps) if total_steps > 0 else 0.0
            step_score = step_ratio * self.expected_step_weight
            details["expected_steps"] = expected_steps
            details["step_ratio"] = round(step_ratio, 3)
        elif inputs.task.max_steps:
            step_ratio = min(1.0, inputs.task.max_steps / total_steps) if total_steps > 0 else 0.0
            step_score = step_ratio * self.expected_step_weight
            details["max_steps"] = inputs.task.max_steps
        else:
            # No baseline - give partial credit if reasonable number of steps
            step_score = self.expected_step_weight * (1.0 if total_steps <= 10 else 10 / total_steps)

        # Detect redundant steps (same tool called with same arguments)
        seen_signatures: Set[str] = set()
        redundant_count = 0
        for step in inputs.trajectory:
            for tc in step.tool_calls:
                call_sig = f"{tc.name}:{json.dumps(tc.arguments, sort_keys=True, default=str)}"
                if call_sig in seen_signatures:
                    redundant_count += 1
                else:
                    seen_signatures.add(call_sig)

        redundancy_ratio = 1.0 - (redundant_count / total_steps) if total_steps > 0 else 1.0
        redundancy_score = redundancy_ratio * self.redundancy_weight
        details["redundant_steps"] = redundant_count

        # Count failures
        failed_calls = sum(
            1 for step in inputs.trajectory
            for tc in step.tool_calls
            if not tc.success
        )
        total_calls = sum(len(step.tool_calls) for step in inputs.trajectory)
        failure_ratio = 1.0 - (failed_calls / total_calls) if total_calls > 0 else 1.0
        failure_score = failure_ratio * self.failure_weight
        details["failed_calls"] = failed_calls

        final_score = step_score + redundancy_score + failure_score

        reason_parts = [f"{total_steps} steps taken"]
        if redundant_count > 0:
            reason_parts.append(f"{redundant_count} redundant")
        if failed_calls > 0:
            reason_parts.append(f"{failed_calls} failed calls")

        return {
            "output": round(final_score, 4),
            "reason": ", ".join(reason_parts),
            "details": details,
        }
