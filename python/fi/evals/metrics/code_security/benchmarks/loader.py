"""
Benchmark loader and runner.

Provides the SecurityBenchmark class for loading test suites
and evaluating models against them.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from collections import defaultdict

from .types import (
    InstructTest,
    AutocompleteTest,
    RepairTest,
    BenchmarkResult,
    CWEBreakdown,
)
from ..types import EvaluationMode
from ..detectors import scan_code


# Path to built-in benchmark data
BENCHMARK_DATA_DIR = Path(__file__).parent / "data"


from ._loader_security_benchmark_load_instruct_tests import _SecurityBenchmarkLoadInstructTestsMethods
from ._loader_security_benchmark_evaluate_autocomplete import _SecurityBenchmarkEvaluateAutocompleteMethods

class SecurityBenchmark(
    _SecurityBenchmarkLoadInstructTestsMethods,
    _SecurityBenchmarkEvaluateAutocompleteMethods,
):
    """
    Security benchmark for evaluating AI code generation.

    Provides curated test suites and evaluation methods for
    measuring how securely AI models generate code.

    Usage:
        benchmark = SecurityBenchmark()

        # Load specific tests
        tests = benchmark.load_instruct_tests("python")

        # Run full evaluation
        result = benchmark.evaluate_model(
            model_fn=lambda prompt: my_model.generate(prompt),
            language="python",
            mode=EvaluationMode.INSTRUCT,
        )

        print(result.to_summary())
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        custom_tests: Optional[Dict[str, List]] = None,
    ):
        """
        Initialize the benchmark.

        Args:
            data_dir: Directory containing benchmark data files
            custom_tests: Optional custom test cases to include
        """
        self.data_dir = data_dir or BENCHMARK_DATA_DIR
        self.custom_tests = custom_tests or {}
        self._cache: Dict[str, Any] = {}


def load_benchmark(
    name: str,
    data_dir: Optional[Path] = None,
) -> SecurityBenchmark:
    """
    Load a named benchmark.

    Args:
        name: Benchmark name (e.g., "python-injection")
        data_dir: Optional custom data directory

    Returns:
        SecurityBenchmark instance
    """
    return SecurityBenchmark(data_dir=data_dir)


def list_available_benchmarks() -> List[str]:
    """List available benchmark names."""
    benchmarks = []

    if BENCHMARK_DATA_DIR.exists():
        for lang_dir in BENCHMARK_DATA_DIR.iterdir():
            if lang_dir.is_dir():
                for test_file in lang_dir.glob("*_tests.json"):
                    mode = test_file.stem.replace("_tests", "")
                    benchmarks.append(f"{lang_dir.name}-{mode}")

    # Add built-in
    benchmarks.extend([
        "python-instruct",
        "python-autocomplete",
        "python-repair",
    ])

    return sorted(set(benchmarks))
