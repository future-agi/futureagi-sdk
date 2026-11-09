"""sdkgen/sync_contract.py: the contract slice the generator reads, refreshed from a backend release."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "sdkgen"))

import sync_contract  # noqa: E402

CATALOG = yaml.safe_load((ROOT / "sdkgen" / "catalog" / "operations.yaml").read_text())
SPEC = json.loads((ROOT / "sdkgen" / "contracts" / "swagger.json").read_text())


def _entry(op_id: str) -> dict:
    return next(e for e in CATALOG["operations"] if e["id"] == op_id)


@pytest.fixture
def out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Write the slice to a scratch file, never over sdkgen/contracts/swagger.json."""
    target = tmp_path / "out" / "swagger.json"
    monkeypatch.setattr(sync_contract, "ROOT", tmp_path)
    monkeypatch.setattr(sync_contract, "OUT", target)
    return target


def test_slice_is_a_fixed_point_of_the_committed_contract(
    tmp_path: Path, out: Path
) -> None:
    """Re-slicing the committed slice changes nothing: every selected operation and
    every definition it reaches is already there, and nothing unselected is."""
    source = tmp_path / "swagger.json"
    source.write_text(json.dumps(SPEC))
    assert sync_contract.sync(source).startswith("wrote ")
    sliced = json.loads(out.read_text())
    assert set(sliced["paths"]) == set(SPEC["paths"])
    assert set(sliced["definitions"]) == set(SPEC["definitions"])


def test_an_unselected_endpoint_never_reaches_the_slice(
    tmp_path: Path, out: Path
) -> None:
    """The catalog is the allowlist: a new backend endpoint is not an SDK method until
    someone adds a catalog entry, so the slice (and the generated clients) ignore it."""
    spec = json.loads(json.dumps(SPEC))
    spec["paths"]["/internal/new-endpoint/"] = {
        "get": {
            "operationId": "internal_new",
            "responses": {"200": {"description": ""}},
        }
    }
    source = tmp_path / "swagger.json"
    source.write_text(json.dumps(spec))
    sync_contract.sync(source)
    sliced = json.loads(out.read_text())
    assert "/internal/new-endpoint/" not in sliced["paths"]


def test_a_removed_exposed_endpoint_fails_closed_and_names_it(
    tmp_path: Path, out: Path
) -> None:
    """A backend release that drops or moves an endpoint the SDK exposes is a breaking
    change: the sync must stop with the operations named, not write a slice that
    silently loses methods (the monorepo's sdk-sync shows this as the job error)."""
    spec = json.loads(json.dumps(SPEC))
    gone = _entry("account.whoami")["operation"]
    del spec["paths"][gone["path"]][gone["method"].lower()]
    moved = _entry("datasets.list")["operation"]
    spec["paths"]["/v2" + moved["path"]] = spec["paths"].pop(moved["path"])
    source = tmp_path / "swagger.json"
    source.write_text(json.dumps(spec))
    with pytest.raises(SystemExit) as stop:
        sync_contract.sync(source)
    message = str(stop.value)
    assert "breaking change" in message
    assert f"account.whoami: {gone['method'].upper()} {gone['path']}" in message
    assert f"datasets.list: {moved['method'].upper()} {moved['path']}" in message
    assert not out.exists(), "nothing may be written when the sync refuses"
