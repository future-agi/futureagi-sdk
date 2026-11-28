"""Non-evals-extra import isolation and value-free local-evaluation errors."""

from __future__ import annotations

from importlib import metadata
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

try:
    import tomllib
except ModuleNotFoundError:  # pytest supplies tomli on Python 3.10.
    import tomli as tomllib


def _evals_only_distributions():
    """Subtract the base and other extras, including their transitive dependencies."""
    project = Path(__file__).resolve().parents[2] / "pyproject.toml"
    with project.open("rb") as source:
        poetry = tomllib.load(source)["tool"]["poetry"]
    dependencies = poetry["dependencies"]
    extras = poetry["extras"]
    base = {
        name for name, spec in dependencies.items()
        if name != "python" and not (isinstance(spec, dict) and spec.get("optional", False))
    }
    other = {name for extra, names in extras.items() if extra != "evals" for name in names}
    pending = []
    for name in base | other:
        spec = dependencies[name]
        requested = spec.get("extras", []) if isinstance(spec, dict) else []
        pending.extend((canonicalize_name(name), extra) for extra in {"", *requested})
    visited = set()
    while pending:
        name, extra = pending.pop()
        if (name, extra) in visited:
            continue
        visited.add((name, extra))
        try:
            installed = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            pytest.fail("Import sweep requires base plus every non-evals extra; missing " + name)
        for value in installed.requires or ():
            requirement = Requirement(value)
            if requirement.marker and not requirement.marker.evaluate({"extra": extra}):
                continue
            pending.extend((canonicalize_name(requirement.name), requested)
                           for requested in {"", *requirement.extras})
    non_evals = {name for name, _ in visited}
    evals_only = {canonicalize_name(name) for name in extras["evals"]} - non_evals
    assert {canonicalize_name(name) for name in ("rouge_score", "litellm", "nltk")} <= evals_only
    # Instrumentation extras supply these transitively, so exclude them from the block list.
    assert {"openai", "opentelemetry-api", "opentelemetry-sdk"} <= non_evals
    return evals_only


_PRELUDE = r'''
import importlib, importlib.abc, importlib.util, json, socket, sys
from pathlib import Path
from types import SimpleNamespace

EXTRA = {"jinja2", "litellm", "nltk", "openai", "opentelemetry", "yaml",
         "rouge_score", "filelock"}
CLOUD = ("Evaluator", "evaluate", "Protect", "Execution", "EvalTemplateManager",
         "list_evaluations")
MESSAGE = ('Local metrics and LLM judges require Python 3.11+ and futureagi[evals]. '
           'On Python 3.11+, install with: pip install "futureagi[evals]".')
blocked = set()
attempts = []

def refuse(*args, **kwargs):
    raise AssertionError("network is forbidden in the dependency contract")

socket.socket.connect = refuse
socket.getaddrinfo = refuse

class WithoutDependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        root = fullname.split(".")[0]
        if root in blocked:
            attempts.append(root)
            raise ModuleNotFoundError("optional dependency is unavailable", name=fullname)
        return None

sys.meta_path.insert(0, WithoutDependencies())
'''


def _run(tmp_path, body, *args):
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path),
           "FI_BASE_URL": "http://127.0.0.1:9",
           "FI_LOGIN_FILE": str(tmp_path / "no-login.json"),
           "LITELLM_LOCAL_MODEL_COST_MAP": "True"}
    result = subprocess.run([sys.executable, "-I", "-c", _PRELUDE + body, *args],
                            cwd=tmp_path, env=env, capture_output=True,
                            text=True, timeout=300)
    assert result.returncode == 0, result.stderr[-4000:]
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("module", [
    "fi.evals.local", "fi.evals.local.evaluator", "fi.evals.local.llm",
    "fi.evals.metrics", "fi.evals.metrics.heuristics.similarity_metrics",
    "fi.evals.metrics.llm_as_judges", "fi.evals.llm",
    "fi.evals.llm.providers.litellm",
])
def test_python310_local_imports_name_python_and_extra_before_dependencies(tmp_path, module):
    result = _run(tmp_path, r'''
blocked.update(EXTRA)
import fi.evals
assert importlib.util.find_spec("fi.evals._extras") is not None, "evals must provide the Python guard"
from fi.evals import _extras
# Patch only the guard's clock, not sys.version_info used by third-party packages.
_extras.sys = SimpleNamespace(version_info=(3, 10, 19, "final", 0))
assert all(getattr(fi.evals, name) is not None for name in CLOUD)
attempts.clear()
try:
    importlib.import_module(sys.argv[1])
except ImportError as exc:
    assert str(exc) == MESSAGE
else:
    raise AssertionError("local evaluation imported on Python 3.10")
assert attempts == [], attempts
print(json.dumps({"message": MESSAGE, "cloud": True}))
''', module)
    assert result["cloud"] is True
    assert "Python 3.11+" in result["message"]
    assert "futureagi[evals]" in result["message"]


def test_cloud_names_import_without_attempting_rouge_or_litellm(tmp_path):
    result = _run(tmp_path, r'''
blocked.update(EXTRA)
import fi.evals
assert "rouge_score" not in attempts
assert "litellm" not in attempts
assert not any(name.split(".")[0] in {"rouge_score", "litellm"} for name in sys.modules)
print(json.dumps({name: getattr(fi.evals, name) is not None for name in CLOUD}))
''')
    assert result and all(result.values()), result


def _evals_only_import_roots():
    """The import roots of the evals-only distributions, which the subprocess blocks."""
    evals_only = _evals_only_distributions()
    import_roots = {
        "jinja2": {"jinja2"}, "litellm": {"litellm"}, "nltk": {"nltk"},
        "pyyaml": {"yaml"}, "rouge-score": {"rouge_score"}, "filelock": {"filelock"},
        # This is a dependency-only metapackage, not the shared opentelemetry namespace.
        "opentelemetry-exporter-otlp": set(),
    }
    assert evals_only <= import_roots.keys(), "Map any new evals-only distribution's imports"
    blocked_modules = set().union(*(import_roots[name] for name in evals_only))
    assert {"rouge_score", "litellm", "nltk"} <= blocked_modules
    return blocked_modules


def test_every_shipped_non_evals_module_imports_without_evals_dependencies(tmp_path):
    # Install base plus all non-evals extras. Evals may also be installed in the
    # test lane: the subprocess makes its exclusive imports unavailable anyway.
    blocked_modules = _evals_only_import_roots()
    result = _run(tmp_path, r'''
blocked.update(json.loads(sys.argv[1]))
import fi
root = Path(fi.__file__).resolve().parent
# Clear-error namespaces deliberately cannot import. Evals cloud exports have their
# own assertion below; optional local evaluation packages are not a base surface.
excluded = {"evals", "opt", "simulate"}
modules = set()
for path in root.rglob("*.py"):
    relative = path.relative_to(root)
    parts = relative.with_suffix("").parts
    if parts[0] in excluded:
        continue
    # No extra can install this integration's dependency; see the note in python/pyproject.toml.
    if parts[:2] == ("sandbox_integrations", "openai_agents"):
        continue
    # Archive exclusions from pyproject.toml, also applicable to editable installs.
    if relative.parts[0] == "alk" or relative.parts[0] in {"deployments", "deployments.py"}:
        continue
    if relative.parts[:2] == ("integrations", "otel") or "__pycache__" in relative.parts:
        continue
    if parts[-1] == "__init__":
        parts = parts[:-1]
    modules.add(".".join(("fi", *parts)))
assert modules and "fi" in modules
assert any(name.startswith("fi.experiments._tracing.") for name in modules)
imported, failed = [], {}
for name in sorted(modules):
    try:
        importlib.import_module(name)
        imported.append(name)
    except Exception as exc:
        failed[name] = type(exc).__name__
import fi.evals
assert all(getattr(fi.evals, name) is not None for name in CLOUD)
assert not any(name.split(".")[0] in blocked for name in sys.modules)
print(json.dumps({"enumerated": sorted(modules), "imported": imported, "failed": failed,
                  "blocked": sorted(blocked)}))
''', json.dumps(sorted(blocked_modules)))
    assert result["failed"] == {}, result["failed"]
    assert result["imported"] == result["enumerated"]
    assert set(result["blocked"]) == blocked_modules


def test_openai_agents_sandbox_integration_raises_missing_extra_without_evals_dependencies(tmp_path):
    # The sweep above skips this package: no extra installs openai-agents 0.24 (it requires
    # openai>=3, the evals extra pins openai<3), so here its import must be a clear error.
    # Another distribution can also provide a top-level ``agents`` package, so the skip is tied to the
    # openai-agents distribution that owns it.
    owners = metadata.packages_distributions().get("agents", [])
    if "openai-agents" in owners and importlib.util.find_spec("agents.sandbox") is not None:
        # An installed Agents SDK that ships agents.sandbox (it comes with the openai-agents extra) lets the
        # integration import, so there is no missing-extra error to check.
        pytest.skip("agents.sandbox is installed with the Agents SDK")
    blocked_modules = _evals_only_import_roots()
    result = _run(tmp_path, r'''
blocked.update(json.loads(sys.argv[1]))
from fi.errors import MissingExtraError
try:
    importlib.import_module("fi.sandbox_integrations.openai_agents")
except MissingExtraError as exc:
    error = exc
else:
    raise AssertionError("fi.sandbox_integrations.openai_agents imported: agents.sandbox is installed")
assert isinstance(error.__cause__, ImportError), repr(error.__cause__)
# The failing import is the Agents SDK itself, not a blocked evals-only module it pulled in.
assert (error.__cause__.name or "").split(".")[0] == "agents", error.__cause__.name
assert "fi.sandbox_integrations.openai_agents" not in sys.modules
# The module that defines the install line loads before the failing import and stays loaded.
install_line = sys.modules["fi.sandbox_integrations.openai_agents._missing"].INSTALL_LINE
assert not any(name.split(".")[0] in blocked for name in sys.modules)
print(json.dumps({"install_hint": error.install_hint, "install_line": install_line,
                  "blocked": sorted(blocked)}))
''', json.dumps(sorted(blocked_modules)))
    assert result["install_line"] and result["install_hint"] == result["install_line"]
    assert set(result["blocked"]) == blocked_modules


def test_rouge_without_dependency_names_extra_and_python(tmp_path):
    # All other local-evaluation dependencies must be present to reach ROUGEScore.
    # Do not skip when only rouge_score is absent: that is the case under test.
    for name in ("jinja2", "nltk", "litellm", "openai"):
        if importlib.util.find_spec(name) is None:
            pytest.skip("futureagi[evals] is not installed: " + name)
    result = _run(tmp_path, r'''
blocked.add("rouge_score")
assert importlib.util.find_spec("fi.evals._extras") is not None, "evals must provide the Python guard"
from fi.evals import _extras
# Exercise the missing-dependency path independently of the interpreter guard.
_extras.sys = SimpleNamespace(version_info=(3, 11, 0, "final", 0))
from fi.evals.metrics import ROUGEScore
assert "rouge_score" not in attempts, "ROUGE must import its dependency lazily"
try:
    ROUGEScore()
except ModuleNotFoundError as exc:
    assert exc.name == "rouge_score"
    assert str(exc) == MESSAGE
    assert exc.__suppress_context__
else:
    raise AssertionError("ROUGE constructed without rouge_score")
assert "rouge_score" in attempts
print(json.dumps({"message": MESSAGE}))
''')
    assert "Python 3.11+" in result["message"]
    assert "futureagi[evals]" in result["message"]
