"""Xxe for injection."""
from __future__ import annotations

from fi.evals.metrics.code_security.detectors.injection import (
    AnalysisResult, BaseDetector, List, Optional, SecurityFinding, Severity, VulnerabilityCategory,
    re, register_detector,
)

@register_detector("xxe")
class XXEDetector(BaseDetector):
    """
    Detects XML External Entity vulnerabilities (CWE-611).

    Identifies:
    - XML parsing without disabling external entities
    - Unsafe XML parser configurations

    Examples of vulnerable code:
        etree.parse(xml_file)
        xml.etree.ElementTree.fromstring(xml)
        DocumentBuilderFactory.newInstance()  # without setFeature
    """

    name = "xxe"
    cwe_ids = ["CWE-611"]
    category = VulnerabilityCategory.INJECTION
    description = "XML External Entity (XXE) Injection"
    default_severity = Severity.HIGH
    supported_languages = {"python", "java"}

    XXE_PATTERNS = {
        "python": [
            (r"etree\.parse\s*\(", "etree.parse without defuse"),
            (r"etree\.fromstring\s*\(", "etree.fromstring without defuse"),
            (r"ET\.parse\s*\(", "ET.parse without defuse"),
            (r"ET\.fromstring\s*\(", "ET.fromstring without defuse"),
            (r"ElementTree\.parse\s*\(", "ElementTree.parse"),
            (r"ElementTree\.fromstring\s*\(", "ElementTree.fromstring"),
            (r"xml\.dom\.minidom\.parse\s*\(", "minidom.parse"),
            (r"xml\.sax\.parse\s*\(", "sax.parse"),
            (r"lxml\.etree\.parse\s*\(", "lxml.etree.parse"),
            (r"lxml\.etree\.fromstring\s*\(", "lxml.etree.fromstring"),
            (r"XMLParser\s*\(", "XMLParser without defuse"),
        ],
        "java": [
            (r"DocumentBuilderFactory\.newInstance\s*\(", "DocumentBuilderFactory without secure config"),
            (r"SAXParserFactory\.newInstance\s*\(", "SAXParserFactory without secure config"),
            (r"XMLInputFactory\.newInstance\s*\(", "XMLInputFactory without secure config"),
        ],
    }

    SAFE_PATTERNS = {
        "python": [
            r"defusedxml",
            r"resolve_entities\s*=\s*False",
        ],
        "java": [
            r"setFeature.*XMLConstants\.FEATURE_SECURE_PROCESSING",
            r"setFeature.*disallow-doctype-decl",
        ],
    }

    def detect(
        self,
        code: str,
        language: str,
        analysis: Optional[AnalysisResult] = None,
    ) -> List[SecurityFinding]:
        """Detect XXE vulnerabilities."""
        if not self.enabled or not self.supports_language(language):
            return []

        findings = []
        lang_lower = language.lower()

        # Check if safe patterns are present in entire code
        safe_patterns = self.SAFE_PATTERNS.get(lang_lower, [])
        has_safe_config = any(re.search(p, code, re.IGNORECASE) for p in safe_patterns)

        if has_safe_config:
            return []

        lines = code.split("\n")
        patterns = self.XXE_PATTERNS.get(lang_lower, [])

        for i, line in enumerate(lines, 1):
            for pattern, description in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(self.create_finding(
                        vulnerability_type="XML External Entity (XXE)",
                        description=f"Potentially unsafe XML parsing: {description}",
                        line=i,
                        snippet=line.strip()[:100],
                        confidence=0.75,
                        suggested_fix="Use defusedxml (Python) or disable external entities (Java).",
                    ))

        return findings
