"""AutoEvalPipeline evaluate operations."""
from __future__ import annotations

from typing import TYPE_CHECKING
from fi.evals.autoeval.pipeline import (
    Any, AutoEvalResult, Dict, EvalConfig, Optional, ScannerConfig, Union,
)

if TYPE_CHECKING:
    from fi.evals.autoeval.pipeline import AutoEvalPipeline


class _AutoEvalPipelineEvaluateMethods:
    __slots__ = ()

    def evaluate(
        self,
        inputs: Dict[str, Any],
        scan_content: Optional[str] = None,
        feedback_store: Optional[Any] = None,
    ) -> AutoEvalResult:
        """
        Run the full evaluation pipeline.

        Executes scanners first (fast), then evaluations.
        If scanners block, evaluations may be skipped.

        Args:
            inputs: Input data for evaluations (e.g., query, response, context)
            scan_content: Content to scan (defaults to response from inputs)

        Returns:
            AutoEvalResult with combined results

        Example:
            result = pipeline.evaluate({
                "query": "What is the patient's blood type?",
                "response": "The patient's blood type is O+.",
                "context": "Medical record: Blood type O+",
            })

            if result.passed:
                print("Evaluation passed!")
            else:
                print(f"Failed: {result.explain()}")
        """
        from fi.evals.autoeval.pipeline import (Any, AutoEvalResult, Dict, Optional, time)
        start_time = time.perf_counter()

        # Build components lazily
        self._build_evaluator()
        self._build_scanner_pipeline()

        scan_result = None
        eval_result = None
        metric_results = []
        blocked_by_scanner = False

        # Run scanners first (fast)
        if self._scanner_pipeline:
            content = scan_content or inputs.get("response", "")
            context = inputs.get("context")
            scan_result = self._scanner_pipeline.scan(content, context)
            blocked_by_scanner = not scan_result.passed

        # Run evaluations if not blocked
        if not blocked_by_scanner:
            # Core metrics via evaluate() API
            metric_results = self._run_core_metrics(inputs, feedback_store=feedback_store)

            # Framework class evals via Evaluator
            if self._evaluator:
                eval_result = self._evaluator.run(inputs)

        # Determine overall pass/fail
        passed = True
        if scan_result and not scan_result.passed:
            passed = False

        # Check core metric results against thresholds
        if metric_results:
            metric_configs = {e.name: e for e in self._get_metric_configs()}
            failed_count = 0
            total_count = len(metric_results)
            for r in metric_results:
                config = metric_configs.get(getattr(r, "eval_name", ""))
                threshold = config.threshold if config else 0.5
                score = getattr(r, "score", None)
                if score is not None and score < threshold:
                    failed_count += 1
            if total_count > 0:
                success_rate = (total_count - failed_count) / total_count
                if success_rate < self.config.global_pass_rate:
                    passed = False

        if eval_result:
            # Check if framework evaluations meet threshold
            batch = eval_result.wait() if eval_result.is_future else eval_result.batch
            if batch and batch.success_rate < self.config.global_pass_rate:
                passed = False

        total_latency = (time.perf_counter() - start_time) * 1000

        return AutoEvalResult(
            passed=passed,
            scan_result=scan_result,
            eval_result=eval_result,
            metric_results=metric_results,
            blocked_by_scanner=blocked_by_scanner,
            total_latency_ms=total_latency,
        )


    def add(self, item: Union[EvalConfig, ScannerConfig]) -> "AutoEvalPipeline":
        """
        Add an evaluation or scanner to the pipeline.

        Args:
            item: EvalConfig or ScannerConfig to add

        Returns:
            Self for chaining

        Example:
            pipeline.add(EvalConfig("CustomEval", threshold=0.8))
            pipeline.add(ScannerConfig("CustomScanner", action="flag"))
        """
        from fi.evals.autoeval.pipeline import (EvalConfig, ScannerConfig, Union)
        if isinstance(item, EvalConfig):
            self.config.evaluations.append(item)
            self._evaluator = None  # Reset to rebuild
        elif isinstance(item, ScannerConfig):
            self.config.scanners.append(item)
            self._scanner_pipeline = None  # Reset to rebuild
        return self


    def remove(self, name: str) -> "AutoEvalPipeline":
        """
        Remove an evaluation or scanner by name.

        Args:
            name: Name of the evaluation or scanner to remove

        Returns:
            Self for chaining

        Example:
            pipeline.remove("CoherenceEval")
        """
        # Try to remove from evaluations
        original_count = len(self.config.evaluations)
        self.config.evaluations = [
            e for e in self.config.evaluations if e.name != name
        ]
        if len(self.config.evaluations) < original_count:
            self._evaluator = None

        # Try to remove from scanners
        original_count = len(self.config.scanners)
        self.config.scanners = [s for s in self.config.scanners if s.name != name]
        if len(self.config.scanners) < original_count:
            self._scanner_pipeline = None

        return self


    def set_threshold(self, name: str, threshold: float) -> "AutoEvalPipeline":
        """
        Set threshold for an evaluation or scanner.

        Args:
            name: Name of the evaluation or scanner
            threshold: New threshold value (0.0-1.0)

        Returns:
            Self for chaining

        Example:
            pipeline.set_threshold("CoherenceEval", 0.9)
        """
        for e in self.config.evaluations:
            if e.name == name:
                e.threshold = threshold
                self._evaluator = None

        for s in self.config.scanners:
            if s.name == name:
                s.threshold = threshold
                self._scanner_pipeline = None

        return self


    def enable(self, name: str) -> "AutoEvalPipeline":
        """Enable an evaluation or scanner."""
        for e in self.config.evaluations:
            if e.name == name:
                e.enabled = True
                self._evaluator = None

        for s in self.config.scanners:
            if s.name == name:
                s.enabled = True
                self._scanner_pipeline = None

        return self


    def disable(self, name: str) -> "AutoEvalPipeline":
        """Disable an evaluation or scanner."""
        for e in self.config.evaluations:
            if e.name == name:
                e.enabled = False
                self._evaluator = None

        for s in self.config.scanners:
            if s.name == name:
                s.enabled = False
                self._scanner_pipeline = None

        return self


    def export_yaml(self, path: str) -> None:
        """
        Export pipeline configuration to YAML file.

        Args:
            path: Path to write YAML file

        Example:
            pipeline.export_yaml("eval_config.yaml")
        """
        from .export import export_yaml

        export_yaml(self.config, path)


    def export_json(self, path: str) -> None:
        """
        Export pipeline configuration to JSON file.

        Args:
            path: Path to write JSON file
        """
        from .export import export_json

        export_json(self.config, path)


    def explain(self) -> str:
        """
        Get human-readable explanation of the pipeline.

        Returns:
            Detailed explanation string

        Example:
            print(pipeline.explain())
        """
        lines = [self.config.summary()]

        if self.analysis:
            lines.append("")
            lines.append("Analysis Details:")
            lines.append(f"  Confidence: {self.analysis.confidence:.0%}")
            lines.append(f"  Explanation: {self.analysis.explanation}")
            if self.analysis.detected_features:
                lines.append(f"  Detected Features: {', '.join(self.analysis.detected_features)}")

        return "\n".join(lines)


    def summary(self) -> str:
        """Get brief summary of the pipeline."""
        return (
            f"AutoEvalPipeline: {self.config.name}\n"
            f"  Evaluations: {len(self.config.evaluations)}\n"
            f"  Scanners: {len(self.config.scanners)}\n"
            f"  Risk Level: {self.config.risk_level}"
        )


    def __repr__(self) -> str:
        return (
            f"AutoEvalPipeline(name={self.config.name!r}, "
            f"evaluations={len(self.config.evaluations)}, "
            f"scanners={len(self.config.scanners)})"
        )
