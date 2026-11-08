"""Wheel gates and offline diagnostics exercise real RECORD files, not distribution imports."""
from __future__ import annotations

import base64
import csv
import hashlib
from importlib import metadata, util
import io
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest

from fi._core import namespace_ownership as ownership

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/packaging/check_ownership.py"
spec = util.spec_from_file_location("check_ownership", SCRIPT)
gate = util.module_from_spec(spec)
spec.loader.exec_module(gate)


def wheel(tmp_path, name="futureagi", version="0.7.0", payload=None, entry=None):
    stem = name.replace("-", "_") + "-" + version
    info = stem + ".dist-info"
    files = dict(payload or {"fi/__init__.py": b"# sample\n"})
    files[info + "/METADATA"] = f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n".encode()
    files[info + "/WHEEL"] = b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    if entry:
        files[info + "/entry_points.txt"] = entry.encode()
    record = info + "/RECORD"
    out = io.StringIO()
    writer = csv.writer(out)
    for path, data in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow((path, "sha256=" + digest, str(len(data))))
    writer.writerow((record, "", ""))
    files[record] = out.getvalue().encode()
    target = tmp_path / (stem + "-py3-none-any.whl")
    with zipfile.ZipFile(target, "w") as archive:
        for path, data in files.items():
            archive.writestr(path, data)
    return target


def install_fixture(tmp_path, archive):
    # Only the test-generated wheels above are extracted.
    with zipfile.ZipFile(archive) as z:
        z.extractall(tmp_path)
    return metadata.PathDistribution(next(tmp_path.glob("*.dist-info")))


@pytest.mark.parametrize("path", ["fi/cli/main.py", "fi/agentcc.py", "fi/alk/x.py", "fi/alk/opt/x.py",
                                 "fi/alk/simulate/x.py", "fi/alk/evals/x.py", "fi/alk/harness/x.py",
                                 "fi/alk/__init__.py", "fi/alk/data.json",
                                 "unrelated.py", "fi/../escape.py", "/fi/x.py"])
def test_candidate_cannot_ship_unowned_paths(tmp_path, path):
    with pytest.raises(ValueError):
        gate.check_combination([wheel(tmp_path, payload={path: b"x"})])


def test_supported_companions_have_disjoint_records(tmp_path):
    sdk = wheel(tmp_path, payload={
        "fi/__init__.py": b"# sdk\n", "fi/evals/__init__.py": b"# sdk evals\n",
        "fi/simulate/__init__.py": b"# sdk error stub\n", "fi/opt/__init__.py": b"# sdk error stub\n",
    })
    alk = wheel(tmp_path, "agent-learning-kit", "0.3.4", {
        "fi/alk/__init__.py": b"# alk\n", "fi/alk/a.py": b"a",
        "fi/alk/evals/__init__.py": b"# alk evals\n", "fi/alk/harness/__init__.py": b"# harness\n",
        "fi/alk/simulate/__init__.py": b"# simulate\n", "fi/alk/opt/__init__.py": b"# opt\n",
    })
    shim = wheel(tmp_path, "agentcc", "2.0.0", {"agentcc/__init__.py": b"a"})
    trace = wheel(tmp_path, "fi-instrumentation-otel", "1.1.0", {"fi_instrumentation/a.py": b"a"})
    assert gate.check_combination([sdk, alk, shim, trace])["status"] == "PASS"


@pytest.mark.parametrize("name,version", [("ai-evaluation", "1.1.0"), ("agent-learning-kit", "0.3.3"),
                                         ("agent-learning-kit", "0.3.4rc1"), ("unknown", "1.0.0")])
def test_legacy_or_unknown_distributions_fail_gate(tmp_path, name, version):
    with pytest.raises(ValueError, match="unsupported distribution"):
        gate.check_combination([wheel(tmp_path, name, version)])


@pytest.mark.parametrize("path", [
    "fi/__init__.py", "fi/evals/__init__.py", "fi/simulate/__init__.py", "fi/opt/__init__.py",
    "alk/__init__.py", "alk/evals/__init__.py",
])
def test_alk_cannot_ship_sdk_namespaces_or_the_retired_top_level_root(tmp_path, path):
    with pytest.raises(ValueError, match="unowned runtime"):
        gate.check_combination([wheel(tmp_path, "agent-learning-kit", "0.3.4", {path: b"x"})])


def test_legacy_console_entry_is_forbidden(tmp_path):
    with pytest.raises(ValueError, match="console script"):
        gate.check_combination([wheel(tmp_path, entry="[console_scripts]\nfi = fi.cli:main\n")])


def test_spread_paths_are_checked_by_installed_destination(tmp_path):
    path = "futureagi-0.7.0.data/purelib/fi/alk/foreign.py"
    with pytest.raises(ValueError, match="unowned runtime"):
        gate.check_combination([wheel(tmp_path, payload={path: b"x"})])


def test_two_archive_names_cannot_alias_one_installed_path(tmp_path):
    payload = {"fi/x.py": b"x", "futureagi-0.7.0.data/purelib/fi/x.py": b"x"}
    with pytest.raises(ValueError, match="duplicate installed path"):
        gate.check_combination([wheel(tmp_path, payload=payload)])


def test_trace_companions_cannot_overlap(tmp_path):
    one = wheel(tmp_path, "fi-instrumentation-otel", "1.1.0", {"fi_instrumentation/a.py": b"a"})
    two = wheel(tmp_path, "traceai-openai", "0.1.10", {"fi_instrumentation/a.py": b"b"})
    with pytest.raises(ValueError, match="overlap"):
        gate.check_combination([one, two])


@pytest.mark.parametrize("mutation", ["content", "unrecorded", "missing", "duplicate-row"])
def test_record_integrity_is_mandatory(tmp_path, mutation):
    target = wheel(tmp_path)
    with zipfile.ZipFile(target) as z:
        files = {p: z.read(p) for p in z.namelist()}
    if mutation == "content":
        files["fi/__init__.py"] = b"changed"
    elif mutation == "unrecorded":
        files["fi/x.py"] = b"unrecorded"
    elif mutation == "missing":
        del files["fi/__init__.py"]
    else:
        files["futureagi-0.7.0.dist-info/RECORD"] += b"fi/__init__.py,,\n"
    with zipfile.ZipFile(target, "w") as z:
        for path, data in files.items():
            z.writestr(path, data)
    with pytest.raises(ValueError):
        gate.check_combination([target])


def test_doctor_names_overlap_changed_and_missing_files(tmp_path):
    archive = wheel(tmp_path, payload={"fi/__init__.py": b"original", "fi/api/auth.py": b"original"})
    site = tmp_path / "site"
    own = install_fixture(site, archive)
    legacy = install_fixture(tmp_path / "legacy", wheel(tmp_path, "ai-evaluation", "1.1.0"))
    # Share the installation target without importing legacy Python.
    legacy.locate_file = lambda path: site / str(path)
    (site / "fi/__init__.py").write_bytes(b"changed")
    (site / "fi/api/auth.py").unlink()
    result = ownership.inspect_installed([own, legacy])
    kinds = {i["kind"] for i in result["issues"]}
    assert {"overlap", "hash-mismatch", "missing-file", "unsupported-distribution"} <= kinds
    assert result["status"] == "FAIL"
    from test_namespace_ownership_safety import assert_manual_only
    assert_manual_only(result, ["ai-evaluation", "futureagi"], "fi/__init__.py")
    assert not any(step.startswith("pip ") for step in result["repair_commands"])


def test_consumer_integrity_reads_missing_record_entries(tmp_path, monkeypatch):
    dist = install_fixture(tmp_path / "site", wheel(tmp_path))
    (tmp_path / "site/fi/__init__.py").unlink()
    probe_spec = util.spec_from_file_location("consumer_probe", SCRIPT.with_name("consumer_probe.py"))
    probe = util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)
    monkeypatch.setattr(probe.metadata, "distribution", lambda _: dist)
    result = probe.record_integrity()
    assert {"kind": "missing", "path": "fi/__init__.py"} in result["errors"]


def test_clean_installed_distribution_passes(tmp_path):
    dist = install_fixture(tmp_path / "site", wheel(tmp_path))
    assert ownership.inspect_installed([dist])["status"] == "PASS"
    assert ownership.inspect_installed([])["status"] == "NOT-INSTALLED"


@pytest.mark.parametrize("version,remove_alk", [("0.3.3", True), ("0.3.4", False)])
def test_repair_preserves_supported_companions(tmp_path, version, remove_alk):
    own = install_fixture(tmp_path / "sdk", wheel(tmp_path))
    (tmp_path / "sdk/fi/__init__.py").unlink()
    alk = install_fixture(tmp_path / "alk", wheel(tmp_path, "agent-learning-kit", version,
                                                {"fi/alk/a.py": b"sample"}))
    result = ownership.inspect_installed([own, alk])
    assert ("agent-learning-kit" in result["repair_commands"][0]) is remove_alk


def test_missing_or_empty_record_is_not_clean():
    dist = SimpleNamespace(metadata={"Name": "futureagi"}, version="0.7.0",
                           read_text=lambda _: None, entry_points=[])
    assert ownership.inspect_installed([dist])["status"] == "FAIL"
    dist.read_text = lambda _: ""
    assert ownership.inspect_installed([dist])["status"] == "FAIL"


def test_doctor_wires_nonzero_ownership_diagnosis(monkeypatch, capsys):
    from fi._cli import ownership as section, main, registry
    monkeypatch.setattr(registry, "entry_points", lambda: [])
    monkeypatch.setattr(section, "inspect_installed", lambda: {
        "status": "FAIL", "checked_files": 1,
        "issues": [{"kind": "missing-file", "distribution": "futureagi", "path": "fi/__init__.py"}],
        "repair_commands": ownership.manifest()["repair_commands"],
    })
    assert main.main(["doctor", "--json", "--offline"]) == 3
    data = json.loads(capsys.readouterr().out)
    assert "missing-file" in data["sections"]["Package ownership"]["problems"][0]


def test_doctor_survives_removed_root_version(monkeypatch, capsys):
    import fi
    from fi._cli import main, registry
    monkeypatch.delattr(fi, "__version__", raising=False)
    monkeypatch.setattr(registry, "entry_points", lambda: [])
    assert main.main(["doctor", "--offline", "--json"]) == 0
    assert "Package ownership" in json.loads(capsys.readouterr().out)["sections"]


def test_matrix_missing_inputs_are_not_passes(tmp_path):
    import subprocess
    import sys
    command = [sys.executable, "-I", str(SCRIPT.with_name("migration_matrix.py"))]
    for key in ("candidate", "legacy", "dependencies", "requirements", "golden", "dependency-status"):
        command += ["--" + key, str(tmp_path / key)]
    output = tmp_path / "matrix"
    command += ["--output", str(output)]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert proc.returncode == 1, proc.stderr
    result = json.loads((output / "matrix.json").read_text())
    assert len(result["cells"]) == 14
    assert {r["status"] for r in result["cells"]} == {"NOT-EVALUATED"}
    assert {(r["manager"], r["case"]) for r in result["cells"]} == {
        (manager, f"M{i}") for manager in ("pip", "uv") for i in range(1, 8)
    }


@pytest.mark.parametrize("missing_dependencies", [[], ["rouge-score==0.1.2"]])
def test_completed_matrix_with_missing_inputs_exits_nonzero(tmp_path, missing_dependencies):
    import subprocess
    import sys

    candidate = wheel(tmp_path)
    inputs = {
        "candidate": candidate,
        "legacy": tmp_path / "legacy",
        "dependencies": tmp_path / "dependencies",
        "requirements": tmp_path / "requirements.txt",
        "golden": tmp_path / "golden.json",
        "dependency-status": tmp_path / "dependency-status.json",
    }
    inputs["legacy"].mkdir()
    inputs["dependencies"].mkdir()
    inputs["requirements"].write_text("")
    inputs["golden"].write_text("{}")
    inputs["dependency-status"].write_text(json.dumps({"missing": missing_dependencies}))
    command = [sys.executable, "-I", str(SCRIPT.with_name("migration_matrix.py"))]
    for name, path in inputs.items():
        command += ["--" + name, str(path)]
    output = tmp_path / "matrix"
    command += ["--output", str(output)]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=10)
    result = json.loads((output / "matrix.json").read_text())
    assert result["status"] == "NOT-EVALUATED"
    assert result["cells"][0]["case"] == "REC-0"
    assert result["cells"][0]["status"] == "PASS"
    assert not any(row["status"] == "FAIL" for row in result["cells"])
    for manager in ("pip", "uv"):
        cells = {row["case"]: row["status"] for row in result["cells"] if row["manager"] == manager}
        assert all(cells[f"M{i}"] == "NOT-EVALUATED" for i in range(1, 8))
    assert proc.returncode == 1, proc.stderr


@pytest.mark.parametrize("metadata_kind", ["egg-info", "dist-info"])
@pytest.mark.parametrize("group,script,forbidden", [
    ("console_scripts", "fi", True),
    ("console_scripts", "other", False),
    ("other_plugins", "fi", False),
])
def test_doctor_checks_entry_points_without_record(tmp_path, metadata_kind, group, script, forbidden):
    own = install_fixture(tmp_path / "site", wheel(tmp_path))
    info = tmp_path / "site" / ("unrelated-1.0.0." + metadata_kind)
    info.mkdir()
    metadata_file = "PKG-INFO" if metadata_kind == "egg-info" else "METADATA"
    (info / metadata_file).write_text("Metadata-Version: 2.1\nName: unrelated\nVersion: 1.0.0\n")
    (info / "entry_points.txt").write_text(f"[{group}]\n{script} = unrelated:main\n")
    companion = metadata.PathDistribution(info)
    assert companion.read_text("RECORD") is None
    assert len(companion.entry_points) == 1

    result = ownership.inspect_installed([own, companion])
    assert result["checked_files"] == 1
    assert result["status"] == ("FAIL" if forbidden else "PASS")
    assert result["issues"] == ([{
        "kind": "legacy-console-script", "distribution": "unrelated", "path": "fi",
    }] if forbidden else [])
    assert bool(result["repair_commands"]) is forbidden


def test_ownership_scan_exception_is_a_problem(monkeypatch):
    from fi._cli import ownership as section
    from fi._cli.doctor import Problem
    def broken():
        raise OSError("metadata unavailable")
    monkeypatch.setattr(section, "inspect_installed", broken)
    assert isinstance(section.section(None)[0], Problem)
