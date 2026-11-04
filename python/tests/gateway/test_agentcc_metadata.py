"""Tests for agentcc.types.agentcc_metadata — AgentCCMetadata, RateLimitInfo."""

from __future__ import annotations


def _full_headers() -> dict[str, str]:
    """Return a complete set of AgentCC response headers."""
    return {
        "x-agentcc-request-id": "req-abc123",
        "x-agentcc-trace-id": "trace-xyz789",
        "x-agentcc-provider": "openai",
        "x-agentcc-latency-ms": "142",
        "x-agentcc-cost": "0.002500",
        "x-agentcc-cache": "hit_exact",
        "x-agentcc-model-used": "gpt-4o",
        "x-agentcc-guardrail-triggered": "true",
        "x-agentcc-fallback-used": "false",
        "x-agentcc-routing-strategy": "round-robin",
        "x-agentcc-timeout-ms": "30000",
        "x-ratelimit-limit-requests": "100",
        "x-ratelimit-remaining-requests": "95",
        "x-ratelimit-reset-requests": "60",
    }


def test_from_headers_full() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers(_full_headers())
    assert meta.request_id == "req-abc123"
    assert meta.trace_id == "trace-xyz789"
    assert meta.provider == "openai"
    assert meta.latency_ms == 142
    assert meta.cost == 0.0025
    assert meta.cache_status == "hit_exact"
    assert meta.model_used == "gpt-4o"
    assert meta.guardrail_triggered is True
    assert meta.fallback_used is False
    assert meta.routing_strategy == "round-robin"
    assert meta.timeout_ms == 30000
    assert meta.ratelimit is not None
    assert meta.ratelimit.limit == 100
    assert meta.ratelimit.remaining == 95
    assert meta.ratelimit.reset == 60


def test_from_headers_minimal() -> None:
    """Minimal headers — defaults used for missing required fields."""
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({})
    assert meta.request_id == "unknown"
    assert meta.trace_id == "unknown"
    assert meta.provider == "unknown"
    assert meta.latency_ms == 0
    assert meta.cost is None
    assert meta.cache_status is None
    assert meta.model_used is None
    assert meta.guardrail_triggered is False
    assert meta.fallback_used is False
    assert meta.routing_strategy is None
    assert meta.timeout_ms is None
    assert meta.ratelimit is None


def test_cost_parsed_from_string() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({"x-agentcc-cost": "0.002500"})
    assert meta.cost == 0.0025


def test_cost_invalid_string() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({"x-agentcc-cost": "not-a-number"})
    assert meta.cost is None


def test_guardrail_triggered_true() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({"x-agentcc-guardrail-triggered": "true"})
    assert meta.guardrail_triggered is True


def test_guardrail_triggered_false() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({"x-agentcc-guardrail-triggered": "false"})
    assert meta.guardrail_triggered is False


def test_guardrail_triggered_case_insensitive() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({"x-agentcc-guardrail-triggered": "True"})
    assert meta.guardrail_triggered is True


def test_guardrail_triggered_absent() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({})
    assert meta.guardrail_triggered is False


def test_fallback_used_true() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({"x-agentcc-fallback-used": "true"})
    assert meta.fallback_used is True


def test_ratelimit_none_when_no_headers() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({"x-agentcc-request-id": "req-1"})
    assert meta.ratelimit is None


def test_ratelimit_partial_headers() -> None:
    """Even one ratelimit header should create the RateLimitInfo."""
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({"x-ratelimit-limit-requests": "50"})
    assert meta.ratelimit is not None
    assert meta.ratelimit.limit == 50
    assert meta.ratelimit.remaining is None
    assert meta.ratelimit.reset is None


def test_http_response_excluded_from_dump() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    mock_response = object()
    meta = AgentCCMetadata.from_headers(_full_headers(), http_response=mock_response)
    assert meta.http_response is mock_response

    dumped = meta.model_dump()
    assert "http_response" not in dumped


def test_http_response_excluded_from_json() -> None:
    import json

    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers(_full_headers(), http_response="should-not-appear")
    json_str = meta.model_dump_json()
    parsed = json.loads(json_str)
    assert "http_response" not in parsed


def test_round_trip() -> None:
    """Construct → dump → construct again → equal."""
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers(_full_headers())
    dumped = meta.model_dump()
    meta2 = AgentCCMetadata.model_validate(dumped)
    assert meta2.request_id == meta.request_id
    assert meta2.trace_id == meta.trace_id
    assert meta2.provider == meta.provider
    assert meta2.latency_ms == meta.latency_ms
    assert meta2.cost == meta.cost
    assert meta2.cache_status == meta.cache_status
    assert meta2.model_used == meta.model_used
    assert meta2.guardrail_triggered == meta.guardrail_triggered
    assert meta2.fallback_used == meta.fallback_used
    assert meta2.routing_strategy == meta.routing_strategy
    assert meta2.timeout_ms == meta.timeout_ms
    assert meta2.ratelimit == meta.ratelimit


def test_latency_ms_invalid_string() -> None:
    from fi.gateway.types.agentcc_metadata import AgentCCMetadata

    meta = AgentCCMetadata.from_headers({"x-agentcc-latency-ms": "not-a-number"})
    assert meta.latency_ms == 0


def test_ratelimit_info_standalone() -> None:
    from fi.gateway.types.agentcc_metadata import RateLimitInfo

    rl = RateLimitInfo(limit=100, remaining=50, reset=30)
    assert rl.limit == 100
    assert rl.remaining == 50
    assert rl.reset == 30


def test_ratelimit_info_defaults() -> None:
    from fi.gateway.types.agentcc_metadata import RateLimitInfo

    rl = RateLimitInfo()
    assert rl.limit is None
    assert rl.remaining is None
    assert rl.reset is None
