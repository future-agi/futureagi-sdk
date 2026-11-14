"""A configuration call names the extra it needs when OpenTelemetry is missing.

``Evaluator.evaluate(..., platform=..., custom_eval_name=...)`` sends the evaluation's
configuration for another tracing platform, tagged with the current span and trace, which it
reads with OpenTelemetry (installed by ``futureagi[evals]``). Without OpenTelemetry the call
raises ``fi.errors.MissingExtraError`` with the install line, before any request is sent,
instead of returning ``None``. With it, the call sends its request and returns the response.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from tests.evals import _mock_http

PYTHON = Path(__file__).resolve().parents[2]
CONFIGURE = ("POST", "/sdk/api/v1/configure-evaluations/")
ACCEPTED = {"status": True, "result": "Evaluation configured."}
INSTALL = 'pip install "futureagi[evals]"'
TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
SPAN_ID = "b7ad6b7169203331"
LANGFUSE = {"langfuse_secret_key": "lf-secret-A", "langfuse_public_key": "lf-public-A",
            "langfuse_host": "http://127.0.0.1:9/langfuse"}

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

backend = _mock_http.FakeBackend({("POST", "/sdk/api/v1/configure-evaluations/"):
                                  lambda call: (200, {"status": True, "result": "Evaluation configured."})})
evaluator = Evaluator(fi_api_key=_mock_http.KEY, fi_secret_key=_mock_http.SECRET,
                      fi_base_url=_mock_http.BASE_URL, **json.loads(sys.argv[2]))
attempts.clear()
outcome = {}
with _mock_http.serve(backend):
    try:
        returned = evaluator.evaluate(eval_templates="toxicity", inputs={"output": "x"},
                                      **json.loads(sys.argv[3]))
        outcome["returned"] = repr(returned)
    except Exception as exc:
        cause = exc.__cause__
        outcome.update(raised=type(exc).__name__, message=str(exc),
                       sdk_error=isinstance(exc, FutureAGIError),
                       extra=getattr(exc, "extra", None), module=getattr(exc, "module", None),
                       install_hint=getattr(exc, "install_hint", None),
                       cause=None if cause is None else type(cause).__name__,
                       cause_is_import_error=isinstance(cause, ImportError))
outcome["requests"] = len(backend.calls)
outcome["attempted"] = sorted({name.split(".")[0] for name in attempts})
print(json.dumps(outcome))
'''


def _configure_without_opentelemetry(tmp_path, call):
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "FI_BASE_URL": _mock_http.BASE_URL,
           "FI_LOGIN_FILE": str(tmp_path / "no-login.json"), "LITELLM_LOCAL_MODEL_COST_MAP": "True"}
    run = subprocess.run(
        [sys.executable, "-I", "-c", _WITHOUT_OPENTELEMETRY, str(PYTHON), json.dumps(LANGFUSE),
         json.dumps(call)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=300,
    )
    assert run.returncode == 0, run.stderr[-4000:]
    return json.loads(run.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize("call", [
    {"platform": "langfuse", "custom_eval_name": "answer-check", "trace_id": TRACE_ID, "span_id": SPAN_ID},
    {"platform": "another-platform", "custom_eval_name": "answer-check"},
], ids=["langfuse-with-ids", "another-platform-without-ids"])
def test_configure_without_opentelemetry_names_the_evals_extra_and_sends_nothing(tmp_path, call):
    outcome = _configure_without_opentelemetry(tmp_path, call)

    assert "opentelemetry" in outcome["attempted"]
    assert outcome.get("raised") == "MissingExtraError", outcome
    assert outcome["sdk_error"] is True
    assert outcome["extra"] == "evals"
    assert outcome["module"] == "opentelemetry"
    assert outcome["install_hint"] == INSTALL
    assert "OpenTelemetry" in outcome["message"]
    assert outcome["message"].endswith("Run: " + INSTALL)
    assert outcome["cause_is_import_error"] is True
    assert outcome["requests"] == 0


def test_configure_with_opentelemetry_sends_the_request_and_returns_the_response():
    pytest.importorskip("opentelemetry.trace")
    from fi.evals import Evaluator

    backend = _mock_http.FakeBackend({CONFIGURE: lambda call: (200, ACCEPTED)})
    evaluator = Evaluator(**LANGFUSE)
    with _mock_http.serve(backend):
        result = evaluator.evaluate(
            "toxicity", {"output": "x"}, model_name="turing_flash", platform="langfuse",
            custom_eval_name="answer-check", trace_id=TRACE_ID, span_id=SPAN_ID,
        )

    assert result == ACCEPTED
    [call] = backend.calls
    assert (call["method"], call["path"]) == CONFIGURE
    assert call["json"] == {
        "eval_config": {"eval_templates": "toxicity", "inputs": {"output": "x"}, "model_name": "turing_flash"},
        "custom_eval_name": "answer-check",
        "platform": "langfuse",
        **LANGFUSE,
        "trace_id": TRACE_ID,
        "span_id": SPAN_ID,
    }


def test_configure_inside_a_span_sends_that_span_and_its_trace():
    pytest.importorskip("opentelemetry.trace")
    sdk_trace = pytest.importorskip("opentelemetry.sdk.trace")
    from fi.evals import Evaluator

    tracer = sdk_trace.TracerProvider(shutdown_on_exit=False).get_tracer("configure-check")
    backend = _mock_http.FakeBackend({CONFIGURE: lambda call: (200, ACCEPTED)})
    with _mock_http.serve(backend), tracer.start_as_current_span("answer") as span:
        result = Evaluator().evaluate(
            "toxicity", {"output": "x"}, platform="another-platform", custom_eval_name="answer-check",
        )

    context = span.get_span_context()
    assert result == ACCEPTED
    [call] = backend.calls
    assert (call["method"], call["path"]) == CONFIGURE
    assert call["json"]["platform"] == "another-platform"
    assert call["json"]["span_id"] == format(context.span_id, "016x")
    assert call["json"]["trace_id"] == format(context.trace_id, "032x")
