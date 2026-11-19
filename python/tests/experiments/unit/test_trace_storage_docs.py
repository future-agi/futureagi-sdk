"""Contract: the SDK's docs say where an uploaded run's traces are stored today, and nothing claims more.

The trace collector stores every project as an Observe project and ignores the resource's ``project_type`` and
``project_version_*`` (finding L-VM2c-3), so a run's traces are in an Observe project, joined to the run by run id.
These tests keep the docstrings saying so, and fail when a doc under ``fi/experiments`` claims an experiment-typed
project or a per-run project version again."""

import ast
import re
from pathlib import Path

import fi.experiments as experiments

PKG = Path(experiments.__file__).parent


def _docs(rel: str) -> dict[str, str]:
    """The module's docstring ("") and each top-level function's, read from the source: the tracing modules import
    OpenTelemetry, which Python 3.14 lacks until TA-1, and these checks are about the words only."""
    tree = ast.parse((PKG / rel).read_text(encoding="utf-8"))
    out = {"": ast.get_docstring(tree) or ""}
    out.update({n.name: ast.get_docstring(n) or "" for n in tree.body if isinstance(n, ast.FunctionDef)})
    return out


def test_the_tracing_docs_say_observe_project_joined_by_run_id():
    export, tracing_pkg, routing = _docs("_tracing/export.py"), _docs("_tracing/__init__.py"), _docs("_tracing/routing.py")
    for doc in (export[""], tracing_pkg[""], experiments.run.__doc__ or ""):
        assert "Observe project" in doc, doc
        assert "run id" in doc, doc
    assert "fi.experiment.run_id" in export[""] and "trace_id" in export[""]
    assert "project_type" in export[""] and "project_type" in export["run_resource"]
    assert "project_version_*" in export[""] and "project_version_*" in export["run_resource"]
    assert "register(..., set_global_tracer_provider=False)" not in routing[""]


_CLAIMS = (
    re.compile(r"project_type\s*=\s*EXPERIMENT"),  # rev2's register(..., project_type=EXPERIMENT, ...) sentence
    re.compile(r"(?<!no )experiment[- ]typed project", re.IGNORECASE),
    re.compile(r"project of (the )?type `?experiment", re.IGNORECASE),
    re.compile(r"(?<!no )(per-run |run-named )project version", re.IGNORECASE),
    # wider wordings of the same two claims (the patterns were narrow)
    re.compile(r"(?<!no )(?<!not an )(?<!not )\b(an|the|its|own) experiment project\b", re.IGNORECASE),
    re.compile(r"project_type\s*=\s*['\"]?experiment['\"]?\s*(project|is|means|makes)", re.IGNORECASE),
    re.compile(r"(?<!no )\bproject version (per|for each) run\b", re.IGNORECASE),
    re.compile(r"\bversion named (after|for) the run\b", re.IGNORECASE),
    re.compile(r"traces (are|go|land) (stored )?(in|to|into) (an |the )?experiment(?! run)", re.IGNORECASE),
)


def test_the_claim_patterns_catch_the_claims_and_pass_the_true_sentences():
    claims = ("the run's traces are stored in an experiment project", "Traces go to the experiment's project",
              "each run gets a project version per run", "a version named after the run",
              "register(project_type=EXPERIMENT, ...)", "an experiment-typed project")
    for text in claims:
        assert any(c.search(text) for c in _CLAIMS), text
    true = ("The traces are stored in the Observe project of that name, joined to the run by run id.",
            "There is no experiment-typed project.", "Runs get no per-run project version.",
            "traces of the experiment run are joined by run id")
    for text in true:
        assert not any(c.search(text) for c in _CLAIMS), text


def test_no_doc_under_fi_experiments_claims_an_experiment_typed_project():
    found = []
    for path in sorted(PKG.rglob("*")):
        if path.suffix not in (".py", ".md") or "__pycache__" in path.parts:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if any(c.search(line) for c in _CLAIMS):
                found.append(f"{path.relative_to(PKG)}:{n}: {line.strip()}")
    assert found == []
