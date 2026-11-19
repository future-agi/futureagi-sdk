"""Refresh the platform model catalog operation from a local certified Swagger.

The paginator and filter overrides describe the server view where Swagger omits
query parameters. They are explicit so a contract repin can audit them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATION_ID = "model-hub_api_models_list_list"
QUERY = ["page", "limit", "name", "search", "model_type", "exclude_providers"]
DESCRIPTION = (
    "List the platform model catalog, not the gateway data-plane catalog. "
    "Returns a page that walks subsequent pages on the same authenticated origin. "
    "Availability describes configured providers; this call does not invoke a model."
)


def operation(swagger: dict) -> tuple[dict, dict]:
    matches = [
        (path, item, item["get"])
        for path, item in swagger["paths"].items()
        if item.get("get", {}).get("operationId") == OPERATION_ID
    ]
    if len(matches) != 1:
        raise ValueError("The certified Swagger must contain exactly one model catalog read")
    path, item, definition = matches[0]
    schema = definition["responses"]["200"]["schema"]
    if "$ref" in schema:
        schema = swagger["definitions"][schema["$ref"].rsplit("/", 1)[1]]
    if not {"count", "results", "next"} <= schema["properties"].keys():
        raise ValueError("The model catalog pagination contract has changed")
    row = {
        "id": "models.list", "method": "GET", "path": path,
        "unwrap": None,
        "pagination": {"page_param": "page", "size_param": "limit", "first_page": 1,
                       "items": "results", "next": "next", "total_items": "count",
                       "current_page": "current_page"},
        "query": sorted(QUERY), "path_params": [], "operation_id": OPERATION_ID,
        "public": "models.list", "description": DESCRIPTION,
    }
    source = {
        "operation_id": OPERATION_ID, "method": "GET", "path": path,
        "response_schema": schema,
        "declared_parameters": item.get("parameters", []) + definition.get("parameters", []),
        "overrides": {
            "query": QUERY,
            "pagination": {"current_page": "current_page", "last_page_selector": "last"},
            "source": ["futureagi/model_hub/views/run_prompt.py:LiteLLMModelListView",
                       "futureagi/tfc/utils/pagination.py:ExtendedPageNumberPagination"],
            "reason": "Swagger omits the view filters, inherited paginator parameters, and resolved current_page metadata",
        },
    }
    return row, source


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("swagger", type=Path)
    args = parser.parse_args()
    raw = args.swagger.read_bytes()
    row, source = operation(json.loads(raw))
    path = ROOT / "openapi/catalog/operations.json"
    catalog = json.loads(path.read_text())
    catalog["operations"] = [r for r in catalog["operations"] if r["id"] != row["id"]] + [row]
    path.write_text(json.dumps(catalog, indent=2) + "\n")
    source["swagger_sha256"] = "sha256:" + hashlib.sha256(raw).hexdigest()
    (ROOT / "openapi/catalog/models-source.json").write_text(json.dumps(source, indent=2) + "\n")


if __name__ == "__main__":
    main()
