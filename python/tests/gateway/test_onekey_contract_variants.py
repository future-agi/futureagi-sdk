"""Retry predicates, positive headers, caller budgets and metadata variants."""

import httpx
import pytest
import fi.gateway as gw
from fi.gateway._retry_policy import RetryPolicy
from fi.gateway._transport._base import BaseClient, RequestOptions, RetryConfig
from onekey_contract_oracle import (
    ROWS, BY_CODE, AFTER, BACKOFF, sample, response, check_error, expected_attempts,
)
from test_onekey_unknown_refusals import invoke, settings, sleeps  # noqa: F401

VARIANTS = [
    (row, variant) for row in ROWS for variant in row.get("variants", [])
]


@pytest.fixture
def anyio_backend():
    return "asyncio"


def evaluate(row, metadata, header, *, policy=None, maximum=5):
    exc = gw.APIStatusError.from_response(response(row, metadata, header))
    client = BaseClient(
        api_key="unit-placeholder", base_url="https://gateway.example.test",
        max_retries=maximum, retry_policy=policy,
        retry_config=RetryConfig(backoff_factor=0.25, backoff_jitter=0, backoff_max=8),
    )
    delays = [client._retry_delay(RequestOptions("POST", "/v1/test"), exc, n, maximum) for n in range(6)]
    return exc, delays


@pytest.mark.parametrize("row,variant", VARIANTS, ids=[v["when"] for _, v in VARIANTS])
@pytest.mark.parametrize("path", ["json", "binary", "stream"])
def test_documented_variant_sync(row, variant, path, sleeps):
    metadata = sample(variant["error"]["metadata"])
    calls = []

    def handle(request):
        calls.append(request)
        return response({**row, "type": variant.get("type", row["type"])}, metadata)

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        with gw.AgentCC(http_client=http, **settings(True)) as client:
            with pytest.raises(gw.APIStatusError) as caught:
                invoke(client, path)
    check_error(caught.value, row, metadata)
    attempts = 1 if path == "stream" else expected_attempts(row, metadata)
    assert len(calls) == attempts
    assert sleeps == [2.0] * (attempts - 1)


@pytest.mark.parametrize("row,variant", VARIANTS, ids=[v["when"] for _, v in VARIANTS])
@pytest.mark.parametrize("path", ["json", "binary", "stream"])
@pytest.mark.anyio
async def test_documented_variant_async(row, variant, path, sleeps):
    metadata = sample(variant["error"]["metadata"])
    calls = []

    def handle(request):
        calls.append(request)
        return response({**row, "type": variant.get("type", row["type"])}, metadata)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        async with gw.AsyncAgentCC(http_client=http, **settings(True)) as client:
            with pytest.raises(gw.APIStatusError) as caught:
                await invoke(client, path)
    check_error(caught.value, row, metadata)
    attempts = 1 if path == "stream" else expected_attempts(row, metadata)
    assert len(calls) == attempts
    assert sleeps == [2.0] * (attempts - 1)


HEADER_ROWS = sorted(AFTER | {"managed_spend_velocity", "managed_credits_insufficient"})


def retry_metadata(code):
    if code == "managed_spend_velocity":
        return {"remedy_hint": "retry"}
    if code == "managed_credits_insufficient":
        return {"limit_source": "agentcc_in_flight", "remedy_hint": "retry"}
    return None


@pytest.mark.parametrize("code", HEADER_ROWS)
@pytest.mark.parametrize("header", [None, "", "0", "-1", "nan", "inf", "bad", "2", "30"])
def test_after_only_requires_positive_finite_header_and_does_not_shorten_it(code, header):
    exc, delays = evaluate(BY_CODE[code], retry_metadata(code), header)
    if header not in ("2", "30"):
        assert delays == [None] * 6
    else:
        limit = 1 if code == "managed_credits_insufficient" else 5
        assert delays == [float(header)] * limit + [None] * (6 - limit)
    assert exc.remedy == BY_CODE[code]["remedy"]


@pytest.mark.parametrize("reason", [
    "request_exceeds_minute_cap", "request_exceeds_hour_cap", "new_org_daily_cap", "unknown_variant",
])
@pytest.mark.parametrize("hint", [None, "retry", "lower_max_tokens"])
def test_nonwindow_spend_variants_never_retry_even_with_misleading_header(reason, hint):
    _, delays = evaluate(BY_CODE["managed_spend_velocity"], {"reason": reason, "remedy_hint": hint}, "2")
    assert delays == [None] * 6


@pytest.mark.parametrize("metadata", [None, {}, [], "bad", {"remedy_hint": "lower_max_tokens"}])
def test_unspecified_spend_variant_never_retries(metadata):
    _, delays = evaluate(BY_CODE["managed_spend_velocity"], metadata, "2")
    assert delays == [None] * 6


@pytest.mark.parametrize("code", sorted(BACKOFF))
@pytest.mark.parametrize("header", [None, "2", "30"])
def test_bounded_backoff_honors_positive_retry_after(code, header):
    _, delays = evaluate(BY_CODE[code], None, header)
    assert delays == ([float(header)] * 5 if header else [0.25, 0.5, 1, 2, 4]) + [None]


@pytest.mark.parametrize("code", HEADER_ROWS + sorted(BACKOFF))
@pytest.mark.parametrize("limit", [0, 1, 3])
@pytest.mark.parametrize("with_policy", [False, True])
def test_retry_limits_follow_status_and_409_uses_429_budget(code, limit, with_policy):
    metadata = retry_metadata(code)
    if code == "budget_state_unavailable":
        metadata = {"reason": "redis_unavailable", "remedy_hint": "retry"}
    status = BY_CODE[code]["status"]
    policy = None
    if with_policy:
        policy = RetryPolicy(RateLimitErrorRetries=0, ServiceUnavailableRetries=0)
        if status in (402, 409, 429):
            policy.RateLimitErrorRetries = limit
        elif status == 503:
            policy.ServiceUnavailableRetries = limit
    _, delays = evaluate(BY_CODE[code], metadata, "2", policy=policy, maximum=5 if with_policy else limit)
    count = min(1, limit) if code == "managed_credits_insufficient" else limit
    assert delays == [2.0] * count + [None] * (6 - count)


@pytest.mark.parametrize("metadata", [
    None, {}, {"reason": "missing_activation"}, {"reason": "stale_policy", "remedy_hint": "retry"},
    {"remedy_hint": "contact_admin"}, {"reason": "other", "remedy_hint": "retry"},
])
def test_budget_state_does_not_invent_an_undocumented_persistence_discriminator(metadata):
    # Every documented producer permits bounded backoff; r2 has no stable
    # persistent/transient wire flag. Caller limits bound persistent failures.
    _, delays = evaluate(BY_CODE["budget_state_unavailable"], metadata, "2")
    assert delays == [2.0] * 5 + [None]


@pytest.mark.parametrize("status,body,expected", [
    (503, {"error": {"code": "new_code"}}, False),
    (503, {"error": {"code": "rate_limit_exceeded"}}, False),
    (504, {"error": {"code": "gateway_timeout"}}, False),
    (504, {"error": {}}, True),
    (429, {"code": "quota_exceeded"}, True),
    (503, {"code": "provider_busy"}, True),
    (429, {"code": "budget_exceeded"}, False),
])
def test_unknown_and_flat_nongateway_codes_keep_distinct_retry_rules(status, body, expected):
    exc = gw.APIStatusError.from_response(httpx.Response(status, json=body, headers={"Retry-After": "2"}))
    client = BaseClient(api_key="unit-placeholder", base_url="https://gateway.example.test")
    delay = client._retry_delay(RequestOptions("POST", "/v1/test"), exc, 0, 5)
    assert (delay is not None) is expected
