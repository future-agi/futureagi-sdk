"""Typed exceptions parsed from HTTP responses."""
from __future__ import annotations
from unittest.mock import MagicMock
from ._exception_fixtures import _make_mock_response


def test_from_response_400() -> None:
    from fi.gateway._exceptions import APIStatusError, BadRequestError

    resp = _make_mock_response(
        400,
        body={
            "error": {
                "message": "Invalid model",
                "type": "invalid_request_error",
                "code": "invalid_param",
                "param": "model",
            }
        },
        headers={"x-agentcc-request-id": "req-123"},
    )
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, BadRequestError)
    assert exc.status_code == 400
    assert exc.message == "Invalid model"
    assert exc.type == "invalid_request_error"
    assert exc.code == "invalid_param"
    assert exc.param == "model"
    assert exc.request_id == "req-123"


def test_from_response_401() -> None:
    from fi.gateway._exceptions import APIStatusError, AuthenticationError

    resp = _make_mock_response(401, body={"error": {"message": "Invalid API key"}})
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, AuthenticationError)
    assert exc.status_code == 401


def test_from_response_403() -> None:
    from fi.gateway._exceptions import APIStatusError, PermissionDeniedError

    resp = _make_mock_response(403, body={"error": {"message": "Forbidden"}})
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, PermissionDeniedError)


def test_from_response_404() -> None:
    from fi.gateway._exceptions import APIStatusError, NotFoundError

    resp = _make_mock_response(404, body={"error": {"message": "Model not found"}})
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, NotFoundError)


def test_from_response_422() -> None:
    from fi.gateway._exceptions import APIStatusError, UnprocessableEntityError

    resp = _make_mock_response(422, body={"error": {"message": "Semantic error"}})
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, UnprocessableEntityError)


def test_from_response_429_with_ratelimit_headers() -> None:
    from fi.gateway._exceptions import APIStatusError, RateLimitError

    resp = _make_mock_response(
        429,
        body={"error": {"message": "Rate limit exceeded"}},
        headers={
            "x-ratelimit-limit-requests": "100",
            "x-ratelimit-remaining-requests": "0",
            "x-ratelimit-reset-requests": "30",
        },
    )
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, RateLimitError)
    assert exc.ratelimit_limit == 100
    assert exc.ratelimit_remaining == 0
    assert exc.ratelimit_reset == 30


def test_from_response_429_without_headers() -> None:
    from fi.gateway._exceptions import APIStatusError, RateLimitError

    resp = _make_mock_response(429, body={"error": {"message": "Rate limited"}})
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, RateLimitError)
    assert exc.ratelimit_limit is None
    assert exc.ratelimit_remaining is None
    assert exc.ratelimit_reset is None


def test_from_response_429_invalid_ratelimit_values() -> None:
    from fi.gateway._exceptions import APIStatusError, RateLimitError

    resp = _make_mock_response(
        429,
        body={"error": {"message": "Rate limited"}},
        headers={
            "x-ratelimit-limit-requests": "not-a-number",
            "x-ratelimit-remaining-requests": "",
        },
    )
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, RateLimitError)
    assert exc.ratelimit_limit is None
    assert exc.ratelimit_remaining is None


def test_from_response_446_guardrail_blocked() -> None:
    from fi.gateway._exceptions import APIStatusError, GuardrailBlockedError

    resp = _make_mock_response(
        446,
        body={"error": {"message": "Content blocked by guardrail"}},
        headers={
            "x-agentcc-guardrail-name": "prompt-guard",
            "x-agentcc-guardrail-action": "block",
            "x-agentcc-guardrail-confidence": "0.95",
            "x-agentcc-guardrail-message": "PII detected",
        },
    )
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, GuardrailBlockedError)
    assert exc.status_code == 446
    assert exc.guardrail_name == "prompt-guard"
    assert exc.guardrail_action == "block"
    assert exc.guardrail_confidence == 0.95
    assert exc.guardrail_message == "PII detected"


def test_from_response_446_without_guardrail_headers() -> None:
    from fi.gateway._exceptions import APIStatusError, GuardrailBlockedError

    resp = _make_mock_response(446, body={"error": {"message": "Blocked"}})
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, GuardrailBlockedError)
    assert exc.guardrail_name is None
    assert exc.guardrail_confidence is None


def test_from_response_446_invalid_confidence() -> None:
    from fi.gateway._exceptions import APIStatusError, GuardrailBlockedError

    resp = _make_mock_response(
        446,
        body={"error": {"message": "Blocked"}},
        headers={"x-agentcc-guardrail-confidence": "not-a-float"},
    )
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, GuardrailBlockedError)
    assert exc.guardrail_confidence is None


def test_from_response_500() -> None:
    from fi.gateway._exceptions import APIStatusError, InternalServerError

    resp = _make_mock_response(500, body={"error": {"message": "Internal error"}})
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, InternalServerError)


def test_from_response_502() -> None:
    from fi.gateway._exceptions import APIStatusError, BadGatewayError

    resp = _make_mock_response(502, body={"error": {"message": "Provider error"}})
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, BadGatewayError)


def test_from_response_503() -> None:
    from fi.gateway._exceptions import APIStatusError, ServiceUnavailableError

    resp = _make_mock_response(503, body={"error": {"message": "Unavailable"}})
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, ServiceUnavailableError)


def test_from_response_504() -> None:
    from fi.gateway._exceptions import APIStatusError, GatewayTimeoutError

    resp = _make_mock_response(504, body={"error": {"message": "Provider timeout"}})
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, GatewayTimeoutError)


def test_from_response_unknown_status_code() -> None:
    """Unknown status codes should return generic APIStatusError."""
    from fi.gateway._exceptions import APIStatusError

    resp = _make_mock_response(418, body={"error": {"message": "I'm a teapot"}})
    exc = APIStatusError.from_response(resp)
    assert type(exc) is APIStatusError
    assert exc.status_code == 418


def test_from_response_no_json_body() -> None:
    """When response has no JSON body, fallback message should work."""
    from fi.gateway._exceptions import APIStatusError

    resp = _make_mock_response(500)  # json() raises
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, APIStatusError)
    assert exc.message == "HTTP 500"
    assert exc.body is None


def test_from_response_non_dict_body() -> None:
    """When JSON body is not a dict (e.g., a string), handle gracefully."""
    from fi.gateway._exceptions import APIStatusError

    resp = _make_mock_response(500, body="not a dict")  # type: ignore[arg-type]
    exc = APIStatusError.from_response(resp)
    assert exc.message == "HTTP 500"


def test_from_response_246_guardrail_warning() -> None:
    from fi.gateway._exceptions import APIStatusError, GuardrailWarning

    body = {
        "id": "chatcmpl-abc123",
        "choices": [{"message": {"content": "Hello"}}],
        "error": {"message": "Content may contain sensitive material"},
    }
    resp = _make_mock_response(
        246,
        body=body,
        headers={
            "x-agentcc-request-id": "req-456",
            "x-agentcc-guardrail-name": "content-filter",
            "x-agentcc-guardrail-action": "warn",
            "x-agentcc-guardrail-confidence": "0.72",
            "x-agentcc-guardrail-message": "Potentially sensitive",
        },
    )
    exc = APIStatusError.from_response(resp)
    assert isinstance(exc, GuardrailWarning)
    assert exc.status_code == 246
    assert exc.completion == body
    assert exc.guardrail_name == "content-filter"
    assert exc.guardrail_action == "warn"
    assert exc.guardrail_confidence == 0.72
    assert exc.guardrail_message == "Potentially sensitive"
    assert exc.request_id == "req-456"
