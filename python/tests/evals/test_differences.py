"""The differences from ai-evaluation 1.1.0 that code and docs can see, listed and each held true.

``fixtures/differences-ai-evaluation-1.1.0.json`` is the list the documentation sweep reads. Every
entry names the tests that pin it, so the list cannot drift from the code; the tests below pin the
entries no other test covered.
"""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest
import requests

from tests.evals import _examples

PYTHON = Path(__file__).resolve().parents[2]
DIFFERENCES = Path(__file__).parent / "fixtures/differences-ai-evaluation-1.1.0.json"
KNOWN = {"cli", "evals-extra", "http-error-retries", "missing-keys-message", "per-instance-keys",
         "success-status", "patch-targets", "registry-session", "ground-truth-setup", "log-privacy",
         "refusal-reason", "configure-needs-opentelemetry", "trace-eval-needs-opentelemetry"}
FIELDS = ("id", "area", "ai_evaluation", "futureagi", "docs", "tests")


def _entries() -> list:
    return json.loads(DIFFERENCES.read_text())["differences"]


def test_the_list_names_every_known_difference_once() -> None:
    ids = [entry["id"] for entry in _entries()]
    assert sorted(ids) == sorted(KNOWN)
    for entry in _entries():
        assert set(FIELDS) <= set(entry), entry["id"]
        assert all(isinstance(entry[f], str) and entry[f].strip() for f in FIELDS[:-1]), entry["id"]
        assert entry["tests"], entry["id"]


def test_every_test_an_entry_names_exists() -> None:
    missing = []
    for entry in _entries():
        for ref in entry["tests"]:
            path, _, name = ref.partition("::")
            tree = ast.parse((PYTHON / path).read_text())
            if not any(isinstance(n, ast.FunctionDef) and n.name == name for n in tree.body):
                missing.append(ref)
    assert missing == []


def test_the_examples_that_differ_on_purpose_are_on_the_list() -> None:
    listed = [name for entry in _entries() for name in entry.get("examples", [])]
    assert sorted(listed) == sorted(_examples.INTENDED_DIFFERENCES)


@pytest.mark.parametrize("command", ["init", "validate", "view", "export", "config"])
def test_the_retired_fi_commands_have_no_evals_counterpart(command, capsys) -> None:
    from fi._cli.main import main

    assert main(["evals", command]) == 2
    assert "invalid choice" in capsys.readouterr().err


def test_evals_run_takes_one_template_and_these_options(capsys) -> None:
    from fi._cli.main import main

    assert main(["evals", "run", "--help"]) == 0
    # the option lines only: the usage line repeats the root command's own options
    lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip().startswith("-")]
    options = {option for line in lines for option in re.findall(r"(?<![\w-])--[a-z][a-z-]*", line.split("  ")[0])}
    assert options == {"--help", "--input", "--inputs", "--model", "--timeout", "--json"}


_BASE_INSTALL = r"""
import importlib, importlib.abc, importlib.util, json, socket, sys

def refuse(*args, **kwargs):
    raise ConnectionRefusedError("no network in this check")

socket.socket.connect = refuse
socket.getaddrinfo = refuse
EXTRA = {"jinja2", "litellm", "nltk", "openai", "opentelemetry", "yaml", "rouge_score", "filelock"}

class WithoutTheExtra(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in EXTRA:
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        return None

sys.meta_path.insert(0, WithoutTheExtra())
import fi.evals
cloud = {n: getattr(fi.evals, n) is not None for n in
         ("Evaluator", "evaluate", "Protect", "Execution", "EvalTemplateManager", "list_evaluations")}
assert "rouge_score" not in sys.modules
assert "litellm" not in sys.modules
local = {}
for name in ("fi.evals.local", "fi.evals.metrics", "fi.evals.llm"):
    try:
        importlib.import_module(name)
        local[name] = "imported"
    except ModuleNotFoundError as exc:
        local[name] = "missing " + exc.name.split(".")[0] if exc.name.split(".")[0] in EXTRA else repr(exc)
    except ImportError as exc:
        assert importlib.util.find_spec("fi.evals._extras") is not None, "evals must provide the Python guard"
        from fi.evals._extras import EVALS_REQUIREMENT
        assert sys.version_info < (3, 11)
        assert str(exc) == EVALS_REQUIREMENT
        local[name] = "missing Python 3.11+ support for futureagi[evals]"
print(json.dumps({"cloud": cloud, "local": local}))
"""


def test_local_metrics_need_the_evals_extra_and_the_cloud_client_does_not(tmp_path) -> None:
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "FI_BASE_URL": "http://127.0.0.1:9",
           "LITELLM_LOCAL_MODEL_COST_MAP": "True", "FI_LOGIN_FILE": str(tmp_path / "no-login.json")}
    run = subprocess.run([sys.executable, "-I", "-c", _BASE_INSTALL], cwd=tmp_path, env=env,
                         capture_output=True, text=True, timeout=300)
    assert run.returncode == 0, run.stderr[-2000:]
    result = json.loads(run.stdout.strip().splitlines()[-1])
    assert all(result["cloud"].values()), result["cloud"]
    assert all(outcome.startswith("missing ") for outcome in result["local"].values()), result["local"]


def _parse(status: int):
    from fi.api.auth import ResponseHandler

    class Handler(ResponseHandler):
        @classmethod
        def _parse_success(cls, response):
            return "success"

        @classmethod
        def _handle_error(cls, response):
            raise RuntimeError(response.status_code)

    response = requests.Response()
    response.status_code = status
    return Handler.parse(response)


@pytest.mark.parametrize("status", [200, 201, 202, 204, 299])
def test_any_2xx_status_is_a_success(status: int) -> None:
    assert _parse(status) == "success"


@pytest.mark.parametrize("status", [199, 300, 400, 500])
def test_a_status_outside_2xx_is_an_error(status: int) -> None:
    with pytest.raises(RuntimeError):
        _parse(status)


def test_moved_code_reads_the_globals_of_its_own_module() -> None:
    import fi.evals.framework.propagation as propagation
    from fi.evals.streaming import StreamingEvaluator

    moved = StreamingEvaluator.add_eval
    assert moved.__module__ == "fi.evals.streaming._evaluator_streaming_evaluator_add_eval"
    assert moved.__globals__["__name__"] == "fi.evals.streaming._evaluator_streaming_evaluator_add_eval"
    carrier = propagation.ContextCarrier
    assert carrier.__module__ == "fi.evals.framework.propagation"  # the class keeps its published name
    assert carrier.capture.__globals__ is not vars(propagation)
    assert carrier.capture.__globals__["__name__"] == "fi.evals.framework._propagation_carrier"


@pytest.mark.parametrize("name", ["load_registry", "get_template_info", "get_required_keys",
                                  "map_inputs_to_backend", "list_known_names"])
def test_the_registry_functions_take_an_optional_session_keyword(name: str) -> None:
    from fi.evals.core import cloud_registry

    parameter = inspect.signature(getattr(cloud_registry, name)).parameters["session"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is None
