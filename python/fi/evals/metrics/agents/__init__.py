"""
Agent Evaluation Metrics.

Trajectory-based evaluation of AI agent performance.
Provides multi-step analysis beyond single-response evaluation.

Based on:
- AgentBench methodology (ICLR 2024)
- Multi-turn agent evaluation frameworks
"""

from .types import (
    AgentTrajectoryInput,
    AgentStep,
    ToolCall,
    TaskDefinition,
    TrajectoryAnalysis,
)
from .metrics import (
    TaskCompletion,
    StepEfficiency,
    ToolSelectionAccuracy,
    TrajectoryScore,
    GoalProgress,
    ActionSafety,
    ReasoningQuality,
)

__all__ = [
    # Types
    "AgentTrajectoryInput",
    "AgentStep",
    "ToolCall",
    "TaskDefinition",
    "TrajectoryAnalysis",
    # Metrics
    "TaskCompletion",
    "StepEfficiency",
    "ToolSelectionAccuracy",
    "TrajectoryScore",
    "GoalProgress",
    "ActionSafety",
    "ReasoningQuality",
]

# ALK-only names from the RL2213 join; deliberately absent from __all__ and dir().
_ALK_REPLACEMENTS = {
    "AgentReportCaseResult": "from fi.alk.evals import AgentReportCaseResult",
    "AgentReportEvalConfig": "from fi.alk.evals import AgentReportEvalConfig",
    "AgentReportEvaluation": "from fi.alk.evals import AgentReportEvaluation",
    "AgentReportEvaluator": "from fi.alk.evals import AgentReportEvaluator",
    "AgentReportMetricResult": "from fi.alk.evals import AgentReportMetricResult",
    "analyze_domain_package_registry_coverage": (
        "from fi.alk.evals import analyze_domain_package_registry_coverage"
    ),
    "diff_domain_package_registries": "from fi.alk.evals import diff_domain_package_registries",
    "evaluate_agent_report": "from fi.alk.evals.metrics.agents import evaluate_agent_report",
    "generate_domain_package_registry_fixtures": (
        "from fi.alk.evals import generate_domain_package_registry_fixtures"
    ),
    "generate_domain_package_registry_mutation_pack": (
        "from fi.alk.evals import generate_domain_package_registry_mutation_pack"
    ),
    "normalize_agent_report": "from fi.alk.evals import normalize_agent_report",
    "replay_domain_package_registry": "from fi.alk.evals import replay_domain_package_registry",
    "select_domain_package_registry_replay_pack": (
        "from fi.alk.evals import select_domain_package_registry_replay_pack"
    ),
    "validate_domain_package_registry": "from fi.alk.evals import validate_domain_package_registry",
}


def __getattr__(name: str):
    replacement = _ALK_REPLACEMENTS.get(name)
    if replacement is not None:
        from fi._alk_moved import name_moved

        # Plain ImportError preserves the migration message for from-imports.
        raise name_moved(__name__, name, replacement)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
