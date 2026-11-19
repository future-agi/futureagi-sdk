"""create_headers(guardrail_policy=) sends X-Guardrail-Policy, the header the gateway reads.

``create_headers`` (bucket F): agentcc 1.x's ``create_headers`` wrote the policy
as ``x-agentcc-guardrail-policy`` (PY/_gateway_config.py:404-405) while its own per-request
``guardrail_policy=`` sent ``X-Guardrail-Policy``, the header the gateway parses
(the gateway's request policy parser). Both now send the same header.
"""

from __future__ import annotations

import httpx

from fi.gateway import AgentCC, create_headers

COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}


def _sent_headers(**params: object) -> httpx.Headers:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=COMPLETION)

    client = AgentCC(
        api_key="gw-key",
        base_url="http://127.0.0.1:8090",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    client.chat.completions.create(model="m", messages=[], **params)  # type: ignore[arg-type]
    return seen[0].headers


def test_create_headers_sends_the_header_the_gateway_reads() -> None:
    assert create_headers(guardrail_policy="strict") == {"X-Guardrail-Policy": "strict"}
    assert create_headers(guardrail_policy="log-only") == {
        "X-Guardrail-Policy": "log-only"
    }


def test_create_headers_and_the_request_parameter_send_the_same_header() -> None:
    built = create_headers(guardrail_policy="disabled")
    sent = _sent_headers(guardrail_policy="disabled")
    assert [name.lower() for name in built] == ["x-guardrail-policy"]
    assert sent["x-guardrail-policy"] == "disabled"
    assert "x-agentcc-guardrail-policy" not in sent


def test_the_1x_header_name_is_gone_from_every_combination() -> None:
    headers = create_headers(
        api_key="gw-key",
        session_id="s",
        cache_ttl=60,
        guardrail_policy="strict",
        properties={"team": "a"},
    )
    assert headers == {
        "Authorization": "Bearer gw-key",
        "x-agentcc-session-id": "s",
        "x-agentcc-cache-ttl": "60",
        "X-Guardrail-Policy": "strict",
        "x-agentcc-property-team": "a",
    }
    assert not any(name.lower() == "x-agentcc-guardrail-policy" for name in headers)


def test_no_policy_no_header() -> None:
    assert create_headers() == {}
    assert "x-guardrail-policy" not in _sent_headers()
