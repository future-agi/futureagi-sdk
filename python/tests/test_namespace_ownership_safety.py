"""Class-level repair safety: no command may delete a supported owner's files.

The 2026-10-30 U26 class ruling supersedes uninstall-then-restore guidance.
Only metadata discovery is substituted; these tests use the real repair selector.
"""
from __future__ import annotations

import pytest

from fi._core import namespace_ownership as ownership
from test_namespace_ownership_repair import FOLLOW_UP, SUPPORTED, distribution, sdk


def damage_record(root, path, damage):
    record = root / "fixture.dist-info/RECORD"
    if damage == "omitted-row":
        record.write_text("".join(line for line in record.read_text().splitlines(keepends=True)
                                  if not line.startswith(path + ",")))
    elif damage == "empty":
        record.write_text("")
    # "missing" is constructed with record=False, without deleting a fixture.


def assert_manual_only(result, names, path):
    steps = result["repair_commands"]
    assert result["status"] == "FAIL"
    assert not any(step.startswith("pip ") for step in steps), steps
    manual = "\n".join(step for step in steps if step.startswith("Manual repair required"))
    for name in names:
        assert name in manual, manual
    assert path in manual
    assert "RECORD" in manual
    assert "back up or restore" in manual
    assert "then repair" in manual
    assert "then re-run" in manual
    assert steps[-1] == "futureagi-py doctor --offline"


@pytest.mark.parametrize("name,version,path", SUPPORTED)
@pytest.mark.parametrize("damage", ["missing", "empty", "omitted-row", "complete"])
@pytest.mark.parametrize("supported_first", [False, True], ids=["offender-first", "supported-first"])
def test_shared_payload_is_protected_even_when_companion_record_cannot_reveal_it(
        tmp_path, name, version, path, damage, supported_first):
    own = sdk(tmp_path)
    companion_root = tmp_path / "companion"
    companion = distribution(companion_root, name, version, record=damage != "missing",
                             payload={path: b"# supported\n"})
    damage_record(companion_root, path, damage)
    offender = distribution(tmp_path / "offender", "foreign-runtime", entry=True,
                            payload={path: b"# foreign\n"})
    # Physical sharing is deliberate, including paths outside fi/.
    offender.locate_file = companion.locate_file
    companions = [companion, offender] if supported_first else [offender, companion]

    result = ownership.inspect_installed([own, *companions])

    assert {"kind": "legacy-console-script", "distribution": "foreign-runtime", "path": "fi"} in result["issues"]
    assert_manual_only(result, [name, "foreign-runtime"], path)
    assert not any(step.startswith(f"pip uninstall -y {name}") for step in result["repair_commands"])


@pytest.mark.parametrize("name,version,path", SUPPORTED)
@pytest.mark.parametrize("damage", ["complete", "missing", "empty", "omitted-row"])
def test_sdk_reinstall_is_blocked_when_its_record_claims_a_companions_payload(
        tmp_path, name, version, path, damage):
    companion_root = tmp_path / "companion"
    companion = distribution(companion_root, name, version, record=damage != "missing",
                             payload={path: b"# supported\n"})
    damage_record(companion_root, path, damage)
    own = distribution(tmp_path / "sdk", "futureagi", "0.7.0",
                       payload={"fi/__init__.py": b"# sdk\n", path: b"# over-claim\n"})
    locate = own.locate_file
    own.locate_file = lambda p: companion.locate_file(p) if str(p) == path else locate(p)
    # Ensure a repair is requested even for a companion outside the fi namespace.
    (tmp_path / "sdk/fi/__init__.py").write_bytes(b"# damaged\n")

    result = ownership.inspect_installed([own, companion])

    assert {"kind": "hash-mismatch", "distribution": "futureagi", "path": "fi/__init__.py"} in result["issues"]
    assert_manual_only(result, ["futureagi", name], path)
    assert "pip install --upgrade --force-reinstall futureagi" not in result["repair_commands"]


@pytest.mark.parametrize("name,version,path", SUPPORTED)
def test_disjoint_owner_specific_commands_remain_available(tmp_path, name, version, path):
    own = sdk(tmp_path)
    companion = distribution(tmp_path / "companion", name, version, payload={path: b"# supported\n"})
    offender = distribution(tmp_path / "offender", "unrelated-cli", entry=True,
                            payload={path: b"# separate installation\n"})
    # Same logical path but distinct physical installations are not shared files.
    result = ownership.inspect_installed([own, companion, offender])

    assert result["status"] == "FAIL"
    assert not any(issue.get("distribution") == name for issue in result["issues"])
    assert_manual_only(result, ["unrelated-cli"], "fi")
    # The companion is never an owner, a command target or a cited location. Its
    # name may appear only inside the offender's own diagnosed RECORD row
    # (agentcc/__init__.py).
    steps = result["repair_commands"]
    owners = {owner.strip() for step in steps
              if step.startswith(("Manual repair required for ", "Manual guidance for "))
              for owner in step.split(":", 1)[0].split(" for ", 1)[1].split(",")}
    assert owners == {"unrelated-cli"}, steps
    references = [step.split("(not a repair step): ", 1)[1].split(". Do not run", 1)[0].strip("'")
                  for step in steps if step.startswith("Manual guidance for ")]
    assert "pip uninstall unrelated-cli" in references, steps
    assert not any(name in command.split() for command in references), references
    assert not any(str(tmp_path / "companion") in step for step in steps), steps
    assert repr(path) in "\n".join(steps)
    assert (tmp_path / "companion" / path).read_bytes() == b"# supported\n"


@pytest.mark.parametrize("bad_row", [
    "../companion/fi/alk/shared.py,,\n",
    "fi/alk/shared.py\n",
    "fi/alk/shared.py,,,\n",
])
def test_untrusted_record_cannot_escape_the_command_safety_gate(tmp_path, bad_row, monkeypatch):
    from fi._cli import ownership as section

    own = sdk(tmp_path)
    companion = distribution(tmp_path / "companion", "agent-learning-kit", "0.3.4",
                             payload={"fi/alk/shared.py": b"# supported\n"})
    offender = distribution(tmp_path / "offender", "foreign-runtime", entry=True)
    record = tmp_path / "offender/fixture.dist-info/RECORD"
    record.write_text(record.read_text() + bad_row)
    monkeypatch.setattr(ownership.metadata, "distributions", lambda: [own, companion, offender])

    lines = section.section(None)

    assert not any(line.startswith("pip ") for line in lines), lines
    assert any("Manual repair required" in line and "foreign-runtime" in line for line in lines)
    assert any("RECORD" in line for line in lines)


@pytest.mark.parametrize("name,version,directory,path", [
    ("agent-learning-kit", "0.3.4", "fi", "fi/alk/shared.py"),
    ("agent-learning-kit", "0.3.4", "fi/alk", "fi/alk/shared.py"),
    ("agent-learning-kit", "0.3.4", "fi/alk/simulate", "fi/alk/simulate/shared.py"),
    ("agent-learning-kit", "0.3.4", "fi/alk/opt", "fi/alk/opt/shared.py"),
    ("fi-instrumentation-otel", "1.1.0", "fi_instrumentation", "fi_instrumentation/shared.py"),
    ("traceai-example", "1.0.0", "traceai_example", "traceai_example/shared.py"),
])
def test_directory_claim_cannot_hide_an_unrecorded_supported_payload(
        tmp_path, name, version, directory, path):
    own = sdk(tmp_path)
    companion = distribution(tmp_path / "companion", name, version, record=False,
                             payload={path: b"# supported\n"})
    offender = distribution(tmp_path / "offender", "foreign-runtime", entry=True)
    record = tmp_path / "offender/fixture.dist-info/RECORD"
    record.write_text(record.read_text() + f"{directory},,\n")
    offender.locate_file = companion.locate_file

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, [name, "foreign-runtime"], directory)


def test_scan_failure_never_falls_back_to_an_unchecked_reinstall(monkeypatch):
    from fi._cli import ownership as section
    from fi._cli.doctor import Problem

    def broken():
        raise OSError("metadata unavailable")

    monkeypatch.setattr(section, "inspect_installed", broken)
    lines = section.section(None)

    assert isinstance(lines[0], Problem)
    assert "OSError" in lines[0]
    assert not any(line.startswith("pip ") for line in lines)
    assert any("Manual repair required" in line and "RECORD" in line for line in lines)
    assert lines[-1] == "futureagi-py doctor --offline"
