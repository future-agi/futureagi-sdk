"""Async agent files use the async executor and retain journals on cancellation."""
import asyncio
import copy
import json

import httpx
import pytest
from fi import AsyncFutureAGIClient
from fi._core.platform_async import AsyncPlatformCore
from fi._core.transport import PlatformShared
from fi.agents.files import read_json
from fi.errors import ConfigurationError, ConflictError

DOCUMENT = {"schemaVersion": "futureagi-agent/v1", "spec": {"name": "Analyst", "role": "Researcher",
    "purpose": "Use supplied context", "responsibilities": [], "workMode": "on_demand", "connectorBindingIds": []}}


@pytest.mark.parametrize("scenario", ["roundtrip", "drift", "race", "cancel", "retarget", "malformed"])
def test_async_agent_code_lifecycle(monkeypatch, tmp_path, scenario):
    monkeypatch.setenv("FI_AGENT_CODE_ENABLED", "1")
    async def go():
        rows, calls = {}, []
        controls = {"race": False, "cancel": False}
        def envelope():
            spec, version = rows["a"]
            agent = {**copy.deepcopy(spec), "id": "a", "version": version, "connectorBindings": []}
            agent.pop("connectorBindingIds")
            if "environmentId" in agent:
                agent["environment"] = {"id": agent.pop("environmentId"), "revision": agent.pop("environmentRevision")}
            return {"schemaVersion": "omega-workforce/v1", "agent": agent}
        async def handler(request):
            calls.append(request)
            if request.method == "GET":
                if request.url.path.endswith("/workforce"):
                    payload = {"schemaVersion": "omega-workforce/v1", "agents": []}
                else:
                    payload = envelope()
                return httpx.Response(200, json=payload)
            body = json.loads(request.content)
            if controls["cancel"]:
                raise asyncio.CancelledError()
            if request.method == "POST":
                rows["a"] = (body, 1)
            else:
                if controls["race"]:
                    return httpx.Response(409, json={"code": "conflict"})
                expected = body.pop("expectedVersion")
                assert expected == rows["a"][1]
                if "environmentId" in body or "environmentRevision" in body:
                    assert "environmentId" in body and "environmentRevision" in body
                rows["a"] = ({**rows["a"][0], **body}, expected + 1)
            return httpx.Response(200, json=envelope())
        client = AsyncFutureAGIClient(api_key="person-key", secret_key="person-secret", base_url="http://127.0.0.1:1",
                                      organization_id="org-a", workspace_id="ws-a", retries=0)
        client.__dict__["_platform"] = AsyncPlatformCore(PlatformShared(client._resolve_platform_origin,
            transport=httpx.MockTransport(handler), retries=0))
        code = client.agents.code
        lock = tmp_path / "state"
        try:
            assert code.validate(DOCUMENT)["spec"]["name"] == "Analyst"
            assert (await code.plan(DOCUMENT, lockfile=lock))["action"] == "create"
            assert not lock.exists()
            await code.apply(DOCUMENT, lockfile=lock)
            saved = lock.read_bytes(), lock.stat().st_mtime_ns
            desired = copy.deepcopy(DOCUMENT)
            desired["spec"]["purpose"] = "New purpose"
            if scenario == "roundtrip":
                assert (await code.apply(DOCUMENT, lockfile=lock))["changed"] is False
                assert (lock.read_bytes(), lock.stat().st_mtime_ns) == saved
                await code.apply(desired, lockfile=lock)
                exported = await code.export("a")
                assert exported == code.validate(desired)
                assert (await code.import_definition(exported, agent_id="a", lockfile=tmp_path / "import"))["changed"] is False
            elif scenario == "drift":
                rows["a"][0]["purpose"] = "Remote edit"
                with pytest.raises(ConfigurationError, match="drift"):
                    await code.apply(desired, lockfile=lock)
                assert lock.read_bytes() == saved[0]
                await code.apply(desired, lockfile=lock, force=True)
            elif scenario in ("race", "cancel"):
                controls[scenario] = True
                with pytest.raises(ConflictError if scenario == "race" else asyncio.CancelledError):
                    await code.apply(desired, lockfile=lock, force=True)
                assert read_json(lock)["status"] == "pending"
                before = len(calls)
                with pytest.raises(ConfigurationError, match="unresolved"):
                    await code.apply(desired, lockfile=lock, force=True)
                assert len(calls) == before
            else:
                if scenario == "retarget":
                    state = read_json(lock)
                    state["target"]["organizationId"] = "org-b"
                    lock.write_text(json.dumps(state))
                else:
                    lock.write_text("null")
                before = len(calls)
                with pytest.raises(ConfigurationError):
                    await code.apply(desired, lockfile=lock, force=True)
                assert len(calls) == before
        finally:
            await client.aclose()
    asyncio.run(go())


def test_async_code_is_default_off_before_network(monkeypatch):
    monkeypatch.delenv("FI_AGENT_CODE_ENABLED", raising=False)
    async def go():
        async with AsyncFutureAGIClient(base_url="http://127.0.0.1:1") as client:
            with pytest.raises(ConfigurationError, match="disabled"):
                await client.agents.code.export("a")
    asyncio.run(go())
