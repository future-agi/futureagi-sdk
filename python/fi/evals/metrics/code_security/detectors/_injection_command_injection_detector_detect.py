"""CommandInjectionDetector detect operations."""
from __future__ import annotations

from fi.evals.metrics.code_security.detectors.injection import (
    AnalysisResult, List, Optional, SecurityFinding,
)


class _CommandInjectionDetectorDetectMethods:
    __slots__ = ()

    def detect(
        self,
        code: str,
        language: str,
        analysis: Optional[AnalysisResult] = None,
    ) -> List[SecurityFinding]:
        """Detect command injection vulnerabilities."""
        from fi.evals.metrics.code_security.detectors.injection import (
            AnalysisResult, List, Optional, SecurityFinding, Severity, re,
        )
        if not self.enabled:
            return []

        findings = []
        lines = code.split("\n")
        lang_lower = language.lower()

        dangerous_funcs = self.DANGEROUS_FUNCTIONS.get(lang_lower, {})

        for i, line in enumerate(lines, 1):
            # Check for backtick command execution (JavaScript)
            if lang_lower in ["javascript", "js", "typescript", "ts"]:
                for pattern, description in self.BACKTICK_PATTERNS:
                    if re.search(pattern, line):
                        findings.append(self.create_finding(
                            vulnerability_type="Command Injection",
                            description=f"Shell command via {description}",
                            line=i,
                            snippet=line.strip()[:100],
                            severity=Severity.CRITICAL,
                            confidence=0.85,
                            suggested_fix="Avoid template literal shell commands. Use proper command builders.",
                        ))
                        break

            for func, description in dangerous_funcs.items():
                # Check if function is called
                func_pattern = rf"\b{re.escape(func.split('.')[-1])}\s*\("
                if not re.search(func_pattern, line):
                    continue

                # Check for variable input or shell=True
                has_variable_input = any(
                    re.search(p, line) for p in self.VARIABLE_INPUT_PATTERNS
                )

                if has_variable_input or "shell=True" in line.lower():
                    severity = Severity.CRITICAL
                    confidence = 0.9 if has_variable_input else 0.85

                    findings.append(self.create_finding(
                        vulnerability_type="Command Injection",
                        description=f"{description} with variable input: {func}",
                        line=i,
                        snippet=line.strip()[:100],
                        severity=severity,
                        confidence=confidence,
                        suggested_fix="Use subprocess with shell=False and list arguments. Validate/sanitize input.",
                    ))

        return findings
