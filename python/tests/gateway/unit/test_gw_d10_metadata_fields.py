"""D-10: ``AgentCCMetadata`` reads ``x-agentcc-config-ignored`` and ``x-agentcc-client-request-id``.

Both are gateway response headers. agentcc 1.x dropped them.
"""

from __future__ import annotations

import httpx

from fi.gateway import AgentCC
from fi.gateway.types.agentcc_metadata import AgentCCMetadata

GW = "http://127.0.0.1:8090"
COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}
CHUNK = (
    'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m",'
    '"choices":[{"index":0,"delta":{"content":"a"},"finish_reason":null}]}\n\n'
    "data: [DONE]\n\n"
)


def test_both_fields_default_to_none() -> None:
    meta = AgentCCMetadata.from_headers({})
    assert meta.config_ignored is None and meta.client_request_id is None


def test_from_headers_reads_both() -> None:
    meta = AgentCCMetadata.from_headers(
        {
            "x-agentcc-config-ignored": "cache.strategy, fallback,retry",
            "x-agentcc-client-request-id": "my-req-7",
            "x-agentcc-request-id": "gw-req-1",
        }
    )
    assert meta.config_ignored == ["cache.strategy", "fallback", "retry"]
    assert meta.client_request_id == "my-req-7"
    assert meta.request_id == "gw-req-1"


def test_an_empty_ignored_list_is_empty() -> None:
    assert (
        AgentCCMetadata.from_headers({"x-agentcc-config-ignored": ""}).config_ignored
        == []
    )


def _client(
    headers: dict[str, str], stream: bool = False
) -> tuple[AgentCC, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if stream:
            return httpx.Response(
                200,
                headers={**headers, "content-type": "text/event-stream"},
                content=CHUNK,
            )
        return httpx.Response(200, headers=headers, json=COMPLETION)

    client = AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    return client, seen


def test_a_response_carries_them() -> None:
    client, seen = _client(
        {
            "X-Agentcc-Config-Ignored": "cache.enabled",
            "X-Agentcc-Client-Request-Id": "mine",
        }
    )
    result = client.chat.completions.create(model="m", messages=[], request_id="mine")
    assert seen[0].headers["x-agentcc-request-id"] == "mine"
    assert result.agentcc.config_ignored == ["cache.enabled"]
    assert result.agentcc.client_request_id == "mine"


def test_a_stream_carries_them() -> None:
    client, _ = _client({"X-Agentcc-Config-Ignored": "retry"}, stream=True)
    with client.chat.completions.stream(model="m", messages=[]) as stream:
        assert stream.agentcc.config_ignored == ["retry"]
        assert stream.get_final_text() == "a"


def test_model_dump_includes_them() -> None:
    dumped = AgentCCMetadata.from_headers(
        {"x-agentcc-config-ignored": "a"}
    ).model_dump()
    assert dumped["config_ignored"] == ["a"] and dumped["client_request_id"] is None
