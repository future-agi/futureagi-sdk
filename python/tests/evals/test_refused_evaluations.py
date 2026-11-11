"""A refused evaluation reaches the caller as the server's own sentence.

The eval endpoint refuses with an error status and a body such as ``{"status": false, "message":
..., "details": {field: [...]}}``. ``Evaluator.evaluate()`` still returns a result instead of
raising; its reason leads with that sentence and the status, never the whole body, and a 403
adds the key hint after them. ``evaluate()`` on the Turing engine reports the refusal as failed, with
the same text as its error. A request that timed out reads the same way: failed, with a plain
sentence.
"""

from __future__ import annotations

import concurrent.futures
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest
import requests

from tests.evals import _mock_http

NEW_EVAL = ("POST", "/sdk/api/v1/new-eval/")
UNEXPECTED_KEYS = "Unexpected keys provided: answer. Accepted keys are: output"
REFUSED = (400, {
    "status": False, "type": "validation_error", "code": "invalid", "detail": "Validation failed",
    "message": "Validation failed", "error": "Validation failed", "result": "Validation failed",
    "attr": "inputs", "details": {"inputs": [UNEXPECTED_KEYS]}, "errors": {"inputs": [UNEXPECTED_KEYS]},
})
REFUSED_TEXT = "Validation failed: inputs: " + UNEXPECTED_KEYS + " (HTTP 400)"
FAILED_RUN = "Failed to run the evaluation."
SERVER_ERROR = (500, {"status": False, "type": "server_error", "code": "server_error",
                      "detail": FAILED_RUN, "message": FAILED_RUN, "error": FAILED_RUN, "result": FAILED_RUN})
OUT_OF_CREDITS = "Your organization has run out of credits. Add credits to keep running evaluations."
NO_CREDITS = (402, {"status": False, "type": "payment_required", "code": "INSUFFICIENT_CREDITS",
                    "detail": OUT_OF_CREDITS, "message": OUT_OF_CREDITS, "error": OUT_OF_CREDITS,
                    "result": OUT_OF_CREDITS, "error_code": "INSUFFICIENT_CREDITS", "retryable": False})
FORBIDDEN = (403, {"detail": "Authentication credentials were not provided."})
KEY_HINT = "Check your API key and secret key."
FORBIDDEN_TEXT = "Authentication credentials were not provided. (HTTP 403) " + KEY_HINT
NO_PERMISSION = "Workspace write permission is required."
NOT_ALLOWED = (403, {"status": False, "type": "permission_denied", "code": "permission_denied",
                     "detail": NO_PERMISSION, "message": NO_PERMISSION, "error": NO_PERMISSION,
                     "result": NO_PERMISSION})
NOT_ALLOWED_TEXT = NO_PERMISSION + " (HTTP 403) " + KEY_HINT
GATEWAY_PAGE = (
    "<html>\n<head><title>502 Bad Gateway</title></head>\n<body>\n"
    "<center><h1>502 Bad Gateway</h1></center>\n</body>\n</html>\n"
)


class _NotJson(_mock_http.FakeBackend):
    """Answers the evaluation request with a body that is not JSON (a proxy's error page)."""

    def __init__(self, status: int, body: str) -> None:
        super().__init__()
        self.status, self.body = status, body

    def send(self, request: requests.PreparedRequest) -> requests.Response:
        if (request.method, urlsplit(request.url or "").path) != NEW_EVAL:
            return super().send(request)
        response = requests.Response()
        response.status_code = self.status
        response._content = self.body.encode("utf-8")
        response.headers["Content-Type"] = "text/html"
        response.encoding = "utf-8"
        response.url = request.url or ""
        response.request = request
        return response


class _TimesOut(_mock_http.FakeBackend):
    """The evaluation request never answers: sending it raises the given timeout."""

    def __init__(self, error: type) -> None:
        super().__init__()
        self.error = error

    def send(self, request: requests.PreparedRequest) -> requests.Response:
        if (request.method, urlsplit(request.url or "").path) != NEW_EVAL:
            return super().send(request)
        raise self.error("no answer")


TIMEOUTS = pytest.mark.parametrize("error", [requests.exceptions.ReadTimeout, concurrent.futures.TimeoutError],
                                   ids=["read-timeout", "timeout"])


@pytest.fixture
def no_retry_pause(monkeypatch):
    """The client re-sends a request that timed out after a 1 s pause; skip the pause."""
    import fi.api.auth

    monkeypatch.setattr(fi.api.auth, "time", SimpleNamespace(sleep=lambda seconds: None))


def _evaluator_result(backend: _mock_http.FakeBackend):
    from fi.evals import Evaluator

    with _mock_http.serve(backend):
        batch = Evaluator().evaluate(eval_templates="toxicity", inputs={"output": "x"}, skip_input_mapping=True)
    assert len(batch.eval_results) == 1
    return batch.eval_results[0]


@pytest.mark.parametrize(("answer", "text"), [
    (REFUSED, REFUSED_TEXT),
    (SERVER_ERROR, FAILED_RUN + " (HTTP 500)"),
    (NO_CREDITS, OUT_OF_CREDITS + " (HTTP 402)"),
    ((404, {"detail": "Not found."}), "Not found. (HTTP 404)"),
    ((400, {"status": False}), 'The evaluation request failed with HTTP 400: {"status": false}'),
    (NOT_ALLOWED, NOT_ALLOWED_TEXT),
    (FORBIDDEN, FORBIDDEN_TEXT),
], ids=["field-error", "server-error", "no-credits", "detail-only", "no-sentence", "no-permission",
        "no-credentials"])
def test_evaluator_reason_leads_with_the_server_sentence_and_status(answer, text) -> None:
    result = _evaluator_result(_mock_http.FakeBackend({NEW_EVAL: lambda call: answer}))
    assert (result.output, result.reason) == (None, text)


@pytest.mark.parametrize(("status", "body", "text"), [
    (502, GATEWAY_PAGE, "The evaluation request failed with HTTP 502: <html> <head><title>502 Bad Gateway"
                        "</title></head> <body> <center><h1>502 Bad Gateway</h1></center> </body> </html>"),
    (504, "x" * 1000, "The evaluation request failed with HTTP 504: " + "x" * 200 + "..."),
    (503, "", "The evaluation request failed with HTTP 503 and an empty body."),
    (403, "", "The evaluation request failed with HTTP 403 and an empty body. " + KEY_HINT),
], ids=["error-page", "long-body", "empty-body", "forbidden-empty-body"])
def test_evaluator_reason_for_a_body_that_is_not_json_is_a_short_excerpt(status, body, text) -> None:
    result = _evaluator_result(_NotJson(status, body))
    assert (result.output, result.reason) == (None, text)


def test_a_403_still_raises_invalid_auth_error_with_the_server_sentence_first() -> None:
    from fi.evals.evaluator import EvalResponseHandler
    from fi.utils.errors import InvalidAuthError

    response = requests.Response()
    response.status_code = 403
    response._content = b'{"status": false, "message": "Workspace write permission is required."}'
    response.encoding = "utf-8"
    with pytest.raises(InvalidAuthError) as raised:
        EvalResponseHandler._handle_error(response)
    assert str(raised.value) == NOT_ALLOWED_TEXT


@pytest.mark.parametrize(("answer", "text"), [
    (REFUSED, REFUSED_TEXT),
    (SERVER_ERROR, FAILED_RUN + " (HTTP 500)"),
    (FORBIDDEN, FORBIDDEN_TEXT),
    (NOT_ALLOWED, NOT_ALLOWED_TEXT),
], ids=["field-error", "server-error", "forbidden", "no-permission"])
def test_turing_evaluate_reports_a_refused_evaluation_as_failed(answer, text) -> None:
    from fi.evals import evaluate

    with _mock_http.serve(_mock_http.FakeBackend({NEW_EVAL: lambda call: answer})):
        result = evaluate("toxicity", engine="turing", output="x")
    assert (result.status, result.error, result.score, result.passed) == ("failed", text, None, None)


def test_refused_turing_evaluations_are_not_counted_as_completed() -> None:
    from fi.evals import evaluate

    with _mock_http.serve(_mock_http.FakeBackend({NEW_EVAL: lambda call: REFUSED})):
        results = evaluate(["toxicity", "tone"], engine="turing", output="x")
    assert [(r.status, r.error) for r in results] == [("failed", REFUSED_TEXT)] * 2
    assert results.success_rate == 0.0


@TIMEOUTS
def test_evaluator_reports_a_timed_out_request_as_failed_with_a_plain_sentence(error, no_retry_pause) -> None:
    from fi.evals import Evaluator

    with _mock_http.serve(_TimesOut(error)):
        batch = Evaluator().evaluate(eval_templates="toxicity", inputs={"output": "x"}, timeout=7,
                                     skip_input_mapping=True)
    [result] = batch.eval_results
    assert (result.output, result.reason, getattr(result, "error", None)) == (
        None, "Evaluation timed out after 7s", "Evaluation timed out after 7s")


@TIMEOUTS
def test_turing_evaluate_reports_a_timed_out_request_as_failed(error, no_retry_pause) -> None:
    from fi.evals import evaluate

    with _mock_http.serve(_TimesOut(error)):
        result = evaluate("toxicity", engine="turing", output="x")
    assert (result.status, result.error, result.score, result.passed) == (
        "failed", "Evaluation timed out after 200s", None, None)
