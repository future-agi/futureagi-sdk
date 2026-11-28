"""Guardrail warning completion access and catch patterns."""
from __future__ import annotations
from unittest.mock import MagicMock
from ._exception_fixtures import _make_mock_response


def test_guardrail_warning_has_completion() -> None:
    """GuardrailWarning is unique: it carries the successful completion."""
    from fi.gateway._exceptions import GuardrailWarning

    completion_body = {
        "id": "abc",
        "choices": [{"message": {"content": "response text"}}],
    }
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
