"""DualJudge judge operations."""
from __future__ import annotations

from fi.evals.metrics.code_security.judges.dual_judge import (Any, Dict, JudgeResult, Optional)


class _DualJudgeJudgeMethods:
    __slots__ = ()

    def judge(
        self,
        code: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None,
    ) -> JudgeResult:
        """
        Judge code using dual-judge system.

        Args:
            code: Source code to analyze
            language: Programming language
            context: Optional context

        Returns:
            JudgeResult with combined findings
        """
        from fi.evals.metrics.code_security.judges.dual_judge import (
            Any, ConsensusMode, Dict, JudgeResult, Optional, time,
        )
        start_time = time.time()

        # Get pattern result (always run)
        pattern_result = self.pattern_judge.judge(code, language, context)

        # Get LLM result if configured
        llm_result = None
        if self.llm_judge is not None:
            if self.consensus_mode == ConsensusMode.CASCADE:
                # Only run LLM if pattern result is uncertain
                if self._should_cascade(pattern_result):
                    llm_result = self._run_llm_judge(code, language, context)
            elif self.parallel:
                # Run in parallel (but we already have pattern result)
                llm_result = self._run_llm_judge(code, language, context)
            else:
                llm_result = self._run_llm_judge(code, language, context)

        # Combine results based on consensus mode
        combined_result = self._combine_results(
            pattern_result, llm_result, language
        )

        execution_time = (time.time() - start_time) * 1000
        combined_result.execution_time_ms = execution_time

        return combined_result


    def _run_llm_judge(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]],
    ) -> Optional[JudgeResult]:
        """Run LLM judge with timeout handling."""
        from fi.evals.metrics.code_security.judges.dual_judge import (
            Any, Dict, JudgeResult, Optional, ThreadPoolExecutor, TimeoutError,
        )
        if self.llm_judge is None:
            return None

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.llm_judge.judge, code, language, context
                )
                return future.result(timeout=self.llm_timeout)
        except TimeoutError:
            return None
        except Exception:
            return None


    def _should_cascade(self, pattern_result: JudgeResult) -> bool:
        """Determine if LLM should be invoked in CASCADE mode."""
        from fi.evals.metrics.code_security.judges.dual_judge import (JudgeResult)
        # Invoke LLM if:
        # 1. Pattern found findings but confidence is moderate
        # 2. Pattern found no findings (might be false negative)

        if not pattern_result.findings:
            # No findings - let LLM check for false negatives
            return True

        # Check if any findings have moderate confidence
        avg_confidence = sum(f.confidence for f in pattern_result.findings) / len(
            pattern_result.findings
        )
        return avg_confidence < self.cascade_threshold


    def _combine_results(
        self,
        pattern_result: JudgeResult,
        llm_result: Optional[JudgeResult],
        language: str,
    ) -> JudgeResult:
        """Combine results based on consensus mode."""
        from fi.evals.metrics.code_security.judges.dual_judge import (
            ConsensusMode, JudgeResult, Optional,
        )
        # If no LLM result, return pattern result
        if llm_result is None:
            return JudgeResult(
                is_secure=pattern_result.is_secure,
                security_score=pattern_result.security_score,
                findings=pattern_result.findings,
                judge_type=self.judge_type,
                language=language,
                pattern_result=pattern_result,
                llm_result=None,
                consensus_mode=self.consensus_mode,
            )

        # Combine based on mode
        if self.consensus_mode == ConsensusMode.ANY:
            return self._combine_any(pattern_result, llm_result, language)
        elif self.consensus_mode == ConsensusMode.BOTH:
            return self._combine_both(pattern_result, llm_result, language)
        elif self.consensus_mode == ConsensusMode.WEIGHTED:
            return self._combine_weighted(pattern_result, llm_result, language)
        elif self.consensus_mode == ConsensusMode.CASCADE:
            return self._combine_cascade(pattern_result, llm_result, language)
        else:
            raise ValueError(f"Unknown consensus mode: {self.consensus_mode}")


    def _combine_any(
        self,
        pattern_result: JudgeResult,
        llm_result: JudgeResult,
        language: str,
    ) -> JudgeResult:
        """ANY mode: Include findings from either judge (union)."""
        from fi.evals.metrics.code_security.judges.dual_judge import (JudgeResult)
        # Merge all findings
        all_findings = list(pattern_result.findings) + list(llm_result.findings)

        # Deduplicate by CWE and location
        unique_findings = self._deduplicate_findings(all_findings)

        # Insecure if either judge says insecure
        is_secure = pattern_result.is_secure and llm_result.is_secure

        # Score is minimum of both
        security_score = min(
            pattern_result.security_score, llm_result.security_score
        )

        return JudgeResult(
            is_secure=is_secure,
            security_score=security_score,
            findings=unique_findings,
            judge_type=self.judge_type,
            language=language,
            pattern_result=pattern_result,
            llm_result=llm_result,
            consensus_mode=self.consensus_mode,
        )


    def _combine_both(
        self,
        pattern_result: JudgeResult,
        llm_result: JudgeResult,
        language: str,
    ) -> JudgeResult:
        """BOTH mode: Only include findings both judges agree on (intersection)."""
        from fi.evals.metrics.code_security.judges.dual_judge import (JudgeResult)
        # Find matching findings
        agreed_findings = self._find_agreed_findings(
            pattern_result.findings, llm_result.findings
        )

        # Insecure only if both say insecure
        is_secure = pattern_result.is_secure or llm_result.is_secure

        # Score is maximum of both (more conservative)
        security_score = max(
            pattern_result.security_score, llm_result.security_score
        )

        return JudgeResult(
            is_secure=self._is_secure(agreed_findings),
            security_score=self._compute_score(agreed_findings),
            findings=agreed_findings,
            judge_type=self.judge_type,
            language=language,
            pattern_result=pattern_result,
            llm_result=llm_result,
            consensus_mode=self.consensus_mode,
        )


    def _combine_weighted(
        self,
        pattern_result: JudgeResult,
        llm_result: JudgeResult,
        language: str,
    ) -> JudgeResult:
        """WEIGHTED mode: Weighted combination of confidences."""
        from fi.evals.metrics.code_security.judges.dual_judge import (JudgeFinding, JudgeResult)
        # Merge findings with weighted confidence
        weighted_findings = []

        # Group findings by CWE
        pattern_by_cwe = self._group_by_cwe(pattern_result.findings)
        llm_by_cwe = self._group_by_cwe(llm_result.findings)

        all_cwes = set(pattern_by_cwe.keys()) | set(llm_by_cwe.keys())

        for cwe in all_cwes:
            pattern_findings = pattern_by_cwe.get(cwe, [])
            llm_findings = llm_by_cwe.get(cwe, [])

            if pattern_findings and llm_findings:
                # Both found - combine confidence
                pattern_conf = max(f.confidence for f in pattern_findings)
                llm_conf = max(f.confidence for f in llm_findings)
                combined_conf = (
                    self.pattern_weight * pattern_conf
                    + self.llm_weight * llm_conf
                )

                # Use LLM finding as base (better description/reasoning)
                best_llm = max(llm_findings, key=lambda f: f.confidence)
                combined = JudgeFinding(
                    cwe_id=best_llm.cwe_id,
                    vulnerability_type=best_llm.vulnerability_type,
                    description=best_llm.description,
                    severity=best_llm.severity,
                    confidence=combined_conf,
                    location=best_llm.location or (
                        pattern_findings[0].location if pattern_findings else None
                    ),
                    suggested_fix=best_llm.suggested_fix,
                    judge_type="dual",
                    reasoning=best_llm.reasoning,
                )
                weighted_findings.append(combined)

            elif pattern_findings:
                # Only pattern found - use pattern weight
                for f in pattern_findings:
                    adjusted = JudgeFinding(
                        cwe_id=f.cwe_id,
                        vulnerability_type=f.vulnerability_type,
                        description=f.description,
                        severity=f.severity,
                        confidence=f.confidence * self.pattern_weight,
                        location=f.location,
                        suggested_fix=f.suggested_fix,
                        judge_type="pattern",
                        reasoning=f.reasoning,
                    )
                    weighted_findings.append(adjusted)

            else:
                # Only LLM found - use LLM weight
                for f in llm_findings:
                    adjusted = JudgeFinding(
                        cwe_id=f.cwe_id,
                        vulnerability_type=f.vulnerability_type,
                        description=f.description,
                        severity=f.severity,
                        confidence=f.confidence * self.llm_weight,
                        location=f.location,
                        suggested_fix=f.suggested_fix,
                        judge_type="llm",
                        reasoning=f.reasoning,
                    )
                    weighted_findings.append(adjusted)

        # Filter by confidence threshold
        filtered = self._filter_findings(weighted_findings)

        # Weighted score
        weighted_score = (
            self.pattern_weight * pattern_result.security_score
            + self.llm_weight * llm_result.security_score
        )

        return JudgeResult(
            is_secure=self._is_secure(filtered),
            security_score=weighted_score,
            findings=filtered,
            judge_type=self.judge_type,
            language=language,
            pattern_result=pattern_result,
            llm_result=llm_result,
            consensus_mode=self.consensus_mode,
        )
