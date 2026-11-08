"""JointSecurityMetrics evaluate operations."""
from __future__ import annotations

from fi.evals.metrics.code_security.joint_metrics import (
    Callable, FunctionalTestCase, FunctionalTestResult, JointMetricsResult, List, Optional,
    SecurityFinding, Union,
)


class _JointSecurityMetricsEvaluateMethods:
    __slots__ = ()

    def evaluate(
        self,
        code: str,
        language: str = "python",
        test_cases: Optional[List[Union[FunctionalTestCase, dict]]] = None,
        test_fn: Optional[Callable[[str], bool]] = None,
    ) -> JointMetricsResult:
        """
        Evaluate a single code sample.

        Args:
            code: The code to evaluate
            language: Programming language
            test_cases: Optional test cases for functional testing
            test_fn: Optional custom test function

        Returns:
            JointMetricsResult with func, sec, and func-sec scores
        """
        from fi.evals.metrics.code_security.joint_metrics import (
            Callable, FunctionalTestCase, FunctionalTestResult, JointMetricsResult, List, Optional,
            Union, scan_code,
        )
        # Security evaluation
        findings = scan_code(code, language)
        confident_findings = [
            f for f in findings if f.confidence >= self.min_confidence
        ]
        sec_score = self._compute_sec_score(confident_findings)
        is_secure = self._is_secure(confident_findings)

        # Functional evaluation
        func_result = None
        func_score = 0.0
        is_functional = False

        if test_fn is not None:
            try:
                is_functional = test_fn(code)
                func_score = 1.0 if is_functional else 0.0
            except Exception as e:
                func_result = FunctionalTestResult(
                    passed=False,
                    execution_error=str(e),
                )
        elif test_cases is not None:
            func_result = self._run_tests(code, test_cases, language)
            is_functional = func_result.passed
            func_score = func_result.pass_rate
        else:
            # No functional tests — can't measure correctness, return sec-only
            is_functional = True
            func_score = 1.0  # Not tested; func-sec@k degrades to sec@k

        # Joint score
        func_sec_score = 1.0 if (is_functional and is_secure) else 0.0

        return JointMetricsResult(
            func_score=func_score,
            sec_score=sec_score,
            func_sec_score=func_sec_score,
            n_samples=1,
            func_at_k=func_score,
            sec_at_k=sec_score,
            func_sec_at_k=func_sec_score,
            security_findings=confident_findings,
            functional_results=func_result,
            sample_results=[{
                "is_functional": is_functional,
                "is_secure": is_secure,
                "is_both": is_functional and is_secure,
                "func_score": func_score,
                "sec_score": sec_score,
            }],
        )


    def evaluate_samples(
        self,
        samples: List[str],
        language: str = "python",
        test_cases: Optional[List[Union[FunctionalTestCase, dict]]] = None,
        test_fn: Optional[Callable[[str], bool]] = None,
    ) -> JointMetricsResult:
        """
        Evaluate multiple code samples for @k metrics.

        Args:
            samples: List of code samples
            language: Programming language
            test_cases: Optional test cases for functional testing
            test_fn: Optional custom test function

        Returns:
            JointMetricsResult with @k metrics
        """
        from fi.evals.metrics.code_security.joint_metrics import (
            Callable, FunctionalTestCase, JointMetricsResult, List, Optional, Union,
        )
        if not samples:
            return JointMetricsResult(
                func_score=0.0,
                sec_score=0.0,
                func_sec_score=0.0,
                n_samples=0,
            )

        # Evaluate each sample
        sample_results = []
        for code in samples:
            result = self.evaluate(
                code=code,
                language=language,
                test_cases=test_cases,
                test_fn=test_fn,
            )
            sample_results.append({
                "is_functional": result.func_score > 0.5,
                "is_secure": result.sec_score > 0.5,
                "is_both": result.func_sec_score == 1.0,
                "func_score": result.func_score,
                "sec_score": result.sec_score,
                "findings": result.security_findings,
            })

        # Compute @k metrics
        n = len(samples)
        func_count = sum(1 for r in sample_results if r["is_functional"])
        sec_count = sum(1 for r in sample_results if r["is_secure"])
        both_count = sum(1 for r in sample_results if r["is_both"])

        func_at_k = func_count / n
        sec_at_k = sec_count / n
        func_sec_at_k = both_count / n

        # Aggregate scores (average across samples)
        avg_func = sum(r["func_score"] for r in sample_results) / n
        avg_sec = sum(r["sec_score"] for r in sample_results) / n
        avg_both = func_sec_at_k

        # Collect all findings
        all_findings = []
        for r in sample_results:
            all_findings.extend(r.get("findings", []))

        return JointMetricsResult(
            func_score=avg_func,
            sec_score=avg_sec,
            func_sec_score=avg_both,
            n_samples=n,
            func_at_k=func_at_k,
            sec_at_k=sec_at_k,
            func_sec_at_k=func_sec_at_k,
            security_findings=self._deduplicate_findings(all_findings),
            sample_results=sample_results,
        )


    def _compute_sec_score(self, findings: List[SecurityFinding]) -> float:
        """Compute security score from findings."""
        from fi.evals.metrics.code_security.joint_metrics import (
            List, SEVERITY_WEIGHTS, SecurityFinding,
        )
        if not findings:
            return 1.0

        total_penalty = sum(
            SEVERITY_WEIGHTS.get(f.severity, 0.1) * f.confidence
            for f in findings
        )

        return max(0.0, 1.0 - min(1.0, total_penalty))


    def _is_secure(self, findings: List[SecurityFinding]) -> bool:
        """Check if findings indicate secure code."""
        from fi.evals.metrics.code_security.joint_metrics import (List, SecurityFinding, Severity)
        severity_order = [
            Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM,
            Severity.LOW, Severity.INFO
        ]
        threshold_idx = severity_order.index(self.severity_threshold)

        for finding in findings:
            finding_idx = severity_order.index(finding.severity)
            if finding_idx <= threshold_idx:
                return False
        return True


    def _run_tests(
        self,
        code: str,
        test_cases: List[Union[FunctionalTestCase, dict]],
        language: str,
    ) -> FunctionalTestResult:
        """
        Run functional tests on code.

        Note: By default, this does static analysis only.
        Set execute_code=True in __init__ for actual execution.
        """
        from fi.evals.metrics.code_security.joint_metrics import (
            FunctionalTestCase, FunctionalTestResult, List, Union,
        )
        if not self.execute_code:
            # Static check only - assume functional if code looks complete
            return self._static_functional_check(code, test_cases)

        # Sandboxed execution not yet implemented
        import warnings
        warnings.warn(
            "execute_code=True requires sandboxed execution (not yet implemented). "
            "Falling back to static functional check.",
            stacklevel=2,
        )
        return self._static_functional_check(code, test_cases)


    def _static_functional_check(
        self,
        code: str,
        test_cases: List[Union[FunctionalTestCase, dict]],
    ) -> FunctionalTestResult:
        """
        Static check for functional correctness.

        Heuristics:
        - Code is not empty
        - Code has function/class definitions
        - No obvious syntax errors
        """
        from fi.evals.metrics.code_security.joint_metrics import (
            FunctionalTestCase, FunctionalTestResult, List, Union,
        )
        # Empty code fails
        if not code or not code.strip():
            return FunctionalTestResult(
                passed=False,
                total_tests=len(test_cases),
                passed_tests=0,
                failed_tests=len(test_cases),
            )

        # Check for function/class definitions
        has_definition = any(
            keyword in code
            for keyword in ["def ", "class ", "function ", "const ", "let ", "var "]
        )

        # Check for return statement (for functions)
        has_return = "return" in code

        # Basic structure check
        is_likely_functional = has_definition and has_return

        return FunctionalTestResult(
            passed=is_likely_functional,
            total_tests=len(test_cases),
            passed_tests=len(test_cases) if is_likely_functional else 0,
            failed_tests=0 if is_likely_functional else len(test_cases),
        )


    def _deduplicate_findings(
        self,
        findings: List[SecurityFinding],
    ) -> List[SecurityFinding]:
        """Remove duplicate findings."""
        from fi.evals.metrics.code_security.joint_metrics import (List, SecurityFinding)
        seen = set()
        unique = []
        for f in findings:
            key = (f.cwe_id, f.vulnerability_type)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique
