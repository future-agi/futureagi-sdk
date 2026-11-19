"""Generated SQL resources against a mock transport. No SQL is executed."""

import asyncio
import json

import httpx
import pytest
from fi.platform import AsyncClient, Client, PermissionDeniedError, models

PROJECT = "00000000-0000-4000-8000-000000000001"
JOB = "00000000-0000-4000-8000-000000000002"
START, END = "2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"
TEXT = "mock-only input; 'quoted'\n"


def job(state, **extra):
    return dict(id=JOB, project_id=PROJECT, state=state, sql=TEXT, created_at=START, expires_at=END,
                finished_at=None, error="", expired=False, result={}, **extra)


def test_personal_job_lifecycle_uses_declared_routes_and_raw_snapshots():
    calls = []
    replies = [
        (202, job("queued", reused=False)),
        (200, {**job("succeeded"), "result": {"rows": [[1, False, "cell", None]], "has_more": True, "next_offset": 1}}),
        (200, {**job("succeeded"), "result": {"rows": [], "has_more": False, "next_offset": None}}),
        (200, job("cancelled")),
        (200, dict(identity_semantics="project", version=1, datasets=[], examples=[], max_rows=10000, max_window_days=31, can_save=False)),
    ]

    def handle(request):
        calls.append((request.method, request.url.path, dict(request.url.params), json.loads(request.content) if request.content else None))
        status, body = replies[len(calls) - 1]
        return httpx.Response(status, json=body)

    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        client = Client(api_key="example", secret_key="example", base_url="http://mock.invalid", http_client=http, strict_responses=True)
        ack = client.sql.run(project_id=PROJECT, sql=TEXT, start=START, end=END, reuse=False)
        assert isinstance(ack, models.SQLExecution) and ack.state == "queued" and ack.reused is False
        page = client.sql.get_result(JOB, project_id=PROJECT, limit=1000)
        assert page.result.rows == [[1, False, "cell", None]] and page.result.has_more is True
        last = client.sql.get_result(JOB, project_id=PROJECT, offset=page.result.next_offset, limit=1000)
        assert last.result.next_offset is None and last.result.has_more is False
        cancelled = client.sql.cancel(JOB, project_id=PROJECT)
        assert cancelled.state == "cancelled" and cancelled.finished_at is None
        catalog = client.sql.get_catalog(project_id=PROJECT)
        assert isinstance(catalog, models.SQLCatalog) and catalog.max_window_days == 31
    root = "/tracer/sql-query/"
    assert calls == [
        ("POST", root + "run/", {}, dict(project_id=PROJECT, sql=TEXT, start=START, end=END, reuse=False)),
        ("GET", f"{root}{JOB}/", {"project_id": PROJECT, "limit": "1000"}, None),
        ("GET", f"{root}{JOB}/", {"project_id": PROJECT, "offset": "1", "limit": "1000"}, None),
        ("POST", f"{root}{JOB}/cancel/", {}, {"project_id": PROJECT}),
        ("GET", root + "catalog/", {"project_id": PROJECT}, None),
    ]


def test_async_read_omits_mcp_page_defaults_and_propagates_denial():
    def deny(request):
        assert request.method == "GET" and dict(request.url.params) == {"project_id": PROJECT}
        return httpx.Response(403, json={"detail": "not available"})

    async def read():
        async with httpx.AsyncClient(transport=httpx.MockTransport(deny)) as http:
            client = AsyncClient(api_key="example", secret_key="example", base_url="http://mock.invalid", http_client=http)
            with pytest.raises(PermissionDeniedError):
                await client.sql.get_result(JOB, project_id=PROJECT)

    asyncio.run(read())


@pytest.mark.parametrize("state", ["queued", "running", "succeeded", "failed", "cancelled"])
def test_execution_states_and_empty_expired_snapshot(state):
    snapshot = models.SQLExecution.model_validate({**job(state), "expired": True}, context={"strict": True})
    assert snapshot.state == state and snapshot.expired and snapshot.result.rows is None
