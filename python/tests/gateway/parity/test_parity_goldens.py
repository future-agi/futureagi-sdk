"""Golden integrity and E-OLD provenance: every hash the goldens rest on."""

from __future__ import annotations

import hashlib
import json

import pytest

from ._fixtures import FIXTURES, GOLDEN, load

MANIFEST = load("golden/MANIFEST.json")
ARTIFACTS = load("e-old/artifacts.json")
REGISTRY = load("e-old/registry-npm.json")
PUBLISHED = ("client", "langchain", "llamaindex", "react", "vercel")


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_lists_every_golden_file_with_its_sha256() -> None:
    on_disk = {
        str(p.relative_to(GOLDEN)): _sha256(p)
        for p in sorted(GOLDEN.rglob("*.json"))
        if p.name != "MANIFEST.json"
    }
    assert on_disk == MANIFEST["files"]


@pytest.mark.parametrize("name", sorted(MANIFEST["goldens"]))
def test_index_hashes_match_the_area_files(name: str) -> None:
    index = json.loads((GOLDEN / name / "index.json").read_text())
    for area, digest in index["files"].items():
        assert _sha256(GOLDEN / name / area) == digest, f"{name}/{area}"


def test_the_recorders_own_byte_identity_report_is_clean() -> None:
    """MANIFEST.json's byte_identity is what install_goldens.py wrote from
    record-e-old.sh's cmp of run 1 and run 2, so this checks the recorder's report
    about itself. The independent proof is a re-record on a fresh host with the
    same script, compared with the committed goldens by ``diff -r``."""
    proof = MANIFEST["byte_identity"]
    assert proof["runs"] == 2 and proof["different"] == 0
    assert proof["files"] == len(MANIFEST["files"])
    assert "another checkout path" in proof["run2"]


def test_pypi_wheel_hash_matches_the_registry_and_the_plan() -> None:
    wheel = ARTIFACTS["pypi_agentcc_1_0_0"]
    assert wheel["sha256_computed"] == wheel["sha256_registry"]
    assert wheel["sha256_computed"].startswith("2eb341ee")
    assert (
        wheel["wheel_vs_release_source_src"]["differ"] == []
        and wheel["wheel_vs_release_source_src"]["only_left"] == []
    )


@pytest.mark.parametrize("pkg", PUBLISHED)
def test_npm_tarball_hashes_match_the_registry(pkg: str) -> None:
    """Against the registry's dist for 1.0.0 itself (not dist-tags.latest, which
    moves), with npm pack's own report as a second, separate check."""
    entry = ARTIFACTS["npm"][f"@agentcc/{pkg}@1.0.0"]
    assert entry["registry_match"] and entry["npm_pack_match"]
    assert entry["sha1_computed"] == entry["npm_pack_shasum"]
    view = REGISTRY["packages"][f"@agentcc/{pkg}"]
    dist = view["version_dist"]["1.0.0"]
    assert view["published"] and dist["npm_view_exit"] == 0
    assert dist["shasum"] == entry["sha1_computed"] == entry["registry_shasum"]
    assert (
        dist["integrity"] == entry["integrity_computed"] == entry["registry_integrity"]
    )
    if pkg == "client":
        assert entry["sha1_computed"].startswith("81b5315b")


@pytest.mark.parametrize("target", ["client-1.0.0", "integrations-1.0.0"])
def test_npm_locks_pin_the_published_integrity(target: str) -> None:
    lock = load(f"e-old/npm/{target}/package-lock.json")["packages"]
    for key, meta in lock.items():
        if key.startswith("node_modules/@agentcc/"):
            name = key.removeprefix("node_modules/")
            assert (
                meta["integrity"]
                == ARTIFACTS["npm"][f"{name}@1.0.0"]["integrity_computed"]
            ), name


def test_local_1_0_1_lock_pins_the_retained_tarball() -> None:
    lock = load("e-old/npm/client-1.0.1/package-lock.json")["packages"][
        "node_modules/@agentcc/client"
    ]
    packed = ARTIFACTS["npm"]["@agentcc/client@1.0.1 (packed from client-patch-source)"]
    assert lock["integrity"] == packed["integrity_computed"]


def test_the_doc_package_name_is_not_published() -> None:
    assert REGISTRY["packages"]["@futureagi/agentcc"]["published"] is False


def test_stream_error_frames_keep_the_retained_payload() -> None:
    data = (FIXTURES / "stream-error-frames.json").read_bytes()
    assert hashlib.sha256(data).hexdigest() == "3758da94c1dc37b5e3dc5319e6a4da0fe87742d1c4f4127e5aee46724b0fa0e7"
    fixture = json.loads(data)
    assert fixture["source"]["record"] == "stream-fixture-source"
    cases = json.dumps(fixture["cases"], sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(cases).hexdigest() == "8479765ed1b15160900b5f110099852e9a94be3fbf438fe100d61c29ea1025d1"
