"""D-14 guard, at every send and on every spelling of the key.

The gateway key may never be the FI key pair. The guard ran only when a client was
built, so a client built before ``FI_API_KEY`` was set kept sending a key that now
equals it; and only exact equality was refused, so ``" <key> "`` or ``"Bearer <key>"``
passed ``create_headers``. The transport now runs the guard before every send, and the
comparison ignores surrounding whitespace and a ``Bearer `` prefix on either side.
"""

from __future__ import annotations

import os

import httpx
import pytest

from ._published_helpers import wire_snapshot
from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC, create_headers

GW = "http://127.0.0.1:8090"
KEY = "shared-key-value-0123456789"
MSG = [{"role": "user", "content": "hi"}]
CHAT = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith(("AGENTCC_", "FI_", "OPENAI_")):
            monkeypatch.delenv(name)


def _sync(seen: list[httpx.Request], key: str = KEY) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(wire_snapshot(request))
        if request.url.path == "/v1/files":
            return httpx.Response(
                200,
                json={
                    "id": "f",
                    "object": "file",
                    "bytes": 1,
                    "created_at": 1,
                    "filename": "a",
                    "purpose": "batch",
                },
            )
        if request.url.path.startswith("/v1/responses"):
            return httpx.Response(200, json={"id": "r", "object": "response"})
        return httpx.Response(200, json=CHAT)

    return AgentCC(
        api_key=key,
        base_url=GW,
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


SENDS = {
    "chat": lambda c: c.chat.completions.create(model="m", messages=MSG),
    "chat stream": lambda c: list(
        c.chat.completions.create(model="m", messages=MSG, stream=True)
    ),
    "files.create": lambda c: c.files.create(file=("a", b"{}"), purpose="batch"),
    "files.list": lambda c: c.files.list(),
    "responses.create": lambda c: c.responses.create(model="m", input="x"),
    "responses.retrieve": lambda c: c.responses.retrieve("r"),
    "audio upload": lambda c: c.audio.transcriptions.create(file=b"a", model="w"),
    "models.list": lambda c: c.models.list(),
}


@pytest.mark.parametrize("name", ["FI_API_KEY", "FI_SECRET_KEY"])
@pytest.mark.parametrize("send", list(SENDS))
def test_a_client_built_before_the_variable_was_set_refuses_to_send(
    monkeypatch: pytest.MonkeyPatch, name: str, send: str
) -> None:
    seen: list[httpx.Request] = []
    client = _sync(seen)
    client.chat.completions.create(model="m", messages=MSG)
    assert len(seen) == 1
    monkeypatch.setenv(name, KEY)
    with pytest.raises(AgentCCError) as info:
        SENDS[send](client)
    assert len(seen) == 1, "nothing is sent once the key equals the FI key pair"
    assert name in str(info.value) and KEY not in str(info.value)


def test_a_with_options_copy_refuses_too(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[httpx.Request] = []
    with pytest.warns(DeprecationWarning, match="^Deprecated gateway compatibility options:"):
        copy = _sync(seen).with_options(timeout=5)
    monkeypatch.setenv("FI_API_KEY", KEY)
    with pytest.raises(AgentCCError):
        copy.chat.completions.create(model="m", messages=MSG)
    assert seen == []


async def test_the_async_client_refuses_at_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(wire_snapshot(request))
        return httpx.Response(200, json=CHAT)

    client = AsyncAgentCC(
        api_key=KEY,
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    monkeypatch.setenv("FI_SECRET_KEY", KEY)
    with pytest.raises(AgentCCError, match="FI_SECRET_KEY"):
        await client.chat.completions.create(model="m", messages=MSG)
    with pytest.raises(AgentCCError):
        await client.chat.completions.create(model="m", messages=MSG, stream=True)
    assert seen == []


SPELLINGS = [
    f" {KEY} ",
    f"{KEY}\n",
    f"Bearer {KEY}",
    f"bearer  {KEY}",
    f"\tBEARER {KEY}",
]


@pytest.mark.parametrize("given", SPELLINGS, ids=repr)
def test_every_spelling_of_the_pair_is_refused(
    monkeypatch: pytest.MonkeyPatch, given: str
) -> None:
    monkeypatch.setenv("FI_API_KEY", KEY)
    with pytest.raises(AgentCCError):
        create_headers(api_key=given)
    with pytest.raises(AgentCCError):
        AgentCC(api_key=given, base_url=GW)


@pytest.mark.parametrize("env_value", [f" {KEY}", f"Bearer {KEY}"], ids=repr)
def test_a_padded_variable_still_matches(
    monkeypatch: pytest.MonkeyPatch, env_value: str
) -> None:
    monkeypatch.setenv("FI_API_KEY", env_value)
    with pytest.raises(AgentCCError):
        create_headers(api_key=KEY)


def test_other_keys_and_blank_variables_are_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FI_API_KEY", "   ")
    monkeypatch.setenv("FI_SECRET_KEY", "\t")
    assert create_headers(api_key="k")["Authorization"] == "Bearer k"
    monkeypatch.setenv("FI_API_KEY", KEY)
    for other in (f"{KEY}x", f"x{KEY}", KEY.upper(), f"Bearer{KEY}"):
        assert create_headers(api_key=other)["Authorization"] == f"Bearer {other}"
    seen: list[httpx.Request] = []
    _sync(seen, key="gw-other").chat.completions.create(model="m", messages=MSG)
    assert seen[0].headers["authorization"] == "Bearer gw-other"
