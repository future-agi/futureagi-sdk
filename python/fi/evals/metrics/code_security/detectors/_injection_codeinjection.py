"""Codeinjection for injection."""
from __future__ import annotations

from fi.evals.metrics.code_security.detectors.injection import (
    AnalysisResult, BaseDetector, List, Optional, SecurityFinding, Severity, VulnerabilityCategory,
    re, register_detector,
)

@register_detector("code_injection")
class CodeInjectionDetector(BaseDetector):
    """
    Detects code injection vulnerabilities (CWE-94).

    Identifies:
    - eval() with user input
    - exec() with user input
    - Dynamic code compilation
    - Template injection

    Examples of vulnerable code:
        eval(user_input)
        exec(f"print({value})")
        compile(code, '<string>', 'exec')
    """

    name = "code_injection"
    cwe_ids = ["CWE-94"]
    category = VulnerabilityCategory.INJECTION
    description = "Code Injection via dynamic execution"
    default_severity = Severity.CRITICAL

    CODE_EXECUTION_PATTERNS = {
        "python": [
            # Any eval/exec call is dangerous if passed variable
            (r"\beval\s*\(\s*[a-zA-Z_]", "eval with variable", Severity.CRITICAL),
            (r"\bexec\s*\(\s*[a-zA-Z_]", "exec with variable", Severity.CRITICAL),
            (r"\beval\s*\([^)]*[\+\$\{]", "eval with concatenation", Severity.CRITICAL),
            (r"\bexec\s*\([^)]*[\+\$\{]", "exec with concatenation", Severity.CRITICAL),
            (r"\beval\s*\(f['\"]", "eval with f-string", Severity.CRITICAL),
            (r"\bexec\s*\(f['\"]", "exec with f-string", Severity.CRITICAL),
            (r"\bcompile\s*\([^)]+,\s*['\"]<string>['\"]", "compile", Severity.HIGH),
        ],
        "javascript": [
            # Any eval call is dangerous
            (r"\beval\s*\(\s*[a-zA-Z_]", "eval with variable", Severity.CRITICAL),
            (r"\beval\s*\([^)]*[\+\$\{]", "eval with concatenation", Severity.CRITICAL),
            (r"\bnew\s+Function\s*\([^)]*[\+\$\{]", "Function constructor", Severity.CRITICAL),
            (r"setTimeout\s*\([^)]*[\+\$\{]", "setTimeout with string", Severity.MEDIUM),
            (r"setInterval\s*\([^)]*[\+\$\{]", "setInterval with string", Severity.MEDIUM),
        ],
    }

    def detect(
        self,
        code: str,
        language: str,
        analysis: Optional[AnalysisResult] = None,
    ) -> List[SecurityFinding]:
        """Detect code injection vulnerabilities."""
        if not self.enabled:
            return []

        findings = []
        lines = code.split("\n")
        lang_lower = language.lower()

        patterns = self.CODE_EXECUTION_PATTERNS.get(lang_lower, [])

        for i, line in enumerate(lines, 1):
            for pattern, description, severity in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(self.create_finding(
                        vulnerability_type="Code Injection",
                        description=f"Dynamic code execution via {description}",
                        line=i,
                        snippet=line.strip()[:100],
                        severity=severity,
                        confidence=0.9,
                        suggested_fix="Avoid eval/exec. Use safer alternatives like ast.literal_eval for Python.",
                    ))
                    break  # One finding per line

        return findings
