"""sdkgen/check_skills_baseline.py --paired: product pairing re-synced only Skills over the paired
SDK commit, so everything else must equal that commit. Runs on copies of the committed files; Git
blob reads are served from memory, without Git history. The default mode (against
x-contract-sources.other) is exercised the same way, with the committed files standing in for
that commit's slice: every unscoped operation is pinned, the scoped groups may move."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
FILES = (
    "sdkgen/contracts/swagger.json",
    "sdkgen/catalog/operations.yaml",
    "python/fi/platform/_operations.py",
    "typescript/futureagi/src/platform/_operations.ts",
)
PAIRED = "a" * 40
PRODUCT = "b" * 40


@pytest.fixture
def baseline(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "sdkgen"))
    import check_skills_baseline as check

    for name in FILES:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / name, tmp_path / name)
    committed = {name: (ROOT / name).read_bytes() for name in FILES}
    other = json.loads(committed[FILES[0]])["x-contract-sources"]["other"]["sdk_commit"]
    blobs = {PAIRED: committed, other: committed}

    def show(args, **_):
        commit, path = args[-1].split(":", 1)
        return blobs[commit][path]

    monkeypatch.setattr(check, "ROOT", tmp_path)
    monkeypatch.setattr(check, "subprocess", SimpleNamespace(check_output=show))
    contract = tmp_path / FILES[0]

    def edit(change):
        doc = json.loads(contract.read_bytes())
        change(doc)
        contract.write_text(json.dumps(doc, indent=2) + "\n")

    def run(*argv):
        check.main(list(argv))

    def as_other(doc):  # the committed slice stands in for x-contract-sources.other's slice
        doc["x-contract-sources"]["other"]["slice_sha256"] = hashlib.sha256(committed[FILES[0]]).hexdigest()

    return SimpleNamespace(run=run, edit=edit, as_other=as_other, committed=json.loads(committed[FILES[0]]))


def _unscoped_route() -> tuple[str, str]:
    import yaml
    from sync_scoped_contract import catalog_scope

    entry = next(e for e in yaml.safe_load((ROOT / FILES[1]).read_bytes())["operations"] if catalog_scope(e) is None)
    return entry["operation"]["path"], entry["operation"]["method"].lower()


def _definitions(scoped: bool) -> set:
    """Definitions the committed catalog's scoped (or unscoped) operations reach."""
    import sync_contract
    import yaml
    from sync_scoped_contract import catalog_scope

    spec = json.loads((ROOT / FILES[0]).read_bytes())
    entries = [e for e in yaml.safe_load((ROOT / FILES[1]).read_bytes())["operations"]
               if (catalog_scope(e) is not None) == scoped]
    return set(sync_contract.project(spec, entries)[1])


def _skills_synced_from(product):
    def change(doc):
        doc["x-contract-sources"]["skills"] = {**doc["x-contract-sources"]["skills"], "backend_commit": product}
    return change


def test_paired_mode_passes_when_only_the_skills_record_moved(baseline):
    baseline.edit(_skills_synced_from(PRODUCT))
    baseline.run("--paired", PAIRED, "--product-commit", PRODUCT)


@pytest.mark.parametrize("scope", ["sql", "epoch", "other"])
def test_paired_mode_rejects_a_changed_pinned_record(baseline, scope):
    def change(doc):
        _skills_synced_from(PRODUCT)(doc)
        record = doc["x-contract-sources"][scope]
        key = "sdk_commit" if scope == "other" else "backend_commit"
        record[key] = "c" * 40
    baseline.edit(change)
    with pytest.raises(SystemExit, match=rf"x-contract-sources\.{scope}"):
        baseline.run("--paired", PAIRED, "--product-commit", PRODUCT)


def test_paired_mode_rejects_a_changed_unscoped_route(baseline):
    def change(doc):
        _skills_synced_from(PRODUCT)(doc)
        methods = ("get", "put", "post", "delete", "patch")
        path, method = next((p, m) for p, item in doc["paths"].items() if not p.startswith("/model-hub/skills/")
                            for m in item if m in methods)
        operation = copy.deepcopy(doc["paths"][path][method])
        operation.setdefault("parameters", []).append(
            {"name": "probe", "in": "query", "required": True, "type": "string"})
        doc["paths"][path][method] = operation
    baseline.edit(change)
    with pytest.raises(SystemExit, match="public paths"):
        baseline.run("--paired", PAIRED, "--product-commit", PRODUCT)


def test_paired_mode_requires_skills_synced_from_this_product_in_this_run(baseline):
    baseline.edit(_skills_synced_from("d" * 40))
    with pytest.raises(SystemExit, match="not synced from this product commit"):
        baseline.run("--paired", PAIRED, "--product-commit", PRODUCT)


@pytest.mark.parametrize("argv", [["--paired", PAIRED], ["--product-commit", PRODUCT]])
def test_paired_and_product_commit_go_together(baseline, argv):
    with pytest.raises(SystemExit, match="go together"):
        baseline.run(*argv)


def test_the_committed_slice_records_every_scope_from_one_product_commit(baseline):
    # The SDK commits full syncs only; a Skills-only re-sync exists only inside product CI.
    sources = baseline.committed["x-contract-sources"]
    assert len({sources[name]["backend_commit"] for name in ("sql", "epoch", "skills")}) == 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__]))


def test_default_mode_lets_a_scoped_definition_move(baseline):
    # A re-sync of epoch or sql from the product changes their definitions; the sync's scope check
    # and pair_check.py compare those with the product, not with the SDK baseline.
    name = sorted(_definitions(scoped=True) - _definitions(scoped=False))[0]

    def change(doc):
        baseline.as_other(doc)
        doc["definitions"][name] = {**doc["definitions"][name], "title": "re-synced from the product"}
    baseline.edit(change)
    baseline.run()


def test_default_mode_rejects_a_changed_unscoped_route(baseline):
    def change(doc):
        baseline.as_other(doc)
        path, method = _unscoped_route()
        doc["paths"][path][method] = {**doc["paths"][path][method], "description": "changed"}
    baseline.edit(change)
    with pytest.raises(SystemExit, match="changed unscoped public paths"):
        baseline.run()


def test_default_mode_rejects_a_definition_scoped_and_unscoped_operations_share(baseline):
    name = sorted(_definitions(scoped=True) & _definitions(scoped=False))[0]

    def change(doc):
        baseline.as_other(doc)
        doc["definitions"][name] = {**doc["definitions"][name], "title": "changed"}
    baseline.edit(change)
    with pytest.raises(SystemExit, match="changed unscoped public schema definitions"):
        baseline.run()
