"""Physical namespace aliases and pip's unrecorded distutils script footprint."""
from __future__ import annotations

from pathlib import Path

import pytest

from fi._core import namespace_ownership as ownership
from test_namespace_ownership_footprint import BOUNDED_FOLLOW_UP, installed, sdk
from test_namespace_ownership_repair import SUPPORTED
from test_namespace_ownership_safety import assert_manual_only


def add_distutils_script(dist, name):
    """pip enumerates metadata/scripts independently of RECORD; never execute it."""
    target = dist._path / "scripts" / name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(b"# unrecorded distutils script\n")
    assert f"{dist._path.name}/scripts/" not in (dist.read_text("RECORD") or "")
    return target


@pytest.mark.parametrize("name,version,path", SUPPORTED)
@pytest.mark.parametrize("damage", ["omitted-row", "missing"])
def test_parent_directory_alias_protects_unrecorded_supported_payload(tmp_path, name, version, path, damage):
    site = tmp_path / "site"
    own = sdk(site)
    companion = installed(site, name, version, payload={path: b"# supported\n"},
                          record="missing" if damage == "missing" else "complete", omitted=[path])
    (site / "alias").symlink_to((site / path).parent, target_is_directory=True)
    alias = "alias/" + Path(path).name
    offender = installed(site, "foreign-runtime", entries={"console_scripts": ["fi"]}, claims=[alias])
    assert offender._path != companion._path
    assert offender.locate_file(alias).resolve() == companion.locate_file(path).resolve()
    assert path not in (companion.read_text("RECORD") or "")

    result = ownership.inspect_installed([own, companion, offender])

    assert {"kind": "legacy-console-script", "distribution": "foreign-runtime", "path": "fi"} in result["issues"]
    assert_manual_only(result, [name, "foreign-runtime"], alias)
    assert (site / path).read_bytes() == b"# supported\n"


@pytest.mark.parametrize("damage", ["omitted-row", "missing"])
def test_supported_namespace_alias_maps_to_physical_payload(tmp_path, damage):
    site = tmp_path / "site"
    own = sdk(site)
    physical = site / "payload"
    physical.mkdir()
    (site / "fi/alk").symlink_to(physical, target_is_directory=True)
    path = "fi/alk/shared.py"
    companion = installed(site, "agent-learning-kit", "0.3.4", payload={path: b"# supported\n"},
                          record="missing" if damage == "missing" else "complete", omitted=[path])
    claim = "payload/shared.py"
    offender = installed(site, "foreign-runtime", entries={"console_scripts": ["fi"]}, claims=[claim])
    assert offender.locate_file(claim).resolve() == companion.locate_file(path).resolve()
    assert path not in (companion.read_text("RECORD") or "")

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["agent-learning-kit", "foreign-runtime"], claim)
    assert (physical / "shared.py").read_bytes() == b"# supported\n"


@pytest.mark.parametrize("name,version,path", SUPPORTED)
def test_disjoint_physical_alias_keeps_owner_specific_guidance(tmp_path, name, version, path):
    site = tmp_path / "site"
    own = sdk(site)
    companion = installed(site, name, version, payload={path: b"# supported\n"})
    foreign = site / "foreign"
    foreign.mkdir()
    (foreign / "payload.py").write_bytes(b"# unrelated\n")
    (site / "alias").symlink_to(foreign, target_is_directory=True)
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi"]},
                         claims=["alias/payload.py"])

    result = ownership.inspect_installed([own, companion, offender])

    assert result["issues"] == [{"kind": "legacy-console-script", "distribution": "unrelated-cli", "path": "fi"}]
    assert_manual_only(result, ["unrelated-cli"], "alias/payload.py")
    assert not any(name in step for step in result["repair_commands"])
    assert (site / path).read_bytes() == b"# supported\n"


@pytest.mark.parametrize("script", ["futureagi-py", "futureagi-py.exe", "futureagi-py-script.py"])
def test_distutils_script_removal_protects_sdk_launcher(tmp_path, script):
    site = tmp_path / "site"
    own = sdk(site)
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi"]})
    add_distutils_script(offender, script)
    executable = tmp_path / "bin" / script
    executable.parent.mkdir()
    executable.write_bytes(b"# supported launcher\n")
    assert all("bin/" not in dist.read_text("RECORD") for dist in [own, offender])

    result = ownership.inspect_installed([own, offender])

    assert result["issues"] == [{"kind": "legacy-console-script", "distribution": "unrelated-cli", "path": "fi"}]
    assert_manual_only(result, ["futureagi", "unrelated-cli"], script)
    assert executable.read_bytes() == b"# supported launcher\n"


@pytest.mark.parametrize("suffix", ["", ".bat"])
def test_record_claim_protects_unrecorded_supported_distutils_script(tmp_path, suffix):
    site = tmp_path / "site"
    own = sdk(site)
    companion = installed(site, "agentcc", "2.0.0")
    add_distutils_script(companion, "shared-tool")
    path = "bin/shared-tool" + suffix
    executable = site / path
    executable.parent.mkdir()
    executable.write_bytes(b"# supported launcher\n")
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi"]}, claims=[path])
    assert path not in companion.read_text("RECORD")

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["agentcc", "unrelated-cli"], path)
    assert executable.read_bytes() == b"# supported launcher\n"


@pytest.mark.parametrize("script", ["shared-tool", "shared-tool.bat"])
def test_entry_point_removal_protects_unrecorded_supported_distutils_script(tmp_path, script):
    site = tmp_path / "site"
    own = sdk(site)
    companion = installed(site, "agentcc", "2.0.0")
    add_distutils_script(companion, "shared-tool")
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi", script]})
    assert "bin/" not in companion.read_text("RECORD")

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["agentcc", "unrelated-cli"], script)


def test_distutils_bat_removal_checks_supported_record_claims(tmp_path):
    site = tmp_path / "site"
    own = sdk(site)
    path = "bin/shared-tool.bat"
    companion = installed(site, "agentcc", "2.0.0", payload={path: b"# supported launcher\n"})
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi"]})
    add_distutils_script(offender, "shared-tool")

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["agentcc", "unrelated-cli"], path)
    assert (site / path).read_bytes() == b"# supported launcher\n"


@pytest.mark.parametrize("name,version,path", SUPPORTED)
def test_supported_distutils_scripts_are_not_flagged_or_advised_for_removal(tmp_path, name, version, path):
    site = tmp_path / "site"
    own = sdk(site)
    companion = installed(site, name, version, payload={path: b"# supported\n"})
    add_distutils_script(companion, "companion-tool")

    healthy = ownership.inspect_installed([own, companion])

    assert healthy["status"] == "PASS"
    assert healthy["issues"] == []
    assert healthy["repair_commands"] == []
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi"]})
    add_distutils_script(offender, "unrelated-tool")

    result = ownership.inspect_installed([own, companion, offender])

    assert result["issues"] == [{"kind": "legacy-console-script", "distribution": "unrelated-cli", "path": "fi"}]
    assert_manual_only(result, ["unrelated-cli"], "unrelated-tool")
    assert not any(name in step for step in result["repair_commands"])


@pytest.mark.parametrize("unreadable_owner", ["unrelated-cli", "agentcc"])
def test_unreadable_distutils_inventory_requires_manual_guidance(tmp_path, monkeypatch, unreadable_owner):
    site = tmp_path / "site"
    own = sdk(site)
    companion = installed(site, "agentcc", "2.0.0")
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi"]})
    selected = offender if unreadable_owner == "unrelated-cli" else companion
    blocked = add_distutils_script(selected, "shared-tool").parent
    original = Path.iterdir

    def inaccessible(path):
        if path == blocked:
            raise PermissionError("fixture scripts inventory is unreadable")
        return original(path)

    monkeypatch.setattr(Path, "iterdir", inaccessible)

    result = ownership.inspect_installed([own, companion, offender])

    assert result["status"] == "FAIL"
    assert not any(step.startswith("pip ") for step in result["repair_commands"])
    assert any(step.startswith("Manual repair required") and unreadable_owner in step
               and "script" in step for step in result["repair_commands"])
    assert result["repair_commands"][-1] == "futureagi-py doctor --offline"
