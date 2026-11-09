"""The catalog is the source of truth: these tests show what it guarantees (no backend needed)."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from sdkgen import generator as generate  # noqa: E402
from sdkgen.generator import python as pygen  # noqa: E402
from sdkgen.generator import typescript as tsgen  # noqa: E402

CONTRACT = json.loads((ROOT / "sdkgen" / "contracts" / "swagger.json").read_text())
CATALOG = yaml.safe_load((ROOT / "sdkgen" / "catalog" / "operations.yaml").read_text())
# The MCP server and its manifest live in the monorepo (futureagi/mcp_server/catalog); the
# catalog here only records which MCP tool each operation corresponds to. The monorepo's
# E2E CI compares the two.
MCP_IDS = {e["id"] for e in CATALOG["operations"] if e["surfaces"].get("mcp") not in (None, False)}


def _with(op_id: str, **changes) -> dict:
    catalog = copy.deepcopy(CATALOG)
    next(e for e in catalog["operations"] if e["id"] == op_id).update(changes)
    return catalog


def test_committed_outputs_are_up_to_date():
    stale = [str(p.relative_to(ROOT)) for p, text in generate.build().items() if p.read_text() != text]
    assert not stale, f"run python sdkgen/generate.py: {stale}"
    missing = [str(p.relative_to(ROOT)) for p in generate.scaffolds() if not p.exists()]
    assert not missing, f"run python sdkgen/generate.py to scaffold: {missing}"


def test_scaffolds_are_owned_by_hand():
    """A resource module is created once and never regenerated: spans.py has a hand-written method."""
    scaffolds = generate.scaffolds()
    spans_py = generate.PY_PLATFORM / "resources" / "spans.py"
    spans_ts = generate.TS_PLATFORM / "resources" / "spans.ts"
    assert spans_py in scaffolds and spans_py not in generate.build()
    assert "def ingest" in spans_py.read_text() and "def ingest" not in scaffolds[spans_py]
    assert "ingest(" in spans_ts.read_text() and "ingest(" not in scaffolds[spans_ts]


def test_resources_can_be_swapped_and_extended():
    from fi.platform import Client
    from fi.platform.resources import Datasets
    from fi.platform.resources.base import (
        DatasetsColumnsResource,
        DatasetsResource,
    )

    class Columns(DatasetsColumnsResource):
        def mine(self) -> str:
            return "custom columns"

    class MyDatasets(Datasets):
        _children = {**DatasetsResource._children, "columns": Columns}

        def mine(self) -> str:
            return "custom datasets"

    class Billing:
        def __init__(self, transport) -> None:
            self._t = transport

    class MyClient(Client):
        _resources = {**Client._resources, "datasets": MyDatasets, "billing": Billing}

    client = MyClient(api_key="k", secret_key="s", base_url="http://unused")
    assert client.datasets.mine() == "custom datasets" and client.datasets.columns.mine() == "custom columns"
    assert callable(client.datasets.columns.add) and callable(client.datasets.rows.add)  # generated methods still there
    assert client.billing._t is client._transport
    assert callable(client.spans.ingest)  # hand-written in fi/platform/resources/spans.py
    assert callable(client.request)


def test_generated_methods_cannot_shadow_the_hand_written_client():
    catalog = copy.deepcopy(CATALOG)
    next(e for e in catalog["operations"] if e["id"] == "datasets.list_names")["id"] = "datasets.request"
    with pytest.raises(generate.CatalogError, match="reserved"):
        pygen.emit_resources(generate.load(CONTRACT, catalog))


def test_typescript_mirrors_the_python_client():
    ops = generate.load(CONTRACT, CATALOG)
    ts = tsgen.emit_resources(ops)
    by_id = {op.id: op for op in ops}
    assert tsgen.ts_method(by_id["datasets.create_from_file"]) == "createFromFile"
    assert tsgen.ts_attr("knowledge_bases") == "knowledgeBases"
    # Same operations, same wire fields, same path params; only the casing differs.
    assert "export class KnowledgeBasesResource extends Resource" in ts
    assert "createFromFile(params: DatasetsCreateFromFileParams, options?: RequestOptions): Promise<models.LocalFileDatasetCreateStartedResult>" in ts
    assert "get(datasetId: string, params: DatasetsGetParams = {}, options?: RequestOptions): Promise<models.DatasetTableResult>" in ts
    assert "list(params: DatasetsListParams = {}, options?: RequestOptions): Pager<models.DatasetListItem>" in ts
    assert "whoami(options?: RequestOptions): Promise<models.UserInfoResponse>" in ts  # no params at all
    assert 'files: { file: params.file }' in ts
    index = tsgen.emit_resource_index(ops)
    assert "knowledgeBases: KnowledgeBases" in index and "annotationQueues: AnnotationQueues" in index


def test_surfaces_ship_independently():
    from fi.platform import Client

    sdk_ids = {e["id"] for e in CATALOG["operations"] if e["surfaces"].get("sdk") is not False}
    assert "datasets.columns.add" in sdk_ids - MCP_IDS  # SDK-only
    client = Client(api_key="k", secret_key="s", base_url="http://unused")
    assert callable(client.datasets.columns.add)


def test_mcp_names_keep_existing_tools_or_follow_the_id():
    # Exact agreement with the serializer-generated manifest pinned at integration.
    ops = {o.id: o for o in generate.load(CONTRACT, CATALOG)}
    names = {op_id: ops[op_id].surfaces["mcp"]["name"] for op_id in MCP_IDS}
    pinned = json.loads((ROOT / "sdkgen/contracts/mcp-tools.json").read_text())
    assert set(names.values()) == {tool["name"] for tool in pinned["tools"]}
    assert names["datasets.list"] == "list_datasets"
    assert names["traces.list"] == "search_traces"
    # Without an override the name follows the id.
    catalog = _with("datasets.columns.add", surfaces={"sdk": {}, "mcp": {"group": "datasets", "access": "write"}})
    op = next(o for o in generate.load(CONTRACT, catalog) if o.id == "datasets.columns.add")
    assert op.surfaces["mcp"]["name"] == "datasets_columns_add"


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"surfaces": {"sdk": {}, "web": {}}}, "unknown surface"),
        ({"surfaces": {"mcp": {"access": "read"}}}, "mcp.group is required"),
        ({"surfaces": {"sdk": {"stability": "alpha"}}}, "stability"),
        ({"surfaces": {"sdk": False, "mcp": False}}, "ships to no surface"),
        ({"operation": {"method": "GET", "path": "/nope/"}}, "not in the contract"),
        ({"pagination": {"page_param": "cursor", "size_param": "page_size", "first_page": 1,
                         "items": "datasets", "total_pages": "total_pages"}}, "not a query param"),
        ({"surfaces": {"mcp": {"name": "create_dataset", "group": "d", "access": "read"}}}, "already used"),
    ],
)
def test_catalog_mistakes_fail_the_build(changes, message):
    with pytest.raises(generate.CatalogError, match=message):
        generate.load(CONTRACT, _with("datasets.list", **changes))


def test_pagination_needs_first_page_and_items():
    with pytest.raises(generate.CatalogError, match="first_page is required"):
        generate.load(CONTRACT, _with("datasets.list", pagination={"page_param": "page", "size_param": "page_size", "items": "datasets", "total_pages": "total_pages"}))


def test_body_params_on_a_paginated_op_fail_the_build():
    # evals.templates.list is a POST with body params; paginating it would drop them silently.
    catalog = _with("evals.templates.list", pagination={"page_param": "page", "size_param": "page_size", "first_page": 1, "items": "items", "total_items": "total"})
    with pytest.raises(generate.CatalogError, match="sends no body"):
        generate.load(CONTRACT, catalog)


def test_sdk_only_parity_ops_do_not_reach_mcp():
    """The hand-written modules' operations ship to the SDK only; the MCP tool list keeps its 105 tools."""
    for op_id in ("prompts.commit", "file_knowledge_bases.create", "knowledge_bases.create", "annotation_queues.create", "scores.create", "datasets.create_from_file"):
        assert op_id not in MCP_IDS
    from fi.platform import Client

    client = Client(api_key="k", secret_key="s", base_url="http://unused")
    assert callable(client.prompts.labels.assign) and callable(client.file_knowledge_bases.files.delete)


def test_request_fixes_replace_what_the_contract_gets_wrong():
    ops = {o.id: o for o in generate.load(CONTRACT, CATALOG)}
    # body: drf-yasg documented the response serializer as the request; the fix names the real fields.
    commit = ops["prompts.commit"]
    assert [(p.name, p.required) for p in commit.params if p.location == "body"][:2] == [("version_name", True), ("message", False)]
    assert commit.returns is None  # untyped: the server answers with a message string
    # body_required: a view that needs fields on a PATCH (the generator makes PATCH bodies partial).
    assert {p.name for p in ops["evals.tasks.update"].params if p.location == "body" and p.required} == {"eval_task_id", "edit_type"}
    # query: a filter the contract leaves out.
    assert "template_id" in {p.name for p in ops["prompts.history"].params if p.location == "query"}
    # `as`: the wire field is `file`, the Python argument is `files`.
    upload = next(p for p in ops["file_knowledge_bases.create"].params if p.name == "file")
    assert upload.arg_name == "files" and ops["file_knowledge_bases.create"].multipart
    # body_fields: one field patched, the rest of the contract's body kept.
    score = {p.name: p for p in ops["scores.create"].params if p.location == "body"}
    assert score["value"].schema.get("x-json-value") and score["value"].required and {"source_type", "label_id", "notes"} <= set(score)
    # returns: a definition of the contract, or an object synthesized from the catalog's fields.
    assert ops["dashboards.create"].returns == {"$ref": "#/definitions/DashboardDetail"}
    assert ops["prompts.run"].returns == {"$ref": "#/definitions/PromptsRunResult"}
    assert set(CONTRACT["definitions"]["PromptsRunResult"]["properties"]) == {"template_id", "prompt_config", "variable_names", "evaluation_configs", "placeholders"}


def test_patch_bodies_are_partial_unless_the_catalog_says_otherwise():
    """[P2, review 2] The contract marks the create serializer's fields required on PATCH too;
    the backend accepts any subset. A description-only dashboard update must type-check."""
    ops = {o.id: o for o in generate.load(CONTRACT, CATALOG)}
    assert CONTRACT["definitions"]["DashboardCreateUpdate"]["required"] == ["name"]
    assert not any(p.required for p in ops["dashboards.update"].params if p.location == "body")
    assert not any(p.required for p in ops["annotation_queues.update"].params if p.location == "body")
    assert any(p.required for p in ops["dashboards.create"].params if p.location == "body")  # a POST keeps them
    import inspect

    from fi.platform.resources.base import DashboardsResource

    assert inspect.signature(DashboardsResource.update).parameters["name"].default is not inspect.Parameter.empty


def test_json_value_inputs_accept_any_json_in_both_languages():
    """[P2, review 2] `x-json-value` fields (and the patched score value) take a string or a
    number as much as an object: `Any` in Python, the recursive `JsonValue` in TypeScript."""
    text = pygen.emit_resources(generate.load(CONTRACT, CATALOG))
    assert "is_run: Any | None | NotGiven = NOT_GIVEN" in text
    assert "value: Any," in text  # scores.create: required, any JSON
    ts = tsgen.emit_resources(generate.load(CONTRACT, CATALOG))
    assert "is_run?: JsonValue | null;" in ts and "  value: JsonValue;" in ts
    assert "import type { FileInput, JsonValue, RequestOptions, Transport }" in ts


def test_a_field_added_to_a_selected_request_schema_reaches_the_generated_signature():
    """The generation objective: the selected surface follows the contract. A field the backend
    adds to a selected operation's request appears in the SDK without a catalog change."""
    contract = copy.deepcopy(CONTRACT)
    contract["definitions"]["DashboardCreateUpdate"]["properties"]["color"] = {"type": "string"}
    ops = {o.id: o for o in generate.load(contract, CATALOG)}
    assert "color" in {p.name for p in ops["dashboards.create"].params} and "color" in {p.name for p in ops["dashboards.update"].params}
    assert "color: str | None | NotGiven = NOT_GIVEN" in pygen.emit_resources(list(ops.values()))
    assert "color?: string | null;" in tsgen.emit_resources(list(ops.values()))
    # The same for a response: a new field appears on the model.
    contract["definitions"]["DashboardDetail"]["properties"]["color"] = {"type": "string"}
    assert "    color: Optional[str] = Field(default=None)" in pygen.emit_models(contract, list(generate.load(contract, CATALOG).__iter__()))


def test_an_operation_the_catalog_does_not_select_stays_out_of_the_sdk():
    """The allowlist is deliberate: a backend route without a catalog entry gets no method, and
    nothing counts that as missing coverage."""
    assert "/model-hub/kb/supported_embedding_models/" not in CONTRACT["paths"]  # not even in the slice
    ops = generate.load(CONTRACT, CATALOG)
    assert not any("supported_embedding_models" in op.path for op in ops)
    from fi.platform.resources.base import KnowledgeBasesResource

    assert not hasattr(KnowledgeBasesResource, "supported_embedding_models")
    assert {"create", "get", "list", "update", "delete"} <= {name for name in dir(KnowledgeBasesResource) if not name.startswith("_")}


@pytest.mark.parametrize(
    "op_id, fix, message",
    [
        ("annotation_queues.update", {"body_required": [], "note": "n"}, "body_required is stale"),
        ("prompts.history", {"query": {"template_id": "string", "page": "integer"}, "note": "n"}, "query.page is stale"),
        ("dashboards.get", {"returns": "DashboardDetail", "note": "n"}, "returns is stale"),
        ("dashboards.create", {"body": {"name": "string", "description": "string"}, "note": "n"}, "body is stale"),
        ("dashboards.create", {"body": {"name": "string"}, "body_fields": {"name": "string"}, "note": "n"}, "use body_fields alone"),
        ("dashboards.create", {"returns": "Nope", "note": "n"}, "not a definition"),
        ("dashboards.create", {"returns": "DashboardDetail", "untyped": True, "note": "n"}, "contradict"),
        ("annotation_queues.get", {"optional_in_response": ["label_ids"], "note": "n"}, "already made optional by annotation_queues.create"),
        ("annotation_queues.get", {"optional_in_response": ["description"], "note": "n"}, "optional_in_response.description is stale"),
    ],
)
def test_a_contract_fix_the_contract_no_longer_needs_fails_the_build(op_id, fix, message):
    """Each fix is a backend bug with a note; once the backend fixes it, the fix must go."""
    with pytest.raises(generate.CatalogError, match=message):
        generate.load(copy.deepcopy(CONTRACT), _with(op_id, contract_fix=fix))
    # `body_fields` too: the score value patch is stale once the contract marks the field itself.
    contract = copy.deepcopy(CONTRACT)
    contract["definitions"]["CreateScore"]["properties"]["value"]["x-json-value"] = True
    with pytest.raises(generate.CatalogError, match="body_fields.value is stale"):
        generate.load(contract, CATALOG)


def test_models_list_their_required_fields_for_strict_mode():
    from fi.platform import models

    assert "organization" in models.KnowledgeBaseItem.__required__
    assert "label_ids" not in models.AnnotationQueue.__required__ and "name" in models.AnnotationQueue.__required__  # optional_in_response
    assert models.PromptsRunResult.__required__ == frozenset()  # synthesized from the catalog: nothing is promised
    assert models.DashboardDetail.__required__ == frozenset({"name"})


@pytest.mark.parametrize(
    "fix, message",
    [
        ({"body": {"x": "blob"}, "note": "n"}, "not one of"),
        ({"body_required": ["nope"], "note": "n"}, "unknown body fields"),
        ({"body": {"upload": "file"}, "note": "n"}, "need `operation.multipart: true`"),
    ],
)
def test_request_fix_mistakes_fail_the_build(fix, message):
    with pytest.raises(generate.CatalogError, match=message):
        generate.load(CONTRACT, _with("datasets.create", contract_fix=fix))


def test_multipart_needs_a_method_that_sends_a_body():
    catalog = _with("datasets.list_names", operation={"method": "GET", "path": "/model-hub/develops/get-datasets-names/", "multipart": True})
    with pytest.raises(generate.CatalogError, match="multipart is only meaningful"):
        generate.load(CONTRACT, catalog)
