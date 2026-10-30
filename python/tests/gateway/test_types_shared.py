"""Tests for agentcc.types.shared — Usage, ErrorBody, ErrorResponse."""

from __future__ import annotations


def test_usage_from_dict() -> None:
    from fi.gateway.types.shared import Usage

    usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30
    assert usage.prompt_tokens_details is None
    assert usage.completion_tokens_details is None


def test_usage_with_details() -> None:
    from fi.gateway.types.shared import Usage

    usage = Usage(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        prompt_tokens_details={"cached_tokens": 5},
        completion_tokens_details={"reasoning_tokens": 10},
    )
    assert usage.prompt_tokens_details == {"cached_tokens": 5}
    assert usage.completion_tokens_details == {"reasoning_tokens": 10}


def test_usage_extra_fields_allowed() -> None:
    """Usage should accept extra fields for forward compatibility."""
    from fi.gateway.types.shared import Usage

    usage = Usage(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        audio_tokens=5,  # type: ignore[call-arg]
    )
    assert usage.prompt_tokens == 10
    # Extra field should be accessible
    dumped = usage.model_dump()
    assert dumped["audio_tokens"] == 5


def test_usage_model_dump() -> None:
    from fi.gateway.types.shared import Usage

    usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    dumped = usage.model_dump()
    assert dumped == {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
        "prompt_tokens_details": None,
        "completion_tokens_details": None,
    }


def test_usage_model_dump_json() -> None:
    import json

    from fi.gateway.types.shared import Usage

    usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    json_str = usage.model_dump_json()
    parsed = json.loads(json_str)
    assert parsed["prompt_tokens"] == 10


def test_error_body_full() -> None:
    from fi.gateway.types.shared import ErrorBody

    body = ErrorBody(
        message="Invalid model",
        type="invalid_request_error",
        code="invalid_param",
        param="model",
    )
    assert body.message == "Invalid model"
    assert body.type == "invalid_request_error"
    assert body.code == "invalid_param"
    assert body.param == "model"


def test_error_body_minimal() -> None:
    from fi.gateway.types.shared import ErrorBody

    body = ErrorBody(message="Something went wrong")
    assert body.message == "Something went wrong"
    assert body.type is None
    assert body.code is None
    assert body.param is None


def test_error_response_parses_standard_gateway_error() -> None:
    from fi.gateway.types.shared import ErrorResponse

    raw = {
        "error": {
            "message": "Model not found",
            "type": "invalid_request_error",
            "code": "model_not_found",
            "param": "model",
        }
    }
    resp = ErrorResponse.model_validate(raw)
    assert resp.error.message == "Model not found"
    assert resp.error.type == "invalid_request_error"
    assert resp.error.code == "model_not_found"


def test_error_response_minimal() -> None:
    from fi.gateway.types.shared import ErrorResponse

    raw = {"error": {"message": "Internal error"}}
    resp = ErrorResponse.model_validate(raw)
    assert resp.error.message == "Internal error"
    assert resp.error.type is None


def test_types_importable_from_init() -> None:
    """Types should be importable from fi.gateway.types."""
    from fi.gateway.types import ErrorBody, ErrorResponse, AgentCCMetadata, RateLimitInfo, Usage

    assert Usage is not None
    assert ErrorBody is not None
    assert ErrorResponse is not None
    assert AgentCCMetadata is not None
    assert RateLimitInfo is not None
