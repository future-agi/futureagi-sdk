"""Xss for injection."""
from __future__ import annotations

from fi.evals.metrics.code_security.detectors.injection import (
    AnalysisResult, BaseDetector, List, Optional, SecurityFinding, Severity, VulnerabilityCategory,
    re, register_detector,
)

@register_detector("xss")
class XSSDetector(BaseDetector):
    """
    Detects Cross-Site Scripting vulnerabilities (CWE-79).

    Identifies:
    - innerHTML assignments with variable
    - document.write with variable
    - Unescaped template rendering
    - Response write without encoding

    Examples of vulnerable code:
        element.innerHTML = userInput
        document.write(data)
        res.send("<div>" + name + "</div>")
    """

    name = "xss"
    cwe_ids = ["CWE-79"]
    category = VulnerabilityCategory.INJECTION
    description = "Cross-Site Scripting via unescaped output"
    default_severity = Severity.MEDIUM
    supported_languages = {"javascript", "js", "typescript", "ts", "python", "php"}

    XSS_SINKS = {
        "javascript": [
            (r"\.innerHTML\s*=", "innerHTML assignment"),
            (r"\.outerHTML\s*=", "outerHTML assignment"),
            (r"document\.write\s*\(", "document.write"),
            (r"document\.writeln\s*\(", "document.writeln"),
            (r"\.insertAdjacentHTML\s*\(", "insertAdjacentHTML"),
            (r"eval\s*\(", "eval"),
        ],
        "python": [
            (r"render_template_string\s*\(", "render_template_string"),
            (r"Markup\s*\(", "Markup without escape"),
            (r"\|safe\b", "Jinja2 safe filter"),
            # Flask/Django returning HTML with f-strings
            (r'return\s+f["\'].*<[a-zA-Z]', "returning HTML with f-string"),
            (r'return\s+["\']<.*\+', "returning HTML with concatenation"),
        ],
        "php": [
            (r"echo\s+\$", "echo with variable"),
            (r"print\s+\$", "print with variable"),
        ],
    }

    def detect(
        self,
        code: str,
        language: str,
        analysis: Optional[AnalysisResult] = None,
    ) -> List[SecurityFinding]:
        """Detect XSS vulnerabilities."""
        if not self.enabled or not self.supports_language(language):
            return []

        findings = []
        lines = code.split("\n")
        lang_lower = language.lower()

        # Normalize language
        if lang_lower in ["ts", "typescript"]:
            lang_lower = "javascript"
        if lang_lower == "js":
            lang_lower = "javascript"

        sinks = self.XSS_SINKS.get(lang_lower, [])

        for i, line in enumerate(lines, 1):
            for pattern, description in sinks:
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if there's variable involvement
                    has_variable = bool(re.search(r"[\+\$\{]|f['\"]|\bvar\b|\blet\b|\bconst\b", line))

                    if has_variable or "innerHTML" in line:
                        findings.append(self.create_finding(
                            vulnerability_type="Cross-Site Scripting (XSS)",
                            description=f"Potential XSS via {description}",
                            line=i,
                            snippet=line.strip()[:100],
                            confidence=0.75 if has_variable else 0.6,
                            suggested_fix="Escape user input before rendering. Use textContent instead of innerHTML.",
                        ))
                        break

        return findings
