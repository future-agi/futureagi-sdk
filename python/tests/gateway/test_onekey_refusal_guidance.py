"""Canonical refusal categories and corrective actions on the status error API."""

import httpx
import pytest

import fi.gateway as gw
from fi.gateway._retry_policy import _REFUSALS, classify_refusal
from test_onekey_unknown_refusals import invoke, response, settings, sleeps  # noqa: F401

from onekey_contract_oracle import BY_CODE

TOP_UP = BY_CODE["managed_credits_exhausted"]["remedy"]
TOP_UP_OR_SMALLER = BY_CODE["managed_credits_insufficient"]["remedy"]
RAISE_CAP = BY_CODE["agent_budget_exhausted"]["remedy"]
ENABLE_CREDITS = BY_CODE["future_agi_credits_off"]["remedy"]
IN_FLIGHT = {"limit_source": "agentcc_in_flight", "remedy_hint": "retry"}

# status, code, class, category, remedy, retry. All expectations are literal oracles.
ROWS = [
    (402, "managed_credits_exhausted", gw.InsufficientCreditsError, "out_of_credits", TOP_UP, False),
    (402, "managed_credits_insufficient", gw.InsufficientCreditsError,
     "out_of_credits", TOP_UP_OR_SMALLER, False),
    (402, "agent_budget_exhausted", gw.AgentBudgetExhaustedError, "agent_budget", RAISE_CAP, False),
    (429, "budget_exceeded", gw.BudgetExceededError, "budget_limit", BY_CODE["budget_exceeded"]["remedy"], False),
    (429, "org_budget_exceeded", gw.BudgetExceededError, "budget_limit", BY_CODE["org_budget_exceeded"]["remedy"], False),
    (429, "managed_spend_velocity", gw.RateLimitError, "rate_limit", BY_CODE["managed_spend_velocity"]["remedy"], False),
    (429, "rate_limit_exceeded", gw.RateLimitError, "rate_limit", BY_CODE["rate_limit_exceeded"]["remedy"], None),
    (503, "managed_billing_unavailable", gw.ServiceUnavailableError, "billing_unavailable", BY_CODE["managed_billing_unavailable"]["remedy"], None),
    (403, "permission_denied", gw.PermissionDeniedError, "permission", BY_CODE["permission_denied"]["remedy"], False),
    (403, "future_agi_credits_off", gw.FutureAGICreditsOffError, "permission", ENABLE_CREDITS, False),
    (401, "invalid_api_key", gw.AuthenticationError, "invalid_key", BY_CODE["invalid_api_key"]["remedy"], False),
    (403, "key_scope_denied", gw.PermissionDeniedError, "permission", BY_CODE["key_scope_denied"]["remedy"], False),
]


def check_guidance(exc, category, remedy):
    # getattr keeps RED failures assertions, not AttributeError on the base source.
    assert getattr(exc, "category", None) == category
    assert getattr(exc, "remedy", "missing") == remedy
    for name in ("category", "remedy"):
        assert isinstance(getattr(type(exc), name, None), property)
        with pytest.raises(AttributeError):
            setattr(exc, name, "replacement")


@pytest.mark.parametrize("row", ROWS, ids=[row[1] for row in ROWS])
def test_every_explicit_row_has_read_only_guidance(row):
    status, code, cls, category, remedy, retry = row
    exc = gw.APIStatusError.from_response(response(status, {"error": {"code": code}}))
    assert type(exc) is cls
    check_guidance(exc, category, remedy)
    assert classify_refusal(status, code) == (cls, retry)
    assert (status, code) in _REFUSALS


@pytest.mark.parametrize("metadata,remedy,retry", [
    (IN_FLIGHT, TOP_UP_OR_SMALLER, True),
    ({"limit_source": "agentcc_in_flight"}, TOP_UP_OR_SMALLER, False),
    ({"remedy_hint": "retry"}, TOP_UP_OR_SMALLER, False),
    ({"limit_source": "other", "remedy_hint": "retry"}, TOP_UP_OR_SMALLER, False),
    (None, TOP_UP_OR_SMALLER, False),
    ([], TOP_UP_OR_SMALLER, False),
])
def test_in_flight_guidance_uses_both_metadata_fields(metadata, remedy, retry):
    status, code = 402, "managed_credits_insufficient"
    exc = gw.APIStatusError.from_response(
        response(status, {"error": {"code": code, "metadata": metadata}}),
    )
    check_guidance(exc, "out_of_credits", remedy)
    assert classify_refusal(status, code, metadata) == (gw.InsufficientCreditsError, retry)


@pytest.mark.parametrize("status", [246, 400, 401, 402, 403, 404, 418, 422, 429, 446, 500, 502, 503, 504])
@pytest.mark.parametrize("code", ["new_refusal", None, "managed_credits_exhausted"])
def test_status_fallback_guidance_is_generic(status, code):
    if (status, code) in _REFUSALS:
        return
    exc = gw.APIStatusError.from_response(response(status, {"error": {"code": code}}))
    check_guidance(exc, "generic", None)
    assert classify_refusal(status, code)[1] is (None if code is None else False)


REASONS = ["future_agi_api_key", "not_a_gateway_key", "missing_api_key", "unknown_api_key", None]
AUTH_ROWS = [(401, "invalid_api_key", reason) for reason in REASONS] + [(403, "key_scope_denied", None)]


@pytest.fixture
def anyio_backend():
    return "asyncio"


def check_auth(exc, status, code, reason):
    cls = gw.AuthenticationError if status == 401 else gw.PermissionDeniedError
    assert type(exc) is cls
    check_guidance(exc, "invalid_key" if status == 401 else "permission", BY_CODE[code]["remedy"])
    if status == 401:
        assert getattr(exc, "reason", "missing") == reason
    assert (status, code) in _REFUSALS
    assert classify_refusal(status, code, {"reason": reason}) == (cls, False)


@pytest.mark.parametrize("status,code,reason", AUTH_ROWS)
@pytest.mark.parametrize("path", ["json", "binary", "stream"])
def test_authentication_and_scope_refusals_sync(status, code, reason, path, sleeps):
    calls = []

    def handle(request):
        calls.append(request)
        metadata = {} if reason is None else {"reason": reason}
        return response(status, {"error": {"code": code, "metadata": metadata}})

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        with gw.AgentCC(http_client=http, **settings(True)) as client:
            with pytest.raises(gw.APIStatusError) as caught:
                invoke(client, path)
    assert len(calls) == 1 and sleeps == []
    check_auth(caught.value, status, code, reason)


@pytest.mark.parametrize("status,code,reason", AUTH_ROWS)
@pytest.mark.parametrize("path", ["json", "binary", "stream"])
@pytest.mark.anyio
async def test_authentication_and_scope_refusals_async(status, code, reason, path, sleeps):
    calls = []

    def handle(request):
        calls.append(request)
        metadata = {} if reason is None else {"reason": reason}
        return response(status, {"error": {"code": code, "metadata": metadata}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        async with gw.AsyncAgentCC(http_client=http, **settings(True)) as client:
            with pytest.raises(gw.APIStatusError) as caught:
                await invoke(client, path)
    assert len(calls) == 1 and sleeps == []
    check_auth(caught.value, status, code, reason)


@pytest.mark.parametrize("metadata", [None, "bad", [], {}, {"reason": None}])
def test_missing_or_malformed_authentication_reason(metadata):
    exc = gw.APIStatusError.from_response(
        response(401, {"error": {"code": "invalid_api_key", "metadata": metadata}}),
    )
    assert getattr(exc, "reason", "missing") is None
