"""PatternJudge judge operations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Set, Tuple
from fi.evals.metrics.code_security.judges.pattern_judge import (
    Any, Dict, JudgeFinding, JudgeResult, List, Optional, PatternRule,
)

if TYPE_CHECKING:
    from fi.evals.metrics.code_security.judges.pattern_judge import PatternJudge


class _PatternJudgeJudgeMethods:
    __slots__ = ()

    def judge(
        self,
        code: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None,
    ) -> JudgeResult:
        """
        Judge code for security vulnerabilities using patterns.

        Args:
            code: Source code to analyze
            language: Programming language
            context: Optional context (unused in pattern judge)

        Returns:
            JudgeResult with findings
        """
        from fi.evals.metrics.code_security.judges.pattern_judge import (
            Any, CodeLocation, Dict, JudgeFinding, JudgeResult, Optional, time,
        )
        start_time = time.time()

        findings: List[JudgeFinding] = []

        for rule in self.rules:
            # Skip excluded rules
            if rule.name in self.exclude_rules:
                continue

            # Skip if CWE filter active and rule not in filter
            if self.cwe_filter and rule.cwe_id not in self.cwe_filter:
                continue

            # Skip if language doesn't match
            if language.lower() not in rule.languages:
                continue

            # Check for matches
            matches = rule.matches(code)
            for line, column, matched_text in matches:
                finding = JudgeFinding(
                    cwe_id=rule.cwe_id,
                    vulnerability_type=rule.name,
                    description=f"{rule.description}: '{matched_text[:50]}...' " if len(matched_text) > 50 else f"{rule.description}: '{matched_text}'",
                    severity=rule.severity,
                    confidence=rule.confidence,
                    location=CodeLocation(
                        line=line,
                        column=column,
                        snippet=matched_text[:100],
                    ),
                    judge_type=self.judge_type,
                )
                findings.append(finding)

        # Filter by confidence
        filtered_findings = self._filter_findings(findings)

        # Deduplicate findings at same location
        unique_findings = self._deduplicate_findings(filtered_findings)

        execution_time = (time.time() - start_time) * 1000

        return JudgeResult(
            is_secure=self._is_secure(unique_findings),
            security_score=self._compute_score(unique_findings),
            findings=unique_findings,
            judge_type=self.judge_type,
            execution_time_ms=execution_time,
            language=language,
        )


    def _deduplicate_findings(
        self,
        findings: List[JudgeFinding],
    ) -> List[JudgeFinding]:
        """Remove duplicate findings at the same location."""
        from fi.evals.metrics.code_security.judges.pattern_judge import (JudgeFinding, List)
        seen: Set[Tuple[str, int, str]] = set()
        unique: List[JudgeFinding] = []

        for finding in findings:
            key = (
                finding.cwe_id,
                finding.location.line if finding.location else 0,
                finding.vulnerability_type,
            )
            if key not in seen:
                seen.add(key)
                unique.append(finding)

        return unique


    def get_rules_for_cwe(self, cwe_id: str) -> List[PatternRule]:
        """Get all rules for a specific CWE."""
        from fi.evals.metrics.code_security.judges.pattern_judge import (List, PatternRule)
        return [r for r in self.rules if r.cwe_id == cwe_id]


    def get_rules_for_language(self, language: str) -> List[PatternRule]:
        """Get all rules for a specific language."""
        from fi.evals.metrics.code_security.judges.pattern_judge import (List, PatternRule)
        return [r for r in self.rules if language.lower() in r.languages]


    @classmethod
    def with_strict_rules(cls) -> "PatternJudge":
        """Factory for strict pattern checking (lower confidence threshold)."""
        from fi.evals.metrics.code_security.judges.pattern_judge import (Severity)
        return cls(
            severity_threshold=Severity.LOW,
            min_confidence=0.5,
        )


    @classmethod
    def with_high_precision(cls) -> "PatternJudge":
        """Factory for high-precision mode (fewer false positives)."""
        from fi.evals.metrics.code_security.judges.pattern_judge import (Severity)
        return cls(
            severity_threshold=Severity.HIGH,
            min_confidence=0.85,
        )


    @classmethod
    def for_injection_only(cls) -> "PatternJudge":
        """Factory for injection-focused scanning."""
        return cls(
            cwe_filter=["CWE-89", "CWE-78", "CWE-79", "CWE-94"],
        )


    @classmethod
    def for_crypto_only(cls) -> "PatternJudge":
        """Factory for cryptography-focused scanning."""
        return cls(
            cwe_filter=["CWE-327", "CWE-330", "CWE-798"],
        )
