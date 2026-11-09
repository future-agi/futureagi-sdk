"""Exercise the complete gateway tour with offline, tool-optional responses."""

from __future__ import annotations

import json
import os
import runpy
import socket
import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from fi.gateway._transport._sync import SyncBaseClient


EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "gateway.py"


def completion(message):
    return {
        "id": "chatcmpl-synthetic",
        "object": "chat.completion",
        "created": 0,
        "model": "synthetic-model",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", **message},
            "finish_reason": "tool_calls" if message.get("tool_calls") else "stop",
        }],
        "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
    }


@pytest.mark.parametrize(
    "message,expected_output",
    [
        pytest.param({"content": "It is sunny in Paris."}, "It is sunny in Paris.", id="omitted-tool-calls"),
        pytest.param({"content": "It is sunny in Paris.", "tool_calls": None}, "It is sunny in Paris.", id="null-tool-calls"),
        pytest.param({"content": "It is sunny in Paris.", "tool_calls": []}, "It is sunny in Paris.", id="empty-tool-calls"),
        pytest.param({"content": None, "refusal": "I cannot provide live weather."}, "I cannot provide live weather.", id="refusal"),
        pytest.param({"content": None}, "No tool call returned.", id="empty-message"),
        pytest.param({
            "content": None,
            "tool_calls": [{
                "id": "call-synthetic",
                "type": "function",
                "function": {"name": "get_weather", "arguments": '{"city":"Paris"}'},
            }],
        }, "get_weather({'city': 'Paris'})", id="tool-call"),
    ],
)
def test_gateway_tour_continues_after_tool_response(message, expected_output, monkeypatch, capsys):
    requests = []

    def deny_network(*args, **kwargs):
        raise AssertionError("The gateway tour test must not use the network")

    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(socket, "getaddrinfo", deny_network)

    def send(request):
        body = json.loads(request.content) if request.content else {}
        requests.append((request.url.path, body))
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={
                "object": "list",
                "data": [{"id": "synthetic-model", "object": "model", "created": 0, "owned_by": "synthetic"}],
            })
        assert request.url.path == "/v1/chat/completions"
        if body.get("model") == "not-a-real-model":
            return httpx.Response(404, json={"error": {"message": "Synthetic model not found"}})
        if body.get("stream"):
            chunk = {
                "id": "chatcmpl-synthetic",
                "object": "chat.completion.chunk",
                "created": 0,
                "model": "synthetic-model",
                "choices": [{"index": 0, "delta": {"content": "one two three four five"}, "finish_reason": "stop"}],
            }
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                content=f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n".encode(),
            )
        response_message = message if body.get("tools") else {"content": "Hello"}
        return httpx.Response(200, json=completion(response_message), headers={"x-agentcc-cost": "0.01"})

    with httpx.Client(transport=httpx.MockTransport(send)) as http:
        with (
            patch.object(SyncBaseClient, "_new_http_client", return_value=http),
            patch.dict(os.environ, {
                "FI_GATEWAY_API_KEY": "synthetic-virtual-key",
                "FI_GATEWAY_URL": "https://gateway.example.test",
            }, clear=True),
            patch.object(sys, "argv", [str(EXAMPLE), "synthetic-model"]),
        ):
            runpy.run_path(str(EXAMPLE), run_name="__main__")

    output = capsys.readouterr().out
    tool_section = output.split("\nTool call\n", 1)[1].split("\nA session", 1)[0]
    assert expected_output in tool_section
    assert "one two three four five" in output
    assert "2 requests" in output
    assert "Errors are typed" in output
    assert "404: Synthetic model not found" in output
    assert len(requests) == 7
    assert requests[0][0] == "/v1/models"
    assert requests[3][1]["tools"][0]["function"]["name"] == "get_weather"
    assert requests[-1][1]["model"] == "not-a-real-model"
