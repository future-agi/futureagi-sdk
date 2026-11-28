"""Unqualified reads remain absent, rather than callable placeholders."""
import importlib.util
import json
from pathlib import Path

import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("client_class", [FutureAGIClient, AsyncFutureAGIClient])
@pytest.mark.parametrize("namespace", ["billing", "keys", "usage"])
def test_unavailable_namespace_is_not_registered(client_class, namespace):
    client = client_class("fixture-api", "fixture-secret", base_url="http://localhost:9031")
    assert not hasattr(client, namespace)
    assert not hasattr(client.with_options(timeout=2), namespace)
    assert importlib.util.find_spec(f"fi.{namespace}") is None
    assert importlib.util.find_spec(f"fi.generated.platform.catalog.{namespace}") is None
    assert not (ROOT / f"python/fi/{namespace}").exists()
    assert not (ROOT / f"typescript/futureagi/src/{namespace}").exists()
    assert not (ROOT / f"typescript/futureagi/src/generated/catalog/{namespace}.ts").exists()


def test_unavailable_reads_have_explicit_language_dispositions():
    mapping = json.loads((ROOT / "openapi/catalog/read-wrapper-map.json").read_text())["operations"]
    rows = {name: row for name, row in mapping.items() if not row.get("methods")}
    assert len(rows) == 10
    for row in rows.values():
        assert row["py"] == row["py_async"] == row["ts"] == "NOT-OFFERED"
        assert row["reason"]
    assert "organization-wide" in rows["accounts_key_get_secret_keys"]["reason"]


def test_no_catalog_operation_uses_organization_bootstrap_or_key_enumeration():
    rows = json.loads((ROOT / "openapi/catalog/operations.json").read_text())["operations"]
    assert not any(row["operation_id"] in {"accounts_keys_list", "accounts_key_get_secret_keys"} for row in rows)
    exports = json.loads((ROOT / "typescript/futureagi/package.json").read_text())["exports"]
    assert "./billing" not in exports
    assert "./keys" not in exports
    assert "./usage" not in exports


def test_not_offered_reads_have_no_callable_catalog_alias():
    mapping = json.loads((ROOT / "openapi/catalog/read-wrapper-map.json").read_text())["operations"]
    excluded = {name for name, row in mapping.items() if row.get("py") == "NOT-OFFERED"}
    rows = json.loads((ROOT / "openapi/catalog/operations.json").read_text())["operations"]
    assert excluded.isdisjoint(row["operation_id"] for row in rows)
