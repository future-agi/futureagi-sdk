"""``files.list(purpose=)`` sends ``purpose`` as one encoded query value.

agentcc 1.x built ``/v1/files?purpose={purpose}`` as given, so a purpose holding ``&``
or ``=`` added or changed query parameters, and a space was sent differently with and
without ``default_query``. A plain purpose (``batch``) goes out exactly as before.
"""

from __future__ import annotations

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC

GW = "http://127.0.0.1:8090"
LIST = {"object": "list", "data": []}
AWKWARD = "t x&limit=1=2"


def _handler(seen: list[httpx.Request]):  # type: ignore[no-untyped-def]
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=LIST)

    return handler


def _sync(seen: list[httpx.Request], **kwargs: object) -> AgentCC:
    transport = httpx.MockTransport(_handler(seen))
    return AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=transport),
        **kwargs,
    )


def _async(seen: list[httpx.Request], **kwargs: object) -> AsyncAgentCC:
    transport = httpx.MockTransport(_handler(seen))
    return AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=transport),
        **kwargs,
    )


def test_a_plain_purpose_is_sent_as_before() -> None:
    seen: list[httpx.Request] = []
    _sync(seen).files.list(purpose="batch")
    assert str(seen[0].url) == f"{GW}/v1/files?purpose=batch"
    _sync(seen).files.list()
    assert str(seen[1].url) == f"{GW}/v1/files"


@pytest.mark.parametrize("default_query", [None, {"tenant": "a b"}])
def test_a_purpose_with_separators_stays_one_value(default_query: object) -> None:
    seen: list[httpx.Request] = []
    _sync(seen, default_query=default_query).files.list(purpose=AWKWARD)
    params = seen[0].url.params
    assert params.get_list("purpose") == [AWKWARD]
    assert "limit" not in params
    expected = {"purpose"} | set(default_query or {})  # type: ignore[arg-type]
    assert set(params.keys()) == expected


async def test_the_async_client_encodes_it_the_same_way() -> None:
    seen: list[httpx.Request] = []
    sync_seen: list[httpx.Request] = []
    await _async(seen).files.list(purpose=AWKWARD)
    _sync(sync_seen).files.list(purpose=AWKWARD)
    assert seen[0].url.params.get_list("purpose") == [AWKWARD]
    assert str(seen[0].url) == str(sync_seen[0].url)
