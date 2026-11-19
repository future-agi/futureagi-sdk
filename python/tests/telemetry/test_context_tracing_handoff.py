from __future__ import annotations

import httpx
import pytest

from fi.context.client import AsyncContextClient, ContextClient
from fi.platform import AsyncClient, ContextAuth
from test_snapshots import Fixture, client as sync_platform


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("policy", ["default", "read-off", "client-off"])
@pytest.mark.asyncio
async def test_read_all_tracing_policy_survives_verified_deepagents_handoff(
    tracing, asynchronous, policy
):
    pytest.importorskip("deepagents")
    from fi.context.adapters.deepagents import ReadOnlyContextBackend

    fixture = Fixture()
    tracer, exporter, _ = tracing
    client_optout = policy == "client-off"
    read_options = {"trace": False} if policy == "read-off" else {}
    with tracer.start_as_current_span("sdk-read") as parent:
        assert parent.is_recording()
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
                verified = await snapshot.read_all(**read_options)
        else:
            with sync_platform(fixture) as platform:
                snapshot = ContextClient(platform, tracing=not client_optout).resolve(
                    "fixture"
                )
                verified = snapshot.read_all(**read_options)

    sdk_loads = [s for s in exporter.get_finished_spans() if s.name in {"context.load", "skill.load"}]
    assert [s.name for s in sdk_loads] == (["context.load"] if policy == "default" else [])
    for span in sdk_loads:
        assert span.parent == parent.get_span_context()
    exporter.clear()

    assert verified._tracing is not client_optout
    backend = ReadOnlyContextBackend(verified, authorize=lambda *args: None)
    with tracer.start_as_current_span("adapter-read"):
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
        # A per-call opt-out must not disable the later independent adapter read.
        assert [span.name for span in loads] == ["skill.load"]
        assert loads[-1].attributes["fi.skill.name"] == "refund"
