"""AutoEval Pipeline - Main API for automatic evaluation pipelines.

Provides the core AutoEvalPipeline class for creating and running
evaluation pipelines from natural language descriptions or templates.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Type, Union

from .types import AutoEvalResult, AppAnalysis
from .config import AutoEvalConfig, EvalConfig, ScannerConfig
from .analyzer import AppAnalyzer
from .recommender import EvalRecommender
from .templates import get_template, list_templates

logger = logging.getLogger(__name__)


# Registry for eval/scanner class lookups
_EVAL_CLASS_REGISTRY: Dict[str, Type] = {}
_SCANNER_CLASS_REGISTRY: Dict[str, Type] = {}


def register_eval_class(name: str, cls: Type) -> None:
    """Register an evaluation class for AutoEval lookup."""
    _EVAL_CLASS_REGISTRY[name] = cls


def register_scanner_class(name: str, cls: Type) -> None:
    """Register a scanner class for AutoEval lookup."""
    _SCANNER_CLASS_REGISTRY[name] = cls


def _get_eval_class(name: str) -> Optional[Type]:
    """Get evaluation class by name."""
    # Try direct registry lookup first
    if name in _EVAL_CLASS_REGISTRY:
        return _EVAL_CLASS_REGISTRY[name]

    # Try to import from framework
    try:
        from fi.evals.framework import EvalRegistry

        if EvalRegistry.is_registered(name):
            return EvalRegistry.get(name)
    except (ImportError, ValueError):
        pass

    # Try to import from evals module
    try:
        from fi.evals import templates as eval_templates

        if hasattr(eval_templates, name):
            return getattr(eval_templates, name)
    except ImportError:
        pass

    return None


def _get_scanner_class(name: str) -> Optional[Type]:
    """Get scanner class by name."""
    # Try direct registry lookup first
    if name in _SCANNER_CLASS_REGISTRY:
        return _SCANNER_CLASS_REGISTRY[name]

    # Try to import from guardrails.scanners
    try:
        from fi.evals.guardrails import scanners as scanner_module

        if hasattr(scanner_module, name):
            return getattr(scanner_module, name)
    except ImportError:
        pass

    return None


from fi.evals._extracted import bind_owner as _bind_owner
from ._pipeline_auto_eval_pipeline_from_description import _AutoEvalPipelineFromDescriptionMethods
from ._pipeline_auto_eval_pipeline_evaluate import _AutoEvalPipelineEvaluateMethods

class AutoEvalPipeline(_AutoEvalPipelineFromDescriptionMethods, _AutoEvalPipelineEvaluateMethods):
    """
    Automatic evaluation pipeline builder.

    Creates evaluation pipelines from natural language descriptions,
    pre-built templates, or manual configuration.

    Example:
        # From natural language description
        pipeline = AutoEvalPipeline.from_description(
            "A RAG-based customer support chatbot for healthcare. "
            "Retrieves patient records and answers questions about appointments."
        )

        # From pre-built template
        pipeline = AutoEvalPipeline.from_template("rag_system")

        # Run evaluation
        result = pipeline.evaluate({
            "query": "When is my appointment?",
            "response": "Your appointment is Monday at 2pm.",
            "context": "Patient has appointment on 2024-01-15 14:00",
        })

        print(result.passed)  # True/False
        print(result.explain())  # Detailed breakdown

        # Export configuration
        pipeline.export_yaml("eval_config.yaml")
    """

    def __init__(
        self,
        config: AutoEvalConfig,
        analysis: Optional[AppAnalysis] = None,
    ):
        """
        Initialize the pipeline with configuration.

        Args:
            config: AutoEvalConfig with evaluations and scanners
            analysis: Optional AppAnalysis for explanation context
        """
        self.config = config
        self.analysis = analysis
        self._evaluator = None
        self._scanner_pipeline = None
        self._eval_instances: List[Any] = []
        self._scanner_instances: List[Any] = []


_bind_owner(AutoEvalPipeline)
