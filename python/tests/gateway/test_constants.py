"""Tests for agentcc._constants — version, defaults, headers, sentinel."""

from __future__ import annotations

import copy


def test_version_format() -> None:
    """Version string follows semver."""
    from fi.gateway._constants import __version__

    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_default_timeout() -> None:
    from fi.gateway._constants import DEFAULT_TIMEOUT

    assert DEFAULT_TIMEOUT == 600.0
    assert isinstance(DEFAULT_TIMEOUT, float)


def test_default_max_retries() -> None:
    from fi.gateway._constants import DEFAULT_MAX_RETRIES

    assert DEFAULT_MAX_RETRIES == 2
    assert isinstance(DEFAULT_MAX_RETRIES, int)


def test_default_connection_pool() -> None:
    from fi.gateway._constants import (
        DEFAULT_KEEPALIVE_CONNECTIONS,
        DEFAULT_KEEPALIVE_EXPIRY,
        DEFAULT_MAX_CONNECTIONS,
    )

    assert DEFAULT_MAX_CONNECTIONS == 100
    assert DEFAULT_KEEPALIVE_CONNECTIONS == 20
    assert DEFAULT_KEEPALIVE_EXPIRY == 5.0


def test_request_headers_are_strings() -> None:
    """All header constants should be non-empty strings."""
    from fi.gateway import _constants

    header_names = [
        attr for attr in dir(_constants)
        if attr.startswith("HEADER_") and not attr.startswith("HEADER_RESPONSE_") and not attr.startswith("HEADER_RATELIMIT_")
    ]
    assert len(header_names) > 0
    for name in header_names:
        val = getattr(_constants, name)
        assert isinstance(val, str), f"{name} is not a str"
        assert len(val) > 0, f"{name} is empty"


def test_response_headers_are_strings() -> None:
    from fi.gateway import _constants

    header_names = [
        attr for attr in dir(_constants)
        if attr.startswith("HEADER_RESPONSE_") or attr.startswith("HEADER_RATELIMIT_")
    ]
    assert len(header_names) > 0
    for name in header_names:
        val = getattr(_constants, name)
        assert isinstance(val, str), f"{name} is not a str"


def test_agentcc_param_to_header_mapping() -> None:
    from fi.gateway._constants import AGENTCC_PARAM_TO_HEADER

    assert isinstance(AGENTCC_PARAM_TO_HEADER, dict)
    assert len(AGENTCC_PARAM_TO_HEADER) > 0

    for param, header in AGENTCC_PARAM_TO_HEADER.items():
        assert isinstance(param, str)
        assert isinstance(header, str)
        # All headers should be lowercase x-agentcc-* or standard
        assert header[0].islower() or header[0].isupper()


def test_agentcc_param_keys() -> None:
    """Verify known param keys exist in the mapping."""
    from fi.gateway._constants import AGENTCC_PARAM_TO_HEADER

    expected_keys = {
        "session_id", "trace_id", "request_metadata", "request_timeout",
        "cache_ttl", "cache_namespace", "cache_force_refresh", "cache_control",
        "guardrail_policy",
    }
    assert set(AGENTCC_PARAM_TO_HEADER.keys()) == expected_keys


def test_retryable_status_codes() -> None:
    from fi.gateway._constants import RETRYABLE_STATUS_CODES

    assert isinstance(RETRYABLE_STATUS_CODES, set)
    expected = {408, 429, 500, 502, 503, 504}
    assert expected == RETRYABLE_STATUS_CODES


def test_retryable_codes_exclude_client_errors() -> None:
    """Normal client errors (400, 401, etc.) should NOT be retryable."""
    from fi.gateway._constants import RETRYABLE_STATUS_CODES

    for code in (400, 401, 403, 404, 422, 446):
        assert code not in RETRYABLE_STATUS_CODES


# --- NOT_GIVEN sentinel tests ---


def test_not_given_is_falsy() -> None:
    from fi.gateway._constants import NOT_GIVEN

    assert not NOT_GIVEN
    assert bool(NOT_GIVEN) is False


def test_not_given_is_not_none() -> None:
    from fi.gateway._constants import NOT_GIVEN

    assert NOT_GIVEN is not None
    assert NOT_GIVEN != None  # noqa: E711


def test_not_given_repr() -> None:
    from fi.gateway._constants import NOT_GIVEN

    assert repr(NOT_GIVEN) == "NOT_GIVEN"
    assert str(NOT_GIVEN) == "NOT_GIVEN"


def test_not_given_singleton() -> None:
    """All references to NOT_GIVEN should be the exact same object."""
    from fi.gateway._constants import NOT_GIVEN, _NotGiven

    assert NOT_GIVEN is _NotGiven()
    assert _NotGiven() is _NotGiven()


def test_not_given_copy_is_same() -> None:
    """Copy/deepcopy of NOT_GIVEN should still work (not crash)."""
    from fi.gateway._constants import NOT_GIVEN

    # Shallow copy should work
    copied = copy.copy(NOT_GIVEN)
    assert not copied
    assert repr(copied) == "NOT_GIVEN"


def test_not_given_usable_in_conditions() -> None:
    """NOT_GIVEN should work in 'if param is NOT_GIVEN' patterns."""
    from fi.gateway._constants import NOT_GIVEN

    param = NOT_GIVEN
    assert param is NOT_GIVEN

    # Setting to None is distinct from NOT_GIVEN
    param2 = None
    assert param2 is not NOT_GIVEN


def test_not_given_in_dict_default() -> None:
    """Common pattern: dict.get(key, NOT_GIVEN) to detect missing keys."""
    from fi.gateway._constants import NOT_GIVEN

    d: dict[str, str] = {"a": "hello"}
    result = d.get("b", NOT_GIVEN)
    assert result is NOT_GIVEN
    result2 = d.get("a", NOT_GIVEN)
    assert result2 is not NOT_GIVEN
    assert result2 == "hello"
