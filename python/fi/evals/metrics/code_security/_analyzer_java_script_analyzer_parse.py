"""JavaScriptAnalyzer parse operations."""
from __future__ import annotations

from fi.evals.metrics.code_security.analyzer import (
    AnalysisResult, Any, Dict, FunctionInfo, ImportInfo, List, Optional, StringLiteral,
)


class _JavaScriptAnalyzerParseMethods:
    __slots__ = ()

    def parse(self, code: str) -> Optional[Dict[str, Any]]:
        """Parse JavaScript using regex (tree-sitter optional)."""
        from fi.evals.metrics.code_security.analyzer import (Any, Dict, Optional)
        # Basic structural analysis without full parsing
        return {"code": code}


    def analyze(self, code: str) -> AnalysisResult:
        """Analyze JavaScript code."""
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

        patterns = [
            # function name(args)
            r"function\s+(\w+)\s*\((.*?)\)",
            # const/let/var name = function(args)
            r"(?:const|let|var)\s+(\w+)\s*=\s*function\s*\((.*?)\)",
            # const/let/var name = (args) =>
            r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\((.*?)\)\s*=>",
            # async function name(args)
            r"async\s+function\s+(\w+)\s*\((.*?)\)",
        ]

        for i, line in enumerate(code.split("\n"), 1):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1)
                    args_str = match.group(2)
                    args = [a.strip().split(":")[0].split("=")[0].strip()
                            for a in args_str.split(",") if a.strip()]

                    is_async = "async" in line[:match.start()]

                    functions.append(FunctionInfo(
                        name=name,
                        line=i,
                        end_line=None,
                        args=args,
                        decorators=[],
                        is_async=is_async,
                        docstring=None,
                        calls=[],
                    ))
                    break

        return functions


    def _extract_imports(self, code: str) -> List[ImportInfo]:
        """Extract import statements."""
        from fi.evals.metrics.code_security.analyzer import (ImportInfo, List, re)
        imports = []

        patterns = [
            # import x from 'module'
            r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
            # import { x, y } from 'module'
            r"import\s*\{([^}]+)\}\s*from\s*['\"]([^'\"]+)['\"]",
            # const x = require('module')
            r"(?:const|let|var)\s+(\w+)\s*=\s*require\s*\(['\"]([^'\"]+)['\"]\)",
        ]

        for i, line in enumerate(code.split("\n"), 1):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    if "{" in pattern:
                        names = [n.strip() for n in match.group(1).split(",")]
                        module = match.group(2)
                    else:
                        names = [match.group(1)]
                        module = match.group(2)

                    imports.append(ImportInfo(
                        module=module,
                        names=names,
                        alias=None,
                        line=i,
                    ))

        return imports


    def _extract_strings(self, code: str) -> List[StringLiteral]:
        """Extract string literals."""
        from fi.evals.metrics.code_security.analyzer import (List, StringLiteral, re)
        strings = []

        for i, line in enumerate(code.split("\n"), 1):
            # Template literals
            for match in re.finditer(r"`([^`]*)`", line):
                strings.append(StringLiteral(
                    value=match.group(1),
                    line=i,
                    column=match.start(),
                    is_fstring="${" in match.group(1),
                    context=None,
                ))

            # Regular strings
            for match in re.finditer(r"['\"]([^'\"]{3,})['\"]", line):
                if not re.search(r"['\"]" + re.escape(match.group(1)) + r"['\"]", line[:match.start()]):
                    strings.append(StringLiteral(
                        value=match.group(1),
                        line=i,
                        column=match.start(),
                        is_fstring=False,
                        context=None,
                    ))

        return strings


    def _extract_variables(self, code: str) -> Dict[str, List[int]]:
        """Extract variable assignments."""
        from fi.evals.metrics.code_security.analyzer import (Dict, List, re)
        variables: Dict[str, List[int]] = {}

        pattern = r"(?:const|let|var)\s+(\w+)\s*="
        for i, line in enumerate(code.split("\n"), 1):
            for match in re.finditer(pattern, line):
                name = match.group(1)
                if name not in variables:
                    variables[name] = []
                variables[name].append(i)

        return variables
