"""Generator contract cases collected through test_generator."""

from __future__ import annotations

import copy
import json
import re

import pytest

from ._generator_support import CATALOG, CONTRACT, _with, generate, pygen, tsgen


def test_patch_bodies_are_partial_unless_the_catalog_says_otherwise():
    """[P2, review 2] The contract marks the create serializer's fields required on PATCH too;
    the backend accepts any subset. A description-only dashboard update must type-check."""
    ops = {o.id: o for o in generate.load(CONTRACT, CATALOG)}
    assert CONTRACT["definitions"]["DashboardCreateUpdate"]["required"] == ["name"]
    assert not any(
        p.required for p in ops["dashboards.update"].params if p.location == "body"
    )
    assert not any(
        p.required
        for p in ops["annotation_queues.update"].params
        if p.location == "body"
    )
    assert any(
        p.required for p in ops["dashboards.create"].params if p.location == "body"
    )  # a POST keeps them
    import inspect

    from fi.platform.resources.base import DashboardsResource

    assert (
        inspect.signature(DashboardsResource.update).parameters["name"].default
        is not inspect.Parameter.empty
    )


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
    contract["definitions"]["DashboardCreateUpdate"]["properties"]["color"] = {
        "type": "string"
    }
    ops = {o.id: o for o in generate.load(contract, CATALOG)}
    assert "color" in {p.name for p in ops["dashboards.create"].params} and "color" in {
        p.name for p in ops["dashboards.update"].params
    }
    assert "color: str | None | NotGiven = NOT_GIVEN" in pygen.emit_resources(
        list(ops.values())
    )
    assert "color?: string | null;" in tsgen.emit_resources(list(ops.values()))
    # The same for a response: a new field appears on the model.
    contract["definitions"]["DashboardDetail"]["properties"]["color"] = {
        "type": "string"
    }
    assert "    color: Optional[str] = Field(default=None)" in pygen.emit_models(
        contract, list(generate.load(contract, CATALOG).__iter__())
    )


def test_an_operation_the_catalog_does_not_select_stays_out_of_the_sdk():
    """The allowlist is deliberate: a backend route without a catalog entry gets no method, and
    nothing counts that as missing coverage."""
    assert (
        "/model-hub/kb/supported_embedding_models/" not in CONTRACT["paths"]
    )  # not even in the slice
    ops = generate.load(CONTRACT, CATALOG)
    assert not any("supported_embedding_models" in op.path for op in ops)
    from fi.platform.resources.base import KnowledgeBasesResource

    assert not hasattr(KnowledgeBasesResource, "supported_embedding_models")
    assert {"create", "get", "list", "update", "delete"} <= {
        name for name in dir(KnowledgeBasesResource) if not name.startswith("_")
    }


@pytest.mark.parametrize(
    "op_id, fix, message",
    [
        (
            "annotation_queues.update",
            {"body_required": [], "note": "n"},
            "body_required is stale",
        ),
        (
            "prompts.history",
            {"query": {"template_id": "string", "page": "integer"}, "note": "n"},
            "query.page is stale",
        ),
        (
            "dashboards.get",
            {"returns": "DashboardDetail", "note": "n"},
            "returns is stale",
        ),
        (
            "dashboards.create",
            {"body": {"name": "string", "description": "string"}, "note": "n"},
            "body is stale",
        ),
        (
            "dashboards.create",
            {
                "body": {"name": "string"},
                "body_fields": {"name": "string"},
                "note": "n",
            },
            "use body_fields alone",
        ),
        ("dashboards.create", {"returns": "Nope", "note": "n"}, "not a definition"),
        (
            "dashboards.create",
            {"returns": "DashboardDetail", "untyped": True, "note": "n"},
            "contradict",
        ),
        (
            "annotation_queues.get",
            {"optional_in_response": ["label_ids"], "note": "n"},
            "already made optional by annotation_queues.create",
        ),
        (
            "annotation_queues.get",
            {"optional_in_response": ["description"], "note": "n"},
            "optional_in_response.description is stale",
        ),
    ],
)
def test_a_contract_fix_the_contract_no_longer_needs_fails_the_build(
    op_id, fix, message
):
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
    assert (
        "label_ids" not in models.AnnotationQueue.__required__
        and "name" in models.AnnotationQueue.__required__
    )  # optional_in_response
    assert (
        models.PromptsRunResult.__required__ == frozenset()
    )  # synthesized from the catalog: nothing is promised
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
    catalog = _with(
        "datasets.list_names",
        operation={
            "method": "GET",
            "path": "/model-hub/develops/get-datasets-names/",
            "multipart": True,
        },
    )
    with pytest.raises(generate.CatalogError, match="multipart is only meaningful"):
        generate.load(CONTRACT, catalog)


def test_docs_reference_covers_every_sdk_operation_once():
    """The docs site's SDK reference (docs/sdk-reference) is generated from the same catalog."""
    from sdkgen.generator import docs as docsgen

    spec, ops, _ = generate.load_ops()
    pages = docsgen.emit_pages(spec, ops)
    headings = [
        line
        for text in pages.values()
        for line in text.splitlines()
        if line.startswith("### ")
    ]
    for op in ops:
        if "sdk" in op.surfaces:
            assert headings.count(f"### {op.id}") == 1, op.id

    def hrefs(items):
        for item in items:
            if "href" in item:
                yield item["href"]
            yield from hrefs(item.get("items", []))

    nav = set(hrefs(json.loads(pages["navigation.json"])["items"]))
    for name in pages:
        if name.endswith(".mdx"):
            href = (
                docsgen.SITE_PATH
                if name == "index.mdx"
                else f"{docsgen.SITE_PATH}/{name[:-4]}"
            )
            assert href in nav, name
            nav.discard(href)
    assert not nav, f"navigation lists pages that do not exist: {nav}"
    for name, text in pages.items():
        if name.endswith(".mdx"):
            assert text.startswith("---\ntitle: ") and "\ndescription: " in text, name
            # Every model link points at a heading or a row anchor on one of the pages.
            for page, anchor in set(
                re.findall(
                    r"\]\((?:"
                    + re.escape(docsgen.SITE_PATH)
                    + r"/([a-z-]+))?#([a-z0-9_-]+)\)",
                    text,
                )
            ):
                page_text = pages[f"{page}.mdx"] if page else text
                anchors = {
                    docsgen.slug(line.lstrip("#").strip())
                    for line in page_text.splitlines()
                    if line.startswith("#")
                } | set(re.findall(r'<span id="([a-z0-9_-]+)">', page_text))
                assert anchor in anchors, (name, page, anchor)
