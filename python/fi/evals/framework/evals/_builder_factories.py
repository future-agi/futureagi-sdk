"""Factories for builder."""
from __future__ import annotations

from fi.evals.framework.evals.builder import (Any, Callable, CustomEvaluation, Dict, List, Optional)

def custom_eval(
    name: str,
    version: str = "1.0.0",
    required_fields: Optional[List[str]] = None,
    threshold: float = 0.7,
    description: str = "",
    auto_register: bool = False,
) -> Callable:
    """Decorator for creating custom evaluations from functions.

    The decorated function should take an inputs dict and return either:
    - A dict with at least "score" and "passed" keys
    - A CustomEvalResult object

    Args:
        name: Unique evaluation name
        version: Evaluation version
        required_fields: List of required input fields
        threshold: Score threshold for passing
        description: Human-readable description
        auto_register: Whether to register with EvalRegistry

    Returns:
        Decorator function

    Example:
        @custom_eval("sentiment", required_fields=["text"])
        def evaluate_sentiment(inputs):
            text = inputs["text"]
            score = analyze_sentiment(text)
            return {"score": score, "passed": score > 0.5}

        # Use it
        result = evaluate_sentiment.evaluate({"text": "Great product!"})
    """
    from fi.evals.framework.evals.builder import (
        Callable, CustomEvaluation, List, Optional, register_evaluation,
    )
    def decorator(fn: Callable) -> CustomEvaluation:
        evaluation = CustomEvaluation(
            name=name,
            evaluator_fn=fn,
            version=version,
            required_fields=required_fields or [],
            threshold=threshold,
            description=description or fn.__doc__ or "",
        )

        if auto_register:
            # Create a class to register
            eval_class = type(
                f"Custom_{name}",
                (CustomEvaluation,),
                {"name": name, "version": version}
            )
            register_evaluation(eval_class)

        return evaluation

    return decorator


def simple_eval(
    name: str,
    scorer: Callable[[Dict[str, Any]], float],
    threshold: float = 0.7,
    required_fields: Optional[List[str]] = None,
) -> CustomEvaluation:
    """Create a simple evaluation from a scoring function.

    This is the simplest way to create a custom evaluation when you
    only need to compute a score.

    Args:
        name: Unique evaluation name
        scorer: Function that takes inputs and returns a score (0-1)
        threshold: Score threshold for passing
        required_fields: List of required input fields

    Returns:
        CustomEvaluation instance

    Example:
        word_count_eval = simple_eval(
            "word_count",
            scorer=lambda inputs: min(1.0, len(inputs["text"].split()) / 100),
            threshold=0.5,
            required_fields=["text"],
        )
    """
    from fi.evals.framework.evals.builder import (
        Any, Callable, CustomEvaluation, Dict, List, Optional,
    )
    def evaluator(inputs: Dict[str, Any]) -> Dict[str, Any]:
        score = scorer(inputs)
        return {
            "score": score,
            "passed": score >= threshold,
        }

    return CustomEvaluation(
        name=name,
        evaluator_fn=evaluator,
        required_fields=required_fields or [],
        threshold=threshold,
    )


def comparison_eval(
    name: str,
    comparator: Callable[[Any, Any], float],
    source_field: str = "response",
    target_field: str = "reference",
    threshold: float = 0.7,
) -> CustomEvaluation:
    """Create an evaluation that compares two fields.

    This is useful for evaluations that compare a response to a reference.

    Args:
        name: Unique evaluation name
        comparator: Function that compares source and target, returns score (0-1)
        source_field: Name of the source field
        target_field: Name of the target field
        threshold: Score threshold for passing

    Returns:
        CustomEvaluation instance

    Example:
        length_match_eval = comparison_eval(
            "length_match",
            comparator=lambda src, tgt: 1 - abs(len(src) - len(tgt)) / max(len(src), len(tgt), 1),
            threshold=0.8,
        )
    """
    from fi.evals.framework.evals.builder import (Any, Callable, CustomEvaluation, Dict)
    def evaluator(inputs: Dict[str, Any]) -> Dict[str, Any]:
        source = inputs.get(source_field, "")
        target = inputs.get(target_field, "")
        score = comparator(source, target)
        return {
            "score": score,
            "passed": score >= threshold,
            "source_field": source_field,
            "target_field": target_field,
        }

    return CustomEvaluation(
        name=name,
        evaluator_fn=evaluator,
        required_fields=[source_field, target_field],
        threshold=threshold,
    )


def threshold_eval(
    name: str,
    metric_fn: Callable[[Dict[str, Any]], float],
    min_threshold: Optional[float] = None,
    max_threshold: Optional[float] = None,
    required_fields: Optional[List[str]] = None,
) -> CustomEvaluation:
    """Create an evaluation based on min/max thresholds.

    Pass if the metric is within the specified range.

    Args:
        name: Unique evaluation name
        metric_fn: Function that computes the metric value
        min_threshold: Minimum acceptable value (inclusive)
        max_threshold: Maximum acceptable value (inclusive)
        required_fields: List of required input fields

    Returns:
        CustomEvaluation instance

    Example:
        length_eval = threshold_eval(
            "response_length",
            metric_fn=lambda inputs: len(inputs["response"]),
            min_threshold=10,
            max_threshold=500,
            required_fields=["response"],
        )
    """
    from fi.evals.framework.evals.builder import (
        Any, Callable, CustomEvaluation, Dict, List, Optional,
    )
    def evaluator(inputs: Dict[str, Any]) -> Dict[str, Any]:
        value = metric_fn(inputs)

        passed = True
        if min_threshold is not None and value < min_threshold:
            passed = False
        if max_threshold is not None and value > max_threshold:
            passed = False

        # Normalize score to 0-1
        if min_threshold is not None and max_threshold is not None:
            range_val = max_threshold - min_threshold
            if range_val > 0:
                score = max(0, min(1, (value - min_threshold) / range_val))
            else:
                score = 1.0 if value == min_threshold else 0.0
        elif min_threshold is not None:
            score = 1.0 if value >= min_threshold else value / min_threshold
        elif max_threshold is not None:
            score = 1.0 if value <= max_threshold else max_threshold / value
        else:
            score = 1.0

        return {
            "score": score,
            "passed": passed,
            "value": value,
            "min_threshold": min_threshold,
            "max_threshold": max_threshold,
        }

    return CustomEvaluation(
        name=name,
        evaluator_fn=evaluator,
        required_fields=required_fields or [],
        threshold=0.5,  # Not used, but required
    )


def pattern_match_eval(
    name: str,
    patterns: List[str],
    field: str = "response",
    mode: str = "any",  # "any", "all", "none"
    case_sensitive: bool = False,
) -> CustomEvaluation:
    """Create an evaluation based on pattern matching.

    Args:
        name: Unique evaluation name
        patterns: List of regex patterns
        field: Field to check patterns against
        mode: "any" (pass if any match), "all" (pass if all match),
              "none" (pass if none match)
        case_sensitive: Whether patterns are case-sensitive

    Returns:
        CustomEvaluation instance

    Example:
        has_greeting = pattern_match_eval(
            "has_greeting",
            patterns=[r"\\b(hello|hi|hey)\\b"],
            field="response",
            mode="any",
        )
    """
    from fi.evals.framework.evals.builder import (Any, CustomEvaluation, Dict, List)
    import re
    flags = 0 if case_sensitive else re.IGNORECASE

    compiled_patterns = [re.compile(p, flags) for p in patterns]

    def evaluator(inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = str(inputs.get(field, ""))
        matches = [bool(p.search(text)) for p in compiled_patterns]

        if mode == "any":
            passed = any(matches)
            score = sum(matches) / len(matches) if matches else 0
        elif mode == "all":
            passed = all(matches)
            score = sum(matches) / len(matches) if matches else 0
        elif mode == "none":
            passed = not any(matches)
            score = 1 - (sum(matches) / len(matches)) if matches else 1
        else:
            raise ValueError(f"Unknown mode: {mode}")

        return {
            "score": score,
            "passed": passed,
            "mode": mode,
            "matches": matches,
            "pattern_count": len(patterns),
        }

    return CustomEvaluation(
        name=name,
        evaluator_fn=evaluator,
        required_fields=[field],
        threshold=0.5,
    )
