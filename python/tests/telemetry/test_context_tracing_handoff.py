from __future__ import annotations

import httpx
import pytest

from fi.context.client import AsyncContextClient, ContextClient
from fi.platform import AsyncClient, ContextAuth
from test_snapshots import Fixture, client as sync_platform


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("client_optout", [False, True])
@pytest.mark.asyncio
async def test_read_all_tracing_policy_survives_verified_deepagents_handoff(
    tracing, asynchronous, client_optout
):
    pytest.importorskip("deepagents")
    from fi.context.adapters.deepagents import ReadOnlyContextBackend

    fixture = Fixture()
    if asynchronous:
        async with AsyncClient(
            auth=ContextAuth("synthetic-credential"),
            base_url="https://fixture.invalid",
            http_client=httpx.AsyncClient(
                transport=httpx.MockTransport(fixture.handle)
            ),
        ) as platform:
            snapshot = await AsyncContextClient(
                platform, tracing=not client_optout
            ).resolve("fixture")
            verified = await snapshot.read_all(
                **({} if client_optout else {"trace": False})
            )
    else:
        with sync_platform(fixture) as platform:
            snapshot = ContextClient(platform, tracing=not client_optout).resolve(
                "fixture"
            )
            verified = snapshot.read_all(
                **({} if client_optout else {"trace": False})
            )

    assert verified._tracing is not client_optout
    backend = ReadOnlyContextBackend(verified, authorize=lambda *args: None)
    tracer, exporter, _ = tracing
    with tracer.start_as_current_span("real-request"):
        assert "Refund rules" in backend.read("/skills/refund/SKILL.md")

    loads = [
        span for span in exporter.get_finished_spans()
        if span.name in {"context.load", "skill.load"}
    ]
    if client_optout:
        assert loads == []
        assert all(
            request.headers["x-fi-skills-tracing"] == "off"
            for request in fixture.requests
            if request.url.path.endswith("/resolve/")
        )
    else:
        # The per-call opt-out suppresses read_all's context event; the later
        # independently traced DeepAgents file read still records its skill load.
        assert [span.name for span in loads] == ["skill.load"]
        assert loads[-1].attributes["fi.skill.name"] == "refund"
