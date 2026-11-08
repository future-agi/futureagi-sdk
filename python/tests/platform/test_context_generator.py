"""Synthetic contract fixtures qualify codegen without inventing production endpoints."""

from __future__ import annotations

import copy
import inspect
import sys
from pathlib import Path
from types import ModuleType

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from sdkgen.generator import catalog, python, typescript  # noqa: E402

SPEC = {
    "definitions": {"FixtureAck": {"type": "object", "required": ["id"], "properties": {"id": {"type": "string"}}}},
    "paths": {
        "/fixture/start/": {"post": {
            "operationId": "fixture_start",
            "parameters": [
                {"name": "Idempotency-Key", "in": "header", "type": "string", "required": True},
                {"name": "body", "in": "body", "schema": {"type": "object", "properties": {"note": {"type": "string"}}}},
            ],
            "responses": {"202": {"schema": {"$ref": "#/definitions/FixtureAck"}}},
        }},
        "/fixture/manifest/": {"get": {
            "operationId": "fixture_manifest",
            "parameters": [
                {"name": "X-Context-Resolution", "in": "header", "type": "string", "required": True},
                {"name": "file_offset", "in": "query", "type": "integer"},
            ],
            "responses": {"200": {"schema": {"type": "object"}}},
        }},
        "/fixture/download/": {"get": {
            "operationId": "fixture_download",
            "parameters": [{"name": "X-Context-Resolution", "in": "header", "type": "string"}],
            "responses": {"200": {"schema": {"type": "file"}}},
        }},
    },
}
CATALOG = {"operations": [
    {"id": "fixture.start", "operation": {"method": "POST", "path": "/fixture/start/"}, "surfaces": {"sdk": {}}},
    {"id": "fixture.manifest", "operation": {"method": "GET", "path": "/fixture/manifest/"}, "surfaces": {"sdk": {}}},
    {"id": "fixture.download", "operation": {"method": "GET", "path": "/fixture/download/", "decode": "bytes"}, "surfaces": {"sdk": {}}},
]}


def test_header_and_download_signatures_match_both_languages():
    ops = catalog.load(copy.deepcopy(SPEC), CATALOG)
    py, ts = python.emit_resources(ops), typescript.emit_resources(ops)
    assert "idempotency_key: str" in py and "resolution_id: str" in py
    assert "options = operation_options(options, {'Idempotency-Key': idempotency_key}, required=('Idempotency-Key',))" in py
    assert "-> bytes:" in py and "-> models.FixtureAck:" in py
    assert '"X-Context-Resolution": params.resolution_id' in ts
    assert "idempotency_key: string;" in ts and "resolution_id: string;" in ts
    assert "Promise<Uint8Array>" in ts and "Promise<models.FixtureAck>" in ts
    assert "class FixtureAck" in python.emit_models(SPEC, ops)
    assert "export interface FixtureAck" in typescript.emit_models(SPEC, ops)
    assert "'decode': 'bytes'" in python.emit_operations(ops)
    assert '"decode": "bytes"' in typescript.emit_operations(ops)
    for line in (py + ts).splitlines():
        if "query =" in line or "body =" in line or "query:" in line or "body:" in line:
            assert "Idempotency-Key" not in line and "X-Context-Resolution" not in line


@pytest.mark.parametrize("name", ["Authorization", "X-Api-Key", "X-Secret-Key", "X-Workspace-Id", "X-Arbitrary"])
def test_non_operation_headers_fail_codegen(name):
    spec = copy.deepcopy(SPEC)
    spec["paths"]["/fixture/start/"]["post"]["parameters"][0]["name"] = name
    with pytest.raises(catalog.CatalogError, match="not allowlisted"):
        catalog.load(spec, CATALOG)


def test_header_duplicates_types_and_argument_collisions_fail_codegen():
    for variation in ("duplicate", "integer", "body_collision", "normalized_collision"):
        spec = copy.deepcopy(SPEC)
        params = spec["paths"]["/fixture/start/"]["post"]["parameters"]
        if variation == "duplicate":
            params.append({**params[0], "name": "idempotency-key"})
        elif variation == "integer":
            params[0]["type"] = "integer"
        else:
            name = "idempotency-key" if variation == "normalized_collision" else "idempotency_key"
            params[1]["schema"]["properties"][name] = {"type": "string"}
        with pytest.raises(catalog.CatalogError):
            catalog.load(spec, CATALOG)


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
@pytest.mark.asyncio
async def test_generated_methods_send_headers_and_return_binary(monkeypatch, is_async):
    from fi.platform import (
        AsyncClient,
        Client,
        ContextAuth,
        RequestOptions,
        _operations,
        models,
    )

    ops = catalog.load(copy.deepcopy(SPEC), CATALOG)
    # Execute the real emitters in their package context, not a hand-written imitation.
    operations = ModuleType("fi.platform.fixture_operations")
    exec(python.emit_operations(ops), operations.__dict__)
    generated_models = ModuleType("fi.platform.fixture_models")
    monkeypatch.setitem(sys.modules, generated_models.__name__, generated_models)
    exec(python.emit_models(SPEC, ops), generated_models.__dict__)
    monkeypatch.setattr(models, "FixtureAck", generated_models.FixtureAck, raising=False)
    for op in ops:
        monkeypatch.setattr(_operations, python.op_constant(op), getattr(operations, python.op_constant(op)), raising=False)
    resources = ModuleType("fi.platform.resources.fixture_base")
    exec(python.emit_resources(ops), resources.__dict__)
    seen = []
    def handle(req):
        seen.append(req)
        if req.url.path.endswith("download/"):
            return httpx.Response(200, content=b"PK\x00\xff")
        if req.url.path.endswith("start/"):
            return httpx.Response(202, json={"status": True, "result": {"id": "job"}})
        return httpx.Response(200, json={"status": True, "result": {"file_offset": 25}})
    cls, http_cls, resource_cls = (AsyncClient, httpx.AsyncClient, resources.AsyncFixtureResource) if is_async else (Client, httpx.Client, resources.FixtureResource)
    client = cls(auth=ContextAuth("synthetic-context"), base_url="https://fixture.test", http_client=http_cls(transport=httpx.MockTransport(handle)))
    fixture = resource_cls(client._transport)
    async def result(value):
        return await value if inspect.isawaitable(value) else value
    ack = await result(fixture.start(idempotency_key="original-key", note="content"))
    assert ack.id == "job"
    assert await result(fixture.manifest(resolution_id="lease-7", file_offset=25)) == {"file_offset": 25}
    assert await result(fixture.download(resolution_id="lease-7")) == b"PK\x00\xff"
    assert seen[0].headers["idempotency-key"] == "original-key"
    assert seen[0].content == b'{"note":"content"}'
    assert seen[1].headers["x-context-resolution"] == "lease-7"
    assert str(seen[1].url) == "https://fixture.test/fixture/manifest/?file_offset=25"
    assert seen[2].headers["x-context-resolution"] == "lease-7"
    with pytest.raises(ValueError, match="conflicting"):
        await result(fixture.manifest(resolution_id="lease-7", options=RequestOptions(resolution_id="lease-8")))
    assert len(seen) == 3
