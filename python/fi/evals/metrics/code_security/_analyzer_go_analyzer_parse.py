"""GoAnalyzer parse operations."""
from __future__ import annotations

from fi.evals.metrics.code_security.analyzer import (
    AnalysisResult, Any, Dict, FunctionInfo, ImportInfo, List, Optional, StringLiteral,
)


class _GoAnalyzerParseMethods:
    __slots__ = ()

    def parse(self, code: str) -> Optional[Dict[str, Any]]:
        """Parse Go using regex."""
        from fi.evals.metrics.code_security.analyzer import (Any, Dict, Optional)
        return {"code": code}


    def analyze(self, code: str) -> AnalysisResult:
        """Analyze Go code."""
        from fi.evals.metrics.code_security.analyzer import (AnalysisResult)
        return AnalysisResult(
            language=self.language,
            functions=self._extract_functions(code),
            imports=self._extract_imports(code),
            strings=self._extract_strings(code),
            variables=self._extract_variables(code),
            dangerous_calls=self._find_dangerous_calls(code),
            parse_errors=[],
            raw_ast=None,
        )


    def _extract_functions(self, code: str) -> List[FunctionInfo]:
        """Extract function definitions."""
        from fi.evals.metrics.code_security.analyzer import (FunctionInfo, List, re)
        functions = []

        pattern = r"func\s+(?:\([^)]+\)\s+)?(\w+)\s*\((.*?)\)"

        for i, line in enumerate(code.split("\n"), 1):
            match = re.search(pattern, line)
            if match:
                name = match.group(1)
                args_str = match.group(2)
                args = []
                if args_str.strip():
                    for arg in args_str.split(","):
                        parts = arg.strip().split()
                        if parts:
                            args.append(parts[0])

                functions.append(FunctionInfo(
                    name=name,
                    line=i,
                    end_line=None,
                    args=args,
                    decorators=[],
                    is_async=False,
                    docstring=None,
                    calls=[],
                ))

        return functions


    def _extract_imports(self, code: str) -> List[ImportInfo]:
        """Extract import statements."""
        from fi.evals.metrics.code_security.analyzer import (ImportInfo, List, re)
        imports = []

        # Single import
        for i, line in enumerate(code.split("\n"), 1):
            match = re.match(r'import\s+"([^"]+)"', line.strip())
            if match:
                imports.append(ImportInfo(
                    module=match.group(1),
                    names=[],
                    alias=None,
                    line=i,
                ))

        # Multi-line import block
        in_import = False
        for i, line in enumerate(code.split("\n"), 1):
            if "import (" in line:
                in_import = True
                continue
            if in_import:
                if ")" in line:
                    in_import = False
                    continue
                match = re.search(r'"([^"]+)"', line)
                if match:
                    imports.append(ImportInfo(
                        module=match.group(1),
                        names=[],
                        alias=None,
                        line=i,
                    ))

        return imports


    def _extract_strings(self, code: str) -> List[StringLiteral]:
        """Extract string literals."""
        from fi.evals.metrics.code_security.analyzer import (List, StringLiteral, re)
        strings = []

        for i, line in enumerate(code.split("\n"), 1):
            # Double-quoted strings
            for match in re.finditer(r'"([^"]{3,})"', line):
                strings.append(StringLiteral(
                    value=match.group(1),
                    line=i,
                    column=match.start(),
                    is_fstring=False,
                    context=None,
                ))

            # Backtick strings (raw)
            for match in re.finditer(r"`([^`]{3,})`", line):
                strings.append(StringLiteral(
                    value=match.group(1),
                    line=i,
                    column=match.start(),
                    is_fstring=False,
                    context=None,
                ))

        return strings


    def _extract_variables(self, code: str) -> Dict[str, List[int]]:
        """Extract variable declarations."""
        from fi.evals.metrics.code_security.analyzer import (Dict, List, re)
        variables: Dict[str, List[int]] = {}

        patterns = [
            r"(\w+)\s*:=",  # Short declaration
            r"var\s+(\w+)",  # Var declaration
        ]

        for i, line in enumerate(code.split("\n"), 1):
            for pattern in patterns:
                for match in re.finditer(pattern, line):
                    name = match.group(1)
                    if name not in variables:
                        variables[name] = []
                    variables[name].append(i)

        return variables
