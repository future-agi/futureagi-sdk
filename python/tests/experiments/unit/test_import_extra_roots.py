"""The import-root table follows pyproject; error hints obey their precedence."""

import importlib
import importlib.util
import re
import sys
from argparse import Namespace
from pathlib import Path

import pytest

EXPERIMENTS_HINT = 'pip install "futureagi[experiments]"'


def _norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def _roots(distribution):
    name = _norm(distribution)
    aliases = {
        "fi-instrumentation-otel": "fi_instrumentation",
        "python-dotenv": "dotenv",
        "python-dateutil": "dateutil",
        "pyyaml": "yaml",
        "levenshtein": "Levenshtein",
    }
    root = ("opentelemetry" if name.startswith("opentelemetry-")
            else aliases.get(name, name.replace("-", "_")))
    # These runtimes are shared via instrumentors as well as direct evals deps
    # (pyproject's dependency comment). Direct membership alone would mislabel them.
    shared = {
        "fi-instrumentation-otel": {"opentelemetry"},
        "traceai-openai": {"openai"},
        "traceai-openai-agents": {"openai"},
    }
    return {root} | shared.get(name, set())


def test_extra_roots_equal_pyproject_membership():
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib  # pytest's TOML dependency on Python 3.10
    assert importlib.util.find_spec("fi._cli.extra_roots") is not None, "CLI must provide extra_roots"
    extra_roots = importlib.import_module("fi._cli.extra_roots")
    EXTRA_ROOTS = getattr(extra_roots, "EXTRA_ROOTS", None)
    assert EXTRA_ROOTS is not None, "CLI extra_roots must provide EXTRA_ROOTS"

    path = Path(__file__).resolve().parents[3] / "pyproject.toml"
    poetry = tomllib.loads(path.read_text())["tool"]["poetry"]
    dependencies = {_norm(name): spec for name, spec in poetry["dependencies"].items()
                    if name != "python"}
    base_roots = set()
    for name, spec in dependencies.items():
        if not isinstance(spec, dict) or not spec.get("optional", False):
            base_roots.update(_roots(name))
    owners = {}
    for extra, distributions in poetry["extras"].items():
        for distribution in distributions:
            name = _norm(distribution)
            assert name in dependencies, f"undeclared extra dependency: {distribution}"
            for root in _roots(name):
                owners.setdefault(root, set()).add(extra)
    expected = {root: next(iter(extras)) for root, extras in owners.items()
                if len(extras) == 1 and root not in base_roots}
    assert EXTRA_ROOTS == expected
    assert not ({"openai", "opentelemetry", "fi_instrumentation", "dotenv", "traceai_langchain"}
                & EXTRA_ROOTS.keys())


@pytest.mark.parametrize("module,extra", [
    ("filelock", "evals"),
    ("jinja2.environment", "evals"),
    ("litellm", "evals"),
    ("nltk.translate", "evals"),
    ("rouge_score.rouge_scorer", "evals"),
    ("yaml", "evals"),
    ("traceai_openai", "openai"),
    ("traceai_openai_agents", "openai-agents"),
])
@pytest.mark.parametrize("default", [None, EXPERIMENTS_HINT])
def test_unique_root_overrides_command_default(module, extra, default):
    from fi._cli.main import missing_extra

    exc = ModuleNotFoundError(f"No module named {module!r}", name=module)
    err = missing_extra(Namespace(install_hint=default), exc)
    hint = f'pip install "futureagi[{extra}]"'
    assert err.install_hint == hint
    assert err.extra == extra
    assert hint in str(err)
    assert EXPERIMENTS_HINT not in str(err)
    if extra == "evals":
        assert "Python 3.11+" in str(err)


def test_exception_hint_beats_root_and_command():
    from fi._cli.main import missing_extra

    exc = ModuleNotFoundError("No module named 'litellm'", name="litellm")
    exc.install_hint = 'pip install "custom-distribution[local]"'
    err = missing_extra(Namespace(install_hint=EXPERIMENTS_HINT), exc)
    assert err.install_hint == exc.install_hint
    assert exc.install_hint in str(err)
    assert "futureagi[evals]" not in str(err)
    assert EXPERIMENTS_HINT not in str(err)


@pytest.mark.parametrize("module", ["opentelemetry.trace", "openai", "traceai_langchain",
                                    "fi_instrumentation", "dotenv", "unknown_package"])
def test_shared_or_unknown_root_keeps_command_default(module):
    from fi._cli.main import missing_extra

    exc = ModuleNotFoundError(f"No module named {module!r}", name=module)
    err = missing_extra(Namespace(install_hint=EXPERIMENTS_HINT), exc)
    assert err.install_hint == EXPERIMENTS_HINT
    assert EXPERIMENTS_HINT in str(err)
    assert "futureagi[evals]" not in str(err)


@pytest.mark.parametrize("module", ["unknown_package.submodule", "opentelemetry", None])
def test_without_a_hint_never_guesses_a_pip_distribution(module):
    from fi._cli.main import missing_extra

    exc = ModuleNotFoundError("missing dependency", name=module)
    err = missing_extra(Namespace(), exc)
    assert err.install_hint is None
    assert "pip install" not in str(err)
    if module:
        assert repr(module.split(".")[0]) in str(err)
    else:
        assert "An optional dependency is missing" in str(err)
