"""The public ``fi.evals`` surface matches ai-evaluation 1.1.0, name for name.

``fi/evals/__init__.py`` wraps the cloud imports in ``try``/``except`` and sets ``Evaluator = None``
when they fail, so ``from fi.evals import Evaluator`` alone would pass on a broken port. These tests
check the flags and the exported names against the 1.1.0 recording, and import every name the
published docs and site use.
"""

from __future__ import annotations

import importlib

import fi.evals
from tests.evals._golden import census, golden


def test_the_cloud_clients_loaded() -> None:
    assert fi.evals._evaluator_available is True
    assert fi.evals.Evaluator is not None
    for name in ("EvalTemplateManager", "Protect", "protect", "list_evaluations", "Execution", "evaluate"):
        assert getattr(fi.evals, name) is not None, name


def test_flags_and_exports_match_1_1_0() -> None:
    surface = golden()["surface"]
    assert fi.evals._evaluator_available == surface["evaluator_available"]
    assert fi.evals._framework_available == surface["framework_available"]
    assert sorted(fi.evals.evaluation_template_names) == surface["template_names"]
    assert len(surface["template_names"]) > 0
    assert sorted(fi.evals.__all__) == surface["all"]


def test_every_documented_name_that_imports_in_1_1_0_imports_here() -> None:
    upstream = golden()["census"]
    assert set(upstream) == set(census()["symbols"]), "the golden file was recorded for another census"
    failures = {}
    for key, outcome in upstream.items():
        if not outcome["ok"]:
            continue
        module, _, name = key.partition(":")
        try:
            mod = importlib.import_module(module)
            if name != "*":
                getattr(mod, name)
        except Exception as exc:  # noqa: BLE001 - every failure is reported together
            failures[key] = f"{type(exc).__name__}: {exc}"
    assert failures == {}


def test_documented_names_that_fail_in_1_1_0_fail_the_same_way_here() -> None:
    """A name the docs import that ai-evaluation 1.1.0 itself cannot import is a docs error, listed
    for the docs sweep; it must fail here with the same error class, so the port neither hides nor
    adds anything the published package did not have."""
    upstream = golden()["census"]
    different = {}
    for key, outcome in upstream.items():
        if outcome["ok"]:
            continue
        module, _, name = key.partition(":")
        try:
            getattr(importlib.import_module(module), name)
            mine = "imports"
        except Exception as exc:  # noqa: BLE001
            mine = type(exc).__name__
        if mine != outcome["error"].split(":", 1)[0]:
            different[key] = (outcome["error"], mine)
    assert different == {}
