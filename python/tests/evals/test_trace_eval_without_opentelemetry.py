"""A traced evaluation names the extra it needs when OpenTelemetry is missing.

``Evaluator.evaluate(..., trace_eval=True, custom_eval_name=...)`` attaches the evaluation to the
current span, which it reads with OpenTelemetry (installed by ``futureagi[evals]``). Without
OpenTelemetry the call raises ``fi.errors.MissingExtraError`` with the install line, before any
request is sent, instead of returning ``None``. Without ``custom_eval_name`` the call still runs
the evaluation untraced, and with OpenTelemetry installed it behaves as before.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from tests.evals import _mock_http

PYTHON = Path(__file__).resolve().parents[2]
EVALUATE = ("POST", "/sdk/api/v1/new-eval/")
INSTALL = 'pip install "futureagi[evals]"'

_WITHOUT_OPENTELEMETRY = r'''
import importlib.abc, json, socket, sys
sys.path.insert(0, sys.argv[1])

def refuse(*args, **kwargs):
    raise ConnectionRefusedError("no network in this check")

socket.socket.connect = refuse
socket.getaddrinfo = refuse
attempts = []

class WithoutOpenTelemetry(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] == "opentelemetry":
            attempts.append(name)
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        return None

sys.meta_path.insert(0, WithoutOpenTelemetry())
from tests.evals import _mock_http
from fi.errors import FutureAGIError
from fi.evals import Evaluator

backend = _mock_http.FakeBackend()
evaluator = Evaluator(fi_api_key=_mock_http.KEY, fi_secret_key=_mock_http.SECRET,
                      fi_base_url=_mock_http.BASE_URL)
attempts.clear()
outcome = {}
with _mock_http.serve(backend):
    try:
        returned = evaluator.evaluate(eval_templates="toxicity", inputs={"output": "x"},
                                      **json.loads(sys.argv[2]))
        outcome["returned"] = repr(returned)
        outcome["outputs"] = [r.output for r in getattr(returned, "eval_results", None) or []]
    except Exception as exc:
        cause = exc.__cause__
        outcome.update(raised=type(exc).__name__, message=str(exc),
                       sdk_error=isinstance(exc, FutureAGIError),
                       extra=getattr(exc, "extra", None), module=getattr(exc, "module", None),
                       install_hint=getattr(exc, "install_hint", None),
                       cause=None if cause is None else type(cause).__name__,
                       cause_is_import_error=isinstance(cause, ImportError))
outcome["requests"] = len(backend.calls)
outcome["evaluations_sent"] = [call["json"] for call in backend.calls
                               if (call["method"], call["path"]) == ("POST", "/sdk/api/v1/new-eval/")]
outcome["attempted"] = sorted({name.split(".")[0] for name in attempts})
print(json.dumps(outcome))
'''


def _evaluate_without_opentelemetry(tmp_path, call):
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "FI_BASE_URL": _mock_http.BASE_URL,
           "FI_LOGIN_FILE": str(tmp_path / "no-login.json"), "LITELLM_LOCAL_MODEL_COST_MAP": "True"}
    run = subprocess.run(
        [sys.executable, "-I", "-c", _WITHOUT_OPENTELEMETRY, str(PYTHON), json.dumps(call)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=300,
    )
    assert run.returncode == 0, run.stderr[-4000:]
    return json.loads(run.stdout.strip().splitlines()[-1])


def test_trace_eval_without_opentelemetry_names_the_evals_extra_and_sends_nothing(tmp_path):
    outcome = _evaluate_without_opentelemetry(
        tmp_path, {"trace_eval": True, "custom_eval_name": "answer-check"})

    assert "opentelemetry" in outcome["attempted"]
    assert outcome.get("raised") == "MissingExtraError", outcome
    assert outcome["sdk_error"] is True
    assert outcome["extra"] == "evals"
    assert outcome["module"] == "opentelemetry"
    assert outcome["install_hint"] == INSTALL
    assert "trace_eval" in outcome["message"]
    assert "OpenTelemetry" in outcome["message"]
    assert outcome["message"].endswith("Run: " + INSTALL)
    assert outcome["cause_is_import_error"] is True
    assert outcome["requests"] == 0


def test_trace_eval_without_a_name_still_evaluates_untraced_without_opentelemetry(tmp_path):
    outcome = _evaluate_without_opentelemetry(tmp_path, {"trace_eval": True})

    assert "raised" not in outcome, outcome
    assert outcome["outputs"] == ["Passed"]
    [sent] = outcome["evaluations_sent"]
    assert sent["eval_name"] == "toxicity"
    assert sent["trace_eval"] is False
    assert sent["span_id"] is None
    assert sent["custom_eval_name"] is None


def _sent_evaluation(backend):
    [call] = [call for call in backend.calls if (call["method"], call["path"]) == EVALUATE]
    return call["json"]


def test_trace_eval_outside_a_span_sends_the_evaluation_untraced():
    pytest.importorskip("opentelemetry.trace")
    from fi.evals import Evaluator

    backend = _mock_http.FakeBackend()
    with _mock_http.serve(backend):
        result = Evaluator().evaluate("toxicity", {"output": "x"}, trace_eval=True,
                                      custom_eval_name="answer-check")

    assert [r.output for r in result.eval_results] == ["Passed"]
    sent = _sent_evaluation(backend)
    assert sent["eval_name"] == "toxicity"
    assert sent["custom_eval_name"] == "answer-check"
    assert sent["trace_eval"] is False
    assert sent["span_id"] is None


def test_trace_eval_inside_a_project_span_sends_that_span(monkeypatch):
    trace = pytest.importorskip("opentelemetry.trace")
    sdk_trace = pytest.importorskip("opentelemetry.sdk.trace")
    resources = pytest.importorskip("opentelemetry.sdk.resources")
    from fi.evals import Evaluator

    provider = sdk_trace.TracerProvider(
        resource=resources.Resource.create({"project_name": "answer-project"}), shutdown_on_exit=False)
    # The evaluation reads the project from the global provider, which a test must not replace.
    monkeypatch.setattr(trace, "get_tracer_provider", lambda: provider)
    tracer = provider.get_tracer("trace-eval-check")
    backend = _mock_http.FakeBackend()
    with _mock_http.serve(backend), tracer.start_as_current_span("answer") as span:
        result = Evaluator().evaluate("toxicity", {"output": "x"}, trace_eval=True,
                                      custom_eval_name="answer-check")

    assert [r.output for r in result.eval_results] == ["Passed"]
    sent = _sent_evaluation(backend)
    assert sent["eval_name"] == "toxicity"
    assert sent["custom_eval_name"] == "answer-check"
    assert sent["trace_eval"] is True
    assert sent["span_id"] == format(span.get_span_context().span_id, "016x")
