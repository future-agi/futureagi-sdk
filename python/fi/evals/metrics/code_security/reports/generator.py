"""
Security Report Generator.

Generates detailed security evaluation reports for individual models
or comparisons.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json

from ..benchmarks.types import BenchmarkResult, CWEBreakdown
from ..types import SecurityFinding, Severity


from ._generator_security_report_to_markdown import _SecurityReportToMarkdownMethods

@dataclass
class SecurityReport(_SecurityReportToMarkdownMethods):
    """Complete security evaluation report."""

    # Metadata
    title: str
    generated_at: datetime
    model_name: str
    language: str

    # Summary
    overall_score: float
    func_at_k: float
    sec_at_k: float
    func_sec_at_k: float

    # Details
    total_samples: int
    secure_samples: int
    vulnerable_samples: int

    # Findings
    total_findings: int
    findings_by_severity: Dict[str, int]
    findings_by_cwe: Dict[str, int]
    top_vulnerabilities: List[Dict[str, Any]]

    # Breakdown
    cwe_breakdown: List[CWEBreakdown]

    # Recommendations
    improvements: List[str]


from ._generator_report_generator_from_benchmark_result import _ReportGeneratorFromBenchmarkResultMethods

class ReportGenerator(_ReportGeneratorFromBenchmarkResultMethods):
    """
    Generate security evaluation reports.

    Usage:
        generator = ReportGenerator()

        # From benchmark result
        report = generator.from_benchmark_result(result, "gpt-4")

        # From raw findings
        report = generator.from_findings(findings, "claude-3")

        print(report.to_markdown())
    """


def generate_security_report(
    result: BenchmarkResult,
    model_name: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """
    Convenience function to generate a security report.

    Args:
        result: Benchmark result
        model_name: Optional model name override
        format: Output format (markdown, json)

    Returns:
        Formatted report string
    """
    generator = ReportGenerator()
    report = generator.from_benchmark_result(result, model_name)

    if format == "json":
        return report.to_json()
    else:
        return report.to_markdown()
