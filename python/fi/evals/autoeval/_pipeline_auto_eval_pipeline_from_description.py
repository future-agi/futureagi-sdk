"""AutoEvalPipeline from description operations."""
from __future__ import annotations

from typing import TYPE_CHECKING
from fi.evals.autoeval.pipeline import (Any, AutoEvalConfig, Dict, EvalConfig, List, Optional)

if TYPE_CHECKING:
    from fi.evals.autoeval.pipeline import AutoEvalPipeline


class _AutoEvalPipelineFromDescriptionMethods:
    __slots__ = ()

    @classmethod
    def from_description(
        cls,
        description: str,
        llm_provider: Optional[Any] = None,
        name: Optional[str] = None,
    ) -> "AutoEvalPipeline":
        """
        Create pipeline from natural language description.

        Uses LLM-powered analysis when available, falls back to
        rule-based analysis otherwise.

        Args:
            description: Natural language application description
            llm_provider: Optional LLM provider for intelligent analysis
            name: Optional name for the pipeline

        Returns:
            Configured AutoEvalPipeline

        Example:
            pipeline = AutoEvalPipeline.from_description(
                "A customer support chatbot for a healthcare company. "
                "It retrieves patient information and answers questions."
            )
        """
        from fi.evals.autoeval.pipeline import (
            Any, AppAnalyzer, AutoEvalConfig, EvalRecommender, Optional,
        )
        # Analyze the description
        analyzer = AppAnalyzer(llm_provider=llm_provider)
        analysis = analyzer.analyze(description)

        # Generate recommendations
        recommender = EvalRecommender()
        evals, scanners = recommender.recommend(analysis)

        # Build config
        config = AutoEvalConfig(
            name=name or f"autoeval_{analysis.category.value}",
            description=description[:200] if len(description) > 200 else description,
            app_category=analysis.category.value,
            risk_level=analysis.risk_level.value,
            domain_sensitivity=analysis.domain_sensitivity.value,
            evaluations=evals,
            scanners=scanners,
        )

        return cls(config, analysis)


    @classmethod
    def from_template(cls, template_name: str) -> "AutoEvalPipeline":
        """
        Create pipeline from pre-built template.

        Available templates:
        - customer_support: Customer service chatbots
        - rag_system: RAG-based document Q&A
        - code_assistant: Code generation and review
        - content_moderation: Content filtering and safety
        - agent_workflow: Autonomous agents with tool use
        - healthcare: Healthcare applications (HIPAA)
        - financial: Financial services

        Args:
            template_name: Name of the template to use

        Returns:
            Configured AutoEvalPipeline

        Raises:
            ValueError: If template not found

        Example:
            pipeline = AutoEvalPipeline.from_template("rag_system")
        """
        from fi.evals.autoeval.pipeline import (get_template, list_templates)
        config = get_template(template_name)
        if config is None:
            available = list(list_templates().keys())
            raise ValueError(
                f"Template '{template_name}' not found. "
                f"Available templates: {available}"
            )
        return cls(config)


    @classmethod
    def from_config(cls, config: AutoEvalConfig) -> "AutoEvalPipeline":
        """
        Create pipeline from existing configuration.

        Args:
            config: AutoEvalConfig instance

        Returns:
            Configured AutoEvalPipeline
        """
        from fi.evals.autoeval.pipeline import (AutoEvalConfig)
        return cls(config)


    @classmethod
    def from_yaml(cls, path: str) -> "AutoEvalPipeline":
        """
        Load pipeline from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            Configured AutoEvalPipeline
        """
        from .export import load_config

        config = load_config(path)
        return cls(config)


    def _is_core_metric(self, name: str) -> bool:
        """Check if a name corresponds to a core metric in the local registry."""
        try:
            from fi.evals.local.registry import get_registry
            return get_registry().is_registered(name)
        except ImportError:
            return False


    def _get_metric_configs(self) -> List[EvalConfig]:
        """Get eval configs that are core metrics (routed through evaluate())."""
        from fi.evals.autoeval.pipeline import (EvalConfig, List)
        return [
            e for e in self.config.evaluations
            if e.enabled and self._is_core_metric(e.name)
        ]


    def _get_class_configs(self) -> List[EvalConfig]:
        """Get eval configs that are framework classes (routed through Evaluator)."""
        from fi.evals.autoeval.pipeline import (EvalConfig, List)
        return [
            e for e in self.config.evaluations
            if e.enabled and not self._is_core_metric(e.name)
        ]


    def _run_core_metrics(
        self,
        inputs: Dict[str, Any],
        feedback_store: Optional[Any] = None,
    ) -> List[Any]:
        """Run core metrics via evaluate() API and return EvalResults."""
        from fi.evals.autoeval.pipeline import (Any, Dict, List, Optional, logger)
        from fi.evals import evaluate as core_evaluate

        metric_configs = self._get_metric_configs()
        if not metric_configs:
            return []

        results = []
        for eval_config in metric_configs:
            try:
                result = core_evaluate(
                    eval_config.name,
                    model=eval_config.model,
                    augment=eval_config.augment,
                    feedback_store=feedback_store,
                    **inputs,
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Core metric '{eval_config.name}' failed: {e}")
        return results


    def _build_evaluator(self) -> None:
        """Build the evaluator with framework-class evaluations only."""
        from fi.evals.autoeval.pipeline import (_get_eval_class, logger)
        if self._evaluator is not None:
            return

        from fi.evals.framework import Evaluator, ExecutionMode

        # Only build for non-metric (framework class) evals
        self._eval_instances = []
        for eval_config in self._get_class_configs():
            eval_class = _get_eval_class(eval_config.name)
            if eval_class is None:
                logger.warning(f"Evaluation class not found: {eval_config.name}")
                continue

            try:
                instance = eval_class(**eval_config.params)
                self._eval_instances.append(instance)
            except Exception as e:
                logger.warning(f"Failed to instantiate {eval_config.name}: {e}")

        if self._eval_instances:
            mode = (
                ExecutionMode.NON_BLOCKING
                if self.config.execution_mode == "non_blocking"
                else ExecutionMode.BLOCKING
            )
            self._evaluator = Evaluator(
                evaluations=self._eval_instances,
                mode=mode,
                max_workers=self.config.parallel_workers,
                fail_fast=self.config.fail_fast,
            )


    def _build_scanner_pipeline(self) -> None:
        """Build the scanner pipeline with configured scanners."""
        from fi.evals.autoeval.pipeline import (_get_scanner_class, logger)
        if self._scanner_pipeline is not None:
            return

        from fi.evals.guardrails.scanners import ScannerPipeline

        # Instantiate scanner classes
        self._scanner_instances = []
        for scanner_config in self.config.scanners:
            if not scanner_config.enabled:
                continue

            scanner_class = _get_scanner_class(scanner_config.name)
            if scanner_class is None:
                logger.warning(f"Scanner class not found: {scanner_config.name}")
                continue

            try:
                instance = scanner_class(**scanner_config.params)
                # Set threshold and action if the scanner supports them
                if hasattr(instance, "threshold"):
                    instance.threshold = scanner_config.threshold
                if hasattr(instance, "action"):
                    from fi.evals.guardrails.scanners.base import ScannerAction

                    instance.action = ScannerAction(scanner_config.action)
                self._scanner_instances.append(instance)
            except Exception as e:
                logger.warning(f"Failed to instantiate {scanner_config.name}: {e}")

        if self._scanner_instances:
            self._scanner_pipeline = ScannerPipeline(
                scanners=self._scanner_instances,
                parallel=True,
                fail_fast=self.config.fail_fast,
            )
