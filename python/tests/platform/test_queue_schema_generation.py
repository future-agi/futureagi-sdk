"""Queue direction metadata is restored from the pinned serializer contract."""
import copy
import json

from ._gates_support import REPO, load


def test_queue_normalization_is_directional_and_idempotent():
    module = load("queue_contract_normalization", "scripts/normalize-queue-contract.py")
    snapshot = json.loads((REPO / module.SNAPSHOT).read_text())
    spec = json.loads((REPO / "openapi/sdk/generated/futureagi-sdk.openapi.json").read_text())
    queue = spec["components"]["schemas"]["AnnotationQueue"]
    # Reproduce Swagger 2's missing writeOnly metadata independently of whether
    # the committed document has already been normalized.
    queue["required"] = list(snapshot["create"]["required"])
    for field in queue["properties"].values():
        field.pop("writeOnly", None)
    body = spec["components"]["requestBodies"]["AnnotationQueue"]
    body["content"]["application/json"]["schema"]["$ref"] = "#/components/schemas/AnnotationQueue"
    old_response = copy.deepcopy(spec["paths"]["/model-hub/annotation-queues/"]["get"])
    module.normalize(spec, snapshot)
    assert "label_ids" not in queue["required"]
    request = spec["components"]["schemas"]["AnnotationQueueRequest"]
    assert "label_ids" in request["required"]
    assert "id" not in request["properties"]
    assert "label_ids" in queue["properties"]  # shared model remains a request builder
    assert spec["paths"]["/model-hub/annotation-queues/"]["get"] == old_response
    once = copy.deepcopy(spec)
    module.normalize(spec, snapshot)
    assert spec == once
