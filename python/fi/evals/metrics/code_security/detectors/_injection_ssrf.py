"""Ssrf for injection."""
from __future__ import annotations

from fi.evals.metrics.code_security.detectors.injection import (
    AnalysisResult, BaseDetector, List, Optional, SecurityFinding, Severity, VulnerabilityCategory,
    re, register_detector,
)

@register_detector("ssrf")
class SSRFDetector(BaseDetector):
    """
    Detects Server-Side Request Forgery vulnerabilities (CWE-918).

    Identifies:
    - HTTP requests with user-controlled URLs
    - URL construction with user input

    Examples of vulnerable code:
        requests.get(user_url)
        urllib.request.urlopen(url)
        fetch(userInput)
    """

    name = "ssrf"
    cwe_ids = ["CWE-918"]
    category = VulnerabilityCategory.INJECTION
    description = "Server-Side Request Forgery"
    default_severity = Severity.HIGH

    HTTP_FUNCTIONS = {
        "python": [
            "requests.get", "requests.post", "requests.put", "requests.delete",
            "requests.head", "requests.patch", "requests.request",
            "urllib.request.urlopen", "urllib2.urlopen",
            "httplib.HTTPConnection", "http.client.HTTPConnection",
            "aiohttp.ClientSession", "httpx.get", "httpx.post",
        ],
        "javascript": [
            "fetch", "axios.get", "axios.post", "axios.put",
            "http.get", "https.get", "request",
        ],
        "java": [
            "URL.openConnection", "HttpURLConnection",
            "HttpClient.execute", "RestTemplate",
        ],
    }

    def detect(
        self,
        code: str,
        language: str,
        analysis: Optional[AnalysisResult] = None,
    ) -> List[SecurityFinding]:
        """Detect SSRF vulnerabilities."""
        if not self.enabled:
            return []

        findings = []
        lines = code.split("\n")
        lang_lower = language.lower()

        functions = self.HTTP_FUNCTIONS.get(lang_lower, [])

        for i, line in enumerate(lines, 1):
            for func in functions:
                func_name = func.split(".")[-1]
                pattern = rf"\b{re.escape(func_name)}\s*\("

                if re.search(pattern, line, re.IGNORECASE):
                    # Check if URL appears to be user-controlled (variable passed)
                    # Match: function(variable) or function(url) - any non-string first arg
                    has_variable = bool(re.search(
                        rf"{re.escape(func_name)}\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*[,\)]",
                        line
                    ))
                    # Also check for concatenation or f-strings
                    has_concat = bool(re.search(r"[\+\$\{]|f['\"]", line))

                    if has_variable or has_concat:
                        findings.append(self.create_finding(
                            vulnerability_type="Server-Side Request Forgery (SSRF)",
                            description=f"HTTP request with potentially user-controlled URL: {func}",
                            line=i,
                            snippet=line.strip()[:100],
                            confidence=0.7 if has_variable else 0.6,
                            suggested_fix="Validate and whitelist allowed URLs. Don't allow user control of full URL.",
                        ))
                        break

        return findings
