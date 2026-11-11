"""A refused evaluation reaches the caller as the server's own sentence.

The eval endpoint refuses with an error status and a body such as ``{"status": false, "message":
..., "details": {field: [...]}}``. ``Evaluator.evaluate()`` still returns a result instead of
raising; its reason leads with that sentence and the status, never the whole body. ``evaluate()``
on the Turing engine reports the refusal as failed, with the same text as its error.
"""

from __future__ import annotations

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
INVALID_KEYS = "Invalid FI Client Authentication, please check your API key and secret key."
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
], ids=["field-error", "server-error", "no-credits", "detail-only", "no-sentence"])
def test_evaluator_reason_leads_with_the_server_sentence_and_status(answer, text) -> None:
    result = _evaluator_result(_mock_http.FakeBackend({NEW_EVAL: lambda call: answer}))
    assert (result.output, result.reason) == (None, text)


@pytest.mark.parametrize(("status", "body", "text"), [
    (502, GATEWAY_PAGE, "The evaluation request failed with HTTP 502: <html> <head><title>502 Bad Gateway"
                        "</title></head> <body> <center><h1>502 Bad Gateway</h1></center> </body> </html>"),
    (504, "x" * 1000, "The evaluation request failed with HTTP 504: " + "x" * 200 + "..."),
    (503, "", "The evaluation request failed with HTTP 503 and an empty body."),
], ids=["error-page", "long-body", "empty-body"])
def test_evaluator_reason_for_a_body_that_is_not_json_is_a_short_excerpt(status, body, text) -> None:
    result = _evaluator_result(_NotJson(status, body))
    assert (result.output, result.reason) == (None, text)


@pytest.mark.parametrize(("answer", "text"), [
    (REFUSED, REFUSED_TEXT),
    (SERVER_ERROR, FAILED_RUN + " (HTTP 500)"),
    (FORBIDDEN, INVALID_KEYS),
], ids=["field-error", "server-error", "forbidden"])
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
