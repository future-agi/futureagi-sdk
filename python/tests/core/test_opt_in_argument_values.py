"""``allow_insecure_http`` opts in to plain HTTP only as the boolean ``True`` or the exact text ``1``, the one value
``FI_ALLOW_INSECURE_HTTP`` accepts. Any other value (``"yes"``, ``"true"``, ``"0"``, ``""``, a number, a container or an
object) is not an opt-in, and an explicit ``False`` overrides the environment. Each row is measured at a loopback listener:
no connection and no marker byte when the opt-in is refused. Names resolve to this machine through a resolver shim."""

from __future__ import annotations

import os
from typing import Any
from unittest import mock

import pytest

from fi._core.http_security import insecure_http_allowed, plaintext_decision
from fi.errors import ConfigurationError
from tests.core._plaintext_oracle import MARKER_KEY, MARKER_SECRET, PROXY_NAMES
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)
from tests.core.test_sender_rules import resolver  # noqa: F401  (the fixture)

class Odd:
    def __repr__(self) -> str:
        return "Odd()"


NOT_AN_OPT_IN = ["yes", "true", "True", "0", "", " 1", "1 ", "01", "on", 1, 2, 0.5, [True], {"a": 1}, (1,), Odd(), b"1"]


@pytest.mark.parametrize("value", NOT_AN_OPT_IN, ids=repr)
def test_a_value_other_than_true_or_one_is_not_an_opt_in(value):
    assert insecure_http_allowed(value, {}) is False
    assert insecure_http_allowed(value, {"FI_ALLOW_INSECURE_HTTP": "1"}) is False
    decision = plaintext_decision("http://remote.test", allow_insecure_http=value, environ={})
    assert not decision.allowed and decision.reason == "not_opted_in"


@pytest.mark.parametrize("value", [True, "1"], ids=repr)
def test_true_and_the_text_one_are_the_opt_in(value):
    assert insecure_http_allowed(value, {}) is True
    assert plaintext_decision("http://remote.test", allow_insecure_http=value, environ={}).reason == "opted_in"


def test_false_overrides_the_environment_and_none_defers_to_it():
    assert insecure_http_allowed(False, {"FI_ALLOW_INSECURE_HTTP": "1"}) is False
    assert insecure_http_allowed(None, {"FI_ALLOW_INSECURE_HTTP": "1"}) is True
    assert insecure_http_allowed(None, {"FI_ALLOW_INSECURE_HTTP": "true"}) is False


def _management(base: str, value: Any) -> None:
    from fi import FutureAGIClient

    FutureAGIClient(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=base, retries=0, allow_insecure_http=value).gateway.config.get_active()


def _async_management(base: str, value: Any) -> None:
    import asyncio

    from fi import AsyncFutureAGIClient

    async def go() -> None:
        async with AsyncFutureAGIClient(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=base, retries=0,
                                        allow_insecure_http=value) as client:
            await client.gateway.config.get_active()

    asyncio.run(go())


def _lazy_key_auth(base: str, value: Any) -> None:
    import httpx

    from fi._credentials import Credentials
    from fi._http import LazyKeyAuth

    creds = Credentials(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=base, keys_source="argument", base_url_source="argument")
    with httpx.Client(auth=LazyKeyAuth(lambda: creds, allow_insecure_http=value), timeout=2) as client:
        client.get(f"{base}/probe")


SENDERS = {"management client": _management, "async management client": _async_management, "LazyKeyAuth": _lazy_key_auth}


def _try(sinks_: dict, send: Any, value: Any) -> Any:
    for each in sinks_.values():
        each.reset()
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, clean, clear=True):
        try:
            send(f"http://plain.example.test:{sinks_['target'].port}", value)
        except Exception as error:  # noqa: BLE001 - the kind of failure is what the tests read
            return error
    return None


@pytest.mark.parametrize("value", NOT_AN_OPT_IN, ids=repr)
@pytest.mark.parametrize("name", list(SENDERS))
def test_a_sender_refuses_plain_http_for_a_value_that_is_not_an_opt_in(sinks, resolver, name, value):
    error = _try(sinks, SENDERS[name], value)
    assert isinstance(error, ConfigurationError) and error.code == "insecure_http_origin", repr(error)
    for each in sinks.values():
        assert each.marker_bytes == 0 and each.requests == 0


@pytest.mark.parametrize("value", [True, "1"], ids=repr)
@pytest.mark.parametrize("name", list(SENDERS))
def test_a_sender_sends_plain_http_for_true_and_the_text_one(sinks, resolver, name, value):
    _try(sinks, SENDERS[name], value)
    assert sinks["target"].requests == 1 and sinks["target"].marker_bytes > 0
