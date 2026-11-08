"""SecurityReport to markdown operations."""
from __future__ import annotations


class _SecurityReportToMarkdownMethods:
    __slots__ = ()

    def to_markdown(self) -> str:
        """Export report as Markdown."""
        lines = [
            f"# {self.title}",
            "",
            f"**Model:** {self.model_name}",
            f"**Language:** {self.language}",
            f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- **Overall Security Score:** {self.overall_score:.1%}",
            f"- **func@k:** {self.func_at_k:.1%}",
            f"- **sec@k:** {self.sec_at_k:.1%}",
            f"- **func-sec@k:** {self.func_sec_at_k:.1%}",
            "",
            f"- **Total Samples:** {self.total_samples}",
            f"- **Secure:** {self.secure_samples} ({self.secure_samples/self.total_samples:.1%})" if self.total_samples else "",
            f"- **Vulnerable:** {self.vulnerable_samples}",
            "",
            "## Vulnerability Summary",
            "",
            f"**Total Findings:** {self.total_findings}",
            "",
            "### By Severity",
            "",
        ]

        for severity, count in sorted(
            self.findings_by_severity.items(),
            key=lambda x: ["critical", "high", "medium", "low", "info"].index(x[0])
            if x[0] in ["critical", "high", "medium", "low", "info"]
            else 5,
        ):
            emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
                "info": "ℹ️",
            }.get(severity, "")
            lines.append(f"- {emoji} **{severity.upper()}:** {count}")

        lines.extend([
            "",
            "### By CWE",
            "",
        ])

        for cwe, count in sorted(
            self.findings_by_cwe.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]:  # Top 10
            lines.append(f"- **{cwe}:** {count}")

        if self.top_vulnerabilities:
            lines.extend([
                "",
                "## Top Vulnerabilities",
                "",
            ])
            for i, vuln in enumerate(self.top_vulnerabilities[:5], 1):
                lines.append(f"### {i}. {vuln.get('cwe_id', 'Unknown')} - {vuln.get('type', 'Unknown')}")
                lines.append(f"**Severity:** {vuln.get('severity', 'Unknown')}")
                if vuln.get('description'):
                    lines.append(f"**Description:** {vuln.get('description')}")
                if vuln.get('count'):
                    lines.append(f"**Occurrences:** {vuln.get('count')}")
                lines.append("")

        if self.improvements:
            lines.extend([
                "## Recommendations",
                "",
            ])
            for improvement in self.improvements:
                lines.append(f"- {improvement}")

        return "\n".join(lines)


    def to_json(self) -> str:
        """Export report as JSON."""
        from fi.evals.metrics.code_security.reports.generator import (json)
        return json.dumps({
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "model_name": self.model_name,
            "language": self.language,
            "summary": {
                "overall_score": self.overall_score,
                "func_at_k": self.func_at_k,
                "sec_at_k": self.sec_at_k,
                "func_sec_at_k": self.func_sec_at_k,
            },
            "samples": {
                "total": self.total_samples,
                "secure": self.secure_samples,
                "vulnerable": self.vulnerable_samples,
            },
            "findings": {
                "total": self.total_findings,
                "by_severity": self.findings_by_severity,
                "by_cwe": self.findings_by_cwe,
            },
            "top_vulnerabilities": self.top_vulnerabilities,
            "recommendations": self.improvements,
        }, indent=2)
