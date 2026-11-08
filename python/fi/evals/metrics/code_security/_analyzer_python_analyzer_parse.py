"""PythonAnalyzer parse operations."""
from __future__ import annotations

from fi.evals.metrics.code_security.analyzer import (
    AnalysisResult, Dict, FunctionInfo, ImportInfo, List, Optional, StringLiteral, Tuple, ast,
)


class _PythonAnalyzerParseMethods:
    __slots__ = ()

    def parse(self, code: str) -> Optional[ast.AST]:
        """Parse Python code into AST."""
        from fi.evals.metrics.code_security.analyzer import (Optional, ast)
        try:
            return ast.parse(code)
        except SyntaxError:
            return None


    def analyze(self, code: str) -> AnalysisResult:
        """Analyze Python code."""
        from fi.evals.metrics.code_security.analyzer import (AnalysisResult)
        tree = self.parse(code)
        parse_errors = []

        if tree is None:
            # Try to extract what we can with regex
            parse_errors.append("Failed to parse Python AST")
            return AnalysisResult(
                language=self.language,
                functions=self._extract_functions_regex(code),
                imports=self._extract_imports_regex(code),
                strings=self._extract_strings_regex(code),
                variables={},
                dangerous_calls=self._find_dangerous_calls(code),
                parse_errors=parse_errors,
                raw_ast=None,
            )

        return AnalysisResult(
            language=self.language,
            functions=self._extract_functions(tree),
            imports=self._extract_imports(tree),
            strings=self._extract_strings(tree, code),
            variables=self._extract_variables(tree),
            dangerous_calls=self._find_dangerous_calls_ast(tree),
            parse_errors=parse_errors,
            raw_ast=tree,
        )


    def _extract_functions(self, tree: ast.AST) -> List[FunctionInfo]:
        """Extract function definitions from AST."""
        from fi.evals.metrics.code_security.analyzer import (FunctionInfo, List, ast)
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Get decorator names
                decorators = []
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators.append(dec.id)
                    elif isinstance(dec, ast.Attribute):
                        decorators.append(f"{self._get_full_name(dec)}")
                    elif isinstance(dec, ast.Call):
                        if isinstance(dec.func, ast.Name):
                            decorators.append(dec.func.id)
                        elif isinstance(dec.func, ast.Attribute):
                            decorators.append(self._get_full_name(dec.func))

                # Get docstring
                docstring = ast.get_docstring(node)

                # Get function calls within this function
                calls = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_name = self._get_call_name(child)
                        if call_name:
                            calls.append(call_name)

                functions.append(FunctionInfo(
                    name=node.name,
                    line=node.lineno,
                    end_line=getattr(node, 'end_lineno', None),
                    args=[arg.arg for arg in node.args.args],
                    decorators=decorators,
                    is_async=isinstance(node, ast.AsyncFunctionDef),
                    docstring=docstring,
                    calls=calls,
                ))

        return functions


    def _extract_imports(self, tree: ast.AST) -> List[ImportInfo]:
        """Extract import statements from AST."""
        from fi.evals.metrics.code_security.analyzer import (ImportInfo, List, ast)
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[],
                        alias=alias.asname,
                        line=node.lineno,
                    ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                imports.append(ImportInfo(
                    module=module,
                    names=names,
                    alias=None,
                    line=node.lineno,
                ))

        return imports


    def _extract_strings(self, tree: ast.AST, code: str) -> List[StringLiteral]:
        """Extract string literals from AST."""
        from fi.evals.metrics.code_security.analyzer import (List, StringLiteral, ast)
        strings = []
        lines = code.split("\n")

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Determine context
                context = self._determine_string_context(node, tree, lines)
                strings.append(StringLiteral(
                    value=node.value,
                    line=node.lineno,
                    column=getattr(node, 'col_offset', None),
                    is_fstring=False,
                    context=context,
                ))
            elif isinstance(node, ast.JoinedStr):  # f-string
                # Reconstruct f-string value
                parts = []
                for value in node.values:
                    if isinstance(value, ast.Constant):
                        parts.append(str(value.value))
                    elif isinstance(value, ast.FormattedValue):
                        parts.append("{...}")

                strings.append(StringLiteral(
                    value="".join(parts),
                    line=node.lineno,
                    column=getattr(node, 'col_offset', None),
                    is_fstring=True,
                    context=self._determine_string_context(node, tree, lines),
                ))

        return strings


    def _determine_string_context(
        self, node: ast.AST, tree: ast.AST, lines: List[str]
    ) -> Optional[str]:
        """Determine the context of a string (SQL, command, path, etc.)."""
        from fi.evals.metrics.code_security.analyzer import (List, Optional, ast)
        line_content = lines[node.lineno - 1].lower() if node.lineno <= len(lines) else ""

        # Check for SQL keywords
        sql_keywords = ["select", "insert", "update", "delete", "drop", "create", "alter"]
        if any(kw in line_content for kw in sql_keywords):
            return "sql_query"

        # Check for file path indicators
        if any(p in line_content for p in ["open(", "file(", "path", "filename"]):
            return "file_path"

        # Check for command execution
        if any(c in line_content for c in ["os.system", "subprocess", "popen", "exec"]):
            return "command"

        # Check for URL
        if any(u in line_content for u in ["http://", "https://", "url", "requests"]):
            return "url"

        return None


    def _extract_variables(self, tree: ast.AST) -> Dict[str, List[int]]:
        """Extract variable assignments."""
        from fi.evals.metrics.code_security.analyzer import (Dict, List, ast)
        variables: Dict[str, List[int]] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id not in variables:
                            variables[target.id] = []
                        variables[target.id].append(node.lineno)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                name = node.target.id
                if name not in variables:
                    variables[name] = []
                variables[name].append(node.lineno)

        return variables


    def _find_dangerous_calls_ast(self, tree: ast.AST) -> List[Tuple[str, int]]:
        """Find dangerous function calls using AST."""
        from fi.evals.metrics.code_security.analyzer import (List, Tuple, ast)
        calls = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name:
                    # Check if it's in our dangerous list
                    for dangerous in self.DANGEROUS_FUNCTIONS:
                        if call_name == dangerous or call_name.endswith(f".{dangerous}"):
                            calls.append((call_name, node.lineno))
                            break
                        # Also check if the last part matches
                        if "." in dangerous:
                            _, func_name = dangerous.rsplit(".", 1)
                            if call_name.endswith(func_name):
                                calls.append((call_name, node.lineno))
                                break

        return calls


    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Get the full name of a function call."""
        from fi.evals.metrics.code_security.analyzer import (Optional, ast)
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return self._get_full_name(node.func)
        return None


    def _get_full_name(self, node: ast.Attribute) -> str:
        """Get full dotted name from Attribute node."""
        from fi.evals.metrics.code_security.analyzer import (ast)
        parts = []
        current = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)

        return ".".join(reversed(parts))


    def _extract_functions_regex(self, code: str) -> List[FunctionInfo]:
        """Fallback regex-based function extraction."""
        from fi.evals.metrics.code_security.analyzer import (FunctionInfo, List, re)
        functions = []
        pattern = r"^\s*(async\s+)?def\s+(\w+)\s*\((.*?)\)"

        for i, line in enumerate(code.split("\n"), 1):
            match = re.match(pattern, line)
            if match:
                is_async = bool(match.group(1))
                name = match.group(2)
                args_str = match.group(3)
                args = [a.strip().split(":")[0].split("=")[0].strip()
                        for a in args_str.split(",") if a.strip()]

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

        return functions
