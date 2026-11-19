"""
Code Analyzer for Security Evaluation.

Provides language-aware code analysis including:
- AST parsing (Python native, regex-based for others)
- Function/class extraction
- String literal extraction
- Import analysis
- Language detection
"""

import ast
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass


@dataclass
class FunctionInfo:
    """Information about a function definition."""
    name: str
    line: int
    end_line: Optional[int]
    args: List[str]
    decorators: List[str]
    is_async: bool
    docstring: Optional[str]
    calls: List[str]  # Functions called within this function


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    names: List[str]  # Specific names imported (empty for "import module")
    alias: Optional[str]
    line: int


@dataclass
class StringLiteral:
    """A string literal found in code."""
    value: str
    line: int
    column: Optional[int]
    is_fstring: bool
    context: Optional[str]  # e.g., "sql_query", "file_path", "command"


@dataclass
class AnalysisResult:
    """Result of code analysis."""
    language: str
    functions: List[FunctionInfo]
    imports: List[ImportInfo]
    strings: List[StringLiteral]
    variables: Dict[str, List[int]]  # Variable name -> lines where assigned
    dangerous_calls: List[Tuple[str, int]]  # (function_name, line)
    parse_errors: List[str]
    raw_ast: Optional[Any]  # Language-specific AST


class LanguageAnalyzer(ABC):
    """Base class for language-specific code analyzers."""

    language: str = "unknown"

    # Dangerous functions to track
    DANGEROUS_FUNCTIONS: List[str] = []

    @abstractmethod
    def parse(self, code: str) -> Optional[Any]:
        """Parse code into AST or structured representation."""
        pass

    @abstractmethod
    def analyze(self, code: str) -> AnalysisResult:
        """Perform full analysis of code."""
        pass

    def _find_dangerous_calls(
        self, code: str, functions: Optional[List[str]] = None
    ) -> List[Tuple[str, int]]:
        """Find calls to dangerous functions."""
        dangerous = functions or self.DANGEROUS_FUNCTIONS
        calls = []

        for i, line in enumerate(code.split("\n"), 1):
            for func in dangerous:
                # Handle both module.function and function patterns
                patterns = [
                    rf"\b{re.escape(func)}\s*\(",
                    rf"\b{func.split('.')[-1]}\s*\(" if "." in func else None,
                ]
                for pattern in patterns:
                    if pattern and re.search(pattern, line):
                        calls.append((func, i))
                        break

        return calls


from ._analyzer_python_analyzer_parse import _PythonAnalyzerParseMethods
from ._analyzer_python_analyzer_extract_imports_regex import _PythonAnalyzerExtractImportsRegexMethods

class PythonAnalyzer(
    _PythonAnalyzerParseMethods,
    _PythonAnalyzerExtractImportsRegexMethods,
    LanguageAnalyzer,
):
    """Python-specific code analyzer using the ast module."""

    language = "python"

    DANGEROUS_FUNCTIONS = [
        # Command execution
        "os.system", "os.popen", "os.spawn", "os.spawnl", "os.spawnle",
        "subprocess.call", "subprocess.run", "subprocess.Popen",
        "subprocess.check_output", "subprocess.check_call",
        "commands.getoutput", "commands.getstatusoutput",
        # Code execution
        "eval", "exec", "compile", "execfile",
        # Deserialization
        "pickle.loads", "pickle.load", "cPickle.loads", "cPickle.load",
        "yaml.load", "yaml.unsafe_load",
        "marshal.loads", "marshal.load",
        # SQL
        "cursor.execute", "connection.execute", "db.execute",
        "engine.execute", "session.execute",
        # File operations
        "open", "file",
        # Network
        "urllib.urlopen", "urllib2.urlopen", "requests.get", "requests.post",
        "httplib.HTTPConnection", "http.client.HTTPConnection",
        # Crypto (weak)
        "hashlib.md5", "hashlib.sha1",
        "Crypto.Cipher.DES", "Crypto.Cipher.ARC4",
        # Random (insecure)
        "random.random", "random.randint", "random.choice",
    ]


from ._analyzer_java_script_analyzer_parse import _JavaScriptAnalyzerParseMethods

class JavaScriptAnalyzer(_JavaScriptAnalyzerParseMethods, LanguageAnalyzer):
    """JavaScript/TypeScript analyzer using regex patterns."""

    language = "javascript"

    DANGEROUS_FUNCTIONS = [
        # Code execution
        "eval", "Function", "setTimeout", "setInterval",
        # Command execution
        "exec", "execSync", "spawn", "spawnSync", "execFile",
        "child_process.exec", "child_process.spawn",
        # DOM manipulation (XSS)
        "innerHTML", "outerHTML", "document.write", "document.writeln",
        # SQL (common ORMs)
        "query", "raw", "execute",
        # Deserialization
        "JSON.parse",
    ]


from ._analyzer_java_analyzer_parse import _JavaAnalyzerParseMethods

class JavaAnalyzer(_JavaAnalyzerParseMethods, LanguageAnalyzer):
    """Java analyzer using regex patterns."""

    language = "java"

    DANGEROUS_FUNCTIONS = [
        # Command execution
        "Runtime.exec", "ProcessBuilder",
        # SQL
        "executeQuery", "executeUpdate", "prepareStatement",
        "createStatement", "Statement.execute",
        # Deserialization
        "ObjectInputStream.readObject", "XMLDecoder.readObject",
        # File operations
        "FileInputStream", "FileOutputStream", "FileReader", "FileWriter",
        # Crypto (weak)
        "MessageDigest.getInstance",
    ]


from ._analyzer_go_analyzer_parse import _GoAnalyzerParseMethods

class GoAnalyzer(_GoAnalyzerParseMethods, LanguageAnalyzer):
    """Go analyzer using regex patterns."""

    language = "go"

    DANGEROUS_FUNCTIONS = [
        # Command execution
        "exec.Command", "os/exec.Command",
        # SQL
        "db.Query", "db.Exec", "db.QueryRow",
        # File operations
        "os.Open", "os.Create", "ioutil.ReadFile", "ioutil.WriteFile",
        # Crypto (weak)
        "md5.New", "sha1.New",
    ]


from ._analyzer_code_analyzer_get_analyzer import _CodeAnalyzerGetAnalyzerMethods

class CodeAnalyzer(_CodeAnalyzerGetAnalyzerMethods):
    """
    Main code analyzer that delegates to language-specific analyzers.

    Usage:
        analyzer = CodeAnalyzer()
        result = analyzer.analyze(code, "python")

        # Auto-detect language
        result = analyzer.analyze(code)
    """

    ANALYZERS: Dict[str, type] = {
        "python": PythonAnalyzer,
        "py": PythonAnalyzer,
        "javascript": JavaScriptAnalyzer,
        "js": JavaScriptAnalyzer,
        "typescript": JavaScriptAnalyzer,
        "ts": JavaScriptAnalyzer,
        "java": JavaAnalyzer,
        "go": GoAnalyzer,
        "golang": GoAnalyzer,
    }

    # Language detection patterns
    LANGUAGE_PATTERNS: Dict[str, List[str]] = {
        "python": [
            r"^\s*def\s+\w+\s*\(",
            r"^\s*import\s+\w+",
            r"^\s*from\s+\w+\s+import",
            r"^\s*class\s+\w+.*:",
            r"^\s*if\s+__name__\s*==",
            r"print\s*\(",
        ],
        "javascript": [
            r"^\s*const\s+\w+\s*=",
            r"^\s*let\s+\w+\s*=",
            r"^\s*function\s+\w+\s*\(",
            r"=>\s*{",
            r"require\s*\(",
            r"module\.exports",
            r"console\.log",
        ],
        "java": [
            r"^\s*public\s+class",
            r"^\s*private\s+\w+",
            r"^\s*import\s+java\.",
            r"System\.out\.println",
            r"public\s+static\s+void\s+main",
        ],
        "go": [
            r"^\s*package\s+\w+",
            r"^\s*func\s+\w+\s*\(",
            r"^\s*import\s+\(",
            r"fmt\.Print",
            r":=",
        ],
    }

    def __init__(self):
        self._analyzers: Dict[str, LanguageAnalyzer] = {}
