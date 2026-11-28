"""Skills and context consumption invariants of the public SDK contract."""

import json
from pathlib import Path

import pytest

CONTRACTS = Path(__file__).resolve().parents[3] / "sdkgen/contracts"
CONTEXTS = "/model-hub/skills/contexts/"
CONSUMPTION = "/model-hub/skills/consumption/"
VERSION = "{resource_id}/versions/{number}/"
RESOLVE = {("get", root + "resolve/") for root in (CONTEXTS, CONSUMPTION)}
LEASED = {
    (method, root + VERSION + endpoint)
    for root in (CONTEXTS, CONSUMPTION)
    for method, endpoint in (("get", "manifest/"), ("get", "files/"), ("post", "access-check/"))
}
INSPECTION = {("get", CONTEXTS + suffix) for suffix in (
    "", "{context_id}/", "{context_id}/versions/", "{context_id}/versions/{number}/inspection/",
)}
ISSUE = ("post", CONTEXTS + "credentials/")
CREDENTIAL_ADMIN = {ISSUE, ("get", CONTEXTS + "credentials/"), ("delete", CONTEXTS + "credentials/{credential_id}/")}
ISOLATED_AUTH = [{"ContextCredential": []}]
PLATFORM_AUTH = [{"X-Api-Key": []}, {"X-Secret-Key": []}]


def assert_context_contract(contract):
    """Classify every operation in the *SDK slice*, not every upstream product route."""
    routes = {
        (method, path): operation
        for path, item in contract["paths"].items() if path.startswith((CONTEXTS, CONSUMPTION))
        for method, operation in item.items() if method != "parameters"
    }
    assert routes.keys() == RESOLVE | LEASED | INSPECTION | CREDENTIAL_ADMIN, "context route inventory changed"
    assert contract["security"] == PLATFORM_AUTH
    for scheme, wire_name in (("ContextCredential", "Authorization"), ("X-Api-Key", "X-Api-Key"), ("X-Secret-Key", "X-Secret-Key")):
        definition = contract["securityDefinitions"][scheme]
        assert (definition["type"], definition["in"], definition["name"]) == ("apiKey", "header", wire_name)

    for route, op in routes.items():
        _, path = route
        expected = ISOLATED_AUTH if route in RESOLVE | LEASED else PLATFORM_AUTH
        assert op.get("security", contract["security"]) == expected, route
        # Check path-level parameters too, so an inherited lease or auth header can't slip in.
        parameters = contract["paths"][path].get("parameters", []) + op.get("parameters", [])
        headers = [p for p in parameters if p["in"] == "header"]
        header = "X-Context-Resolution" if route in LEASED else "Idempotency-Key" if route == ISSUE else None
        assert [p["name"] for p in headers] == ([header] if header else []), route
        if headers:
            assert headers[0].get("required") is True and headers[0].get("type") == "string", route
            assert headers[0].get("format") == "uuid", route
        assert not any(p["name"].lower() == "x-context-resolution" and p["in"] != "header" for p in parameters), route


def test_pinned_consumption_contract_declares_exclusive_auth_and_wire_identity():
    contract = json.loads((CONTRACTS / "swagger.json").read_text())
    assert_context_contract(contract)
    manifest = contract["definitions"]["SkillsContextConsumptionManifest"]["properties"]
    assert {"resource_id", "kind", "resolution_id", "resolution_expires_at"} <= manifest.keys()
    assert not {"context_id", "skill_id"} & manifest.keys()


@pytest.fixture
def pinned_contract():
    return json.loads((CONTRACTS / "swagger.json").read_text())


@pytest.mark.parametrize("method,path", sorted(RESOLVE | LEASED | INSPECTION | CREDENTIAL_ADMIN))
def test_context_inventory_rejects_missing_operation(pinned_contract, method, path):
    del pinned_contract["paths"][path][method]
    with pytest.raises(AssertionError, match="inventory"):
        assert_context_contract(pinned_contract)


@pytest.mark.parametrize("method,path", [("patch", CONTEXTS), ("get", CONSUMPTION + "future/")])
def test_context_inventory_rejects_unclassified_operation(pinned_contract, method, path):
    pinned_contract["paths"].setdefault(path, {})[method] = {"security": PLATFORM_AUTH}
    with pytest.raises(AssertionError, match="inventory"):
        assert_context_contract(pinned_contract)


@pytest.mark.parametrize("method,path,reclassified", [
    ("get", CONTEXTS + "resolve/", PLATFORM_AUTH),
    ("post", CONSUMPTION + VERSION + "access-check/", ISOLATED_AUTH + PLATFORM_AUTH),
    ("get", CONTEXTS, ISOLATED_AUTH),
    (*ISSUE, ISOLATED_AUTH),
    ("delete", CONTEXTS + "credentials/{credential_id}/", []),
    ("get", CONTEXTS + "{context_id}/versions/", [{}]),
])
def test_context_contract_rejects_auth_reclassification(pinned_contract, method, path, reclassified):
    pinned_contract["paths"][path][method]["security"] = reclassified
    with pytest.raises(AssertionError):
        assert_context_contract(pinned_contract)


@pytest.mark.parametrize("change", [{"in": "query"}, {"required": False}, {"type": "integer"}])
def test_context_contract_rejects_changed_lease(pinned_contract, change):
    params = pinned_contract["paths"][CONSUMPTION + VERSION + "files/"]["get"]["parameters"]
    next(p for p in params if p["name"] == "X-Context-Resolution").update(change)
    with pytest.raises(AssertionError):
        assert_context_contract(pinned_contract)
