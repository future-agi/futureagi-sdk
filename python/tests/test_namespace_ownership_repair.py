"""Owner-specific repair guidance; fixtures never import installed companion code."""
from __future__ import annotations

import base64
import csv
import hashlib
from importlib import metadata
import io

import pytest

from fi._core import namespace_ownership as ownership


FOLLOW_UP = [
    "pip install --upgrade --force-reinstall --no-deps futureagi",
    "futureagi-py doctor --offline",
]
SUPPORTED = [
    ("agent-learning-kit", "0.3.4", "fi/alk/example.py"),
    ("agentcc", "2.0.0", "agentcc/__init__.py"),
    ("fi-instrumentation-otel", "1.1.0", "fi_instrumentation/example.py"),
    ("traceai-example", "1.0.0", "traceai_example/__init__.py"),
]


def distribution(root, name, version="1.0.0", *, payload=None, record=True, entry=False):
    """Build real local metadata, optionally without the uninstall RECORD."""
    info = root / "fixture.dist-info"
    info.mkdir(parents=True)
    files = dict(payload or {"unrelated.py": b"# fixture\n"})
    files["fixture.dist-info/METADATA"] = (
        f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
    ).encode()
    if entry:
        files["fixture.dist-info/entry_points.txt"] = b"[console_scripts]\nfi = unrelated:main\n"
    rows = io.StringIO()
    writer = csv.writer(rows)
    for path, data in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow((path, "sha256=" + digest, str(len(data))))
    if record:
        writer.writerow(("fixture.dist-info/RECORD", "", ""))
        (info / "RECORD").write_text(rows.getvalue())
    return metadata.PathDistribution(info)


def sdk(tmp_path):
    return distribution(tmp_path / "sdk", "futureagi", "0.7.0",
                        payload={"fi/__init__.py": b"# sdk\n"})


@pytest.mark.parametrize("name,version", [
    ("unrelated-cli", "1.0.0"),
    ("ai-evaluation", "1.1.0"),
    ("agent-learning-kit", "0.3.3"),
    ("agentcc", "1.0.0"),
])
def test_forbidden_console_repair_uninstalls_only_its_owner(tmp_path, name, version):
    own = sdk(tmp_path)
    offender = distribution(tmp_path / "offender", name, version, entry=True)
    result = ownership.inspect_installed([own, offender])
    assert result["status"] == "FAIL"
    assert {"kind": "legacy-console-script", "distribution": name, "path": "fi"} in result["issues"]
    from test_namespace_ownership_safety import assert_manual_only
    assert_manual_only(result, [name], "fi")


@pytest.mark.parametrize("path", ["fi/evals/foreign.py", "fi/cli/foreign.py"])
def test_unowned_path_repair_names_the_record_owner(tmp_path, path):
    own = sdk(tmp_path)
    offender = distribution(tmp_path / "offender", "foreign-runtime", payload={path: b"# foreign\n"})
    result = ownership.inspect_installed([own, offender])
    assert result["issues"] == [{"kind": "unowned-path", "distribution": "foreign-runtime", "path": path}]
    assert result["repair_commands"] == ["pip uninstall foreign-runtime", *FOLLOW_UP]


def test_multiple_forbidden_owners_are_each_removed_once(tmp_path):
    own = sdk(tmp_path)
    legacy = distribution(tmp_path / "legacy", "ai-evaluation", "1.1.0", entry=True,
                          payload={"fi/evals/legacy.py": b"# legacy\n"})
    unrelated = distribution(tmp_path / "unrelated", "unrelated-cli", entry=True)
    result = ownership.inspect_installed([own, unrelated, legacy])
    assert {issue["distribution"] for issue in result["issues"]} == {"ai-evaluation", "unrelated-cli"}
    from test_namespace_ownership_safety import assert_manual_only
    assert_manual_only(result, ["ai-evaluation", "unrelated-cli"], "fi")


@pytest.mark.parametrize("metadata_kind", ["egg-info", "dist-info"])
def test_recordless_unrelated_owner_requires_manual_repair(tmp_path, metadata_kind, monkeypatch):
    from fi._cli import ownership as section

    own = sdk(tmp_path)
    info = tmp_path / ("unrelated-cli-1.0.0." + metadata_kind)
    info.mkdir()
    metadata_file = "PKG-INFO" if metadata_kind == "egg-info" else "METADATA"
    (info / metadata_file).write_text("Metadata-Version: 2.1\nName: unrelated-cli\nVersion: 1.0.0\n")
    (info / "entry_points.txt").write_text("[console_scripts]\nfi = unrelated:main\n")
    offender = metadata.PathDistribution(info)
    assert offender.read_text("RECORD") is None
    result = ownership.inspect_installed([own, offender])
    assert result["status"] == "FAIL"
    assert result["issues"] == [{"kind": "legacy-console-script", "distribution": "unrelated-cli", "path": "fi"}]
    manual, *follow_up = result["repair_commands"]
    assert manual.startswith("Manual repair required for unrelated-cli:")
    assert "RECORD" in manual and "original installer" in manual and "remove" in manual
    assert "metadata" in manual and "fi" in manual
    assert follow_up == FOLLOW_UP
    assert not any("pip uninstall" in step for step in result["repair_commands"])
    assert not any("ai-evaluation" in step for step in result["repair_commands"])
    monkeypatch.setattr(section, "inspect_installed", lambda: result)
    lines = section.section(None)
    assert manual in lines
    assert lines.index(manual) < lines.index(FOLLOW_UP[0]) < lines.index(FOLLOW_UP[1])


@pytest.mark.parametrize("name,version", [("ai-evaluation", "1.1.0"), ("agent-learning-kit", "0.3.3")])
def test_recordless_legacy_owner_does_not_get_an_unusable_uninstall(tmp_path, name, version):
    own = sdk(tmp_path)
    offender = distribution(tmp_path / "offender", name, version, record=False, entry=True)
    result = ownership.inspect_installed([own, offender])
    assert {"kind": "missing-record", "distribution": name} in result["issues"]
    assert result["repair_commands"][0].startswith(f"Manual repair required for {name}:")
    assert "RECORD" in result["repair_commands"][0]
    assert not any("pip uninstall" in step for step in result["repair_commands"])


@pytest.mark.parametrize("name,version,path", SUPPORTED)
@pytest.mark.parametrize("damaged_sdk", [False, True])
def test_supported_companions_are_never_flagged_or_given_removal_advice(tmp_path, name, version, path, damaged_sdk):
    own = sdk(tmp_path)
    companion = distribution(tmp_path / "companion", name, version, payload={path: b"# supported\n"})
    if damaged_sdk:
        (tmp_path / "sdk/fi/__init__.py").write_bytes(b"# damaged\n")
    result = ownership.inspect_installed([own, companion])
    assert result["status"] == ("FAIL" if damaged_sdk else "PASS")
    assert result["issues"] == ([{
        "kind": "hash-mismatch", "distribution": "futureagi", "path": "fi/__init__.py",
    }] if damaged_sdk else [])
    assert result["repair_commands"] == (FOLLOW_UP if damaged_sdk else [])
    assert not any(name in step or "pip uninstall" in step for step in result["repair_commands"])


def test_overlap_does_not_select_the_supported_owner_for_removal(tmp_path):
    own = sdk(tmp_path)
    path = "fi/alk/example.py"
    companion = distribution(tmp_path / "companion", "agent-learning-kit", "0.3.4", payload={path: b"# supported\n"})
    offender = distribution(tmp_path / "offender", "foreign-runtime", payload={path: b"# foreign\n"})
    offender.locate_file = companion.locate_file
    result = ownership.inspect_installed([own, companion, offender])
    assert {"kind": "overlap", "path": path, "distributions": ["agent-learning-kit", "foreign-runtime"]} in result["issues"]
    assert not any(issue.get("distribution") == "agent-learning-kit" for issue in result["issues"])
    from test_namespace_ownership_safety import assert_manual_only
    assert_manual_only(result, ["foreign-runtime", "agent-learning-kit"], path)
    assert not any("uninstall" in step and "agent-learning-kit" in step for step in result["repair_commands"])
    assert "pip install --upgrade --force-reinstall agent-learning-kit" not in result["repair_commands"]
    assert result["repair_commands"][-1] == FOLLOW_UP[-1]


@pytest.mark.parametrize("name,version,path", SUPPORTED)
def test_supported_version_with_forbidden_script_needs_targeted_manual_repair(tmp_path, name, version, path):
    own = sdk(tmp_path)
    offender = distribution(tmp_path / "offender", name, version, payload={path: b"# supported path\n"}, entry=True)
    result = ownership.inspect_installed([own, offender])
    assert result["issues"] == [{"kind": "legacy-console-script", "distribution": name, "path": "fi"}]
    assert result["repair_commands"][0].startswith(f"Manual repair required for {name}:")
    assert "fi" in result["repair_commands"][0]
    assert not any("pip uninstall" in step for step in result["repair_commands"])


def test_invalid_distribution_name_is_not_interpolated_into_a_shell_command(tmp_path):
    own = sdk(tmp_path)
    name = "unrelated;echo unsafe"
    offender = distribution(tmp_path / "offender", name, entry=True)
    result = ownership.inspect_installed([own, offender])
    assert result["issues"] == [{"kind": "legacy-console-script", "distribution": name, "path": "fi"}]
    assert result["repair_commands"][0].startswith("Manual repair required")
    assert name in result["repair_commands"][0]
    assert result["repair_commands"][1:] == FOLLOW_UP
    assert not any("pip uninstall" in step for step in result["repair_commands"])


@pytest.mark.parametrize("record_text", [
    pytest.param("", id="empty"),
    pytest.param("\n \n", id="blank-lines"),
    pytest.param(",,\n", id="empty-fields"),
    pytest.param("unrelated.py,,\n", id="payload-only"),
    pytest.param("fixture.dist-info/RECORD,,\n", id="record-only"),
    pytest.param("fixture.dist-info/entry_points.txt,,\nfixture.dist-info/RECORD,,\n",
                 id="missing-metadata"),
    pytest.param("fixture.dist-info/METADATA,,\nfixture.dist-info/RECORD,,\n",
                 id="missing-entry-points"),
    pytest.param("other.dist-info/METADATA,,\nother.dist-info/entry_points.txt,,\n"
                 "other.dist-info/RECORD,,\n", id="other-installation-metadata"),
])
def test_unusable_record_requires_owner_specific_manual_repair(tmp_path, record_text):
    own = sdk(tmp_path)
    offender = distribution(tmp_path / "offender", "unrelated-cli", entry=True)
    (tmp_path / "offender/fixture.dist-info/RECORD").write_text(record_text)
    assert offender.read_text("RECORD") is not None

    result = ownership.inspect_installed([own, offender])

    assert result["status"] == "FAIL"
    assert result["issues"] == [{
        "kind": "legacy-console-script", "distribution": "unrelated-cli", "path": "fi",
    }]
    manual, *follow_up = result["repair_commands"]
    assert manual.startswith("Manual repair required for unrelated-cli:")
    assert "usable RECORD" in manual and "original installer" in manual
    assert "remove" in manual and "metadata" in manual and "fi" in manual
    assert follow_up == FOLLOW_UP
    assert not any("pip uninstall" in step for step in result["repair_commands"])


@pytest.mark.parametrize("supported_first", [False, True], ids=["legacy-first", "supported-first"])
@pytest.mark.parametrize("name,old_version,new_version,old_path,new_path", [
    ("agent-learning-kit", "0.3.3", "0.3.4", "fi/alk/old.py", "fi/alk/new.py"),
    ("agentcc", "1.0.0", "2.0.0", "agentcc/old.py", "agentcc/new.py"),
])
def test_duplicate_name_versions_require_targeted_manual_repair(
        tmp_path, supported_first, name, old_version, new_version, old_path, new_path):
    own = sdk(tmp_path)
    legacy = distribution(tmp_path / "legacy", name, old_version, payload={old_path: b"# legacy\n"})
    supported = distribution(tmp_path / "supported", name, new_version, payload={new_path: b"# supported\n"})
    companions = [supported, legacy] if supported_first else [legacy, supported]

    result = ownership.inspect_installed([own, *companions])

    assert result["status"] == "FAIL"
    assert result["issues"] == [{
        "kind": "unsupported-distribution", "distribution": name, "version": old_version,
    }]
    manual, *follow_up = result["repair_commands"]
    assert manual.startswith(f"Manual repair required for {name}:")
    assert "multiple installations" in manual and "original installer" in manual
    assert old_version in manual and new_version in manual
    assert str(tmp_path / "legacy/fixture.dist-info") in manual
    assert str(tmp_path / "supported/fixture.dist-info") in manual
    assert "preserve supported" in manual and "metadata location" in manual
    assert follow_up == FOLLOW_UP
    assert not any("pip uninstall" in step for step in result["repair_commands"])
    assert not any(name in step for step in follow_up)


@pytest.mark.parametrize("recordless_first", [False, True], ids=["recorded-first", "recordless-first"])
def test_duplicate_unrelated_owner_does_not_inherit_another_installations_record(tmp_path, recordless_first):
    own = sdk(tmp_path)
    recorded = distribution(tmp_path / "recorded", "unrelated-cli", "1.0.0", entry=True)
    recordless = distribution(tmp_path / "recordless", "Unrelated_CLI", "2.0.0", record=False, entry=True)
    offenders = [recordless, recorded] if recordless_first else [recorded, recordless]

    result = ownership.inspect_installed([own, *offenders])

    assert result["status"] == "FAIL"
    assert result["issues"] == [{
        "kind": "legacy-console-script", "distribution": "unrelated-cli", "path": "fi",
    }] * 2
    manual, *follow_up = result["repair_commands"]
    assert manual.startswith("Manual repair required for unrelated-cli:")
    assert "multiple installations" in manual and "original installer" in manual
    assert "1.0.0" in manual and "2.0.0" in manual and "'fi'" in manual
    assert str(tmp_path / "recorded/fixture.dist-info") in manual
    assert str(tmp_path / "recordless/fixture.dist-info") in manual
    assert follow_up == FOLLOW_UP
    assert not any("pip uninstall" in step for step in result["repair_commands"])


@pytest.mark.parametrize("name,version,path", SUPPORTED)
def test_supported_installations_at_distinct_locations_get_no_removal_advice(tmp_path, name, version, path):
    own = sdk(tmp_path)
    companions = [distribution(tmp_path / location, name, version, payload={path: b"# supported\n"})
                  for location in ("first", "second")]

    result = ownership.inspect_installed([own, *companions])

    assert result["status"] == "PASS"
    assert result["issues"] == []
    assert result["repair_commands"] == []


@pytest.mark.parametrize("supported_first", [False, True], ids=["legacy-first", "supported-first"])
def test_overlap_with_ambiguous_companion_requires_manual_repair_before_removal(tmp_path, supported_first):
    own = sdk(tmp_path)
    path = "fi/alk/shared.py"
    legacy = distribution(tmp_path / "legacy", "agent-learning-kit", "0.3.3", payload={path: b"# legacy\n"})
    supported = distribution(tmp_path / "supported", "agent-learning-kit", "0.3.4", payload={path: b"# supported\n"})
    offender = distribution(tmp_path / "offender", "foreign-runtime", payload={path: b"# foreign\n"})
    legacy.locate_file = supported.locate_file
    offender.locate_file = supported.locate_file
    companions = [supported, legacy] if supported_first else [legacy, supported]

    result = ownership.inspect_installed([own, *companions, offender])

    assert result["status"] == "FAIL"
    assert {"kind": "unsupported-distribution", "distribution": "agent-learning-kit",
            "version": "0.3.3"} in result["issues"]
    assert {"kind": "overlap", "path": path, "distributions": [
        "agent-learning-kit", "agent-learning-kit", "foreign-runtime",
    ]} in result["issues"]
    assert any(step.startswith("Manual repair required for agent-learning-kit:")
               for step in result["repair_commands"])
    assert any(step.startswith("Manual repair required for foreign-runtime:")
               and path in step and "preserve supported" in step
               for step in result["repair_commands"])
    assert result["repair_commands"][-2:] == FOLLOW_UP
    assert not any("pip uninstall" in step for step in result["repair_commands"])
    assert "pip install --upgrade --force-reinstall agent-learning-kit" not in result["repair_commands"]


@pytest.mark.parametrize("supported_first", [False, True], ids=["offender-first", "supported-first"])
@pytest.mark.parametrize("record_damage", ["missing-metadata", "invalid-path"])
def test_overlap_with_unrestorable_companion_requires_manual_repair(tmp_path, supported_first, record_damage):
    own = sdk(tmp_path)
    path = "fi/alk/shared.py"
    companion = distribution(tmp_path / "companion", "agent-learning-kit", "0.3.4", payload={path: b"# supported\n"})
    offender = distribution(tmp_path / "offender", "foreign-runtime", payload={path: b"# foreign\n"})
    record = tmp_path / "companion/fixture.dist-info/RECORD"
    invalid_path = "fi/../fi/alk/other.py"
    if record_damage == "missing-metadata":
        record.write_text("".join(line for line in record.read_text().splitlines(keepends=True)
                                  if not line.startswith("fixture.dist-info/METADATA,")))
    else:
        record.write_text(record.read_text() + f"{invalid_path},,\n")
    offender.locate_file = companion.locate_file
    companions = [companion, offender] if supported_first else [offender, companion]
    result = ownership.inspect_installed([own, *companions])
    assert result["status"] == "FAIL"
    assert {"kind": "overlap", "path": path, "distributions": [
        "agent-learning-kit", "foreign-runtime",
    ]} in result["issues"]
    assert [i for i in result["issues"] if i.get("distribution") == "agent-learning-kit"] == (
        [{"kind": "invalid-record-path", "distribution": "agent-learning-kit", "path": invalid_path}]
        if record_damage == "invalid-path" else [])
    assert any(step.startswith("Manual repair required for foreign-runtime:")
               and path in step and "preserve supported" in step for step in result["repair_commands"])
    assert any(step.startswith("Manual repair required for agent-learning-kit:")
               and "original installer" in step and "restore" in step for step in result["repair_commands"])
    assert not any("pip uninstall" in step for step in result["repair_commands"])
    assert "pip install --upgrade --force-reinstall agent-learning-kit" not in result["repair_commands"]
    if record_damage == "missing-metadata":
        assert result["repair_commands"][-2:] == FOLLOW_UP
    else:
        # A supported owner's nonlexical RECORD row fails the SIMPLE audit, so
        # even the bounded SDK reinstall is reference-only.
        from test_namespace_ownership_safety import assert_manual_only
        assert_manual_only(result, ["agent-learning-kit", "foreign-runtime", "futureagi"], path)
        assert not any(step.startswith("pip ") for step in result["repair_commands"])
        assert result["repair_commands"][-1] == FOLLOW_UP[-1]
        assert any(step.startswith("Manual repair required for agent-learning-kit, futureagi:")
                   and "agent-learning-kit's namespace audit failed: nonlexical RECORD location" in step
                   and invalid_path in step for step in result["repair_commands"])
        assert any(step.startswith("Manual guidance for futureagi: command text for reference only "
                                   f"(not a repair step): {FOLLOW_UP[0]!r}.")
                   for step in result["repair_commands"])


@pytest.mark.parametrize("invalid_path", ["fi/../fi/alk/shared.py", "fi/alk\\shared.py"])
def test_invalid_record_owner_never_gets_blind_uninstall(tmp_path, invalid_path):
    own = sdk(tmp_path)
    companion = distribution(tmp_path / "companion", "agent-learning-kit", "0.3.4",
                             payload={"fi/alk/shared.py": b"# supported\n"})
    offender = distribution(tmp_path / "offender", "foreign-runtime")
    record = tmp_path / "offender/fixture.dist-info/RECORD"
    record.write_text(record.read_text() + f"{invalid_path},,\n")
    offender.locate_file = companion.locate_file
    result = ownership.inspect_installed([own, companion, offender])
    assert result["status"] == "FAIL"
    assert result["issues"] == [{
        "kind": "invalid-record-path", "distribution": "foreign-runtime", "path": invalid_path,
    }]
    manual, *follow_up = result["repair_commands"]
    assert manual.startswith("Manual repair required for foreign-runtime:")
    assert "RECORD" in manual and "invalid" in manual and "original installer" in manual
    assert repr(invalid_path) in manual and "preserve supported" in manual
    assert follow_up == FOLLOW_UP
    assert not any("pip uninstall" in step for step in result["repair_commands"])
    assert not any("agent-learning-kit" in step for step in result["repair_commands"])


def test_blank_record_guidance_through_real_cli_boundary(tmp_path, monkeypatch):
    from fi._cli import ownership as section

    own = sdk(tmp_path)
    offender = distribution(tmp_path / "offender", "unrelated-cli", entry=True)
    (tmp_path / "offender/fixture.dist-info/RECORD").write_text("\n \n")
    # Use the real scan and CLI exception boundary, not a stubbed scan result.
    monkeypatch.setattr(ownership.metadata, "distributions", lambda: [own, offender])
    lines = section.section(None)
    manual = [line for line in lines if line.startswith("Manual repair required for unrelated-cli:")]
    assert len(manual) == 1, lines
    assert "usable RECORD" in manual[0] and "original installer" in manual[0]
    assert "remove" in manual[0] and "metadata" in manual[0] and "'fi'" in manual[0]
    assert lines.index(manual[0]) < lines.index(FOLLOW_UP[0]) < lines.index(FOLLOW_UP[1])
    assert not any("pip uninstall" in line or "Ownership check failed" in line for line in lines)
