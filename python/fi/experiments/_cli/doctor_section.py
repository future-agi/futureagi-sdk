"""``futureagi-py doctor``'s experiments section: the extra, each tracing add-on, the judge, an optional TARGET and
``--dataset``, the server's routes and ``OPENAI_BASE_URL``. Split out of ``run.py`` (the 400-line module rule).

Tracing add-ons: each installed traceAI instrumentor is imported and instrumented in a subprocess
(``_tracing/probe.py``). One that does both is "installed (imports, instruments)" ("installed (imports)" when only
the import could be tried); one that fails either step is a doctor problem (exit 3), reported as BROKEN with its
error, both installed versions and the fix, never as "installed". A broken add-on is skipped by
``instrument='auto'`` runs (they say so), and refused when ``--instrument`` / ``instrument=[...]`` names it.
"""

from __future__ import annotations

import importlib.util
import os
from typing import Any

from fi.experiments._cli.targets import discover, load_object, parse_target


def _have(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def instrument_lines() -> list[str]:
    """One line per known instrumentor: not installed, installed (it imports), or BROKEN (a doctor problem)."""
    from fi._cli.doctor import Problem
    from fi.experiments._tracing.instrument import INSTRUMENTORS, versions_and_fix
    from fi.experiments._tracing.probe import probe_imports

    installed = {name: (module, cls) for name, (module, cls, _) in INSTRUMENTORS.items() if _have(module)}
    probes = probe_imports(installed) if installed else {}
    lines: list[str] = []
    for name, (_, _, pkg) in INSTRUMENTORS.items():
        probe = probes.get(name)
        if probe is None:
            lines.append(f"Instrument {pkg:<24} not installed")
        elif probe.ok:
            lines.append(f"Instrument {pkg:<24} installed (imports{', instruments' if probe.instrumented else ''})")
        else:
            versions, fix = versions_and_fix(name)
            what = (f"installed and it imports, but instrument() fails ({probe.error})" if probe.stage == "instrument"
                    else f"installed, but importing it fails ({probe.error})")
            lines.append(Problem(
                f"Instrument {pkg:<24} BROKEN: {what}. Installed: "
                f"{versions}. To trace it, {fix}. Until then 'auto' runs go on without its spans and say so, and "
                f"--instrument / instrument=[...] naming {name!r} is refused"))
    return lines


def doctor_lines(args: Any) -> list[str]:
    from fi.experiments._tracing.instrument import python_supported

    lines = []
    otel = _have("opentelemetry.sdk") and _have("fi_instrumentation")
    missing_line = 'missing (pip install "futureagi[experiments]")'
    lines.append("Extra      experiments: " + ("installed" if otel else missing_line))
    if not python_supported():
        lines.append("Tracing    Python 3.14+: tracing refuses until TA-1; use --no-trace")
    lines += instrument_lines()
    judge = getattr(args, "judge_model", None) or os.environ.get("FI_JUDGE_MODEL")
    unset = "not set (LLM-judge templates need --judge-model or FI_JUDGE_MODEL; judge() defaults to gpt-4.1-mini)"
    # the value is for the LLM-judge templates only; judge() takes its own model= (L-SDK2c review, nit)
    lines.append(f"Judge      {judge} (for LLM-judge templates; judge() takes its own model=, default gpt-4.1-mini)"
                 if judge else f"Judge      {unset}")
    text = getattr(args, "target", None)
    if text:
        from fi.experiments.adapters import resolve_task

        target = parse_target(text)
        if target.kind == "object":
            runner = resolve_task(load_object(target))
            lines.append(f"Target     {text}: {runner.describe()}")
        else:
            from fi.experiments._cli import file_mode

            paths = [target.path] if target.kind == "file" else discover(target.path)  # type: ignore[list-item]
            for d in file_mode.collect(paths):
                runner = resolve_task(d.kwargs.get("task"))
                lines.append(f"Run        {d.name}: {runner.describe()}")
    if getattr(args, "dataset", None):
        from fi.experiments._dataset import is_local_source, load_local

        if is_local_source(args.dataset):
            ds = load_local(args.dataset)
            lines.append(f"Dataset    {args.dataset}: {len(ds.rows)} rows · {ds.roles.describe()}")
        else:
            lines.append(f"Dataset    {args.dataset}: a server dataset (pinned to a version when the run starts)")
    from fi.experiments._cli.routes import doctor_route_lines, openai_base_url_lines

    lines += doctor_route_lines(args)
    return lines + openai_base_url_lines(args)
