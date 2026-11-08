"""summarize_artifacts.py, the E-OLD hash check (regression check, finding 3).

A tarball matches only the registry's dist for its exact version, never npm
pack's own report and never ``dist-tags.latest``; a missing published tarball
fails; the committed evidence passes the same check. And the README states
what the published tarballs' differences from a the recorded source build are (finding 2).
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json

import pytest

from ._fixtures import FIXTURES, load

_spec = importlib.util.spec_from_file_location(
    "summarize_artifacts", FIXTURES / "e-old" / "summarize_artifacts.py"
)
sa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sa)

TGZ = b"not really a tarball, but bytes with a known digest"
SHA1 = hashlib.sha1(TGZ).hexdigest()
INTEGRITY = "sha512-" + base64.b64encode(hashlib.sha512(TGZ).digest()).decode()


def _layout(tmp_path, specs, registry_dist, pack_override=None):
    """An out/ and work/ pair as fetch-artifacts.sh leaves them, one fake tarball per spec."""
    out, work = tmp_path / "out", tmp_path / "work"
    (out / "raw").mkdir(parents=True)
    (work / "npm-published").mkdir(parents=True)
    entries, exits, dist_exits = [], [], []
    for spec in specs:
        name, version = spec.rsplit("@", 1)
        filename = name.lstrip("@").replace("/", "-") + f"-{version}.tgz"
        (work / "npm-published" / filename).write_bytes(TGZ)
        entries.append(
            {
                "id": spec,
                "name": name,
                "version": version,
                "filename": filename,
                "shasum": SHA1,
                "integrity": INTEGRITY,
                "files": [{}],
                **(pack_override or {}),
            }
        )
        safe = name.replace("/", "__")
        view = {"name": name, "versions": ["1.0.0", "1.0.1"]}
        view["dist-tags"] = {"latest": "1.0.1"}  # latest has moved on
        view["dist"] = {"shasum": "0" * 40, "integrity": "sha512-other"}
        (out / "raw" / f"npm-view-{safe}.json").write_text(json.dumps(view))
        exits.append(f"{name} 0")
        dist = registry_dist(spec)
        (out / "raw" / f"npm-view-dist-{spec.replace('/', '__')}.json").write_text(
            json.dumps(dist if dist is not None else {"error": {"code": "E404"}})
        )
        dist_exits.append(f"{spec} {0 if dist is not None else 1}")
    (out / "raw" / "npm-pack-published.json").write_text(json.dumps(entries))
    (out / "npm-view-exit.txt").write_text("\n".join(exits) + "\n")
    (out / "npm-view-dist-exit.txt").write_text("\n".join(dist_exits) + "\n")
    registry = sa.npm_registry(out)
    return {"npm": sa.npm_artifacts(out, work, registry)}, registry


def _good_wheel(artifacts):
    artifacts["pypi_agentcc_1_0_0"] = {"registry_match": True, "prefix_match": True}
    return artifacts


def _with_client_prefix(artifacts):
    artifacts["npm"][sa.CLIENT][
        "prefix_match"
    ] = True  # the fake bytes are not 81b5315b
    return artifacts


def test_a_match_is_the_exact_versions_registry_dist_even_after_latest_moves(
    tmp_path,
) -> None:
    artifacts, registry = _layout(
        tmp_path, sa.PUBLISHED, lambda s: {"shasum": SHA1, "integrity": INTEGRITY}
    )
    entry = artifacts["npm"]["@agentcc/react@1.0.0"]
    assert entry["registry_shasum"] == SHA1 and entry["registry_match"]
    assert sa.problems(_with_client_prefix(_good_wheel(artifacts)), registry) == []


def test_npm_packs_own_report_never_stands_in_for_the_registry(tmp_path) -> None:
    other = {"shasum": "f" * 40, "integrity": INTEGRITY}
    artifacts, registry = _layout(
        tmp_path,
        sa.PUBLISHED,
        lambda s: (
            other
            if s == "@agentcc/vercel@1.0.0"
            else {"shasum": SHA1, "integrity": INTEGRITY}
        ),
    )
    vercel = artifacts["npm"]["@agentcc/vercel@1.0.0"]
    assert vercel["npm_pack_match"] and not vercel["registry_match"]
    assert sa.problems(_with_client_prefix(_good_wheel(artifacts)), registry) == [
        "@agentcc/vercel@1.0.0: the tarball is not the registry's dist for @agentcc/vercel@1.0.0"
    ]


def test_no_registry_answer_for_the_version_is_a_mismatch(tmp_path) -> None:
    artifacts, registry = _layout(
        tmp_path,
        sa.PUBLISHED,
        lambda s: (
            None
            if s == "@agentcc/llamaindex@1.0.0"
            else {"shasum": SHA1, "integrity": INTEGRITY}
        ),
    )
    assert registry["packages"]["@agentcc/llamaindex"]["version_dist"]["1.0.0"] == {
        "npm_view_exit": 1
    }
    found = sa.problems(_with_client_prefix(_good_wheel(artifacts)), registry)
    assert found == [
        "@agentcc/llamaindex@1.0.0: the tarball is not the registry's dist for @agentcc/llamaindex@1.0.0"
    ]


def test_a_missing_published_tarball_is_a_mismatch(tmp_path) -> None:
    present = tuple(p for p in sa.PUBLISHED if p != "@agentcc/react@1.0.0")
    artifacts, registry = _layout(
        tmp_path, present, lambda s: {"shasum": SHA1, "integrity": INTEGRITY}
    )
    found = sa.problems(_with_client_prefix(_good_wheel(artifacts)), registry)
    assert found == ["@agentcc/react@1.0.0: no tarball was packed"]


def test_a_pack_report_that_disagrees_with_the_bytes_is_a_mismatch(tmp_path) -> None:
    artifacts, registry = _layout(
        tmp_path,
        sa.PUBLISHED,
        lambda s: {"shasum": SHA1, "integrity": INTEGRITY},
        pack_override={"shasum": "e" * 40},
    )
    found = sa.problems(_with_client_prefix(_good_wheel(artifacts)), registry)
    assert len(found) == len(sa.PUBLISHED)
    assert all("npm pack reported other hashes" in p for p in found)


def test_the_client_prefix_and_the_wheel_are_checked(tmp_path) -> None:
    artifacts, registry = _layout(
        tmp_path, sa.PUBLISHED, lambda s: {"shasum": SHA1, "integrity": INTEGRITY}
    )
    artifacts["pypi_agentcc_1_0_0"] = {"registry_match": False, "prefix_match": True}
    assert sa.problems(artifacts, registry) == [
        "the PyPI wheel's sha256 is not the registry's",
        f"{sa.CLIENT}: the shasum does not start with 81b5315b",
    ]


def test_the_committed_evidence_passes_the_same_check() -> None:
    artifacts, registry = load("e-old/artifacts.json"), load("e-old/registry-npm.json")
    assert artifacts["hash_check"] == {"ok": True, "problems": []}
    stored = {k: v for k, v in artifacts.items() if k != "hash_check"}
    assert sa.problems(stored, registry) == []
    for spec in sa.PUBLISHED:
        name, version = spec.rsplit("@", 1)
        dist = registry["packages"][name]["version_dist"][version]
        assert dist["shasum"] == artifacts["npm"][spec]["sha1_computed"], spec
        assert dist["integrity"] == artifacts["npm"][spec]["integrity_computed"], spec


@pytest.mark.parametrize("spec", sa.PUBLISHED)
def test_the_readme_names_every_file_a_published_tarball_differs_in(spec: str) -> None:
    readme = (FIXTURES / "README.md").read_text()
    compared = load("e-old/artifacts.json")["published_vs_release_source_build"][spec]
    assert not compared["only_left"] and not compared["only_right"], spec
    beyond = [f for f in compared["differ"] if f not in sa.NOT_BUILT]
    for name in beyond:
        assert f"`{name}`" in readme, f"{spec}: README does not name {name}"
        assert compared["text_diffs"][name], f"{spec}: no diff recorded for {name}"
    assert set(compared["text_diffs"]) == set(beyond)
