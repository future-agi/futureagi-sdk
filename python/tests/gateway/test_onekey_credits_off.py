"""Credits-off refusals stay terminal across retry settings, copies and stream opens."""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest
import respx

import fi.gateway as gw
from fi.gateway import _exceptions
from fi.gateway._retry_policy import RetryPolicy, classify_refusal
from fi.gateway._transport import _async as async_transport
from fi.gateway._transport import _sync as sync_transport

BASE = "https://gateway.test"
CODE = "future_agi_credits_off"
NAME = "FutureAGICreditsOffError"
REMEDY = (
    'An organization Owner or Admin uses the "Turn on Future AGI credits" control '
    "on the Gateway Models page, or adds their own provider key on the Gateway Providers page."
)
MESSAGE = (
    'model "managed-example" is a Future AGI model, and Future AGI credits are off '
    "for your organization. " + REMEDY
)
BODY = {"error": {"message": MESSAGE, "type": "permission", "code": CODE}}


class EveryStatusRetryPolicy(RetryPolicy):
    """Even a policy granting retries for 403 cannot override a terminal refusal."""

    def get_retries_for_status(self, status_code: int) -> int:
        return 5


def _options(setting: str) -> dict:
    if setting == "max-zero":
        return {"max_retries": 0}
    if setting == "max-five":
        return {"max_retries": 5}
    policy = EveryStatusRetryPolicy if setting == "every-status" else RetryPolicy
    return {"max_retries": 5, "retry_policy": policy(**{
        name: 5 for name in RetryPolicy.__dataclass_fields__
    })}


@pytest.fixture
def sleeps(monkeypatch):
    slept = []

    async def asleep(delay):
        slept.append(delay)

    monkeypatch.setattr(sync_transport, "time", SimpleNamespace(sleep=slept.append))
    monkeypatch.setattr(async_transport, "anyio", SimpleNamespace(sleep=asleep))
    return slept


def _check(exc, route, sleeps):
    assert route.call_count == 1
    assert sleeps == []
    assert type(exc) is getattr(gw, NAME)
    assert isinstance(exc, gw.PermissionDeniedError)
    assert (exc.status_code, exc.type, exc.code) == (403, "permission", CODE)
    assert exc.message == MESSAGE and str(exc) == f"Error code: 403 - {MESSAGE}"
    assert exc.body == BODY and exc.remedy == REMEDY
    assert exc.request_id == "req-credits-off"


def _route(mock):
    return mock.post(f"{BASE}/v1/chat/completions").respond(
        403, json=BODY, headers={
            "retry-after": "2", "x-should-retry": "true",
            "x-agentcc-request-id": "req-credits-off",
        },
    )


@pytest.mark.parametrize("setting", ["max-zero", "max-five", "generous", "every-status"])
@pytest.mark.parametrize("copy", [False, True], ids=["direct", "with-options"])
@pytest.mark.parametrize("stream", [False, True], ids=["completion", "stream-open"])
def test_credits_off_is_never_retried_sync(setting, copy, stream, sleeps):
    with respx.mock() as mock:
        route = _route(mock)
        with gw.AgentCC(api_key="test-key", base_url=BASE, **_options(setting)) as root:
            with root.with_options(max_retries=_options(setting)["max_retries"]) if copy else root as client:
                with pytest.raises(gw.PermissionDeniedError) as caught:
                    client.chat.completions.create(model="managed-example", messages=[], stream=stream)
    _check(caught.value, route, sleeps)


@pytest.mark.parametrize("setting", ["max-zero", "max-five", "generous", "every-status"])
@pytest.mark.parametrize("copy", [False, True], ids=["direct", "with-options"])
@pytest.mark.parametrize("stream", [False, True], ids=["completion", "stream-open"])
@pytest.mark.anyio
async def test_credits_off_is_never_retried_async(setting, copy, stream, sleeps):
    with respx.mock() as mock:
        route = _route(mock)
        async with gw.AsyncAgentCC(api_key="test-key", base_url=BASE, **_options(setting)) as root:
            async with root.with_options(max_retries=_options(setting)["max_retries"]) if copy else root as client:
                with pytest.raises(gw.PermissionDeniedError) as caught:
                    await client.chat.completions.create(model="managed-example", messages=[], stream=stream)
    _check(caught.value, route, sleeps)


def test_credits_off_is_public_and_the_remedy_is_read_only():
    cls = getattr(gw, NAME)
    assert cls is getattr(_exceptions, NAME)
    assert NAME in gw.__all__ and NAME in dir(gw)
    assert issubclass(cls, gw.PermissionDeniedError)
    exc = cls("gateway message", status_code=403)
    assert exc.message == "gateway message" and exc.remedy == REMEDY
    with pytest.raises(AttributeError):
        exc.remedy = "retry"
    with pytest.raises(AttributeError):
        del exc.remedy


@pytest.mark.parametrize("metadata", [None, {"limit_source": "agentcc_in_flight", "remedy_hint": "retry"}])
def test_credits_off_has_a_terminal_classification_even_with_retry_metadata(metadata):
    assert classify_refusal(403, CODE, metadata) == (getattr(gw, NAME), False)


@pytest.mark.parametrize("type_", [None, "permission", "rate_limit_error"])
def test_credits_off_classification_uses_status_and_code_not_type(type_):
    exc = gw.APIStatusError.from_response(httpx.Response(
        403, json={"error": {"message": MESSAGE, "type": type_, "code": CODE}},
    ))
    assert type(exc) is getattr(gw, NAME)
    assert classify_refusal(403, "permission_denied") == (gw.PermissionDeniedError, False)
    assert classify_refusal(403, "other_code") == (gw.PermissionDeniedError, False)
    assert classify_refusal(429, CODE) == (gw.RateLimitError, False)
