"""PythonAnalyzer extract imports regex operations."""
from __future__ import annotations

from fi.evals.metrics.code_security.analyzer import (ImportInfo, List, StringLiteral)


class _PythonAnalyzerExtractImportsRegexMethods:
    __slots__ = ()

    def _extract_imports_regex(self, code: str) -> List[ImportInfo]:
        """Fallback regex-based import extraction."""
        from fi.evals.metrics.code_security.analyzer import (ImportInfo, List, re)
        imports = []

        # import module
        for i, line in enumerate(code.split("\n"), 1):
            match = re.match(r"^\s*import\s+([\w.]+)(?:\s+as\s+(\w+))?", line)
            if match:
                imports.append(ImportInfo(
                    module=match.group(1),
                    names=[],
                    alias=match.group(2),
                    line=i,
                ))

            # from module import names
            match = re.match(r"^\s*from\s+([\w.]+)\s+import\s+(.+)", line)
            if match:
                names = [n.strip().split(" as ")[0] for n in match.group(2).split(",")]
                imports.append(ImportInfo(
                    module=match.group(1),
                    names=names,
                    alias=None,
                    line=i,
                ))

        return imports


    def _extract_strings_regex(self, code: str) -> List[StringLiteral]:
        """Fallback regex-based string extraction."""
        from fi.evals.metrics.code_security.analyzer import (List, StringLiteral, re)
        strings = []

        # Match various string patterns
        patterns = [
            (r'f["\']([^"\']*)["\']', True),   # f-strings
            (r'["\']([^"\']{3,})["\']', False),  # Regular strings (3+ chars)
        ]

        for i, line in enumerate(code.split("\n"), 1):
            for pattern, is_fstring in patterns:
                for match in re.finditer(pattern, line):
                    strings.append(StringLiteral(
                        value=match.group(1),
                        line=i,
                        column=match.start(),
                        is_fstring=is_fstring,
                        context=None,
                    ))

        return strings
