"""What a user's project sees: the installed wheel, not this repository's sources.

CI builds the wheel, installs it into an empty virtualenv, runs this file and type-checks it
with mypy. Every call here is one that must work (and type-check) for a user; each block names
the review finding it guards (nik13, PR #35, 2026-11-03). No backend: an httpx mock transport
answers with the shapes the live backend sends.
"""

from __future__ import annotations

import json
from typing import Any

import fi
import httpx
from fi.platform import (
    NOT_GIVEN,
    ApiKeyAuth,
    AsyncClient,
    Client,
    ContextAuth,
    RequestOptions,
    ResponseValidationError,
    models,
)
from fi.platform.models import DashboardDetail, KnowledgeBaseItem, PromptsRunResult

SEEN: list[dict[str, Any]] = []
DASHBOARD = {"id": "d1", "name": "review", "description": "", "widgets": []}
KB = {"id": "k1", "name": "k", "embedding_model": "BAAI/bge-small-en-v1.5", "chunk_size": 256, "organization": "o", "created_at": "2026-11-03T00:00:00Z", "updated_at": "2026-11-03T00:00:00Z"}


def handler(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content) if request.content else None
    SEEN.append({"method": request.method, "path": request.url.path, "body": body})
    if request.url.path.startswith("/tracer/dashboard/"):
        return httpx.Response(200, json={"status": True, "result": {**DASHBOARD, **(body or {})}})
    if request.url.path.startswith("/model-hub/kb/"):
        return httpx.Response(200, json={"status": True, "result": KB})
    if request.url.path.endswith("/run_template/"):
        return httpx.Response(200, json={"status": True, "result": {"template_id": "p1", "prompt_config": [], "variable_names": {}, "evaluation_configs": [], "placeholders": {}}})
    if request.url.path == "/model-hub/scores/":
        return httpx.Response(200, json={"status": True, "result": {"id": "s1", "source_type": "dataset_row", "value": (body or {})["value"]}})
    if request.url.path == "/model-hub/develops/create-empty-dataset/":
        return httpx.Response(200, json={"status": True, "result": {}})  # a broken backend: no dataset_id
    return httpx.Response(200, json={"status": True, "result": {"value": 1}})


client = Client(api_key="x", secret_key="y", base_url="http://backend.test", http_client=httpx.Client(transport=httpx.MockTransport(handler)))
assert fi.Client is Client

# JSON-value inputs take a string, a boolean or a number as much as an object.
receipt: PromptsRunResult = client.prompts.run("p1", version="v1", is_run="prompt")
client.prompts.run("p1", version="v1", is_run=False, placeholders={"nested": [1, "two", None]})
assert SEEN[-1]["body"]["is_run"] is False
score: models.Score = client.scores.create(source_type="dataset_row", source_id="r1", label_id="l1", value=0.7)
assert score.value == 0.7

# A PATCH is a partial update: a description-only dashboard update needs no name.
updated: DashboardDetail = client.dashboards.update("d1", description="description only")
assert SEEN[-1]["body"] == {"description": "description only"} and updated.description == "description only"

# A create answers with the detail, so the returned identifier feeds the next call.
template_id: str | None = receipt.template_id
dashboard: DashboardDetail = client.dashboards.create(name="review")
assert dashboard.id == "d1" and client.dashboards.get(dashboard.id).name == "review"
kb: KnowledgeBaseItem = client.knowledge_bases.create(name="k", chunk_size=256)
assert client.knowledge_bases.get(kb.id or "").chunk_size == 256
client.knowledge_bases.delete(kb.id or "")

# Omitted arguments are left out; an explicit None is sent as null.
client.dashboards.update("d1", name=NOT_GIVEN, description=None)
assert SEEN[-1]["body"] == {"description": None}

# Strict mode holds a response to the contract's required fields; the default is tolerant.
strict = Client(api_key="x", secret_key="y", base_url="http://backend.test", strict_responses=True, http_client=httpx.Client(transport=httpx.MockTransport(handler)))
try:
    strict.datasets.create(new_dataset_name="x")
    raise AssertionError("strict mode accepted a dataset-create result without dataset_id")
except ResponseValidationError:
    pass
assert client.datasets.create(new_dataset_name="x").dataset_id is None

# The escape hatches keep their types.
whole: Any = client.request("GET", "/x/", unwrap=None)
assert whole == {"status": True, "result": {"value": 1}}
# Explicit auth and immutable continuation remain usable from the installed wheel.
def context_handler(request: httpx.Request) -> httpx.Response:
    assert request.headers["authorization"] == "Context synthetic-context"
    assert request.headers["x-context-resolution"] == "synthetic-lease"
    assert not {"x-api-key", "x-secret-key"} & set(request.headers)
    return httpx.Response(200, content=b"PK\x00\xff")


context = Client(auth=ContextAuth("synthetic-context"), base_url="https://backend.test", http_client=httpx.Client(transport=httpx.MockTransport(context_handler)))
assert context.request("GET", "/fixture/", decode="bytes", options=RequestOptions(resolution_id="synthetic-lease")) == b"PK\x00\xff"
explicit = Client(auth=ApiKeyAuth("x", "y"), base_url="http://backend.test", http_client=httpx.Client(transport=httpx.MockTransport(handler)))
assert explicit.request("GET", "/x/") == {"value": 1}
async_context = AsyncClient(auth=ContextAuth("synthetic-context"), base_url="https://backend.test")
print(f"consumer: ok ({len(SEEN)} requests, template {template_id})")
