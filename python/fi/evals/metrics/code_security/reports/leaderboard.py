"""
Security Leaderboard for Model Comparison.

Compares multiple models on security benchmarks and generates
rankings and detailed analysis.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..benchmarks.types import BenchmarkResult, CWEBreakdown


@dataclass
class ModelEntry:
    """Entry for a model in the leaderboard."""

    name: str
    results: List[BenchmarkResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def avg_func_at_k(self) -> float:
        """Average func@k across all results."""
        if not self.results:
            return 0.0
        return sum(r.func_at_k for r in self.results) / len(self.results)

    @property
    def avg_sec_at_k(self) -> float:
        """Average sec@k across all results."""
        if not self.results:
            return 0.0
        return sum(r.sec_at_k for r in self.results) / len(self.results)

    @property
    def avg_func_sec_at_k(self) -> float:
        """Average func-sec@k across all results."""
        if not self.results:
            return 0.0
        return sum(r.func_sec_at_k for r in self.results) / len(self.results)

    @property
    def total_tests(self) -> int:
        """Total tests across all results."""
        return sum(r.total_tests for r in self.results)


@dataclass
class CWEComparison:
    """Comparison of models on a specific CWE."""

    cwe_id: str
    model_scores: Dict[str, float]  # model_name -> secure_rate
    best_model: str
    worst_model: str
    average_score: float


@dataclass
class LanguageComparison:
    """Comparison of models on a specific language."""

    language: str
    model_scores: Dict[str, Dict[str, float]]  # model -> {metric: value}
    best_overall: str
    rankings: List[str]


from ._leaderboard_leaderboard_report_to_markdown import _LeaderboardReportToMarkdownMethods

@dataclass
class LeaderboardReport(_LeaderboardReportToMarkdownMethods):
    """Complete leaderboard report with rankings and analysis."""

    # Metadata
    generated_at: datetime
    total_models: int
    total_tests: int

    # Rankings
    overall_ranking: List[str]  # Models ranked by func-sec@k
    func_ranking: List[str]  # Ranked by func@k
    sec_ranking: List[str]  # Ranked by sec@k

    # Detailed scores
    model_scores: Dict[str, Dict[str, float]]  # model -> {metric: value}

    # Breakdowns
    cwe_comparison: List[CWEComparison]
    language_comparison: List[LanguageComparison]

    # Recommendations
    recommendations: Dict[str, str]  # use_case -> recommended_model


from fi.evals._extracted import bind_owner as _bind_owner
from ._leaderboard_security_leaderboard_add_result import _SecurityLeaderboardAddResultMethods

class SecurityLeaderboard(_SecurityLeaderboardAddResultMethods):
    """
    Compare multiple models on security benchmarks.

    Usage:
        leaderboard = SecurityLeaderboard()

        # Add benchmark results for each model
        leaderboard.add_result("gpt-4", gpt4_benchmark_result)
        leaderboard.add_result("claude-3", claude_benchmark_result)
        leaderboard.add_result("codellama", codellama_benchmark_result)

        # Generate report
        report = leaderboard.generate_report()
        print(report.to_markdown())

        # Export
        with open("leaderboard.json", "w") as f:
            f.write(report.to_json())
    """

    def __init__(self):
        """Initialize empty leaderboard."""
        self.models: Dict[str, ModelEntry] = {}


_bind_owner(SecurityLeaderboard)
