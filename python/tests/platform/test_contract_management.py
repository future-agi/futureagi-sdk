"""Management coverage requires explicit public calls in both languages."""
import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fi._resources import AsyncCoreResource, CoreResource
from fi.errors import BadRequestError

from ._contract_runtime import Runtime, resolve
from ._gates_support import REPO, load


def inputs():
    doc = {"openapi": "3.0.3", "paths": {"/agentcc/config/": {"get": {
        "operationId": "activeConfig", "responses": {"200": {"description": "OK"}}}}}}
    mapping = {"operations": {"gateway.config.get_active": {"operation_id": "activeConfig", "methods": [{
        "py": "client.gateway.config.get_active", "ts": "client.gateway.config.getActive",
        "contract": {"py": {"args": [], "kwargs": {}}, "ts": {"args": []}}
    }]}}}
    return doc, mapping


def generator(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "scripts/platform"))
    return load("management_contract_cases", "scripts/platform/contract_cases.py")


def test_management_spec_generates_public_contract_adapters(monkeypatch):
    module = generator(monkeypatch)
    doc, mapping = inputs()
    rows = module.management_cases(doc, mapping)
    assert len(rows) == 1
    row = rows[0]
    assert row["adapter"] == "management"
    assert (row["method"], row["path"]) == ("GET", "/agentcc/config/")
    assert row["wrapper"]["py"] == "client.gateway.config.get_active"
    assert row["wrapper"]["ts"] == "client.gateway.config.getActive"
    assert row["invocation"] == mapping["operations"]["gateway.config.get_active"]["methods"][0]["contract"]


@pytest.mark.parametrize("language", ["py", "ts"])
def test_management_not_offered_twin_is_excluded_from_its_schedule(monkeypatch, language):
    module = generator(monkeypatch)
    doc, mapping = inputs()
    method = mapping["operations"]["gateway.config.get_active"]["methods"][0]
    method.pop(language)
    method["contract"].pop(language)
    method["not_offered"] = {language: {"status": "NOT-OFFERED", "reason": "Unavailable"}}
    rows = module.management_cases(doc, mapping)
    scheduled, excluded = module.public_inventory(rows, {}, {})
    for mode in ("py_sync", "py_async", "ts"):
        assert bool(excluded[mode]) == mode.startswith(language)
        assert bool(scheduled[mode]) != mode.startswith(language)


@pytest.mark.parametrize("mutation", ["missing_twin", "missing_fixture", "unmapped", "wrong_identity"])
def test_management_coverage_is_fail_closed(monkeypatch, mutation):
    module = generator(monkeypatch)
    doc, mapping = inputs()
    entry = mapping["operations"]["gateway.config.get_active"]
    if mutation == "missing_twin":
        entry["methods"][0].pop("ts")
    elif mutation == "missing_fixture":
        entry["methods"][0].pop("contract")
    elif mutation == "unmapped":
        mapping["operations"] = {}
    else:
        entry["operation_id"] = "unknown"
    with pytest.raises(ValueError):
        module.management_cases(doc, mapping)


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_missing_management_wrapper_never_falls_back_to_transport(monkeypatch, mode):
    row = generator(monkeypatch).management_cases(*inputs())[0]
    async def run():
        def unexpected_request(_):
            raise AssertionError("missing public method must not dispatch")
        from . import _contract_runtime
        client_name = "AsyncFutureAGIClient" if mode == "async" else "FutureAGIClient"
        real_client = getattr(_contract_runtime, client_name)
        class MissingMethodClient(real_client):
            @property
            def gateway(self):
                # Model a public namespace with its real method removed; never
                # assign the accepted client's read-only gateway accessor.
                return SimpleNamespace(config=SimpleNamespace())
        monkeypatch.setattr(_contract_runtime, client_name, MissingMethodClient)
        subject = Runtime(row, mode, unexpected_request)
        try:
            with pytest.raises(AttributeError, match="get_active"):
                await resolve(subject.call())
        finally:
            await subject.close()
    asyncio.run(run())


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_management_adapter_executes_explicit_public_call_and_envelope(monkeypatch, mode):
    row = generator(monkeypatch).management_cases(*inputs())[0]
    row["wrapper"] = {"py": "client.contract_fixture.get_active", "ts": "client.contractFixture.getActive"}
    operation = SimpleNamespace(__name__="fixture.active_config",
        _get_kwargs=lambda: {"method": "GET", "url": "/agentcc/config/"})
    class PublicFixture(CoreResource):
        def get_active(self):
            return self._request(operation)
    class AsyncPublicFixture(AsyncCoreResource):
        async def get_active(self):
            return await self._request(operation)
    async def run():
        requests, payload = [], [{"status": True, "result": {"revision": "fixture"}}]
        def handler(request):
            requests.append(request)
            return httpx.Response(200, json=payload[0], headers={"X-Request-Id": "management-fixture"})
        subject = Runtime(row, mode, handler)
        subject.client.contract_fixture = (AsyncPublicFixture if mode == "async" else PublicFixture)(subject.client.generated_client)
        try:
            assert await resolve(subject.call()) == {"revision": "fixture"}
            assert requests[0].url.path == row["path"]
            assert requests[0].method == row["method"]
            payload[0] = {"status": False, "code": "invalid", "result": "refused"}
            with pytest.raises(BadRequestError):
                await resolve(subject.call())
        finally:
            await subject.close()
    asyncio.run(run())
