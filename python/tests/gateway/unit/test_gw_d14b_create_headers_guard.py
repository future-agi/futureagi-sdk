"""D-14b: ``create_headers(api_key=)`` refuses the FI key pair, and so does every other
public entry point that takes a gateway key.

The gateway takes a virtual key. A key equal to ``FI_API_KEY`` or ``FI_SECRET_KEY`` from
the environment raises :class:`AgentCCError` (the message names the variable, never the
value) instead of becoming ``Authorization: Bearer <the FI key>``. agentcc 1.0's
``create_headers`` had no guard. The sweep at the end finds every public callable with
an ``api_key`` parameter, so a new one that skips the guard fails here.
"""

from __future__ import annotations

import inspect
import os
from collections.abc import Callable
from typing import Any

import pytest

import fi.gateway
import fi.gateway.testing
from fi.gateway import AgentCCError, create_headers, openai_kwargs

GW = "http://127.0.0.1:8090"
FI_KEY = "fi-api-key-value-0123456789"
FI_SECRET = "fi-secret-key-value-0123456789"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith(("AGENTCC_", "FI_", "OPENAI_")):
            monkeypatch.delenv(name)


@pytest.fixture
def no_egress(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every httpx send records its URL and fails, so a refusal provably sends nothing."""
    import httpx

    sent: list[str] = []

    def refuse(url: Any, *args: Any, **kwargs: Any) -> Any:
        sent.append(str(url))
        raise AssertionError("nothing may be sent with the FI key pair")

    def refuse_send(self: Any, request: Any, *args: Any, **kwargs: Any) -> Any:
        return refuse(request.url)

    monkeypatch.setattr(httpx, "get", refuse)
    monkeypatch.setattr(httpx.Client, "send", refuse_send)
    monkeypatch.setattr(httpx.AsyncClient, "send", refuse_send)
    return sent


@pytest.mark.parametrize(
    "name, value", [("FI_API_KEY", FI_KEY), ("FI_SECRET_KEY", FI_SECRET)]
)
def test_create_headers_refuses_the_fi_key_pair_and_names_only_the_variable(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)
    with pytest.raises(AgentCCError) as info:
        create_headers(api_key=value, session_id="s")
    message = str(info.value)
    assert name in message and "virtual key" in message
    assert value not in message


def test_a_gateway_key_that_differs_from_the_pair_is_sent_as_before(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FI_API_KEY", FI_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FI_SECRET)
    assert create_headers(api_key="sk-gw-1", session_id="s") == {
        "Authorization": "Bearer sk-gw-1",
        "x-agentcc-session-id": "s",
    }


def test_no_api_key_means_no_authorization_header_and_no_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FI_API_KEY", FI_KEY)
    assert create_headers(trace_id="t") == {"x-agentcc-trace-id": "t"}


def test_an_empty_fi_variable_never_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FI_API_KEY", "")
    monkeypatch.setenv("FI_SECRET_KEY", "")
    assert create_headers(api_key="k")["Authorization"] == "Bearer k"


def test_the_pair_in_another_variable_is_not_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Only FI_API_KEY and FI_SECRET_KEY are the pair; a gateway key that happens to be
    # in another variable is the caller's to send.
    monkeypatch.setenv("FI_GATEWAY_API_KEY", "gw-from-env")
    assert (
        create_headers(api_key="gw-from-env")["Authorization"] == "Bearer gw-from-env"
    )


def test_openai_kwargs_still_refuses_the_pair_before_building_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FI_API_KEY", FI_KEY)
    with pytest.raises(AgentCCError):
        openai_kwargs(api_key=FI_KEY, base_url=GW)
    monkeypatch.setenv("FI_GATEWAY_API_KEY", FI_KEY)
    with pytest.raises(AgentCCError):
        openai_kwargs(base_url=GW)


# -- every public entry point that takes a key ------------------------------


def _raises(call: Callable[[str], Any]) -> Callable[[str], str]:
    def check(value: str) -> str:
        with pytest.raises(AgentCCError) as info:
            call(value)
        return str(info.value)

    return check


def _health_check(value: str) -> str:
    # health_check reports instead of raising (as for every other failure it meets).
    result = fi.gateway.health_check(api_key=value, base_url=GW)
    assert result["status"] == "error", result
    return str(result["error"])


# How each entry point is called with the pair as its key, returning the refusal text.
ENTRY_POINTS: dict[str, Callable[[str], str]] = {
    "AgentCC": _raises(lambda v: fi.gateway.AgentCC(api_key=v, base_url=GW)),
    "AsyncAgentCC": _raises(lambda v: fi.gateway.AsyncAgentCC(api_key=v, base_url=GW)),
    "check_valid_key": _raises(lambda v: fi.gateway.check_valid_key(v, GW)),
    "create_headers": _raises(lambda v: fi.gateway.create_headers(api_key=v)),
    "create_mock_client": _raises(lambda v: fi.gateway.create_mock_client(api_key=v)),
    "health_check": _health_check,
    "openai_kwargs": _raises(
        lambda v: fi.gateway.openai_kwargs(api_key=v, base_url=GW)
    ),
}
PUBLIC_MODULES = (fi.gateway, fi.gateway.testing)


def _takes_api_key(obj: Any) -> bool:
    targets = [obj]
    if inspect.isclass(obj):
        targets = [obj.__init__] + [
            member
            for name, member in inspect.getmembers(obj, inspect.isfunction)
            if not name.startswith("_")
        ]
    for target in targets:
        try:
            if "api_key" in inspect.signature(target).parameters:
                return True
        except (TypeError, ValueError):
            continue
    return False


def test_the_sweep_lists_every_public_callable_that_takes_a_key() -> None:
    found = {
        name
        for module in PUBLIC_MODULES
        for name in module.__all__
        if callable(getattr(module, name)) and _takes_api_key(getattr(module, name))
    }
    assert found == set(ENTRY_POINTS)


@pytest.mark.parametrize("entry", sorted(ENTRY_POINTS))
@pytest.mark.parametrize(
    "name, value", [("FI_API_KEY", FI_KEY), ("FI_SECRET_KEY", FI_SECRET)]
)
def test_every_entry_point_refuses_the_pair_without_sending_anything(
    monkeypatch: pytest.MonkeyPatch,
    no_egress: list[str],
    entry: str,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(name, value)
    message = ENTRY_POINTS[entry](value)
    assert name in message and value not in message
    assert no_egress == []
