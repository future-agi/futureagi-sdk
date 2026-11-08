"""LeaderboardReport to markdown operations."""
from __future__ import annotations


class _LeaderboardReportToMarkdownMethods:
    __slots__ = ()

    def to_markdown(self) -> str:
        """Export report as Markdown."""
        lines = [
            "# AI Code Security Leaderboard",
            "",
            f"*Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*Models: {self.total_models} | Tests: {self.total_tests}*",
            "",
            "## Overall Rankings",
            "",
            "| Rank | Model | func@k | sec@k | func-sec@k |",
            "|------|-------|--------|-------|------------|",
        ]

        for i, model in enumerate(self.overall_ranking, 1):
            scores = self.model_scores[model]
            lines.append(
                f"| {i} | {model} | "
                f"{scores.get('func_at_k', 0):.1%} | "
                f"{scores.get('sec_at_k', 0):.1%} | "
                f"{scores.get('func_sec_at_k', 0):.1%} |"
            )

        lines.extend([
            "",
            "## Key Metrics Comparison",
            "",
            "### Functional Correctness (func@k)",
            "",
        ])
        for i, model in enumerate(self.func_ranking, 1):
            lines.append(
                f"{i}. **{model}**: {self.model_scores[model].get('func_at_k', 0):.1%}"
            )

        lines.extend([
            "",
            "### Security (sec@k)",
            "",
        ])
        for i, model in enumerate(self.sec_ranking, 1):
            lines.append(
                f"{i}. **{model}**: {self.model_scores[model].get('sec_at_k', 0):.1%}"
            )

        if self.cwe_comparison:
            lines.extend([
                "",
                "## CWE Breakdown (Top 5)",
                "",
                "| CWE | Best Model | Avg Score |",
                "|-----|------------|-----------|",
            ])
            for cwe in self.cwe_comparison[:5]:
                lines.append(
                    f"| {cwe.cwe_id} | {cwe.best_model} | {cwe.average_score:.1%} |"
                )

        if self.recommendations:
            lines.extend([
                "",
                "## Recommendations",
                "",
            ])
            for use_case, model in self.recommendations.items():
                lines.append(f"- **{use_case}**: {model}")

        return "\n".join(lines)


    def to_json(self) -> str:
        """Export report as JSON."""
        from fi.evals.metrics.code_security.reports.leaderboard import (json)
        data = {
            "generated_at": self.generated_at.isoformat(),
            "total_models": self.total_models,
            "total_tests": self.total_tests,
            "rankings": {
                "overall": self.overall_ranking,
                "functional": self.func_ranking,
                "security": self.sec_ranking,
            },
            "model_scores": self.model_scores,
            "cwe_comparison": [
                {
                    "cwe_id": c.cwe_id,
                    "model_scores": c.model_scores,
                    "best_model": c.best_model,
                    "average_score": c.average_score,
                }
                for c in self.cwe_comparison
            ],
            "recommendations": self.recommendations,
        }
        return json.dumps(data, indent=2)


    def to_html(self) -> str:
        """Export report as HTML."""
        # Convert markdown to basic HTML
        md = self.to_markdown()
        html_lines = [
            "<!DOCTYPE html>",
            "<html><head>",
            "<title>AI Code Security Leaderboard</title>",
            "<style>",
            "body { font-family: -apple-system, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f4f4f4; }",
            ".rank-1 { background-color: #ffd700; }",
            ".rank-2 { background-color: #c0c0c0; }",
            ".rank-3 { background-color: #cd7f32; }",
            "</style>",
            "</head><body>",
        ]

        # Simple markdown to HTML conversion
        for line in md.split("\n"):
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("| "):
                # Table handling
                if "---" in line:
                    continue
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if cells[0] == "Rank":
                    html_lines.append("<table><thead><tr>")
                    for cell in cells:
                        html_lines.append(f"<th>{cell}</th>")
                    html_lines.append("</tr></thead><tbody>")
                else:
                    rank = cells[0] if cells else ""
                    rank_class = f"rank-{rank}" if rank in ["1", "2", "3"] else ""
                    html_lines.append(f'<tr class="{rank_class}">')
                    for cell in cells:
                        html_lines.append(f"<td>{cell}</td>")
                    html_lines.append("</tr>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith("*") and line.endswith("*"):
                html_lines.append(f"<p><em>{line[1:-1]}</em></p>")
            elif line.strip():
                html_lines.append(f"<p>{line}</p>")

        html_lines.append("</tbody></table></body></html>")
        return "\n".join(html_lines)
