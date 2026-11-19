"""SecurityBenchmark load instruct tests operations."""
from __future__ import annotations

from typing import Dict
from fi.evals.metrics.code_security.benchmarks.loader import (
    AutocompleteTest, BenchmarkResult, Callable, EvaluationMode, InstructTest, List, Optional,
    RepairTest,
)


class _SecurityBenchmarkLoadInstructTestsMethods:
    __slots__ = ()

    def load_instruct_tests(
        self,
        language: str = "python",
        tags: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
    ) -> List[InstructTest]:
        """
        Load instruct mode test cases.

        Args:
            language: Programming language
            tags: Filter by tags
            difficulty: Filter by difficulty

        Returns:
            List of instruct test cases
        """
        from fi.evals.metrics.code_security.benchmarks.loader import (InstructTest, List, Optional)
        # Try to load from file
        cache_key = f"instruct_{language}"
        if cache_key not in self._cache:
            tests = self._load_tests_from_file(language, "instruct", InstructTest)

            # Add built-in tests
            from .builtin import PYTHON_INSTRUCT_TESTS

            if language == "python":
                tests.extend(PYTHON_INSTRUCT_TESTS)

            self._cache[cache_key] = tests

        tests = self._cache[cache_key]

        # Apply filters
        if tags:
            tests = [t for t in tests if t.tags and any(tag in t.tags for tag in tags)]
        if difficulty:
            tests = [t for t in tests if t.difficulty == difficulty]

        return tests


    def load_autocomplete_tests(
        self,
        language: str = "python",
        tags: Optional[List[str]] = None,
    ) -> List[AutocompleteTest]:
        """Load autocomplete mode test cases."""
        from fi.evals.metrics.code_security.benchmarks.loader import (
            AutocompleteTest, List, Optional,
        )
        cache_key = f"autocomplete_{language}"
        if cache_key not in self._cache:
            tests = self._load_tests_from_file(
                language, "autocomplete", AutocompleteTest
            )

            # Add built-in tests
            from .builtin import PYTHON_AUTOCOMPLETE_TESTS

            if language == "python":
                tests.extend(PYTHON_AUTOCOMPLETE_TESTS)

            self._cache[cache_key] = tests

        tests = self._cache[cache_key]

        if tags:
            tests = [t for t in tests if t.tags and any(tag in t.tags for tag in tags)]

        return tests


    def load_repair_tests(
        self,
        language: str = "python",
        cwes: Optional[List[str]] = None,
    ) -> List[RepairTest]:
        """Load repair mode test cases."""
        from fi.evals.metrics.code_security.benchmarks.loader import (List, Optional, RepairTest)
        cache_key = f"repair_{language}"
        if cache_key not in self._cache:
            tests = self._load_tests_from_file(language, "repair", RepairTest)

            # Add built-in tests
            from .builtin import PYTHON_REPAIR_TESTS

            if language == "python":
                tests.extend(PYTHON_REPAIR_TESTS)

            self._cache[cache_key] = tests

        tests = self._cache[cache_key]

        if cwes:
            tests = [
                t for t in tests if any(cwe in t.cwes_to_fix for cwe in cwes)
            ]

        return tests


    def _load_tests_from_file(
        self,
        language: str,
        mode: str,
        test_class: type,
    ) -> List:
        """Load tests from JSON file if it exists."""
        from fi.evals.metrics.code_security.benchmarks.loader import (List, json)
        file_path = self.data_dir / language / f"{mode}_tests.json"
        if file_path.exists():
            with open(file_path) as f:
                data = json.load(f)
            return [test_class(**item) for item in data]
        return []


    def evaluate_model(
        self,
        model_fn: Callable[[str], str],
        language: str = "python",
        mode: EvaluationMode = EvaluationMode.INSTRUCT,
        max_tests: Optional[int] = None,
        k: int = 1,
    ) -> BenchmarkResult:
        """
        Run full benchmark against a model.

        Args:
            model_fn: Function that takes a prompt and returns generated code
            language: Programming language
            mode: Evaluation mode
            max_tests: Maximum number of tests to run (None = all)
            k: Number of samples per prompt for @k metrics

        Returns:
            BenchmarkResult with comprehensive metrics
        """
        from fi.evals.metrics.code_security.benchmarks.loader import (
            BenchmarkResult, Callable, EvaluationMode, Optional, time,
        )
        start_time = time.time()

        if mode == EvaluationMode.INSTRUCT:
            return self._evaluate_instruct(model_fn, language, max_tests, k)
        elif mode == EvaluationMode.AUTOCOMPLETE:
            return self._evaluate_autocomplete(model_fn, language, max_tests, k)
        elif mode == EvaluationMode.REPAIR:
            return self._evaluate_repair(model_fn, language, max_tests, k)
        else:
            raise ValueError(f"Unsupported mode: {mode}")


    def _evaluate_instruct(
        self,
        model_fn: Callable[[str], str],
        language: str,
        max_tests: Optional[int],
        k: int,
    ) -> BenchmarkResult:
        """Evaluate instruct mode."""
        from fi.evals.metrics.code_security.benchmarks.loader import (
            BenchmarkResult, CWEBreakdown, Callable, Optional, defaultdict, scan_code, time,
        )
        tests = self.load_instruct_tests(language)
        if max_tests:
            tests = tests[:max_tests]

        start_time = time.time()
        results = []
        cwe_counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"total": 0, "secure": 0}
        )
        all_cwes_found: List[str] = []

        for test in tests:
            # Generate k samples
            samples = []
            for _ in range(k):
                try:
                    generated = model_fn(test.prompt)
                    samples.append(generated)
                except Exception:
                    samples.append("")

            # Evaluate each sample
            test_results = []
            for sample in samples:
                if not sample:
                    test_results.append(
                        {"functional": False, "secure": True, "cwes": []}
                    )
                    continue

                # Security check
                findings = scan_code(sample, language)
                cwes = [f.cwe_id for f in findings]
                is_secure = len(findings) == 0

                # Functional check (basic - checks if code is valid)
                is_functional = self._check_functional(
                    sample, language, test.functional_tests
                )

                test_results.append(
                    {
                        "functional": is_functional,
                        "secure": is_secure,
                        "cwes": cwes,
                    }
                )
                all_cwes_found.extend(cwes)

            # Track CWE performance
            if test.expected_cwes:
                for cwe in test.expected_cwes:
                    cwe_counts[cwe]["total"] += 1
                    if any(r["secure"] for r in test_results):
                        cwe_counts[cwe]["secure"] += 1

            results.append(test_results)

        # Compute metrics
        total_tests = len(tests)
        completed = len([r for r in results if r])

        # func@k: at least one sample is functional
        func_at_k = sum(
            1 for r in results if any(s["functional"] for s in r)
        ) / total_tests if total_tests > 0 else 0

        # sec@k: at least one sample is secure
        sec_at_k = sum(
            1 for r in results if any(s["secure"] for s in r)
        ) / total_tests if total_tests > 0 else 0

        # func-sec@k: at least one sample is both
        func_sec_at_k = sum(
            1
            for r in results
            if any(s["functional"] and s["secure"] for s in r)
        ) / total_tests if total_tests > 0 else 0

        # CWE breakdown
        cwe_breakdown = [
            CWEBreakdown(
                cwe_id=cwe,
                total_tests=counts["total"],
                secure_count=counts["secure"],
                vulnerable_count=counts["total"] - counts["secure"],
                secure_rate=counts["secure"] / counts["total"]
                if counts["total"] > 0
                else 1.0,
            )
            for cwe, counts in cwe_counts.items()
        ]

        # Most common CWE
        cwe_freq = defaultdict(int)
        for cwe in all_cwes_found:
            cwe_freq[cwe] += 1
        most_common = max(cwe_freq.items(), key=lambda x: x[1])[0] if cwe_freq else None

        total_time = (time.time() - start_time) * 1000

        return BenchmarkResult(
            benchmark_name=f"instruct_{language}",
            language=language,
            mode="instruct",
            total_tests=total_tests,
            completed_tests=completed,
            func_at_k=func_at_k,
            sec_at_k=sec_at_k,
            func_sec_at_k=func_sec_at_k,
            overall_security_score=sec_at_k,
            cwe_breakdown=cwe_breakdown,
            most_common_cwe=most_common,
            total_time_ms=total_time,
            avg_time_per_test_ms=total_time / total_tests if total_tests > 0 else 0,
        )
