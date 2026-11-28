"""
Eval Delegate Scanner for Guardrails.

Delegates scanning to existing evaluation templates for overlapping functionality:
- PII Detection → Template 14, 22 (PII, DataPrivacyCompliance)
- Toxicity → Template 15 (Toxicity)
- Prompt Injection → Template 18 (PromptInjection)
- Bias Detection → Template 69, 77-79 (BiasDetection, NoRacialBias, etc.)
- Content Safety → Template 93 (ContentSafety)
- NSFW/Sexist → Template 17, 20 (Sexist, SafeForWorkText)

This scanner bridges the guardrails system with the evaluation framework,
allowing you to use battle-tested LLM-based evaluations as safety scanners.
"""

import time
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from fi.evals.guardrails.scanners.base import (
    BaseScanner,
    ScanResult,
    ScanMatch,
    ScannerAction,
    register_scanner,
)


class EvalCategory(str, Enum):
    """Categories of evals that can be delegated to."""
    PII = "pii"
    TOXICITY = "toxicity"
    PROMPT_INJECTION = "prompt_injection"
    BIAS = "bias"
    RACIAL_BIAS = "racial_bias"
    GENDER_BIAS = "gender_bias"
    AGE_BIAS = "age_bias"
    CONTENT_SAFETY = "content_safety"
    NSFW = "nsfw"
    SEXIST = "sexist"


# Mapping from category to eval template info
EVAL_TEMPLATE_MAP: Dict[EvalCategory, Dict[str, Any]] = {
    EvalCategory.PII: {
        "eval_id": "14",
        "eval_name": "pii",
        "description": "Detects personally identifiable information",
        "threshold": 0.5,  # Score above this = PII detected
        "invert": True,  # High score = bad (PII found)
    },
    EvalCategory.TOXICITY: {
        "eval_id": "15",
        "eval_name": "toxicity",
        "description": "Detects toxic or harmful content",
        "threshold": 0.5,
        "invert": True,
    },
    EvalCategory.PROMPT_INJECTION: {
        "eval_id": "18",
        "eval_name": "prompt_injection",
        "description": "Detects prompt injection attempts",
        "threshold": 0.5,
        "invert": True,
    },
    EvalCategory.BIAS: {
        "eval_id": "69",
        "eval_name": "bias_detection",
        "description": "Detects various forms of bias",
        "threshold": 0.5,
        "invert": True,
    },
    EvalCategory.RACIAL_BIAS: {
        "eval_id": "77",
        "eval_name": "no_racial_bias",
        "description": "Detects racial bias",
        "threshold": 0.5,
        "invert": False,  # High score = good (no bias)
    },
    EvalCategory.GENDER_BIAS: {
        "eval_id": "78",
        "eval_name": "no_gender_bias",
        "description": "Detects gender bias",
        "threshold": 0.5,
        "invert": False,
    },
    EvalCategory.AGE_BIAS: {
        "eval_id": "79",
        "eval_name": "no_age_bias",
        "description": "Detects age bias",
        "threshold": 0.5,
        "invert": False,
    },
    EvalCategory.CONTENT_SAFETY: {
        "eval_id": "93",
        "eval_name": "content_safety_violation",
        "description": "Detects content safety violations",
        "threshold": 0.5,
        "invert": True,
    },
    EvalCategory.NSFW: {
        "eval_id": "20",
        "eval_name": "safe_for_work_text",
        "description": "Detects NSFW content",
        "threshold": 0.5,
        "invert": False,  # High score = safe
    },
    EvalCategory.SEXIST: {
        "eval_id": "17",
        "eval_name": "sexist",
        "description": "Detects sexist content",
        "threshold": 0.5,
        "invert": True,
    },
}


@dataclass
class EvalDelegateConfig:
    """Configuration for EvalDelegateScanner."""
    # Categories to check
    categories: List[EvalCategory] = field(default_factory=lambda: [EvalCategory.TOXICITY])

    # Thresholds per category (overrides defaults)
    thresholds: Dict[EvalCategory, float] = field(default_factory=dict)

    # Use local evaluator if available (faster, no API calls)
    prefer_local: bool = True

    # API key for cloud evaluation (if not using local)
    api_key: Optional[str] = None

    # Timeout for evaluation calls (seconds)
    timeout: int = 30

    # Whether to run categories in parallel
    parallel: bool = True

    # Aggregation mode: "any" (fail if any category fails) or "all" (fail only if all fail)
    aggregation: str = "any"


from fi.evals._extracted import bind_owner as _bind_owner
from ._eval_delegate_eval_delegate_scanner_for_toxicity import _EvalDelegateScannerForToxicityMethods
from ._eval_delegate_eval_delegate_scanner_scan import _EvalDelegateScannerScanMethods

@register_scanner("eval_delegate")
class EvalDelegateScanner(
    _EvalDelegateScannerForToxicityMethods,
    _EvalDelegateScannerScanMethods,
    BaseScanner,
):
    """
    Scanner that delegates detection to existing evaluation templates.

    This scanner bridges guardrails with the evaluation framework, using
    proven LLM-based evaluations for safety detection.

    Supported Categories:
    - pii: Detect personally identifiable information
    - toxicity: Detect toxic or harmful content
    - prompt_injection: Detect prompt injection attempts
    - bias: Detect various forms of bias
    - racial_bias, gender_bias, age_bias: Specific bias detection
    - content_safety: Detect content safety violations
    - nsfw: Detect not-safe-for-work content
    - sexist: Detect sexist content

    Usage:
        # Single category
        scanner = EvalDelegateScanner(categories=[EvalCategory.TOXICITY])
        result = scanner.scan("Your content here")

        # Multiple categories
        scanner = EvalDelegateScanner(
            categories=[EvalCategory.TOXICITY, EvalCategory.PII, EvalCategory.BIAS]
        )

        # With custom thresholds
        scanner = EvalDelegateScanner(
            categories=[EvalCategory.TOXICITY],
            thresholds={EvalCategory.TOXICITY: 0.7}
        )

        # Factory methods
        scanner = EvalDelegateScanner.for_toxicity()
        scanner = EvalDelegateScanner.for_pii()
        scanner = EvalDelegateScanner.for_safety()  # Multiple categories

    Note:
        This scanner requires either:
        - API key for cloud-based evaluation (more accurate, slower)
        - Local LLM setup for local evaluation (faster, may be less accurate)
    """

    name = "eval_delegate"
    category = "eval_delegate"
    description = "Delegates to evaluation templates"
    default_action = ScannerAction.BLOCK

    def __init__(
        self,
        categories: Optional[List[EvalCategory]] = None,
        thresholds: Optional[Dict[EvalCategory, float]] = None,
        prefer_local: bool = True,
        api_key: Optional[str] = None,
        timeout: int = 30,
        parallel: bool = True,
        aggregation: str = "any",
        action: Optional[ScannerAction] = None,
        enabled: bool = True,
    ):
        """
        Initialize the eval delegate scanner.

        Args:
            categories: List of eval categories to check
            thresholds: Custom thresholds per category
            prefer_local: Use local evaluator if available
            api_key: API key for cloud evaluation
            timeout: Timeout in seconds
            parallel: Run categories in parallel
            aggregation: "any" or "all" for failure aggregation
            action: Action to take on detection
            enabled: Whether scanner is enabled
        """
        super().__init__(action=action, enabled=enabled)

        self.categories = categories or [EvalCategory.TOXICITY]
        self.thresholds = thresholds or {}
        self.prefer_local = prefer_local
        self.api_key = api_key
        self.timeout = timeout
        self.parallel = parallel
        self.aggregation = aggregation

        # Lazy-loaded evaluators
        self._local_evaluator = None
        self._cloud_evaluator = None


_bind_owner(EvalDelegateScanner)


# Convenience aliases
PIIScanner = lambda **kwargs: EvalDelegateScanner.for_pii(**kwargs)
ToxicityScanner = lambda **kwargs: EvalDelegateScanner.for_toxicity(**kwargs)
PromptInjectionScanner = lambda **kwargs: EvalDelegateScanner.for_prompt_injection(**kwargs)
BiasScanner = lambda **kwargs: EvalDelegateScanner.for_bias(**kwargs)
SafetyScanner = lambda **kwargs: EvalDelegateScanner.for_safety(**kwargs)
ContentModerationScanner = lambda **kwargs: EvalDelegateScanner.for_content_moderation(**kwargs)
