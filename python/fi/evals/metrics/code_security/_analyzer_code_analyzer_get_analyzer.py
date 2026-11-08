"""CodeAnalyzer get analyzer operations."""
from __future__ import annotations

from typing import Dict
from fi.evals.metrics.code_security.analyzer import (
    AnalysisResult, LanguageAnalyzer, List, Optional,
)


class _CodeAnalyzerGetAnalyzerMethods:
    __slots__ = ()

    def get_analyzer(self, language: str) -> Optional[LanguageAnalyzer]:
        """Get or create an analyzer for the given language."""
        from fi.evals.metrics.code_security.analyzer import (LanguageAnalyzer, Optional)
        lang_lower = language.lower()
        if lang_lower not in self._analyzers:
            analyzer_cls = self.ANALYZERS.get(lang_lower)
            if analyzer_cls:
                self._analyzers[lang_lower] = analyzer_cls()
        return self._analyzers.get(lang_lower)


    def detect_language(self, code: str) -> str:
        """Auto-detect the programming language of code."""
        from fi.evals.metrics.code_security.analyzer import (re)
        scores: Dict[str, int] = {lang: 0 for lang in self.LANGUAGE_PATTERNS}

        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, code, re.MULTILINE):
                    scores[lang] += 1

        # Return language with highest score, default to python
        if max(scores.values()) == 0:
            return "python"

        return max(scores, key=lambda k: scores[k])


    def analyze(
        self, code: str, language: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze code for security evaluation.

        Args:
            code: Source code to analyze
            language: Programming language (auto-detected if not provided)

        Returns:
            AnalysisResult with functions, imports, strings, etc.
        """
        from fi.evals.metrics.code_security.analyzer import (AnalysisResult, Optional)
        # Detect language if not provided
        if language is None:
            language = self.detect_language(code)

        analyzer = self.get_analyzer(language)
        if analyzer is None:
            # Return basic analysis for unsupported languages
            return AnalysisResult(
                language=language,
                functions=[],
                imports=[],
                strings=[],
                variables={},
                dangerous_calls=[],
                parse_errors=[f"Unsupported language: {language}"],
                raw_ast=None,
            )

        return analyzer.analyze(code)


    def supports_language(self, language: str) -> bool:
        """Check if a language is supported."""
        return language.lower() in self.ANALYZERS


    def supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        from fi.evals.metrics.code_security.analyzer import (List)
        return list(set(
            analyzer_cls.language
            for analyzer_cls in self.ANALYZERS.values()
        ))
