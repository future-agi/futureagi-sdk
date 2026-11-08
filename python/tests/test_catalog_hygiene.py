"""Public-text hygiene of the files the catalog slice owns, with the shared scanner unchanged.

The shared platform scanner's rules run over exactly these files: the operations source,
the runtime adapters, the generated namespaces in both languages, the generator and the
catalog tests. Gateway files that came in with the gateway client line are outside this
check; their wording has its own owner and gate.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNED = [
    "openapi/catalog",
    "python/fi/_core/catalog.py",
    "python/fi/_core/catalog_registration.py",
    "python/fi/generated/platform/catalog",
    "python/fi/gateway/_session_tracking.py",
    "python/tests/catalog_smoke",
    "python/tests/gateway/unit/test_catalog_compatibility.py",
    "python/tests/test_catalog_gates.py",
    "python/tests/test_catalog_hygiene.py",
    "python/tests/test_catalog_namespaces.py",
    "python/tests/test_catalog_typing.py",
    "scripts/generate-catalog-namespaces.py",
    "typescript/futureagi/src/_core/catalog.ts",
    "typescript/futureagi/src/_core/__tests__/catalog-namespaces.test.ts",
    "typescript/futureagi/src/generated/catalog",
]
# Review and planning words the shared rules do not cover. Each is assembled so this
# file passes its own check.
PROCESS = re.compile(
    "|".join(
        [
            "fold" + " plan",
            "fix" + " round",
            "finding" + r" \d",
            "ver" + r"ify\d",
            "independent" + " verify",
            "PL" + r"AN [0-9§]",
            r"\bru" + r"ling \d",
        ]
    ),
    re.IGNORECASE,
)
COMMIT_ID = re.compile(r"\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b")
# The catalog retains its public source URL and a descriptive inventory record, not a revision exemption.
SOURCE_RECORD = json.loads((ROOT / "openapi/catalog/operations.json").read_text())["source_record"]


def _scanner():
    spec = importlib.util.spec_from_file_location(
        "catalog_hygiene_scan", ROOT / "scripts/platform/hygiene_scan.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _owned_files(scan) -> list[str]:
    files = scan.list_files(OWNED, ROOT)
    assert "openapi/catalog/operations.json" in files
    assert any(f.startswith("typescript/futureagi/src/generated/catalog/") for f in files)
    return files


def test_the_shared_rules_find_nothing_in_the_catalog_files() -> None:
    scan = _scanner()
    count, hits = scan.scan_paths(OWNED, scan.load_rules(), ROOT)
    assert count >= 15
    assert SOURCE_RECORD == "public-catalog-operation-inventory"
    assert hits == []


def test_no_review_wording_or_unpublished_revision_in_the_catalog_files() -> None:
    scan = _scanner()
    found = []
    for rel in _owned_files(scan):
        for number, line in enumerate((ROOT / rel).read_text().splitlines(), 1):
            if PROCESS.search(line):
                found.append(f"{rel}:{number}: {line.strip()}")
            for token in COMMIT_ID.findall(line):
                found.append(f"{rel}:{number}: revision {token}")
    assert found == []


def test_the_wording_check_bites() -> None:
    assert PROCESS.search("see the " + "fold" + " plan, section 5")
    assert PROCESS.search("fix" + " round 2")
    assert COMMIT_ID.findall("merged at " + "ab12" + "cd3 today") == ["ab12" + "cd3"]
    assert COMMIT_ID.findall("a uuid-free word: deadbeef") == []
    assert COMMIT_ID.findall("version 1234567") == []
