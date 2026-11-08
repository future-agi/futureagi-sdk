"""Offline effects of published callbacks and explicit metrics/recording opt-ins."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import httpx
import pytest

from fi.gateway import (AgentCC, AsyncAgentCC, BadRequestError,
                        InternalServerError)
from fi.gateway.callbacks import (CallbackHandler, LoggingCallback,
                                  MetricsCallback, RequestOptions, CallbackRequest, CallbackResponse)
from fi.gateway.testing import RequestRecorder
from fi.gateway.types.chat import ChatCompletion

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

GW = "http://127.0.0.1:8090"
COMPLETION = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1,
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "finish_reason": "stop",
            "message": {"role": "assistant", "content": "hi"},
        }
    ],
    "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
}
GATEWAY_HEADERS = {
    "x-agentcc-provider": "openai",
    "x-agentcc-latency-ms": "42",
    "x-agentcc-cost": "0.25",
}
MSG = [{"role": "user", "content": "x"}]


def _replies(*statuses: int):
    queue = list(statuses)

    def handler(request: httpx.Request) -> httpx.Response:
        status = queue.pop(0)
        if status == 200:
            return httpx.Response(200, json=COMPLETION, headers=GATEWAY_HEADERS)
        return httpx.Response(
            status, json={"error": {"message": f"status {status}", "type": "x"}}
        )

    return handler


def _client(callbacks: list[Any], *statuses: int, **kw: Any) -> AgentCC:
    return AgentCC(
        api_key="gw-key",
        base_url=GW,
        callbacks=callbacks,
        http_client=httpx.Client(transport=httpx.MockTransport(_replies(*statuses))),
        **kw,
    )


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("time.sleep", lambda s: None)


class _Seen(CallbackHandler):
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def on_request_start(self, request: RequestOptions) -> None:
        self.calls.append(("on_request_start", (request,)))

    def on_request_end(self, request: RequestOptions, response: Any) -> None:
        self.calls.append(("on_request_end", (request, response)))

    def on_error(self, request: RequestOptions, error: Exception) -> None:
        self.calls.append(("on_error", (request, error)))

    def on_retry(
        self, request: RequestOptions, error: Exception, attempt: int, delay: float
    ) -> None:
        self.calls.append(("on_retry", (request, error, attempt, delay)))


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_the_hooks_get_the_request_descriptor_and_the_returned_model() -> None:
    seen = _Seen()
    result = _client([seen], 200).chat.completions.create(model="m", messages=MSG)
    assert [name for name, _ in seen.calls] == ["on_request_start", "on_request_end"]
    request, response = seen.calls[1][1]
    assert isinstance(request, RequestOptions)
    assert (request.method, request.url) == ("POST", "/v1/chat/completions")
    assert isinstance(response, CallbackResponse)
    assert response._parsed is result and isinstance(result, ChatCompletion)
    assert response.body["id"] == result.id
    assert response.body == result.model_dump()

    snapshot = _Seen()
    snapshot_result = _client([snapshot], 200, callback_mode="snapshot").chat.completions.create(model="m", messages=MSG)
    snapshot_request, snapshot_response = snapshot.calls[1][1]
    assert isinstance(snapshot_request, CallbackRequest)
    assert (snapshot_request.method, snapshot_request.url) == ("POST", GW + "/v1/chat/completions")
    assert isinstance(snapshot_response, CallbackResponse)
    assert snapshot_response._parsed is not snapshot_result
    assert snapshot_response.body["id"] == snapshot_result.id


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_retry_then_error_fires_retry_then_error() -> None:
    seen = _Seen()
    with pytest.raises(BadRequestError):
        _client([seen], 500, 400, max_retries=2).chat.completions.create(
            model="m", messages=MSG
        )
    names = [name for name, _ in seen.calls]
    assert names == ["on_request_start", "on_retry", "on_error"]
    _, error, attempt, delay = seen.calls[1][1]
    assert isinstance(error, InternalServerError) and attempt == 1 and delay >= 0
    assert isinstance(seen.calls[2][1][1], BadRequestError)


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_logging_callback_logs_every_firing_hook(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="agentcc"):
        _client([LoggingCallback()], 200).chat.completions.create(
            model="m", messages=MSG
        )
        with pytest.raises(BadRequestError):
            _client(
                [LoggingCallback()], 503, 400, max_retries=1
            ).chat.completions.create(model="m", messages=MSG)
    lines = [
        (r.levelname, r.getMessage()) for r in caplog.records if r.name == "agentcc"
    ]
    assert lines[0] == ("INFO", "Request: POST /v1/chat/completions")
    assert lines[1] == (
        "INFO",
        "Response: status=200 provider=openai latency=42ms cost=0.25",
    )
    assert lines[2] == ("INFO", "Request: POST /v1/chat/completions")
    assert lines[3][0] == "WARNING" and lines[3][1].startswith("Retry 1 after ")
    assert lines[4][0] == "ERROR" and lines[4][1].startswith(
        "Error: POST /v1/chat/completions - "
    )
    assert len(lines) == 5


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_metrics_callback_counts_requests_errors_tokens_cost_and_latency() -> None:
    metrics = MetricsCallback(count_tokens=True)
    client = _client([metrics], 200, 200, 400, max_retries=0)
    client.chat.completions.create(model="m", messages=MSG)
    client.chat.completions.create(model="m", messages=MSG)
    with pytest.raises(BadRequestError):
        client.chat.completions.create(model="m", messages=MSG)
    assert metrics.total_requests == 2
    assert metrics.total_errors == 1
    assert metrics.total_tokens == 16
    assert metrics.total_cost == 0.5
    assert metrics.avg_latency == 42.0
    assert metrics.error_rate == pytest.approx(1 / 3)


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_request_recorder_records_the_request_and_the_response(tmp_path: Path) -> None:
    path = tmp_path / "recordings.json"
    with RequestRecorder(str(path), format="compact") as recorder:
        _client([recorder], 200, callback_mode="snapshot").chat.completions.create(
            model="gpt-4o-mini", messages=MSG
        )
    (rec,) = json.loads(path.read_text())
    assert rec["request"] == {
        "method": "POST",
        "url": GW + "/v1/chat/completions",
        "body": {"model": "gpt-4o-mini", "messages": MSG},
    }
    assert rec["response"]["status_code"] == 200
    assert rec["response"]["body"]["id"] == "chatcmpl-1"
    assert rec["response"]["body"]["usage"]["total_tokens"] == 8
    assert "agentcc" not in rec["response"]["body"]


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
async def test_the_async_client_fires_the_same_hooks() -> None:
    seen = _Seen()
    metrics = MetricsCallback(count_tokens=True)
    client = AsyncAgentCC(
        api_key="gw-key",
        base_url=GW,
        callbacks=[seen, metrics],
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(_replies(200))),
    )
    await client.chat.completions.create(model="m", messages=MSG)
    assert [name for name, _ in seen.calls] == ["on_request_start", "on_request_end"]
    assert metrics.total_requests == 1 and metrics.total_tokens == 8
