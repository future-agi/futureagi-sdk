"""Billing and budget refusals from the gateway: typed errors and retry behaviour.

The gateway refuses a request it will not bill with the usual error body,
``{"error": {"message", "type", "code", "metadata": {...}}}``, and may send a
``Retry-After`` header. The SDK classifies on ``error.code``, never on
``error.type``: a 429 budget refusal and a 429 rate limit share the type
``rate_limit_error``.

=======  ============================  =========================  ==========================
status   error.code                    raises                     retried
=======  ============================  =========================  ==========================
402      managed_credits_exhausted     InsufficientCreditsError   never
402      managed_credits_insufficient  InsufficientCreditsError   only in flight (below)
402      agent_budget_exhausted        AgentBudgetExhaustedError  never
429      budget_exceeded               BudgetExceededError        never
429      org_budget_exceeded           BudgetExceededError        never
429      managed_spend_velocity        RateLimitError             yes, after Retry-After
429      rate_limit_exceeded           RateLimitError             yes, as before
503      managed_billing_unavailable   ServiceUnavailableError    yes, as before
403      permission_denied             PermissionDeniedError      never, as before
403      future_agi_credits_off        FutureAGICreditsOffError    never
=======  ============================  =========================  ==========================

In flight means ``metadata.limit_source == "agentcc_in_flight"`` and
``metadata.remedy_hint == "retry"``; such a refusal is retried within the
configured retries, at most once, after ``Retry-After``
(test_onekey_in_flight_retry_once.py). BudgetExceededError is a
RateLimitError, so an existing ``except RateLimitError`` still catches it.
Every test here is offline (respx); sleeps are recorded, not slept.
"""

from __future__ import annotations

import pickle
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
import respx

import fi.gateway as gw
from fi.gateway._retry_policy import RetryPolicy
from fi.gateway._transport import _async as async_transport
from fi.gateway._transport import _sync as sync_transport

BASE = "https://gateway.test"
URL = f"{BASE}/v1/chat/completions"
KEY = "sk-agentcc-TEST"
MODEL = "openai/gpt-4o-mini"
MESSAGES = [{"role": "user", "content": "Hi"}]
COMPLETION = {
    "id": "chatcmpl-onekey",
    "object": "chat.completion",
    "created": 1761177600,
    "model": MODEL,
    "choices": [
        {"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}
    ],
    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
}
IN_FLIGHT = {"limit_source": "agentcc_in_flight", "remedy_hint": "retry", "required_usd": 0.02}
OTHER = {"limit_source": "example_source", "remedy_hint": "example_hint"}
FIELDS = ("required_usd", "available_usd", "limit_source", "remedy_hint", "scope", "resets_at", "reason")
NEW = {"InsufficientCreditsError", "AgentBudgetExhaustedError", "BudgetExceededError"}

# (id, status, error.type, error.code, error.metadata, class name, attempts at max_retries=2)
ROWS = [
    ("402-credits-exhausted", 402, "payment_required", "managed_credits_exhausted", OTHER,
     "InsufficientCreditsError", 1),
    ("402-credits-insufficient", 402, "payment_required", "managed_credits_insufficient", OTHER,
     "InsufficientCreditsError", 1),
    ("402-in-flight-without-retry-hint", 402, "payment_required", "managed_credits_insufficient",
     {"limit_source": "agentcc_in_flight", "remedy_hint": "example_hint"}, "InsufficientCreditsError", 1),
    ("402-retry-hint-not-in-flight", 402, "payment_required", "managed_credits_insufficient",
     {"limit_source": "example_source", "remedy_hint": "retry"}, "InsufficientCreditsError", 1),
    ("402-in-flight", 402, "payment_required", "managed_credits_insufficient", IN_FLIGHT,
     "InsufficientCreditsError", 2),
    ("402-agent-budget", 402, None, "agent_budget_exhausted", {"scope": "agent"},
     "AgentBudgetExhaustedError", 1),
    ("429-budget", 429, "rate_limit_error", "budget_exceeded", {"scope": "key"}, "BudgetExceededError", 1),
    ("429-org-budget", 429, "rate_limit_error", "org_budget_exceeded", {"scope": "org"},
     "BudgetExceededError", 1),
    ("429-spend-velocity", 429, "rate_limit_error", "managed_spend_velocity",
     {"remedy_hint": "retry"}, "RateLimitError", 3),
    ("429-rate-limit", 429, "rate_limit_error", "rate_limit_exceeded", None, "RateLimitError", 3),
    ("503-billing-unavailable", 503, None, "managed_billing_unavailable", None, "ServiceUnavailableError", 3),
    ("403-unpriced-model", 403, None, "permission_denied", None, "PermissionDeniedError", 1),
    ("403-credits-off", 403, "permission", "future_agi_credits_off", None,
     "FutureAGICreditsOffError", 1),
]
IDS = [row[0] for row in ROWS]
TYPED = [row for row in ROWS if row[5] in NEW]


def _refusal(
    status: int, type_: str | None, code: str | None, metadata: Any = None, **headers: str
) -> httpx.Response:
    error: dict[str, Any] = {"message": f"refused ({code})", "code": code}
    if type_ is not None:
        error["type"] = type_
    if metadata is not None:
        error["metadata"] = metadata
    return httpx.Response(
        status,
        json={"error": error},
        headers={"retry-after": "2", "x-agentcc-request-id": "req-refused", **headers},
    )


def _replies(*responses: httpx.Response) -> Any:
    """A respx side effect: the given replies in order, then the last one again."""
    queue = list(responses)

    def reply(request: httpx.Request) -> httpx.Response:
        out = queue.pop(0) if len(queue) > 1 else queue[0]
        return httpx.Response(out.status_code, headers=out.headers, content=out.content)

    return reply


def _check(exc: BaseException, row: tuple) -> None:
    _, status, type_, code, metadata, name, _ = row
    assert type(exc) is getattr(gw, name)
    assert (exc.status_code, exc.type, exc.code) == (status, type_, code)
    assert exc.request_id == "req-refused"
    if name in NEW:
        assert exc.metadata == (metadata or {})


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    slept: list[float] = []

    async def asleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr(sync_transport, "time", SimpleNamespace(sleep=slept.append))
    monkeypatch.setattr(async_transport, "anyio", SimpleNamespace(sleep=asleep))
    return slept


# --- every contract row, through the public client --------------------------------


@pytest.mark.parametrize("row", ROWS, ids=IDS)
def test_each_refusal_raises_its_class_and_retries_by_the_contract_sync(row, sleeps) -> None:
    _, status, type_, code, metadata, _, attempts = row
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_replies(_refusal(status, type_, code, metadata)))
        with gw.AgentCC(api_key=KEY, base_url=BASE) as client:
            with pytest.raises(gw.APIStatusError) as info:
                client.chat.completions.create(model=MODEL, messages=MESSAGES)
    _check(info.value, row)
    assert route.call_count == attempts
    assert sleeps == [2.0] * (attempts - 1)


@pytest.mark.parametrize("row", ROWS, ids=IDS)
@pytest.mark.anyio
async def test_each_refusal_raises_its_class_and_retries_by_the_contract_async(row, sleeps) -> None:
    _, status, type_, code, metadata, _, attempts = row
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_replies(_refusal(status, type_, code, metadata)))
        async with gw.AsyncAgentCC(api_key=KEY, base_url=BASE) as client:
            with pytest.raises(gw.APIStatusError) as info:
                await client.chat.completions.create(model=MODEL, messages=MESSAGES)
    _check(info.value, row)
    assert route.call_count == attempts
    assert sleeps == [2.0] * (attempts - 1)


# --- the in-flight refusal: retried after Retry-After, within the configured retries ---


def test_an_in_flight_refusal_is_retried_once_then_succeeds_sync(sleeps) -> None:
    first = _refusal(402, "payment_required", "managed_credits_insufficient", IN_FLIGHT)
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_replies(first, httpx.Response(200, json=COMPLETION)))
        with gw.AgentCC(api_key=KEY, base_url=BASE) as client:
            result = client.chat.completions.create(model=MODEL, messages=MESSAGES)
    assert result.id == COMPLETION["id"]
    assert route.call_count == 2 and sleeps == [2.0]


@pytest.mark.anyio
async def test_an_in_flight_refusal_is_retried_once_then_succeeds_async(sleeps) -> None:
    first = _refusal(402, "payment_required", "managed_credits_insufficient", IN_FLIGHT)
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_replies(first, httpx.Response(200, json=COMPLETION)))
        async with gw.AsyncAgentCC(api_key=KEY, base_url=BASE) as client:
            result = await client.chat.completions.create(model=MODEL, messages=MESSAGES)
    assert result.id == COMPLETION["id"]
    assert route.call_count == 2 and sleeps == [2.0]


# --- budget refusals: never retried, still caught as RateLimitError --------------------


@pytest.mark.parametrize("code", ["budget_exceeded", "org_budget_exceeded"])
def test_a_budget_refusal_is_not_retried_under_a_generous_retry_policy(code, sleeps) -> None:
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_replies(_refusal(429, "rate_limit_error", code)))
        policy = RetryPolicy(RateLimitErrorRetries=5)
        with gw.AgentCC(api_key=KEY, base_url=BASE, retry_policy=policy) as client:
            with pytest.raises(gw.BudgetExceededError):
                client.chat.completions.create(model=MODEL, messages=MESSAGES)
    assert route.call_count == 1 and sleeps == []


def test_an_existing_rate_limit_handler_still_catches_a_budget_refusal(sleeps) -> None:
    refusal = _refusal(
        429, "rate_limit_error", "budget_exceeded", {"scope": "key"},
        **{"x-ratelimit-limit-requests": "100", "x-ratelimit-remaining-requests": "0"},
    )
    caught = None
    with respx.mock() as mock:
        mock.post(URL).mock(side_effect=_replies(refusal))
        with gw.AgentCC(api_key=KEY, base_url=BASE) as client:
            try:
                client.chat.completions.create(model=MODEL, messages=MESSAGES)
            except gw.RateLimitError as exc:
                caught = exc
    assert isinstance(caught, gw.BudgetExceededError)
    assert (caught.ratelimit_limit, caught.ratelimit_remaining) == (100, 0)
    assert caught.scope == "key"


# --- a stream is refused before it starts -----------------------------------------------

STREAM_REFUSALS = [
    (402, "payment_required", "managed_credits_exhausted", "InsufficientCreditsError"),
    (402, None, "agent_budget_exhausted", "AgentBudgetExhaustedError"),
    (429, "rate_limit_error", "budget_exceeded", "BudgetExceededError"),
]


@pytest.mark.parametrize("refusal", STREAM_REFUSALS, ids=lambda r: r[2])
def test_a_stream_is_refused_before_any_chunk_sync(refusal, sleeps) -> None:
    status, type_, code, name = refusal
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_replies(_refusal(status, type_, code, OTHER)))
        with gw.AgentCC(api_key=KEY, base_url=BASE) as client:
            with pytest.raises(gw.APIStatusError) as info:
                client.chat.completions.create(model=MODEL, messages=MESSAGES, stream=True)
    assert type(info.value) is getattr(gw, name) and info.value.metadata == OTHER
    assert route.call_count == 1


@pytest.mark.parametrize("refusal", STREAM_REFUSALS, ids=lambda r: r[2])
@pytest.mark.anyio
async def test_a_stream_is_refused_before_any_chunk_async(refusal, sleeps) -> None:
    status, type_, code, name = refusal
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_replies(_refusal(status, type_, code, OTHER)))
        async with gw.AsyncAgentCC(api_key=KEY, base_url=BASE) as client:
            with pytest.raises(gw.APIStatusError) as info:
                await client.chat.completions.create(model=MODEL, messages=MESSAGES, stream=True)
    assert type(info.value) is getattr(gw, name) and info.value.metadata == OTHER
    assert route.call_count == 1


# --- metadata, pickling, exports ---------------------------------------------------------


def test_the_metadata_and_its_fields_are_exposed() -> None:
    metadata = {
        "limit_source": "agentcc_in_flight", "remedy_hint": "retry", "required_usd": 0.02,
        "available_usd": 0.0, "scope": "org", "resets_at": "2026-12-01T00:00:00Z",
        "reason": "example reason", "extra": {"kept": True},
    }
    exc = gw.APIStatusError.from_response(
        _refusal(402, "payment_required", "managed_credits_insufficient", metadata)
    )
    assert isinstance(exc, gw.InsufficientCreditsError)
    assert exc.metadata == metadata
    assert tuple(getattr(exc, f) for f in FIELDS) == tuple(metadata[f] for f in FIELDS)


@pytest.mark.parametrize("metadata", [None, "not an object", ["a", "list"], {}])
def test_missing_or_malformed_metadata_reads_as_empty(metadata) -> None:
    exc = gw.APIStatusError.from_response(_refusal(429, "rate_limit_error", "budget_exceeded", metadata))
    assert isinstance(exc, gw.BudgetExceededError)
    assert exc.metadata == {}
    assert all(getattr(exc, f) is None for f in FIELDS)


@pytest.mark.parametrize("row", TYPED, ids=[row[0] for row in TYPED])
def test_a_typed_refusal_survives_a_pickle_round_trip(row) -> None:
    _, status, type_, code, metadata, name, _ = row
    exc = gw.APIStatusError.from_response(
        _refusal(status, type_, code, metadata, **{"x-ratelimit-limit-requests": "7"})
    )
    back = pickle.loads(pickle.dumps(exc))
    assert type(back) is type(exc) is getattr(gw, name)
    assert (str(back), repr(back), back.args) == (str(exc), repr(exc), exc.args)
    for attr in ("message", "status_code", "type", "code", "param", "body", "request_id", "metadata"):
        assert getattr(back, attr) == getattr(exc, attr), attr
    assert back.response is None and exc.response is not None
    if isinstance(exc, gw.RateLimitError):
        assert back.ratelimit_limit == exc.ratelimit_limit == 7


def test_the_typed_refusals_are_importable_from_fi_gateway() -> None:
    from fi.gateway import AgentBudgetExhaustedError, BudgetExceededError, InsufficientCreditsError
    from fi.gateway import _exceptions

    assert InsufficientCreditsError is _exceptions.InsufficientCreditsError
    assert AgentBudgetExhaustedError is _exceptions.AgentBudgetExhaustedError
    assert BudgetExceededError is _exceptions.BudgetExceededError
    assert issubclass(BudgetExceededError, gw.RateLimitError)
    for cls in (InsufficientCreditsError, AgentBudgetExhaustedError):
        assert issubclass(cls, gw.APIStatusError) and not issubclass(cls, gw.RateLimitError)
    for cls in (InsufficientCreditsError, AgentBudgetExhaustedError, BudgetExceededError):
        assert issubclass(cls, gw.AgentCCError)


# --- backward compatibility and the single decision point --------------------------------


def test_an_unlisted_402_code_keeps_the_generic_error_and_is_not_retried(sleeps) -> None:
    with respx.mock() as mock:
        route = mock.post(URL).mock(side_effect=_replies(_refusal(402, "payment_required", "other_code")))
        with gw.AgentCC(api_key=KEY, base_url=BASE) as client:
            with pytest.raises(gw.APIStatusError) as info:
                client.chat.completions.create(model=MODEL, messages=MESSAGES)
    assert type(info.value) is gw.APIStatusError and info.value.status_code == 402
    assert route.call_count == 1


def test_the_class_follows_the_code_not_the_type() -> None:
    def raised(status: int, type_: str | None, code: str | None) -> type:
        return type(gw.APIStatusError.from_response(_refusal(status, type_, code)))

    assert raised(429, "rate_limit_error", "rate_limit_exceeded") is gw.RateLimitError
    assert raised(429, "budget_exceeded", "rate_limit_exceeded") is gw.RateLimitError
    assert raised(429, "rate_limit_error", "budget_exceeded") is gw.BudgetExceededError
    assert raised(429, None, None) is gw.RateLimitError
    assert raised(402, "payment_required", None) is gw.APIStatusError
    assert raised(403, None, "permission_denied") is gw.PermissionDeniedError


def test_one_function_holds_every_class_and_retry_decision() -> None:
    from fi.gateway._retry_policy import classify_refusal

    expected = {
        (402, "managed_credits_exhausted", None): (gw.InsufficientCreditsError, False),
        (402, "managed_credits_insufficient", None): (gw.InsufficientCreditsError, False),
        (402, "managed_credits_insufficient", "in-flight"): (gw.InsufficientCreditsError, True),
        (402, "agent_budget_exhausted", "in-flight"): (gw.AgentBudgetExhaustedError, False),
        (429, "budget_exceeded", None): (gw.BudgetExceededError, False),
        (429, "org_budget_exceeded", "in-flight"): (gw.BudgetExceededError, False),
        (429, "managed_spend_velocity", None): (gw.RateLimitError, False),
        (429, "rate_limit_exceeded", None): (gw.RateLimitError, None),
        (503, "managed_billing_unavailable", None): (gw.ServiceUnavailableError, None),
        (403, "permission_denied", None): (gw.PermissionDeniedError, False),
        (402, "other_code", None): (gw.APIStatusError, False),
        (418, None, None): (gw.APIStatusError, None),
    }
    for (status, code, meta), verdict in expected.items():
        metadata = IN_FLIGHT if meta == "in-flight" else None
        assert classify_refusal(status, code, metadata) == verdict, (status, code, meta)


def test_a_refusal_constructs_like_api_status_error_and_status_errors_expose_metadata() -> None:
    body = {"error": {"message": "out", "metadata": {"scope": "org", "available_usd": 0.0}}}
    exc = gw.InsufficientCreditsError("out", status_code=402, body=body)
    assert (exc.args, exc.scope, exc.required_usd) == (("out",), "org", None)
    assert exc.metadata == body["error"]["metadata"]
    assert (str(exc), repr(exc)) == ("Error code: 402 - out", "InsufficientCreditsError(status_code=402, message='out')")
    assert gw.BudgetExceededError(message="cap", status_code=429).metadata == {}
    plain = gw.APIStatusError.from_response(_refusal(429, "rate_limit_error", "rate_limit_exceeded", OTHER))
    assert type(plain) is gw.RateLimitError and plain.metadata == OTHER
