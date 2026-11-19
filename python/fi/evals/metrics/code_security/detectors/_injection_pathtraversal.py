"""Pathtraversal for injection."""
from __future__ import annotations

from fi.evals.metrics.code_security.detectors.injection import (
    AnalysisResult, BaseDetector, List, Optional, SecurityFinding, Severity, VulnerabilityCategory,
    re, register_detector,
)

@register_detector("path_traversal")
class PathTraversalDetector(BaseDetector):
    """
    Detects Path Traversal vulnerabilities (CWE-22).

    Identifies:
    - File operations with user-controlled paths
    - Lack of path sanitization

    Examples of vulnerable code:
        open(user_path)
        os.path.join(base, user_input)
        fs.readFile(userPath)
    """

    name = "path_traversal"
    cwe_ids = ["CWE-22"]
    category = VulnerabilityCategory.INPUT_VALIDATION
    description = "Path Traversal via unsanitized file paths"
    default_severity = Severity.HIGH

    FILE_OPERATIONS = {
        "python": [
            "open", "file", "os.path.join", "pathlib.Path",
            "shutil.copy", "shutil.move", "os.remove", "os.unlink",
            "os.rename", "os.listdir", "os.makedirs", "send_file",
            "send_from_directory",
        ],
        "javascript": [
            "fs.readFile", "fs.writeFile", "fs.unlink", "fs.mkdir",
            "fs.readFileSync", "fs.writeFileSync", "path.join",
            "fs.createReadStream", "fs.createWriteStream",
        ],
        "java": [
            "FileInputStream", "FileOutputStream", "FileReader",
            "FileWriter", "File", "Files.readAllBytes",
        ],
    }

    def detect(
        self,
        code: str,
        language: str,
        analysis: Optional[AnalysisResult] = None,
    ) -> List[SecurityFinding]:
        """Detect path traversal vulnerabilities."""
        if not self.enabled:
            return []

        findings = []
        lines = code.split("\n")
        lang_lower = language.lower()

        operations = self.FILE_OPERATIONS.get(lang_lower, [])

        for i, line in enumerate(lines, 1):
            for op in operations:
                op_name = op.split(".")[-1]
                pattern = rf"\b{re.escape(op_name)}\s*\("

                if re.search(pattern, line, re.IGNORECASE):
                    # Check for variable input - any non-string literal arg
                    has_variable = bool(re.search(
                        rf"{re.escape(op_name)}\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*[,\)]",
                        line
                    ))

                    # Also check for concatenation or f-strings
                    has_concat = bool(re.search(r"[\+\$\{]|f['\"]", line))

                    # Check for path traversal indicators
                    has_traversal = bool(re.search(r"\.\./|\.\.\\", line))

                    if has_variable or has_concat or has_traversal:
                        confidence = 0.85 if has_traversal else (0.7 if has_variable else 0.6)

                        findings.append(self.create_finding(
                            vulnerability_type="Path Traversal",
                            description=f"File operation with potentially unsafe path: {op}",
                            line=i,
                            snippet=line.strip()[:100],
                            confidence=confidence,
                            suggested_fix="Validate and sanitize file paths. Use os.path.realpath() and check against allowed directories.",
                        ))
                        break

        return findings
