import httpx
import pytest
from conftest import Source
from fi import __version__
from fi.platform import Client, ContextAuth
from fi.skills import SkillsClient
from fi.telemetry import configure


@pytest.mark.parametrize("mode", ["on", "load_only", "off", "no_otel"])
def test_resolve_header_only_and_versioned_user_agent(tracing, monkeypatch, mode):
    import opentelemetry.trace as trace
    _, _, provider = tracing
    source = Source()
    seen = []
    if mode == "no_otel":
        configure()
        monkeypatch.delitem(__import__("sys").modules, "fi_instrumentation.otel", raising=False)
        monkeypatch.setattr(trace, "get_tracer_provider", lambda: trace.ProxyTracerProvider())
    else:
        configure(skills_tracing=mode, tracer_provider=provider)
    def handler(request):
        seen.append(request)
        if request.url.path.endswith("resolve/"):
            result = source.resolve(name="refund", selector={"label": "production"})
        else:
            from fi.context.snapshot import SnapshotIdentity
            identity = SnapshotIdentity("skill", source.id, source.name, 3, source.version_id,
                                        source.resolve(name="refund", selector={"label": "production"})["digest"])
            result = source.chunk(identity, path=request.url.params["path"], offset=0, options=None)
        return httpx.Response(200, json={"result": result})
    with Client(auth=ContextAuth(credential="synthetic-context-credential"), base_url="https://fixture.invalid",
                http_client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
        snapshot = SkillsClient(client).resolve("refund")
        snapshot.read_file("SKILL.md")
    assert seen[0].headers["User-Agent"] == "futureagi-python/" + __version__
    assert seen[0].headers["X-FI-Skills-Tracing"] == mode
    assert "X-FI-Skills-Tracing" not in seen[1].headers


def test_client_optout_header(tracing):
    from types import SimpleNamespace

    from fi.context.source import ConsumptionSource
    seen = []
    def call(*args, **kwargs):
        seen.append(kwargs)
    source = ConsumptionSource(SimpleNamespace(_transport=SimpleNamespace(call=call)), kind="skill", tracing=False)
    source.resolve(name="refund", selector={"label": "production"})
    assert seen[0]["options"].headers == {"X-FI-Skills-Tracing": "off"}
