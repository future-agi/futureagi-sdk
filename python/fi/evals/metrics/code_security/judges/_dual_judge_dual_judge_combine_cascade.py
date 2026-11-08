"""DualJudge combine cascade operations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple
from fi.evals.metrics.code_security.judges.dual_judge import (Dict, JudgeFinding, JudgeResult, List)

if TYPE_CHECKING:
    from fi.evals.metrics.code_security.judges.dual_judge import DualJudge


class _DualJudgeCombineCascadeMethods:
    __slots__ = ()

    def _combine_cascade(
        self,
        pattern_result: JudgeResult,
        llm_result: JudgeResult,
        language: str,
    ) -> JudgeResult:
        """CASCADE mode: Pattern first, LLM validates/refines."""
        from fi.evals.metrics.code_security.judges.dual_judge import (JudgeFinding, JudgeResult)
        # LLM result refines pattern result
        # - Confirms or rejects pattern findings
        # - May add new findings pattern missed

        final_findings = []

        # Check which pattern findings LLM confirms
        pattern_by_cwe = self._group_by_cwe(pattern_result.findings)
        llm_by_cwe = self._group_by_cwe(llm_result.findings)

        for cwe, pattern_findings in pattern_by_cwe.items():
            if cwe in llm_by_cwe:
                # LLM confirms - boost confidence
                for f in pattern_findings:
                    confirmed = JudgeFinding(
                        cwe_id=f.cwe_id,
                        vulnerability_type=f.vulnerability_type,
                        description=f.description,
                        severity=f.severity,
                        confidence=min(1.0, f.confidence * 1.3),  # Boost
                        location=f.location,
                        suggested_fix=llm_by_cwe[cwe][0].suggested_fix or f.suggested_fix,
                        judge_type="dual",
                        reasoning=llm_by_cwe[cwe][0].reasoning,
                    )
                    final_findings.append(confirmed)
            else:
                # LLM doesn't confirm - reduce confidence
                for f in pattern_findings:
                    unconfirmed = JudgeFinding(
                        cwe_id=f.cwe_id,
                        vulnerability_type=f.vulnerability_type,
                        description=f.description,
                        severity=f.severity,
                        confidence=f.confidence * 0.5,  # Reduce
                        location=f.location,
                        suggested_fix=f.suggested_fix,
                        judge_type="pattern",
                        reasoning="LLM did not confirm this finding",
                    )
                    final_findings.append(unconfirmed)

        # Add LLM-only findings (pattern false negatives)
        for cwe, llm_findings in llm_by_cwe.items():
            if cwe not in pattern_by_cwe:
                for f in llm_findings:
                    final_findings.append(f)

        # Filter
        filtered = self._filter_findings(final_findings)

        return JudgeResult(
            is_secure=self._is_secure(filtered),
            security_score=self._compute_score(filtered),
            findings=filtered,
            judge_type=self.judge_type,
            language=language,
            pattern_result=pattern_result,
            llm_result=llm_result,
            consensus_mode=self.consensus_mode,
        )


    def _deduplicate_findings(
        self,
        findings: List[JudgeFinding],
    ) -> List[JudgeFinding]:
        """Remove duplicate findings, keeping highest confidence."""
        from fi.evals.metrics.code_security.judges.dual_judge import (JudgeFinding, List)
        # Group by (CWE, line)
        by_key: Dict[Tuple[str, Optional[int]], JudgeFinding] = {}

        for f in findings:
            line = f.location.line if f.location else None
            key = (f.cwe_id, line)

            if key not in by_key or f.confidence > by_key[key].confidence:
                by_key[key] = f

        return list(by_key.values())


    def _find_agreed_findings(
        self,
        pattern_findings: List[JudgeFinding],
        llm_findings: List[JudgeFinding],
    ) -> List[JudgeFinding]:
        """Find findings that both judges agree on."""
        from fi.evals.metrics.code_security.judges.dual_judge import (JudgeFinding, List)
        pattern_cwes = {f.cwe_id for f in pattern_findings}
        llm_cwes = {f.cwe_id for f in llm_findings}
        agreed_cwes = pattern_cwes & llm_cwes

        # Return LLM findings for agreed CWEs (better descriptions)
        return [f for f in llm_findings if f.cwe_id in agreed_cwes]


    def _group_by_cwe(
        self,
        findings: List[JudgeFinding],
    ) -> Dict[str, List[JudgeFinding]]:
        """Group findings by CWE ID."""
        from fi.evals.metrics.code_security.judges.dual_judge import (Dict, JudgeFinding, List)
        by_cwe: Dict[str, List[JudgeFinding]] = {}
        for f in findings:
            if f.cwe_id not in by_cwe:
                by_cwe[f.cwe_id] = []
            by_cwe[f.cwe_id].append(f)
        return by_cwe


    @classmethod
    def pattern_only(cls) -> "DualJudge":
        """Factory for pattern-only mode (fast, no API calls)."""
        from fi.evals.metrics.code_security.judges.dual_judge import (PatternJudge)
        return cls(
            pattern_judge=PatternJudge(),
            llm_judge=None,
        )


    @classmethod
    def high_recall(cls, llm_model: str = "gpt-4") -> "DualJudge":
        """Factory for high recall mode (catches more vulnerabilities)."""
        from fi.evals.metrics.code_security.judges.dual_judge import (
            ConsensusMode, LLMJudge, PatternJudge,
        )
        return cls(
            pattern_judge=PatternJudge.with_strict_rules(),
            llm_judge=LLMJudge(model=llm_model),
            consensus_mode=ConsensusMode.ANY,
        )


    @classmethod
    def high_precision(cls, llm_model: str = "gpt-4") -> "DualJudge":
        """Factory for high precision mode (fewer false positives)."""
        from fi.evals.metrics.code_security.judges.dual_judge import (
            ConsensusMode, LLMJudge, PatternJudge,
        )
        return cls(
            pattern_judge=PatternJudge.with_high_precision(),
            llm_judge=LLMJudge(model=llm_model),
            consensus_mode=ConsensusMode.BOTH,
        )


    @classmethod
    def balanced(cls, llm_model: str = "gpt-4") -> "DualJudge":
        """Factory for balanced mode (default)."""
        from fi.evals.metrics.code_security.judges.dual_judge import (
            ConsensusMode, LLMJudge, PatternJudge,
        )
        return cls(
            pattern_judge=PatternJudge(),
            llm_judge=LLMJudge(model=llm_model),
            consensus_mode=ConsensusMode.WEIGHTED,
        )


    @classmethod
    def efficient(cls, llm_model: str = "gpt-3.5-turbo") -> "DualJudge":
        """Factory for efficient mode (pattern first, LLM only when needed)."""
        from fi.evals.metrics.code_security.judges.dual_judge import (
            ConsensusMode, LLMJudge, PatternJudge,
        )
        return cls(
            pattern_judge=PatternJudge(),
            llm_judge=LLMJudge(model=llm_model),
            consensus_mode=ConsensusMode.CASCADE,
        )
