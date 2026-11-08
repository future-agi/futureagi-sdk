"""Catalog regeneration participates in the complete platform byte-identity gate."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/generate-catalog-namespaces.py"


def test_isolated_catalog_regeneration_and_drift_check(tmp_path):
    args = [sys.executable, str(SCRIPT), "--out", str(tmp_path)]
    subprocess.run(args, check=True, capture_output=True)
    files = sorted(p for p in tmp_path.rglob("*") if p.is_file())
    assert files
    for path in files:
        assert path.read_bytes() == (ROOT / path.relative_to(tmp_path)).read_bytes()
    subprocess.run([*args, "--check"], check=True, capture_output=True)
    victim = files[0]
    victim.write_text(victim.read_text() + "\n# changed\n")
    changed = subprocess.run([*args, "--check"], capture_output=True, text=True)
    assert changed.returncode != 0
    assert "generated output differs" in changed.stderr


@pytest.mark.parametrize("language", ["python", "typescript"])
@pytest.mark.parametrize("mutation", ["swap", "missing", "duplicate"])
def test_isolated_model_twin_query_drift_is_rejected(tmp_path, language, mutation):
    args = [sys.executable, str(SCRIPT), "--out", str(tmp_path)]
    subprocess.run(args, check=True, capture_output=True)
    query = ["exclude_providers", "limit", "model_type", "name", "page", "search"]
    changed_query = list(query)
    if mutation == "swap":
        changed_query[3], changed_query[4] = changed_query[4], changed_query[3]
    elif mutation == "missing":
        changed_query.remove("search")
    else:
        changed_query.append("search")
    if language == "python":
        path = tmp_path / "python/fi/generated/platform/catalog/models.py"
        old, new = repr(tuple(query)), repr(tuple(changed_query))
    else:
        path = tmp_path / "typescript/futureagi/src/generated/catalog/models.ts"
        old, new = json.dumps(query), json.dumps(changed_query)
    text = path.read_text()
    assert text.count(old) == 1
    path.write_text(text.replace(old, new))
    result = subprocess.run([*args, "--check"], capture_output=True, text=True)
    assert result.returncode != 0
    assert "generated output differs" in result.stderr
    assert str(path) in result.stderr


def test_isolated_catalog_check_rejects_stale_output(tmp_path):
    args = [sys.executable, str(SCRIPT), "--out", str(tmp_path)]
    subprocess.run(args, check=True, capture_output=True)
    stale = tmp_path / "python/fi/generated/platform/catalog/stale.py"
    stale.write_text("# Generated stale namespace\n")
    changed = subprocess.run([*args, "--check"], capture_output=True, text=True)
    assert changed.returncode != 0
    assert "stale generated output" in changed.stderr
