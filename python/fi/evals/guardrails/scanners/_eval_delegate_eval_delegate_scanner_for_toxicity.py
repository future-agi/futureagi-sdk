"""EvalDelegateScanner for toxicity operations."""
from __future__ import annotations

from typing import TYPE_CHECKING
from fi.evals.guardrails.scanners.eval_delegate import (Any, Dict, EvalCategory, Optional)

if TYPE_CHECKING:
    from fi.evals.guardrails.scanners.eval_delegate import EvalDelegateScanner


class _EvalDelegateScannerForToxicityMethods:
    __slots__ = ()

    @classmethod
    def for_toxicity(cls, threshold: float = 0.5, **kwargs) -> "EvalDelegateScanner":
        """Create a scanner for toxicity detection."""
        from fi.evals.guardrails.scanners.eval_delegate import (EvalCategory)
        return cls(
            categories=[EvalCategory.TOXICITY],
            thresholds={EvalCategory.TOXICITY: threshold},
            **kwargs
        )


    @classmethod
    def for_pii(cls, threshold: float = 0.5, **kwargs) -> "EvalDelegateScanner":
        """Create a scanner for PII detection."""
        from fi.evals.guardrails.scanners.eval_delegate import (EvalCategory)
        return cls(
            categories=[EvalCategory.PII],
            thresholds={EvalCategory.PII: threshold},
            **kwargs
        )


    @classmethod
    def for_prompt_injection(cls, threshold: float = 0.5, **kwargs) -> "EvalDelegateScanner":
        """Create a scanner for prompt injection detection."""
        from fi.evals.guardrails.scanners.eval_delegate import (EvalCategory)
        return cls(
            categories=[EvalCategory.PROMPT_INJECTION],
            thresholds={EvalCategory.PROMPT_INJECTION: threshold},
            **kwargs
        )


    @classmethod
    def for_bias(cls, include_specific: bool = True, threshold: float = 0.5, **kwargs) -> "EvalDelegateScanner":
        """
        Create a scanner for bias detection.

        Args:
            include_specific: Include racial, gender, age bias checks
            threshold: Detection threshold
        """
        from fi.evals.guardrails.scanners.eval_delegate import (EvalCategory)
        categories = [EvalCategory.BIAS]
        if include_specific:
            categories.extend([
                EvalCategory.RACIAL_BIAS,
                EvalCategory.GENDER_BIAS,
                EvalCategory.AGE_BIAS,
            ])

        thresholds = {cat: threshold for cat in categories}
        return cls(categories=categories, thresholds=thresholds, **kwargs)


    @classmethod
    def for_safety(cls, threshold: float = 0.5, **kwargs) -> "EvalDelegateScanner":
        """
        Create a comprehensive safety scanner.

        Includes: toxicity, PII, prompt injection, content safety, NSFW
        """
        from fi.evals.guardrails.scanners.eval_delegate import (EvalCategory)
        categories = [
            EvalCategory.TOXICITY,
            EvalCategory.PII,
            EvalCategory.PROMPT_INJECTION,
            EvalCategory.CONTENT_SAFETY,
            EvalCategory.NSFW,
        ]
        thresholds = {cat: threshold for cat in categories}
        return cls(categories=categories, thresholds=thresholds, **kwargs)


    @classmethod
    def for_content_moderation(cls, threshold: float = 0.5, **kwargs) -> "EvalDelegateScanner":
        """
        Create a content moderation scanner.

        Includes: toxicity, NSFW, sexist, content safety
        """
        from fi.evals.guardrails.scanners.eval_delegate import (EvalCategory)
        categories = [
            EvalCategory.TOXICITY,
            EvalCategory.NSFW,
            EvalCategory.SEXIST,
            EvalCategory.CONTENT_SAFETY,
        ]
        thresholds = {cat: threshold for cat in categories}
        return cls(categories=categories, thresholds=thresholds, **kwargs)


    def _get_local_evaluator(self):
        """Get or create local evaluator."""
        if self._local_evaluator is None:
            try:
                from fi.evals.local import LocalEvaluator
                self._local_evaluator = LocalEvaluator()
            except ImportError:
                self._local_evaluator = None
        return self._local_evaluator


    def _get_cloud_evaluator(self):
        """Get or create cloud evaluator."""
        if self._cloud_evaluator is None:
            try:
                from fi.evals.evaluator import Evaluator
                self._cloud_evaluator = Evaluator(fi_api_key=self.api_key)
            except Exception:
                self._cloud_evaluator = None
        return self._cloud_evaluator


    def _get_threshold(self, category: EvalCategory) -> float:
        """Get threshold for a category."""
        from fi.evals.guardrails.scanners.eval_delegate import (EVAL_TEMPLATE_MAP, EvalCategory)
        if category in self.thresholds:
            return self.thresholds[category]
        return EVAL_TEMPLATE_MAP[category].get("threshold", 0.5)


    def _evaluate_category(
        self,
        content: str,
        category: EvalCategory,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate content for a single category.

        Returns:
            Dict with keys: passed, score, reason, latency_ms
        """
        from fi.evals.guardrails.scanners.eval_delegate import (
            Any, Dict, EVAL_TEMPLATE_MAP, EvalCategory, Optional, time,
        )
        template_info = EVAL_TEMPLATE_MAP[category]
        eval_name = template_info["eval_name"]
        threshold = self._get_threshold(category)
        invert = template_info.get("invert", True)

        start_time = time.perf_counter()

        # Prepare input
        eval_input = {"response": content}
        if context:
            eval_input["context"] = context

        # Try local evaluation first if preferred
        if self.prefer_local:
            local_eval = self._get_local_evaluator()
            if local_eval and local_eval.can_run_locally(eval_name):
                try:
                    result = local_eval.evaluate(
                        metric_name=eval_name,
                        inputs=[eval_input],
                    )
                    if result.results.eval_results:
                        eval_result = result.results.eval_results[0]
                        score = eval_result.output or 0.0
                        latency = (time.perf_counter() - start_time) * 1000

                        # Determine pass/fail
                        if invert:
                            passed = score < threshold
                        else:
                            passed = score >= threshold

                        return {
                            "passed": passed,
                            "score": score,
                            "reason": eval_result.reason or f"{eval_name}: {score:.2f}",
                            "latency_ms": latency,
                            "source": "local",
                        }
                except Exception as e:
                    # Fall through to cloud evaluation
                    pass

        # Try cloud evaluation
        cloud_eval = self._get_cloud_evaluator()
        if cloud_eval:
            try:
                result = cloud_eval.evaluate(
                    eval_templates=[eval_name],
                    inputs=[eval_input],
                )
                if result.eval_results:
                    eval_result = result.eval_results[0]
                    score = eval_result.output or 0.0
                    latency = (time.perf_counter() - start_time) * 1000

                    if invert:
                        passed = score < threshold
                    else:
                        passed = score >= threshold

                    return {
                        "passed": passed,
                        "score": score,
                        "reason": eval_result.reason or f"{eval_name}: {score:.2f}",
                        "latency_ms": latency,
                        "source": "cloud",
                    }
            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000
                return {
                    "passed": True,  # Default to pass on error
                    "score": 0.0,
                    "reason": f"Evaluation error: {str(e)}",
                    "latency_ms": latency,
                    "source": "error",
                }

        # No evaluator available
        latency = (time.perf_counter() - start_time) * 1000
        return {
            "passed": True,
            "score": 0.0,
            "reason": "No evaluator available",
            "latency_ms": latency,
            "source": "none",
        }
