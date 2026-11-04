"""Tests for agentcc._exceptions — exception hierarchy, from_response, guardrail handling."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

# --- Hierarchy tests ---


def test_agentcc_error_is_exception() -> None:
    from fi.gateway._exceptions import AgentCCError

    assert issubclass(AgentCCError, Exception)
    exc = AgentCCError("test error")
    assert str(exc) == "test error"
    assert exc.message == "test error"


def test_agentcc_error_repr() -> None:
    from fi.gateway._exceptions import AgentCCError

    exc = AgentCCError("something failed")
    assert repr(exc) == "AgentCCError('something failed')"


def test_api_connection_error_hierarchy() -> None:
    from fi.gateway._exceptions import APIConnectionError, AgentCCError

    assert issubclass(APIConnectionError, AgentCCError)

    exc = APIConnectionError("connection refused")
    assert exc.message == "connection refused"
    assert exc.request is None


def test_api_connection_error_with_request() -> None:
    from fi.gateway._exceptions import APIConnectionError

    mock_request = MagicMock()
    exc = APIConnectionError("DNS failure", request=mock_request)
    assert exc.request is mock_request


def test_api_timeout_error_hierarchy() -> None:
    from fi.gateway._exceptions import APIConnectionError, APITimeoutError, AgentCCError

    assert issubclass(APITimeoutError, APIConnectionError)
    assert issubclass(APITimeoutError, AgentCCError)

    exc = APITimeoutError()
    assert exc.message == "Request timed out"
    assert exc.request is None


def test_api_timeout_error_custom_message() -> None:
    from fi.gateway._exceptions import APITimeoutError

    exc = APITimeoutError("Custom timeout after 30s")
    assert exc.message == "Custom timeout after 30s"


def test_api_status_error_hierarchy() -> None:
    from fi.gateway._exceptions import APIStatusError, AgentCCError

    assert issubclass(APIStatusError, AgentCCError)

    exc = APIStatusError(
        message="Bad request",
        status_code=400,
        type="invalid_request_error",
        code="invalid_param",
        param="model",
    )
    assert exc.status_code == 400
    assert exc.type == "invalid_request_error"
    assert exc.code == "invalid_param"
    assert exc.param == "model"
    assert exc.response is None
    assert exc.body is None
    assert exc.request_id is None


def test_api_status_error_str_format() -> None:
    from fi.gateway._exceptions import APIStatusError

    exc = APIStatusError(message="Not found", status_code=404)
    assert str(exc) == "Error code: 404 - Not found"


def test_api_status_error_repr() -> None:
    from fi.gateway._exceptions import APIStatusError

    exc = APIStatusError(message="Bad request", status_code=400)
    assert repr(exc) == "APIStatusError(status_code=400, message='Bad request')"


# --- Specific error class tests ---


def test_4xx_error_classes() -> None:
    from fi.gateway._exceptions import (
        APIStatusError,
        AuthenticationError,
        BadRequestError,
        NotFoundError,
        PermissionDeniedError,
        RateLimitError,
        UnprocessableEntityError,
    )

    classes = [
        (BadRequestError, 400),
        (AuthenticationError, 401),
        (PermissionDeniedError, 403),
        (NotFoundError, 404),
        (UnprocessableEntityError, 422),
        (RateLimitError, 429),
    ]
    for cls, code in classes:
        assert issubclass(cls, APIStatusError), f"{cls.__name__} not subclass of APIStatusError"
        exc = cls(message=f"Error {code}", status_code=code)
        assert exc.status_code == code


def test_5xx_error_classes() -> None:
    from fi.gateway._exceptions import (
        APIStatusError,
        BadGatewayError,
        GatewayTimeoutError,
        InternalServerError,
        ServiceUnavailableError,
    )

    classes = [
        (InternalServerError, 500),
        (BadGatewayError, 502),
        (ServiceUnavailableError, 503),
        (GatewayTimeoutError, 504),
    ]
    for cls, code in classes:
        assert issubclass(cls, APIStatusError)
        exc = cls(message=f"Error {code}", status_code=code)
        assert exc.status_code == code


def test_stream_error_hierarchy() -> None:
    from fi.gateway._exceptions import AgentCCError, StreamError

    assert issubclass(StreamError, AgentCCError)
    exc = StreamError("malformed SSE")
    assert exc.message == "malformed SSE"


# --- from_response factory tests ---


def _make_mock_response(
    status_code: int,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    if body is not None:
        resp.json.return_value = body
    else:
        resp.json.side_effect = Exception("No JSON body")
    return resp


def test_from_response_400() -> None:
    from fi.gateway._exceptions import APIStatusError, BadRequestError

    resp = _make_mock_response(
        400,
        body={"error": {"message": "Invalid model", "type": "invalid_request_error", "code": "invalid_param", "param": "model"}},
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


# --- Guardrail Warning (246) tests ---


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


def test_guardrail_warning_has_completion() -> None:
    """GuardrailWarning is unique: it carries the successful completion."""
    from fi.gateway._exceptions import GuardrailWarning

    completion_body = {"id": "abc", "choices": [{"message": {"content": "response text"}}]}
    exc = GuardrailWarning(
        message="Warned",
        status_code=246,
        completion=completion_body,
    )
    assert exc.completion == completion_body
    assert exc.completion["choices"][0]["message"]["content"] == "response text"


def test_guardrail_warning_is_catchable_as_api_status_error() -> None:
    """GuardrailWarning should be catchable as APIStatusError."""
    from fi.gateway._exceptions import APIStatusError, GuardrailWarning

    exc = GuardrailWarning(message="Warned", status_code=246)
    assert isinstance(exc, APIStatusError)

    # Test catch pattern
    try:
        raise exc
    except APIStatusError as e:
        assert isinstance(e, GuardrailWarning)


def test_guardrail_warning_catch_pattern() -> None:
    """User-facing pattern: catch GuardrailWarning, access .completion."""
    from fi.gateway._exceptions import GuardrailWarning

    completion = {"id": "abc", "choices": [{"message": {"content": "hello"}}]}
    exc = GuardrailWarning(message="Warned", status_code=246, completion=completion)

    try:
        raise exc
    except GuardrailWarning as e:
        assert e.completion is not None
        assert e.completion["id"] == "abc"


# --- Status code map tests ---


def test_status_code_map_completeness() -> None:
    """Verify all expected status codes are mapped."""
    from fi.gateway._exceptions import _STATUS_CODE_MAP

    expected_codes = {400, 401, 403, 404, 422, 429, 446, 500, 502, 503, 504}
    assert set(_STATUS_CODE_MAP.keys()) == expected_codes


def test_status_code_map_correct_classes() -> None:
    from fi.gateway._exceptions import (
        _STATUS_CODE_MAP,
        AuthenticationError,
        BadGatewayError,
        BadRequestError,
        GatewayTimeoutError,
        GuardrailBlockedError,
        InternalServerError,
        NotFoundError,
        PermissionDeniedError,
        RateLimitError,
        ServiceUnavailableError,
        UnprocessableEntityError,
    )

    assert _STATUS_CODE_MAP[400] is BadRequestError
    assert _STATUS_CODE_MAP[401] is AuthenticationError
    assert _STATUS_CODE_MAP[403] is PermissionDeniedError
    assert _STATUS_CODE_MAP[404] is NotFoundError
    assert _STATUS_CODE_MAP[422] is UnprocessableEntityError
    assert _STATUS_CODE_MAP[429] is RateLimitError
    assert _STATUS_CODE_MAP[446] is GuardrailBlockedError
    assert _STATUS_CODE_MAP[500] is InternalServerError
    assert _STATUS_CODE_MAP[502] is BadGatewayError
    assert _STATUS_CODE_MAP[503] is ServiceUnavailableError
    assert _STATUS_CODE_MAP[504] is GatewayTimeoutError


# --- Exception usability tests ---


def test_exceptions_are_catchable() -> None:
    """All exception classes should be raiseable and catchable."""
    from fi.gateway._exceptions import (
        APIConnectionError,
        APITimeoutError,
        AgentCCError,
        StreamError,
    )

    for exc_cls, args, kwargs in [
        (AgentCCError, ("test",), {}),
        (APIConnectionError, ("test",), {}),
        (APITimeoutError, (), {}),
        (StreamError, ("test",), {}),
    ]:
        try:
            raise exc_cls(*args, **kwargs)
        except AgentCCError:
            pass  # All should be caught by AgentCCError


def test_exception_message_preserved_in_args() -> None:
    """Exception .args[0] should be the message (standard Python exception behavior)."""
    from fi.gateway._exceptions import AgentCCError

    exc = AgentCCError("test message")
    assert exc.args[0] == "test message"


def test_api_status_error_body_stored() -> None:
    """The raw response body should be accessible on the exception."""
    from fi.gateway._exceptions import APIStatusError

    body = {"error": {"message": "Bad", "type": "invalid"}}
    exc = APIStatusError(message="Bad", status_code=400, body=body)
    assert exc.body is body
    assert exc.body["error"]["type"] == "invalid"
