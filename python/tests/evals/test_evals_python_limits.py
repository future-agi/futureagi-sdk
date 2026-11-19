"""[evals] dependencies with a Python upper bound fail with a typed, named error."""

import ast
import importlib
import json
import sys
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from fi.evals import _extras


def _clock(monkeypatch, version):
    # Patch only the guard's clock, not sys.version_info used by other packages.
    monkeypatch.setattr(_extras, "sys", SimpleNamespace(version_info=version))


@pytest.mark.parametrize("name, limit", sorted(_extras.PYTHON_LIMITS.items()))
def test_requirement_names_the_dependency_and_limit_beyond_it(monkeypatch, name, limit):
    _clock(monkeypatch, (limit[0], limit[1], 0, "final", 0))
    message = _extras.dependency_requirement(name)
    assert name in message
    assert "%d.%d" % limit in message


@pytest.mark.parametrize("name, limit", sorted(_extras.PYTHON_LIMITS.items()))
def test_requirement_is_the_install_hint_below_the_limit(monkeypatch, name, limit):
    _clock(monkeypatch, (limit[0], limit[1] - 1, 0, "final", 0))
    assert _extras.dependency_requirement(name) == _extras.EVALS_REQUIREMENT


def test_absent_litellm_raises_the_typed_requirement(monkeypatch):
    _clock(monkeypatch, (3, 15, 0, "final", 0))
    monkeypatch.setitem(sys.modules, "litellm", None)
    monkeypatch.delitem(sys.modules, "fi.evals.llm.providers.litellm", raising=False)
    with pytest.raises(ModuleNotFoundError) as caught:
        importlib.import_module("fi.evals.llm.providers.litellm")
    assert caught.value.name == "litellm"
    assert "3.15" in str(caught.value)
    assert caught.value.__suppress_context__


def test_import_litellm_raises_the_typed_requirement(monkeypatch):
    _clock(monkeypatch, (3, 15, 0, "final", 0))
    monkeypatch.setitem(sys.modules, "litellm", None)
    with pytest.raises(ModuleNotFoundError) as caught:
        _extras.import_litellm()
    assert caught.value.name == "litellm"
    assert "3.15" in str(caught.value)
    assert "No module named 'litellm'" in str(caught.value)


@pytest.mark.parametrize("minor", [11, 14])
def test_missing_litellm_below_the_limit_is_a_missing_extra(monkeypatch, minor):
    # The CLI reports its exact EVALS_REQUIREMENT text as a Python-version
    # problem; a supported interpreter must keep the standard missing-module error.
    from fi._cli.extra_roots import is_evals_requirement

    _clock(monkeypatch, (3, minor, 0, "final", 0))
    monkeypatch.setitem(sys.modules, "litellm", None)
    with pytest.raises(ModuleNotFoundError) as caught:
        _extras.import_litellm()
    assert caught.value.name == "litellm"
    assert str(caught.value) != _extras.EVALS_REQUIREMENT
    assert not is_evals_requirement(caught.value)
    assert not caught.value.__suppress_context__


def test_missing_litellm_below_the_evals_floor_is_a_python_version_error(
    monkeypatch, capsys
):
    # Generated grading criteria import LiteLLM lazily, without the package
    # guards; on the base SDK's Python 3.10 the CLI must still report the floor.
    from fi._cli.main import _dispatch
    from fi.evals.core.prompt_generator import generate_grading_criteria

    _clock(monkeypatch, (3, 10, 0, "final", 0))
    monkeypatch.setitem(sys.modules, "litellm", None)
    with pytest.raises(ModuleNotFoundError) as caught:
        generate_grading_criteria("rubric", "any-model", {}, cache=False)
    exc = caught.value
    assert exc.name == "litellm"
    assert str(exc) == _extras.EVALS_REQUIREMENT

    def handler(args):
        raise exc

    assert _dispatch(Namespace(func=handler, json=True, install_hint=None)) == 3
    error = json.loads(capsys.readouterr().out)["error"]
    assert error["code"] == "MISSING_EXTRA"
    assert error["reason"] == "python_version"
    assert error["required_python"] == "3.11"
    assert error["extra"] == "evals"


def test_every_litellm_import_goes_through_the_typed_guard():
    # A direct import elsewhere would surface a raw ImportError on 3.15+.
    root = Path(__file__).resolve().parents[2] / "fi"
    direct = []
    for path in sorted(root.rglob("*.py")):
        if path.name == "_extras.py" and path.parent.name == "evals":
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            if any(name.split(".")[0] == "litellm" for name in names):
                direct.append(f"{path.relative_to(root)}:{node.lineno}")
    assert direct == [], direct
