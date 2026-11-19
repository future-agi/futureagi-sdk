"""The vendored respx is the unmodified 0.23.1 release, and it is the copy these tests use."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

import respx

VENDOR = Path(__file__).resolve().parents[1] / "_vendor"
MANIFEST = json.loads((VENDOR / "VENDORED.json").read_text(encoding="utf-8"))


def _record_hash(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def test_every_vendored_file_matches_the_wheel_record() -> None:
    package = VENDOR / "respx"
    on_disk = {p.name for p in package.iterdir() if p.is_file()}
    assert on_disk == set(MANIFEST["record_sha256"]), "a file was added or removed"
    for name, expected in MANIFEST["record_sha256"].items():
        assert (
            _record_hash(package / name) == expected
        ), f"{name} differs from respx 0.23.1"


def test_the_license_ships_with_the_code() -> None:
    text = (VENDOR / "respx" / "LICENSE.md").read_text(encoding="utf-8")
    assert text.startswith("BSD 3-Clause License")
    assert MANIFEST["license"] == "BSD-3-Clause"


def test_the_suite_imports_the_copy_it_was_told_to() -> None:
    from_vendor = Path(respx.__file__).resolve().parent == (VENDOR / "respx").resolve()
    if os.environ.get("FI_GATEWAY_TEST_RESPX", "vendored") == "installed":
        assert (
            not from_vendor
        ), "FI_GATEWAY_TEST_RESPX=installed but the vendored copy loaded"
    else:
        assert from_vendor, f"expected the vendored respx, got {respx.__file__}"
    assert respx.__version__ == MANIFEST["version"]
