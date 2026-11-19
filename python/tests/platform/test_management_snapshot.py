"""Management snapshots preserve wire schema fields while removing prose."""
import hashlib
import json
import runpy

from ._gates_support import REPO


def test_public_admin_snapshot_is_digest_bound():
    source = json.loads((REPO / "openapi/fa-mgmt/source.json").read_text())
    digest = "sha256:" + hashlib.sha256((REPO / "openapi/fa-mgmt/admin.schema.json").read_bytes()).hexdigest()
    assert source["public_admin_sha256"] == digest
    assert source["admin_sha256"].startswith("sha256:")
    assert len(source["admin_sha256"]) == 71


def test_public_schema_keeps_wire_names_and_literal_values():
    public_schema = runpy.run_path(str(REPO / "scripts/fa-management/snapshot.py"))["public_schema"]
    schema = {"description": "private implementation notes", "type": "object", "required": ["description"],
              "properties": {"description": {"type": "string", "description": "notes", "default": "kept"}},
              "default": {"description": "literal wire value"}, "enum": [{"description": "literal enum"}]}
    public = public_schema(schema)
    assert "description" not in public
    assert public["properties"] == {"description": {"type": "string", "default": "kept"}}
    assert public["required"] == ["description"]
    assert public["default"] == schema["default"]
    assert public["enum"] == schema["enum"]
    assert public["type"] == "object"
    assert schema["description"] == "private implementation notes"
