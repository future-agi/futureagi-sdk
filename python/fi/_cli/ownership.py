"""Offline packaging diagnostics that remain usable after a legacy uninstall."""
from __future__ import annotations

from typing import Any

from fi._core.namespace_ownership import inspect_installed


def section(args: Any) -> list[str]:
    """Render ownership failures as doctor problems, never silently pass a failed scan."""
    from fi._cli.doctor import Problem

    try:
        result = inspect_installed()
    except Exception as exc:
        return [Problem(f"Ownership check failed ({type(exc).__name__}); automatic repair safety is unknown."),
                "Manual repair required: use the original installer to identify the affected owners "
                "and shared paths from complete, valid RECORD metadata. First back up or restore "
                "supported owners' files, then repair the diagnosed metadata, then re-run doctor. "
                "Do not uninstall or replace distributions while ownership is unknown.",
                "futureagi-py doctor --offline"]
    if result["status"] == "NOT-INSTALLED":
        return ["futureagi is not installed as a distribution; wheel ownership was not evaluated."]
    lines: list[str] = [f"Checked {result['checked_files']} futureagi files."]
    for name in result.get("editable_installs", []):
        lines.append(f"{name}: editable development install; source mapping validated, not wheel hash integrity.")
    for issue in result["issues"]:
        who = ", ".join(issue.get("distributions", [issue.get("distribution", "")]))
        lines.append(Problem(f"{issue['kind']}: {issue.get('path', who)}"
                             + (f" ({who})" if issue.get("path") else "")))
    if result["issues"]:
        lines.append("Repair steps in this order (complete manual steps before commands; "
                     "diagnosis only; no files were changed):")
        lines.extend(result["repair_commands"])
    else:
        lines.append("No namespace overlap, legacy distributions or damaged files found.")
    return lines
