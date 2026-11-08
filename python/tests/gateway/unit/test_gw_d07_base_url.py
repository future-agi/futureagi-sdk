"""D-07: trailing slashes and one trailing ``/v1`` are dropped from the base URL, always.

agentcc 1.x used the base URL as given (only a trailing slash went), so the ``<origin>/v1``
that FA's management API hands out became ``/v1/v1/chat/completions``. The shapes are the
parity env matrix's (``env.base_url.*``).
"""

from __future__ import annotations

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, check_valid_key, health_check
from fi.gateway._env import normalize_base_url

URL = "https://gateway.example.test"
SHAPES = {
    "trailing_slash": (URL + "/", URL),
    "v1": (URL + "/v1", URL),
    "v1_slash": (URL + "/v1/", URL),
    "v1_twice": (URL + "/v1/v1", URL + "/v1"),
    "prefix": (URL + "/gw", URL + "/gw"),
    "prefix_v1": (URL + "/gw/v1", URL + "/gw"),
    "port": ("http://127.0.0.1:8090", "http://127.0.0.1:8090"),
    "localhost": ("http://localhost:8090/v1", "http://localhost:8090"),
    "uppercase_v1": (URL + "/V1", URL + "/V1"),
    "slashes": (URL + "/v1//", URL),
}
COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}


def _recording_transport(seen: list[httpx.Request]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"object": "list", "data": []})
        return httpx.Response(200, json=COMPLETION)

    return httpx.MockTransport(handler)


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_normalize(name: str) -> None:
    given, origin = SHAPES[name]
    assert normalize_base_url(given) == origin


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_the_client_sends_to_origin_plus_resource_path(name: str) -> None:
    given, origin = SHAPES[name]
    seen: list[httpx.Request] = []
    client = AgentCC(
        api_key="k",
        base_url=given,
        http_client=httpx.Client(transport=_recording_transport(seen)),
    )
    client.chat.completions.create(model="m", messages=[])
    client.models.list()
    assert [str(r.url) for r in seen] == [
        f"{origin}/v1/chat/completions",
        f"{origin}/v1/models",
    ]
    assert repr(client).startswith(f"AgentCC(base_url={origin!r}")


async def test_the_async_client_normalizes_too() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=COMPLETION)

    client = AsyncAgentCC(
        api_key="k",
        base_url=URL + "/v1/",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    await client.chat.completions.create(model="m", messages=[])
    assert str(seen[0].url) == f"{URL}/v1/chat/completions"


def test_the_env_base_url_is_normalized(monkeypatch) -> None:
    monkeypatch.setenv("AGENTCC_BASE_URL", URL + "/v1")
    seen: list[httpx.Request] = []
    client = AgentCC(
        api_key="k", http_client=httpx.Client(transport=_recording_transport(seen))
    )
    client.chat.completions.create(model="m", messages=[])
    assert str(seen[0].url) == f"{URL}/v1/chat/completions"


def test_with_options_keeps_the_origin() -> None:
    seen: list[httpx.Request] = []
    client = AgentCC(
        api_key="k",
        base_url=URL + "/v1",
        http_client=httpx.Client(transport=_recording_transport(seen)),
    )
    client.with_options(max_retries=0).chat.completions.create(model="m", messages=[])
    assert str(seen[0].url) == f"{URL}/v1/chat/completions"


def test_check_valid_key_and_health_check_strip_v1_too(monkeypatch) -> None:
    urls: list[str] = []

    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        urls.append(url)
        return httpx.Response(200, json={})

    monkeypatch.setattr("fi.gateway._utils.httpx.get", fake_get)
    assert check_valid_key("k", URL + "/v1/") is True
    assert health_check(api_key="k", base_url=URL + "/v1")["status"] == "ok"
    assert urls[0] == f"{URL}/v1/models"
    assert not urls[1].startswith(f"{URL}/v1/")
