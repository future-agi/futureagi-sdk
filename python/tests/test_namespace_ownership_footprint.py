"""Uninstall effects beyond literal RECORD rows; no installer or network execution."""
from __future__ import annotations

import base64
import csv
import hashlib
from importlib import metadata
import io

import pytest

from fi._core import namespace_ownership as ownership
from test_namespace_ownership_repair import SUPPORTED
from test_namespace_ownership_safety import assert_manual_only


BOUNDED_FOLLOW_UP = [
    "pip install --upgrade --force-reinstall --no-deps futureagi",
    "futureagi-py doctor --offline",
]


def installed(site, name, version="1.0.0", *, payload=None, entries=None,
              record="complete", omitted=(), claims=()):
    """Distinct real metadata directories sharing one site, without importing payloads."""
    info = site / f"{name.replace('-', '_')}-{version}.dist-info"
    info.mkdir(parents=True)
    files = dict(payload or {f"{name.replace('-', '_')}.py": b"# fixture\n"})
    files[f"{info.name}/METADATA"] = (
        f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
    ).encode()
    if entries:
        files[f"{info.name}/entry_points.txt"] = "".join(
            f"[{group}]\n" + "".join(f"{script} = fixture:main\n" for script in scripts)
            for group, scripts in entries.items()
        ).encode()
    rows = io.StringIO()
    writer = csv.writer(rows)
    for path, data in files.items():
        target = site / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if path not in omitted:
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            writer.writerow((path, "sha256=" + digest, str(len(data))))
    for path in claims:
        writer.writerow((path, "", ""))
    writer.writerow((f"{info.name}/RECORD", "", ""))
    if record != "missing":
        (info / "RECORD").write_text("" if record == "empty" else rows.getvalue())
    return metadata.PathDistribution(info)


def sdk(site):
    return installed(site, "futureagi", "0.7.0", payload={"fi/__init__.py": b"# sdk\n"},
                     entries={"console_scripts": ["futureagi-py"]})


@pytest.mark.parametrize("alias", [
    "./fi/alk/shared.py", "fi//alk/shared.py", "fi/alk/./shared.py", "./fi//alk//shared.py",
])
@pytest.mark.parametrize("damage", ["missing", "omitted-row"])
def test_noncanonical_rows_cannot_hide_possible_supported_ownership(tmp_path, alias, damage):
    site = tmp_path / "site"
    own = sdk(site)
    path = "fi/alk/shared.py"
    companion = installed(site, "agent-learning-kit", "0.3.4", payload={path: b"# supported\n"},
                          record="missing" if damage == "missing" else "complete", omitted=[path])
    offender = installed(site, "foreign-runtime", entries={"console_scripts": ["fi"]}, claims=[alias])
    assert offender._path != companion._path
    assert offender.locate_file(alias).resolve() == companion.locate_file(path).resolve()
    assert path not in (companion.read_text("RECORD") or "")

    result = ownership.inspect_installed([own, companion, offender])

    assert {"kind": "legacy-console-script", "distribution": "foreign-runtime", "path": "fi"} in result["issues"]
    assert_manual_only(result, ["agent-learning-kit", "foreign-runtime"], alias)
    assert (site / path).read_bytes() == b"# supported\n"


@pytest.mark.parametrize("group", ["console_scripts", "gui_scripts"])
@pytest.mark.parametrize("script", ["futureagi-py", "futureagi-py.exe", "futureagi-py-script.py"])
def test_implicit_entry_point_removal_cannot_delete_the_sdk_wrapper(tmp_path, group, script):
    site = tmp_path / "site"
    own = sdk(site)
    entries = {"console_scripts": ["fi"]}
    entries.setdefault(group, []).append(script)
    offender = installed(site, "unrelated-cli", entries=entries)
    executable = tmp_path / "bin" / script
    executable.parent.mkdir()
    executable.write_bytes(b"# supported launcher\n")
    assert all("bin/" not in dist.read_text("RECORD") for dist in [own, offender])
    assert own._path != offender._path

    result = ownership.inspect_installed([own, offender])

    assert result["issues"] == [{"kind": "legacy-console-script", "distribution": "unrelated-cli", "path": "fi"}]
    assert_manual_only(result, ["futureagi", "unrelated-cli"], script)
    assert executable.read_bytes() == b"# supported launcher\n"


@pytest.mark.parametrize("group", ["console_scripts", "gui_scripts"])
def test_implicit_wrapper_removal_checks_supported_record_claims(tmp_path, group):
    site = tmp_path / "site"
    own = sdk(site)
    companion = installed(site, "agentcc", "2.0.0", payload={"bin/shared-tool": b"# supported\n"})
    entries = {"console_scripts": ["fi"]}
    entries.setdefault(group, []).append("shared-tool")
    offender = installed(site, "unrelated-cli", entries=entries)
    assert "shared-tool" not in offender.read_text("RECORD")

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["agentcc", "unrelated-cli"], "shared-tool")
    assert (site / "bin/shared-tool").read_bytes() == b"# supported\n"


def test_record_claim_cannot_remove_an_unrecorded_supported_entry_point(tmp_path):
    site = tmp_path / "site"
    own = sdk(site)
    executable = site / "bin/futureagi-py"
    executable.parent.mkdir()
    executable.write_bytes(b"# supported launcher\n")
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi"]},
                         claims=["bin/futureagi-py"])
    assert "bin/futureagi-py" not in own.read_text("RECORD")

    result = ownership.inspect_installed([own, offender])

    assert_manual_only(result, ["futureagi", "unrelated-cli"], "bin/futureagi-py")
    assert executable.read_bytes() == b"# supported launcher\n"


def test_directory_claim_cannot_remove_unrecorded_supported_wrappers(tmp_path):
    site = tmp_path / "site"
    own = sdk(site)
    executable = site / "bin/futureagi-py"
    executable.parent.mkdir()
    executable.write_bytes(b"# supported launcher\n")
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi"]}, claims=["bin"])
    assert "bin/futureagi-py" not in own.read_text("RECORD")

    result = ownership.inspect_installed([own, offender])

    assert_manual_only(result, ["futureagi", "unrelated-cli"], "bin")
    assert executable.read_bytes() == b"# supported launcher\n"


@pytest.mark.parametrize("script", ["../agentcc/__init__.py", "..\\agentcc\\__init__.py", "C:futureagi-py"])
def test_path_spreading_entry_points_require_manual_repair(tmp_path, script):
    site = tmp_path / "site"
    own = sdk(site)
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi", script]})

    result = ownership.inspect_installed([own, offender])

    assert not any(step.startswith("pip ") for step in result["repair_commands"])
    assert any(step.startswith("Manual repair required for unrelated-cli:")
               and "entry-point" in step for step in result["repair_commands"])
    assert result["repair_commands"][-1] == "futureagi-py doctor --offline"


def test_sdk_reinstall_cannot_expand_to_unchecked_dependencies(tmp_path):
    site = tmp_path / "site"
    own = sdk(site)
    path = "agentcc/__init__.py"
    companion = installed(site, "agentcc", "2.0.0", payload={path: b"# supported\n"})
    dependency = installed(site, "requests", "2.32.0", claims=[path])
    (site / "fi/__init__.py").write_bytes(b"# damaged sdk\n")
    assert dependency.locate_file(path) == companion.locate_file(path)

    result = ownership.inspect_installed([own, companion, dependency])

    assert result["issues"] == [{
        "kind": "hash-mismatch", "distribution": "futureagi", "path": "fi/__init__.py",
    }]
    assert_manual_only(result, ["futureagi"], "futureagi")
    assert not any("requests" in step or "agentcc" in step for step in result["repair_commands"])
    assert (site / path).read_bytes() == b"# supported\n"


@pytest.mark.parametrize("name,version,path", SUPPORTED)
@pytest.mark.parametrize("damage", ["omitted-row", "missing", "empty"])
def test_supported_metadata_is_protected_independently_of_its_record(tmp_path, name, version, path, damage):
    site = tmp_path / "site"
    own = sdk(site)
    metadata_path = f"{name.replace('-', '_')}-{version}.dist-info/METADATA"
    companion = installed(site, name, version, payload={path: b"# supported\n"},
                          record="complete" if damage == "omitted-row" else damage,
                          omitted=[metadata_path])
    offender = installed(site, "foreign-runtime", entries={"console_scripts": ["fi"]},
                         claims=[metadata_path])
    assert offender._path != companion._path
    assert companion.metadata["Name"] == name
    assert metadata_path not in (companion.read_text("RECORD") or "")
    assert offender.locate_file(metadata_path) == companion._path / "METADATA"

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, [name, "foreign-runtime"], metadata_path)
    assert companion.metadata["Name"] == name
    assert (site / path).read_bytes() == b"# supported\n"


@pytest.mark.parametrize("name,version,path", SUPPORTED)
def test_disjoint_scripts_and_metadata_keep_owner_specific_removal(tmp_path, name, version, path):
    site = tmp_path / "site"
    own = sdk(site)
    companion = installed(site, name, version, payload={path: b"# supported\n"},
                          entries={"console_scripts": ["companion-tool"]})
    offender = installed(site, "unrelated-cli", entries={"console_scripts": ["fi"]})

    result = ownership.inspect_installed([own, companion, offender])

    assert result["issues"] == [{"kind": "legacy-console-script", "distribution": "unrelated-cli", "path": "fi"}]
    assert [step for step in result["repair_commands"] if step.startswith("pip uninstall")] == []
    assert_manual_only(result, ["unrelated-cli"], "fi")
    assert not any(step.startswith("pip install ") for step in result["repair_commands"])
    assert result["repair_commands"][-1] == "futureagi-py doctor --offline"
    assert not any(name in step for step in result["repair_commands"])


@pytest.mark.parametrize("name,version,path", SUPPORTED)
def test_supported_owner_scripts_are_not_diagnosed_or_advised_for_removal(tmp_path, name, version, path):
    site = tmp_path / "site"
    own = sdk(site)
    companion = installed(site, name, version, payload={path: b"# supported\n"},
                          entries={"console_scripts": ["companion-tool"]})

    result = ownership.inspect_installed([own, companion])

    assert result["status"] == "PASS"
    assert result["issues"] == []
    assert result["repair_commands"] == []


@pytest.mark.parametrize("metadata_kind", ["egg-info", "dist-info"])
def test_recordless_unrelated_script_owner_still_gets_named_manual_guidance(tmp_path, metadata_kind, monkeypatch):
    from fi._cli import ownership as section

    site = tmp_path / "site"
    own = sdk(site)
    info = site / f"unrelated_cli-1.0.0.{metadata_kind}"
    info.mkdir()
    (info / ("PKG-INFO" if metadata_kind == "egg-info" else "METADATA")).write_text(
        "Metadata-Version: 2.1\nName: unrelated-cli\nVersion: 1.0.0\n"
    )
    (info / "entry_points.txt").write_text("[console_scripts]\nfi = fixture:main\n")
    offender = metadata.PathDistribution(info)
    monkeypatch.setattr(ownership.metadata, "distributions", lambda: [own, offender])

    lines = section.section(None)

    assert any(line.startswith("Manual repair required for unrelated-cli:")
               and "RECORD" in line and "remove this distribution" in line for line in lines)
    assert not any(line.startswith("pip uninstall") or "ai-evaluation" in line for line in lines)
    assert lines[-1] == "futureagi-py doctor --offline"
