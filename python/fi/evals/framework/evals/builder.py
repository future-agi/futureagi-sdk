"""Custom evaluation builder for creating evaluations without full classes.

This module provides a builder pattern and decorator-based approach
for defining custom evaluations with minimal boilerplate.

Example using decorator:
    from fi.evals.framework.evals.builder import custom_eval

    @custom_eval("sentiment_score")
    def evaluate_sentiment(inputs):
        text = inputs["text"]
        # Your evaluation logic here
        positive_words = ["good", "great", "excellent"]
        score = sum(1 for w in text.lower().split() if w in positive_words) / 10
        return {"score": min(1.0, score), "passed": score > 0.5}

Example using builder:
    from fi.evals.framework.evals.builder import EvalBuilder

    sentiment_eval = (
        EvalBuilder("sentiment_score")
        .version("1.0.0")
        .required_fields(["text"])
        .threshold(0.5)
        .evaluator(lambda inputs: {"score": 0.8, "passed": True})
        .build()
    )
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps

from ..protocols import BaseEvaluation, register_evaluation


@dataclass
class CustomEvalResult:
    """Result from a custom evaluation.

    This flexible result type supports any evaluation output format.

    Attributes:
        score: Evaluation score between 0 and 1
        passed: Whether the evaluation passed
        confidence: Confidence in the result (0-1)
        details: Additional evaluation details
    """

    score: float
    passed: bool
    confidence: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomEvalResult":
        """Create result from dictionary."""
        return cls(
            score=data.get("score", 0.0),
            passed=data.get("passed", False),
            confidence=data.get("confidence", 1.0),
            details={k: v for k, v in data.items()
                    if k not in ("score", "passed", "confidence")},
        )


class CustomEvaluation(BaseEvaluation):
    """Dynamically created evaluation from builder or decorator."""

    def __init__(
        self,
        name: str,
        evaluator_fn: Callable[[Dict[str, Any]], Union[Dict[str, Any], CustomEvalResult]],
        version: str = "1.0.0",
        required_fields: Optional[List[str]] = None,
        threshold: float = 0.7,
        description: str = "",
        span_attributes_fn: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ):
        """Initialize custom evaluation.

        Args:
            name: Unique evaluation name
            evaluator_fn: Function that performs the evaluation
            version: Evaluation version
            required_fields: List of required input fields
            threshold: Score threshold for passing
            description: Human-readable description
            span_attributes_fn: Optional function to extract span attributes
        """
        self._name = name
        self._version = version
        self._evaluator_fn = evaluator_fn
        self._required_fields = required_fields or []
        self._threshold = threshold
        self._description = description
        self._span_attributes_fn = span_attributes_fn

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def threshold(self) -> float:
        return self._threshold

    @property
    def description(self) -> str:
        return self._description

    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """Validate required inputs."""
        errors = []
        for field in self._required_fields:
            if field not in inputs:
                errors.append(f"Missing required field: {field}")
        return errors

    def evaluate(self, inputs: Dict[str, Any]) -> CustomEvalResult:
        """Run the evaluation.

        Args:
            inputs: Dictionary of evaluation inputs

        Returns:
            CustomEvalResult with evaluation outcome
        """
        result = self._evaluator_fn(inputs)

        if isinstance(result, CustomEvalResult):
            return result
        elif isinstance(result, dict):
            return CustomEvalResult.from_dict(result)
        else:
            raise ValueError(
                f"Evaluator function must return dict or CustomEvalResult, "
                f"got {type(result).__name__}"
            )

    def get_span_attributes(self, result: CustomEvalResult) -> Dict[str, Any]:
        """Get span attributes for tracing.

        Args:
            result: Evaluation result

        Returns:
            Dictionary of span attributes
        """
        if self._span_attributes_fn:
            return self._span_attributes_fn(result)

        return {
            "score": result.score,
            "passed": result.passed,
            "confidence": result.confidence,
            "threshold": self._threshold,
        }


class EvalBuilder:
    """Builder for creating custom evaluations.

    Provides a fluent interface for configuring evaluations.

    Example:
        eval = (
            EvalBuilder("my_eval")
            .version("2.0.0")
            .required_fields(["text", "reference"])
            .threshold(0.8)
            .description("Checks text quality")
            .evaluator(my_evaluation_function)
            .build()
        )
    """

    def __init__(self, name: str):
        """Initialize builder with evaluation name.

        Args:
            name: Unique evaluation name
        """
        self._name = name
        self._version = "1.0.0"
        self._required_fields: List[str] = []
        self._threshold = 0.7
        self._description = ""
        self._evaluator_fn: Optional[Callable] = None
        self._span_attributes_fn: Optional[Callable] = None
        self._register = False

    def version(self, version: str) -> "EvalBuilder":
        """Set evaluation version.

        Args:
            version: Semantic version string

        Returns:
            Self for chaining
        """
        self._version = version
        return self

    def required_fields(self, fields: List[str]) -> "EvalBuilder":
        """Set required input fields.

        Args:
            fields: List of field names

        Returns:
            Self for chaining
        """
        self._required_fields = fields
        return self

    def require(self, *fields: str) -> "EvalBuilder":
        """Add required input fields.

        Args:
            *fields: Field names to require

        Returns:
            Self for chaining
        """
        self._required_fields.extend(fields)
        return self

    def threshold(self, threshold: float) -> "EvalBuilder":
        """Set score threshold for passing.

        Args:
            threshold: Threshold value (0-1)

        Returns:
            Self for chaining
        """
        self._threshold = threshold
        return self

    def description(self, description: str) -> "EvalBuilder":
        """Set human-readable description.

        Args:
            description: Description text

        Returns:
            Self for chaining
        """
        self._description = description
        return self

    def evaluator(
        self,
        fn: Callable[[Dict[str, Any]], Union[Dict[str, Any], CustomEvalResult]]
    ) -> "EvalBuilder":
        """Set the evaluator function.

        The function should take an inputs dict and return either:
        - A dict with at least "score" and "passed" keys
        - A CustomEvalResult object

        Args:
            fn: Evaluator function

        Returns:
            Self for chaining
        """
        self._evaluator_fn = fn
        return self

    def span_attributes(
        self,
        fn: Callable[[CustomEvalResult], Dict[str, Any]]
    ) -> "EvalBuilder":
        """Set custom span attributes extractor.

        Args:
            fn: Function to extract span attributes from result

        Returns:
            Self for chaining
        """
        self._span_attributes_fn = fn
        return self

    def auto_register(self, register: bool = True) -> "EvalBuilder":
        """Enable automatic registration with EvalRegistry.

        Args:
            register: Whether to auto-register

        Returns:
            Self for chaining
        """
        self._register = register
        return self

    def build(self) -> CustomEvaluation:
        """Build the custom evaluation.

        Returns:
            Configured CustomEvaluation instance

        Raises:
            ValueError: If evaluator function not set
        """
        if self._evaluator_fn is None:
            raise ValueError("Evaluator function must be set via .evaluator()")

        evaluation = CustomEvaluation(
            name=self._name,
            evaluator_fn=self._evaluator_fn,
            version=self._version,
            required_fields=self._required_fields,
            threshold=self._threshold,
            description=self._description,
            span_attributes_fn=self._span_attributes_fn,
        )

        if self._register:
            register_evaluation(evaluation.__class__)

        return evaluation


from ._builder_factories import custom_eval
custom_eval.__module__ = __name__


from ._builder_factories import simple_eval
simple_eval.__module__ = __name__


from ._builder_factories import comparison_eval
comparison_eval.__module__ = __name__


from ._builder_factories import threshold_eval
threshold_eval.__module__ = __name__


from ._builder_factories import pattern_match_eval
pattern_match_eval.__module__ = __name__
