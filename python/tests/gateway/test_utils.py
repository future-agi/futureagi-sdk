"""Tests for agentcc._utils — parse_timeout, redact_headers, serialize_agentcc_param."""

from __future__ import annotations

import json


def test_parse_timeout_float() -> None:
    from fi.gateway._utils import parse_timeout

    t = parse_timeout(30.0)
    assert t.connect == 30.0
    assert t.read == 30.0


def test_parse_timeout_int() -> None:
    from fi.gateway._utils import parse_timeout

    t = parse_timeout(60)
    assert t.connect == 60.0


def test_parse_timeout_none_uses_default() -> None:
    from fi.gateway._constants import DEFAULT_TIMEOUT
    from fi.gateway._utils import parse_timeout

    t = parse_timeout(None)
    assert t.connect == DEFAULT_TIMEOUT


def test_parse_timeout_dataclass() -> None:
    from fi.gateway._base_client import Timeout
    from fi.gateway._utils import parse_timeout

    t = parse_timeout(Timeout(connect=5.0, read=30.0, write=10.0, pool=2.0))
    assert t.connect == 5.0
    assert t.read == 30.0
    assert t.write == 10.0
    assert t.pool == 2.0


def test_redact_headers_authorization() -> None:
    from fi.gateway._utils import redact_headers

    headers = {"Authorization": "Bearer sk-abc123xyz789", "Content-Type": "application/json"}
    result = redact_headers(headers)
    assert result["Authorization"] == "Bearer sk-...z789"
    assert result["Content-Type"] == "application/json"


def test_redact_headers_short_auth() -> None:
    from fi.gateway._utils import redact_headers

    headers = {"Authorization": "short"}
    result = redact_headers(headers)
    assert result["Authorization"] == "***"


def test_redact_headers_case_insensitive() -> None:
    from fi.gateway._utils import redact_headers

    headers = {"authorization": "Bearer sk-abc123xyz789"}
    result = redact_headers(headers)
    assert "..." in result["authorization"]


def test_redact_headers_no_auth() -> None:
    from fi.gateway._utils import redact_headers

    headers = {"Content-Type": "application/json", "x-agentcc-trace-id": "abc"}
    result = redact_headers(headers)
    assert result == headers


def test_serialize_request_metadata() -> None:
    from fi.gateway._utils import serialize_agentcc_param

    meta = {"user": "test", "session": 123}
    result = serialize_agentcc_param("request_metadata", meta)
    parsed = json.loads(result)
    assert parsed == meta


def test_serialize_cache_force_refresh_true() -> None:
    from fi.gateway._utils import serialize_agentcc_param

    assert serialize_agentcc_param("cache_force_refresh", True) == "true"


def test_serialize_cache_force_refresh_false() -> None:
    from fi.gateway._utils import serialize_agentcc_param

    assert serialize_agentcc_param("cache_force_refresh", False) == "false"


def test_serialize_generic_param() -> None:
    from fi.gateway._utils import serialize_agentcc_param

    assert serialize_agentcc_param("session_id", "abc-123") == "abc-123"
    assert serialize_agentcc_param("cache_ttl", "10m") == "10m"
    assert serialize_agentcc_param("request_timeout", 30) == "30"
