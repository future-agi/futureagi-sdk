"""client.simulation.calls.workers, against an in-process httpx MockTransport (no backend)."""

from __future__ import annotations

import asyncio

import fi.platform as fp
import httpx

BASE = "http://backend.test"
CALL = "22222222-2222-4222-8222-22222222222b"
WORKERS = {
    "status": True,
    "result": {"workers": [{"name": "dispatcher"}, {"name": "billing"}], "state": "collecting", "next_read_at": None},
}


def _handler(sent: list[httpx.Request], status: int = 200, body: dict | None = WORKERS):
    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(status) if body is None else httpx.Response(status, json=body)

    return handler


def test_workers_reads_one_trials_workers():
    sent: list[httpx.Request] = []
    http = httpx.Client(transport=httpx.MockTransport(_handler(sent)))
    client = fp.Client(api_key="k", secret_key="s", base_url=BASE, http_client=http)

    result = client.simulation.calls.workers(CALL, attempt="2")

    assert (sent[0].method, sent[0].url.path) == ("GET", f"/simulate/v3/call-executions/{CALL}/workers/")
    assert sent[0].url.params["attempt"] == "2"
    assert [worker.name for worker in result.workers] == ["dispatcher", "billing"]
    assert result.state == "collecting"


def test_async_client_has_the_same_method():
    sent: list[httpx.Request] = []

    async def run():
        http = httpx.AsyncClient(transport=httpx.MockTransport(_handler(sent)))
        async with fp.AsyncClient(api_key="k", secret_key="s", base_url=BASE, http_client=http) as client:
            return await client.simulation.calls.workers(CALL)

    result = asyncio.run(run())

    assert sent[0].url.path == f"/simulate/v3/call-executions/{CALL}/workers/"
    assert "attempt" not in sent[0].url.params
    assert len(result.workers) == 2


def test_traces_still_being_collected_return_pending():
    sent: list[httpx.Request] = []
    pending = {"status": True, "result": {"pending": True, "next_read_at": "2026-11-26T10:00:00Z", "participants_declared": True}}
    http = httpx.Client(transport=httpx.MockTransport(_handler(sent, 202, pending)))
    client = fp.Client(api_key="k", secret_key="s", base_url=BASE, http_client=http)

    result = client.simulation.calls.workers(CALL)

    assert result.pending is True
    assert result.next_read_at == "2026-11-26T10:00:00Z"
    assert result.workers is None


def test_a_trial_without_a_hand_off_returns_none():
    sent: list[httpx.Request] = []
    http = httpx.Client(transport=httpx.MockTransport(_handler(sent, 204, None)))
    client = fp.Client(api_key="k", secret_key="s", base_url=BASE, http_client=http)

    assert client.simulation.calls.workers(CALL) is None
