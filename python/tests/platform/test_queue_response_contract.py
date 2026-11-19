"""Queue responses never contain the serializer's write-only creation inputs."""
import json

import httpx
import pytest
from fi import FutureAGIClient
from fi.generated.openapi_client.models.annotation_queue import AnnotationQueue

from ._gates_support import REPO

QUEUE_ID = "00000000-0000-4000-8000-000000000001"
QUEUE = {"id": QUEUE_ID, "name": "Review", "labels": []}
SNAPSHOT = json.loads((REPO / "tests/fixtures/server-contracts/annotation-queue-create.json").read_text())
WRITE_ONLY = {name for name, field in SNAPSHOT["serializer"]["declared_fields"].items()
              if field.get("write_only")}


@pytest.mark.parametrize("operation", ["list", "get", "create", "update"])
def test_public_queue_responses_omit_write_only_inputs(operation):
    response = {"count": 1, "next": None, "previous": None, "results": [QUEUE]} if operation == "list" else QUEUE
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(201 if operation == "create" else 200, json=response)
    with FutureAGIClient(api_key="fixture", secret_key="fixture", base_url="http://127.0.0.1:9") as client:
        client.generated_client.set_httpx_client(httpx.Client(
            base_url="http://127.0.0.1:9", transport=httpx.MockTransport(handler)))
        queues = client.annotation_queues
        if operation == "list":
            result = queues.list()
        elif operation == "get":
            result = queues.get(QUEUE_ID)
        elif operation == "create":
            result = queues.create({"name": "Review", "label_ids": [QUEUE_ID]})
        else:
            result = queues.update(QUEUE_ID, {"name": "Review", "label_ids": [QUEUE_ID]})
    assert result == response
    assert len(requests) == 1
    assert WRITE_ONLY.isdisjoint(QUEUE)
    if operation in ("create", "update"):
        assert json.loads(requests[0].content)["label_ids"] == [QUEUE_ID]


def test_shared_queue_constructor_and_response_parser_preserve_compatibility():
    assert AnnotationQueue(name="Review").to_dict() == {"name": "Review"}
    assert AnnotationQueue.from_dict(QUEUE).to_dict() == QUEUE


def test_generated_schema_separates_required_request_fields_from_response():
    spec = json.loads((REPO / "openapi/sdk/generated/futureagi-sdk.openapi.json").read_text())
    schemas = spec["components"]["schemas"]
    response = schemas["AnnotationQueue"]
    assert WRITE_ONLY.isdisjoint(response["required"])
    assert all(response["properties"][name]["writeOnly"] for name in WRITE_ONLY)
    create = spec["paths"]["/model-hub/annotation-queues/"]["post"]
    body = create["requestBody"]
    if "$ref" in body:
        body = spec["components"]["requestBodies"][body["$ref"].rsplit("/", 1)[-1]]
    ref = body["content"]["application/json"]["schema"]["$ref"]
    request = schemas[ref.rsplit("/", 1)[-1]]
    assert set(SNAPSHOT["create"]["required"]) <= set(request["required"])
    assert request is not response
