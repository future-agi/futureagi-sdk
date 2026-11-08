"""Compatibility errors preserve SDK exports without loading agent-learning-kit.

The SDK owns fi.* except fi.alk. Retired namespaces receive guidance only when
no installed provider can resolve them.
These tests use the evals suite's existing no-egress guard and dependencies.
"""

import builtins
from collections import Counter
import importlib
from importlib.abc import MetaPathFinder
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from fi._alk_moved import ALK_DISTRIBUTION, ALK_LAST_FI_LAYOUT_VERSION

DIST = f"{ALK_DISTRIBUTION} {ALK_LAST_FI_LAYOUT_VERSION}"
FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "alk-compat-2213.json").read_text()
)
TARGET_NAMESPACES = {
    "fi.simulate": "fi.alk.simulate",
    "fi.opt": "fi.alk.optimize",
}
NAME_MODULES = ("fi.evals.metrics", "fi.evals.metrics.agents")


def _namespace_message(namespace):
    target = TARGET_NAMESPACES[namespace]
    return (
        f"{namespace} belonged to {DIST} and moved to the separate fi.alk package. "
        f"Use {target} instead of {namespace}; {namespace}.X -> {target}.X. "
        "Underscore-prefixed (private) modules have no public replacement. "
        f"Install {ALK_DISTRIBUTION} and import from fi.alk."
    )


def _is_alk_module(name):
    return name in {"alk", "fi.alk"} or name.startswith(("alk.", "fi.alk."))


# Attempt lists of the guards currently active (innermost last). A module first imported inside
# one test may keep a reference to that test's wrapper; such a wrapper reports to whichever guard
# is active when it is called, and does nothing when none is.
_ACTIVE_GUARDS = []


@pytest.fixture(autouse=True)
def _forbid_alk_imports(monkeypatch):
    """Catch old/new-root imports even if cached or their errors are swallowed."""
    attempts = []
    before = {name for name in sys.modules if _is_alk_module(name)}
    original_import = builtins.__import__
    original_import_module = importlib.import_module

    def reject(name):
        if _ACTIVE_GUARDS and _is_alk_module(name):
            _ACTIVE_GUARDS[-1].append(name)
            raise AssertionError(f"SDK compatibility errors must not import {name}")

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        absolute_name = name
        if level and globals and globals.get("__package__"):
            absolute_name = importlib.util.resolve_name("." * level + name, globals["__package__"])
        reject(absolute_name)
        for member in fromlist or ():
            reject(f"{absolute_name}.{member}")
        return original_import(name, globals, locals, fromlist, level)

    def guarded_import_module(name, package=None):
        reject(importlib.util.resolve_name(name, package) if name.startswith(".") else name)
        return original_import_module(name, package)

    class NoAlkFinder(MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            reject(fullname)
            return None

    # Insert into the interpreter's own list; finders that dependencies add meanwhile must stay.
    finder = NoAlkFinder()
    sys.meta_path.insert(0, finder)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(importlib, "import_module", guarded_import_module)
    _ACTIVE_GUARDS.append(attempts)
    try:
        yield
    finally:
        # Remove by identity: equal (e.g. empty) ledgers of nested guards must not be confused.
        for index in range(len(_ACTIVE_GUARDS) - 1, -1, -1):
            if _ACTIVE_GUARDS[index] is attempts:
                del _ACTIVE_GUARDS[index]
                break
        for index in range(len(sys.meta_path) - 1, -1, -1):
            if sys.meta_path[index] is finder:
                del sys.meta_path[index]
                break
    assert attempts == []
    after = {name for name in sys.modules if _is_alk_module(name)}
    assert after == before


_INTERPRETER_META_PATH = sys.meta_path


def test_the_guard_keeps_the_interpreter_meta_path_list():
    """The guard must add its finder to the interpreter's own ``sys.meta_path`` list.

    Swapping in a new list loses every finder a dependency installs during the test. The
    importlib_metadata backport appends one on first import and disables the stdlib
    PathFinder's distribution lookup, so after teardown no distribution could be found.
    """
    assert sys.meta_path is _INTERPRETER_META_PATH
    assert type(sys.meta_path[0]).__name__ == "NoAlkFinder"


def test_fixture_has_only_the_approved_frozen_scope_and_separate_gaps():
    assert FIXTURE["join_sha256"] == (
        "28bdda9c84a5313ec677f45883a40aa47f852b728b1b054f6e873bfa6e8af971"
    )
    rows = FIXTURE["stub_modules"]
    assert Counter(row["namespace"] for row in rows) == {
        "fi.simulate": 118, "fi.opt": 44,
    }
    assert len({row["module"] for row in rows}) == 162
    assert sum(row["error_target"] is None for row in rows) == 3
    owned = FIXTURE["alk_owned_modules"]
    assert Counter(row["namespace"] for row in owned) == {"fi.alk": 252}
    assert all(row["module"] == "fi.alk" or row["module"].startswith("fi.alk.") for row in owned)
    assert all(row["error_target"] in (None, row["module"]) for row in owned)
    assert len({row["module"] for row in rows + owned}) == 414
    assert sum(row["error_target"] is None for row in rows + owned) == 60
    assert Counter(row["module"] for row in FIXTURE["fi_evals_names"]) == {
        "fi.evals.metrics": 7, "fi.evals.metrics.agents": 14,
    }
    assert len({(row["module"], row["name"]) for row in FIXTURE["fi_evals_names"]}) == 21
    assert FIXTURE["fi_evals_modules"] == [{
        "module": "fi.evals.metrics.agents.report",
        "alk_target": "fi.alk.evals.metrics.agents.report",
    }]
    assert FIXTURE["pending_reconcile"] == []
    assert FIXTURE["simulate_reconciliation"]["sha256"] == (
        "aacbb1511c62996b6c458f5792feabf3f42f15f795ae18b2dd13092545a2e46b"
    )


def test_sdk_ships_no_fi_alk_source_or_package_data():
    python = Path(__file__).resolve().parents[2]
    assert not (python / "fi" / "alk").exists()
    project = (python / "pyproject.toml").read_text()
    exclusions = project.split("exclude = [", 1)[1].split("]", 1)[0]
    assert '"fi/alk"' in exclusions
    assert "prune fi/alk" in (python / "MANIFEST.in").read_text().splitlines()


@pytest.mark.parametrize("row", FIXTURE["stub_modules"], ids=lambda row: row["module"])
def test_every_frozen_module_raises_its_fixed_namespace_error(row):
    namespace = row["namespace"]
    with pytest.raises(ImportError) as caught:
        importlib.import_module(row["module"])
    assert type(caught.value) is ImportError
    message = str(caught.value)
    assert message == _namespace_message(namespace)
    target_namespace = TARGET_NAMESPACES[namespace]
    assert f"{namespace}.X -> {target_namespace}.X" in message
    assert f"Use {target_namespace} instead of {namespace}" in message
    if row["error_target"] is not None:
        # The frozen historical fixture predates the optimizer target correction.
        recorded_namespace = "fi.alk.opt" if namespace == "fi.opt" else target_namespace
        assert row["error_target"] == recorded_namespace + row["module"][len(namespace):]
    private = any(part.startswith("_") for part in row["module"].split("."))
    if row["error_target"] is None:
        assert private
    if private:
        assert "Underscore-prefixed (private) modules have no public replacement" in message
    assert namespace not in sys.modules
    assert row["module"] not in sys.modules


@pytest.mark.parametrize("namespace", TARGET_NAMESPACES)
def test_from_fi_import_preserves_the_namespace_error(namespace):
    with pytest.raises(ImportError) as caught:
        exec(f"from fi import {namespace.rsplit('.', 1)[1]}", {})
    assert type(caught.value) is ImportError
    assert str(caught.value) == _namespace_message(namespace)


@pytest.mark.parametrize("row", FIXTURE["fi_evals_modules"], ids=lambda row: row["module"])
@pytest.mark.parametrize("access", ["module", "from_import"])
def test_report_module_points_to_its_alk_replacement(row, access):
    with pytest.raises(ImportError) as caught:
        if access == "module":
            importlib.import_module(row["module"])
        else:
            parent, name = row["module"].rsplit(".", 1)
            exec(f"from {parent} import {name}", {})
    assert type(caught.value) is ImportError
    assert str(caught.value) == (
        f"{row['module']} belonged to {DIST} "
        f"and moved to the separate fi.alk package. Install {ALK_DISTRIBUTION} "
        f"and import {row['alk_target']} instead."
    )
    assert row["module"] not in sys.modules


@pytest.mark.parametrize(
    "row", FIXTURE["fi_evals_names"], ids=lambda row: f"{row['module']}.{row['name']}"
)
@pytest.mark.parametrize("access", ["attribute", "from_import"])
def test_only_listed_names_raise_with_the_exact_replacement_import(row, access):
    module = importlib.import_module(row["module"])
    name = row["name"]
    assert name not in module.__all__
    assert name not in dir(module)
    with pytest.raises(ImportError) as caught:
        if access == "attribute":
            getattr(module, name)
        else:
            exec(f"from {row['module']} import {name}", {})
    assert type(caught.value) is ImportError
    assert str(caught.value) == (
        f"{row['module']}.{name} belonged to {DIST} and moved "
        f"to the separate fi.alk package. Install {ALK_DISTRIBUTION} and use "
        f"`{row['replacement_import']}` instead. fi.evals keeps the futureagi SDK API."
    )
    assert name not in vars(module)
    assert name not in dir(module)


@pytest.mark.parametrize("module_name", NAME_MODULES)
@pytest.mark.parametrize("name", ["unlisted_for_rl2213", "agentreportcaseresult", "_AgentReportEvaluator"])
def test_unlisted_missing_names_keep_normal_attribute_errors(module_name, name):
    module = importlib.import_module(module_name)
    with pytest.raises(AttributeError) as caught:
        getattr(module, name)
    assert type(caught.value) is AttributeError
    assert str(caught.value) == f"module {module_name!r} has no attribute {name!r}"


@pytest.mark.parametrize("module_name,required", [
    ("fi.evals", ("evaluate", "EvalResult", "BatchResult", "Turing", "Execution", "StreamingEvaluator")),
    ("fi.evals.metrics", ("AggregatedMetric", "IsJson", "BLEUScore", "Regex", "CustomLLMJudge")),
    ("fi.evals.metrics.agents", ("AgentTrajectoryInput", "AgentStep", "TaskCompletion", "ReasoningQuality")),
])
def test_sdk_packages_and_existing_exports_still_resolve(module_name, required):
    module = importlib.import_module(module_name)
    assert set(required) <= set(module.__all__)
    exported = {}
    exec(f"from {module_name} import *", exported)
    for name in module.__all__:
        assert exported[name] is getattr(module, name)
    for name in required:
        assert exported[name] is not None
    for row in FIXTURE["fi_evals_names"]:
        if row["module"] == module_name:
            assert row["name"] not in exported
            assert row["name"] not in dir(module)
