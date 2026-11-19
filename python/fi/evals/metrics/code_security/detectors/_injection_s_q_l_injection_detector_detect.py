"""SQLInjectionDetector detect operations."""
from __future__ import annotations

from fi.evals.metrics.code_security.detectors.injection import (
    AnalysisResult, List, Optional, SecurityFinding,
)


class _SQLInjectionDetectorDetectMethods:
    __slots__ = ()

    def detect(
        self,
        code: str,
        language: str,
        analysis: Optional[AnalysisResult] = None,
    ) -> List[SecurityFinding]:
        """Detect SQL injection vulnerabilities."""
        from fi.evals.metrics.code_security.detectors.injection import (
            AnalysisResult, List, Optional, SecurityFinding, re,
        )
        if not self.enabled:
            return []

        findings = []
        lines = code.split("\n")
        lang_lower = language.lower()

        # Get patterns for this language
        unsafe_patterns = self.UNSAFE_PATTERNS.get(lang_lower, self.UNSAFE_PATTERNS["python"])
        safe_patterns = self.SAFE_PATTERNS.get(lang_lower, [])

        for i, line in enumerate(lines, 1):
            line_lower = line.lower()

            # Skip if no SQL keywords
            if not any(kw in line_lower for kw in self.SQL_KEYWORDS):
                continue

            # Skip if matches safe pattern
            if any(re.search(p, line, re.IGNORECASE) for p in safe_patterns):
                continue

            # Check unsafe patterns
            for pattern, description in unsafe_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Determine confidence based on context
                    confidence = 0.8
                    if analysis and analysis.functions:
                        # Higher confidence if in a route/endpoint
                        func = self._find_function(analysis, i)
                        if func and any(d in ["route", "get", "post", "api"] for d in func.decorators):
                            confidence = 0.95

                    findings.append(self.create_finding(
                        vulnerability_type="SQL Injection",
                        description=f"{description}: {line.strip()[:60]}...",
                        line=i,
                        snippet=line.strip()[:100],
                        confidence=confidence,
                        suggested_fix="Use parameterized queries: cursor.execute(query, (param,))",
                    ))
                    break  # One finding per line

        return findings


    def _find_function(self, analysis: AnalysisResult, line: int):
        """Find the function containing the given line."""
        from fi.evals.metrics.code_security.detectors.injection import (AnalysisResult)
        for func in analysis.functions:
            if func.line <= line and (func.end_line is None or func.end_line >= line):
                return func
        return None
