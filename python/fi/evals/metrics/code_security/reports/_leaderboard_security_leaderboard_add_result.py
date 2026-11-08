"""SecurityLeaderboard add result operations."""
from __future__ import annotations

from typing import TYPE_CHECKING
from fi.evals.metrics.code_security.reports.leaderboard import (
    Any, BenchmarkResult, CWEComparison, Dict, LanguageComparison, LeaderboardReport, List,
    ModelEntry, Optional,
)

if TYPE_CHECKING:
    from fi.evals.metrics.code_security.reports.leaderboard import SecurityLeaderboard


class _SecurityLeaderboardAddResultMethods:
    __slots__ = ()

    def add_result(
        self,
        model_name: str,
        result: BenchmarkResult,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a benchmark result for a model.

        Args:
            model_name: Name of the model
            result: Benchmark result to add
            metadata: Optional metadata about the model
        """
        from fi.evals.metrics.code_security.reports.leaderboard import (
            Any, BenchmarkResult, Dict, ModelEntry, Optional,
        )
        if model_name not in self.models:
            self.models[model_name] = ModelEntry(
                name=model_name,
                metadata=metadata or {},
            )

        self.models[model_name].results.append(result)

        if metadata:
            self.models[model_name].metadata.update(metadata)


    def add_model_entry(self, entry: ModelEntry) -> None:
        """Add a complete model entry."""
        from fi.evals.metrics.code_security.reports.leaderboard import (ModelEntry)
        self.models[entry.name] = entry


    def get_rankings(self, metric: str = "func_sec_at_k") -> List[str]:
        """
        Get model rankings by metric.

        Args:
            metric: Metric to rank by (func_at_k, sec_at_k, func_sec_at_k)

        Returns:
            List of model names, best to worst
        """
        from fi.evals.metrics.code_security.reports.leaderboard import (List)
        if metric == "func_at_k":
            key_fn = lambda m: m.avg_func_at_k
        elif metric == "sec_at_k":
            key_fn = lambda m: m.avg_sec_at_k
        else:
            key_fn = lambda m: m.avg_func_sec_at_k

        sorted_models = sorted(
            self.models.values(),
            key=key_fn,
            reverse=True,
        )
        return [m.name for m in sorted_models]


    def get_cwe_comparison(self) -> List[CWEComparison]:
        """Get per-CWE comparison across models."""
        from fi.evals.metrics.code_security.reports.leaderboard import (CWEComparison, List)
        # Collect all CWE data
        cwe_data: Dict[str, Dict[str, List[float]]] = {}

        for model_name, model in self.models.items():
            for result in model.results:
                for cwe_breakdown in result.cwe_breakdown:
                    cwe_id = cwe_breakdown.cwe_id
                    if cwe_id not in cwe_data:
                        cwe_data[cwe_id] = {}
                    if model_name not in cwe_data[cwe_id]:
                        cwe_data[cwe_id][model_name] = []
                    cwe_data[cwe_id][model_name].append(cwe_breakdown.secure_rate)

        # Create comparisons
        comparisons = []
        for cwe_id, model_scores in cwe_data.items():
            # Average scores for each model
            avg_scores = {
                model: sum(scores) / len(scores)
                for model, scores in model_scores.items()
            }

            best = max(avg_scores.items(), key=lambda x: x[1])
            worst = min(avg_scores.items(), key=lambda x: x[1])
            avg = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0

            comparisons.append(CWEComparison(
                cwe_id=cwe_id,
                model_scores=avg_scores,
                best_model=best[0],
                worst_model=worst[0],
                average_score=avg,
            ))

        # Sort by average score (worst CWEs first)
        return sorted(comparisons, key=lambda c: c.average_score)


    def get_language_comparison(self) -> List[LanguageComparison]:
        """Get per-language comparison across models."""
        from fi.evals.metrics.code_security.reports.leaderboard import (LanguageComparison, List)
        # Collect language data
        lang_data: Dict[str, Dict[str, Dict[str, List[float]]]] = {}

        for model_name, model in self.models.items():
            for result in model.results:
                lang = result.language
                if lang not in lang_data:
                    lang_data[lang] = {}
                if model_name not in lang_data[lang]:
                    lang_data[lang][model_name] = {
                        "func_at_k": [],
                        "sec_at_k": [],
                        "func_sec_at_k": [],
                    }
                lang_data[lang][model_name]["func_at_k"].append(result.func_at_k)
                lang_data[lang][model_name]["sec_at_k"].append(result.sec_at_k)
                lang_data[lang][model_name]["func_sec_at_k"].append(result.func_sec_at_k)

        # Create comparisons
        comparisons = []
        for lang, models in lang_data.items():
            # Average scores
            model_scores = {}
            for model, metrics in models.items():
                model_scores[model] = {
                    metric: sum(values) / len(values)
                    for metric, values in metrics.items()
                }

            # Rank by func_sec_at_k
            rankings = sorted(
                model_scores.keys(),
                key=lambda m: model_scores[m].get("func_sec_at_k", 0),
                reverse=True,
            )

            comparisons.append(LanguageComparison(
                language=lang,
                model_scores=model_scores,
                best_overall=rankings[0] if rankings else "",
                rankings=rankings,
            ))

        return comparisons


    def generate_recommendations(self) -> Dict[str, str]:
        """Generate use-case recommendations."""
        from fi.evals.metrics.code_security.reports.leaderboard import (Dict)
        recommendations = {}

        if not self.models:
            return recommendations

        # Best for security
        sec_ranking = self.get_rankings("sec_at_k")
        if sec_ranking:
            recommendations["Highest Security"] = sec_ranking[0]

        # Best overall (balanced)
        overall_ranking = self.get_rankings("func_sec_at_k")
        if overall_ranking:
            recommendations["Best Overall (func-sec@k)"] = overall_ranking[0]

        # Best functional
        func_ranking = self.get_rankings("func_at_k")
        if func_ranking:
            recommendations["Highest Correctness"] = func_ranking[0]

        # Best for specific CWEs
        cwe_comparison = self.get_cwe_comparison()
        if cwe_comparison:
            # Find model that handles the worst CWE best
            worst_cwe = cwe_comparison[0]
            recommendations[f"Best for {worst_cwe.cwe_id}"] = worst_cwe.best_model

        return recommendations


    def generate_report(self) -> LeaderboardReport:
        """
        Generate comprehensive leaderboard report.

        Returns:
            LeaderboardReport with rankings, comparisons, and recommendations
        """
        from fi.evals.metrics.code_security.reports.leaderboard import (LeaderboardReport, datetime)
        # Compute all rankings
        overall_ranking = self.get_rankings("func_sec_at_k")
        func_ranking = self.get_rankings("func_at_k")
        sec_ranking = self.get_rankings("sec_at_k")

        # Compute model scores
        model_scores = {}
        for model_name, model in self.models.items():
            model_scores[model_name] = {
                "func_at_k": model.avg_func_at_k,
                "sec_at_k": model.avg_sec_at_k,
                "func_sec_at_k": model.avg_func_sec_at_k,
                "total_tests": model.total_tests,
            }

        # Total tests
        total_tests = sum(m.total_tests for m in self.models.values())

        return LeaderboardReport(
            generated_at=datetime.now(),
            total_models=len(self.models),
            total_tests=total_tests,
            overall_ranking=overall_ranking,
            func_ranking=func_ranking,
            sec_ranking=sec_ranking,
            model_scores=model_scores,
            cwe_comparison=self.get_cwe_comparison(),
            language_comparison=self.get_language_comparison(),
            recommendations=self.generate_recommendations(),
        )


    def export_markdown(self) -> str:
        """Export leaderboard as Markdown."""
        return self.generate_report().to_markdown()


    def export_json(self) -> str:
        """Export leaderboard as JSON."""
        return self.generate_report().to_json()


    def export_html(self) -> str:
        """Export leaderboard as HTML."""
        return self.generate_report().to_html()


    @classmethod
    def from_results(
        cls,
        results: Dict[str, List[BenchmarkResult]],
    ) -> "SecurityLeaderboard":
        """
        Create leaderboard from results dictionary.

        Args:
            results: Dict mapping model names to their benchmark results

        Returns:
            SecurityLeaderboard instance
        """
        from fi.evals.metrics.code_security.reports.leaderboard import (BenchmarkResult, Dict, List)
        leaderboard = cls()
        for model_name, model_results in results.items():
            for result in model_results:
                leaderboard.add_result(model_name, result)
        return leaderboard
