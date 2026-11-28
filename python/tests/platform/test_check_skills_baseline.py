"""sdkgen/check_skills_baseline.py --paired: product pairing re-synced only Skills over the paired
SDK commit, so everything else must equal that commit. Runs on copies of the committed files; Git
blob reads are served from memory, without Git history. (The default mode, against
x-contract-sources.other, needs that commit's real slice and runs in the SDK's own CI.)"""

from __future__ import annotations

import copy
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
    blobs = {PAIRED: committed}

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

    return SimpleNamespace(run=run, edit=edit, committed=json.loads(committed[FILES[0]]))


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
        path = next(p for p in doc["paths"] if not p.startswith("/model-hub/skills/"))
        method = next(iter(doc["paths"][path]))
        doc["paths"][path][method] = {**copy.deepcopy(doc["paths"][path][method]), "summary": "changed"}
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
