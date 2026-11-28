"""Exception hierarchy, status map and usability."""
from __future__ import annotations
from unittest.mock import MagicMock
from ._exception_fixtures import _make_mock_response


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
    from fi.gateway._exceptions import AgentCCError, APIConnectionError

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
    from fi.gateway._exceptions import AgentCCError, APIConnectionError, APITimeoutError

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
    from fi.gateway._exceptions import AgentCCError, APIStatusError

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
        assert issubclass(
            cls, APIStatusError
        ), f"{cls.__name__} not subclass of APIStatusError"
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


def test_exceptions_are_catchable() -> None:
    """All exception classes should be raiseable and catchable."""
    from fi.gateway._exceptions import (
        AgentCCError,
        APIConnectionError,
        APITimeoutError,
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
