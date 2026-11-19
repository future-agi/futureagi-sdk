"""Editable health and conservative repair selection must hold together."""
from __future__ import annotations

import base64
import csv
import hashlib
from importlib import metadata
import io
import json

import pytest

from fi._core import namespace_ownership as ownership


def install(site, name="futureagi", version="0.7.0", payload=None):
    info = site / f"{name.replace('-', '_')}-{version}.dist-info"
    info.mkdir(parents=True)
    files = dict(payload or {"fi/__init__.py": b"# sdk\n"})
    files[f"{info.name}/METADATA"] = (
        f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
    ).encode()
    rows = io.StringIO()
    writer = csv.writer(rows)
    for path, data in files.items():
        target = site / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow((path, "sha256=" + digest, str(len(data))))
    writer.writerow((f"{info.name}/RECORD", "", ""))
    (info / "RECORD").write_text(rows.getvalue())
    return metadata.PathDistribution(info)


def editable(site, name="futureagi", version="0.7.0", path="fi", mode="pth"):
    project = site / "projects" / name
    source = project / "src"
    package = source / path
    package.mkdir(parents=True)
    (package / "__init__.py").write_bytes(b"# editable source\n")
    if name == "futureagi":
        (package / "_core").mkdir()
        (package / "_core/namespace_ownership.py").write_bytes(b"# sdk marker\n")
    stem = name.replace("-", "_")
    info = f"{stem}-{version}.dist-info"
    payload = {f"{info}/direct_url.json": json.dumps({
        "url": project.as_uri(), "dir_info": {"editable": True},
    }).encode()}
    if mode == "finder":
        module = f"__editable___{stem}_finder"
        payload[f"{stem}.pth"] = f"import {module}; {module}.install()\n".encode()
        payload[f"{module}.py"] = (
            f"MAPPING = {{'fi': {str(package)!r}}}\n"
            "def install():\n    raise RuntimeError('must not execute')\n"
        ).encode()
    else:
        payload[f"{stem}.pth"] = (str(source) + "\n").encode()
    dist = install(site, name, version, payload)
    if mode == "poetry":
        rows = list(csv.reader(io.StringIO(dist.read_text("RECORD"))))
        output = io.StringIO()
        csv.writer(output).writerows((str(site / p), digest, size) for p, digest, size in rows)
        (dist._path / "RECORD").write_text(output.getvalue())
    return dist, package


def manual_only(result, *names):
    assert result["status"] == "FAIL"
    steps = result["repair_commands"]
    assert steps and steps[-1] == "futureagi-py doctor --offline"
    assert not any(step.startswith("pip ") for step in steps)
    guidance = " ".join(step for step in steps if step.startswith("Manual repair required"))
    assert guidance
    assert all(name in guidance for name in names)
    assert "back up or restore" in guidance
    assert guidance.index("back up or restore") < guidance.index("then repair")
    assert guidance.index("then repair") < guidance.index("then re-run")


@pytest.mark.parametrize("mode", ["pth", "finder", "poetry"])
def test_editable_sdk_with_forbidden_owner_is_manual_only(tmp_path, mode):
    site = tmp_path.resolve() / "site"
    own, source = editable(site, mode=mode)
    foreign = install(site, "foreign-runtime", "1.0.0", {"fi/cli/foreign.py": b"# foreign\n"})
    before = (source / "__init__.py").read_bytes()
    result = ownership.inspect_installed([own, foreign])
    manual_only(result, "futureagi")
    assert {"kind": "unowned-path", "distribution": "foreign-runtime",
            "path": "fi/cli/foreign.py"} in result["issues"]
    assert not any(i["kind"] == "empty-runtime-record" for i in result["issues"])
    assert result["editable_installs"] == ["futureagi"]
    assert (source / "__init__.py").read_bytes() == before


@pytest.mark.parametrize("name,version,path", [
    ("agent-learning-kit", "0.3.4", "fi/alk"),
    ("agentcc", "2.0.0", "agentcc"),
    ("fi-instrumentation-otel", "1.1.0", "fi_instrumentation"),
    ("traceai-example", "1.0.0", "traceai_example"),
])
def test_editable_supported_companion_gets_no_destructive_command(tmp_path, name, version, path):
    site = tmp_path.resolve() / "site"
    own = install(site)
    companion, source = editable(site, name, version, path)
    shared = (source / "__init__.py").relative_to(site).as_posix()
    before = (source / "__init__.py").read_bytes()
    foreign = install(site, "foreign-runtime", "1.0.0", {
        "fi/cli/foreign.py": b"# foreign\n", shared: before,
    })
    assert shared not in companion.read_text("RECORD")
    assert shared in foreign.read_text("RECORD")
    assert ownership.inspect_installed([own, companion])["status"] == "PASS"
    result = ownership.inspect_installed([own, companion, foreign])
    manual_only(result, name, "foreign-runtime")
    assert shared in " ".join(result["repair_commands"])
    assert not any(i.get("distribution") == name for i in result["issues"])
    assert (source / "__init__.py").read_bytes() == before


@pytest.mark.parametrize("name", ["futureagi", "foreign-runtime"])
@pytest.mark.parametrize("bad_row", [
    'broken.py,only-two-fields\n',
    '"broken.py"trailer,,\n',
    '"broken.py,,\n',
])
def test_malformed_record_is_manual_only_and_names_its_row(tmp_path, name, bad_row):
    site = tmp_path.resolve() / "site"
    own = install(site)
    foreign = install(site, "foreign-runtime", "1.0.0", {"fi/cli/foreign.py": b"# foreign\n"})
    damaged = own if name == "futureagi" else foreign
    record = damaged._path / "RECORD"
    text = record.read_text()
    row_number = len(text.splitlines()) + 1
    record.write_text(text + bad_row)
    result = ownership.inspect_installed([own, foreign])
    manual_only(result, name)
    invalid = [i for i in result["issues"] if i["kind"] == "invalid-record"]
    assert len(invalid) == 1
    assert invalid[0]["distribution"] == name
    assert invalid[0].get("row") == row_number
    assert invalid[0]["path"] in {"broken.py", f"RECORD row {row_number}"}
    assert "RECORD" in " ".join(result["repair_commands"])
    assert (site / "fi/__init__.py").read_bytes() == b"# sdk\n"


@pytest.mark.parametrize("mode", ["pth", "finder", "poetry"])
def test_validated_editable_empty_runtime_is_healthy(tmp_path, mode):
    own, source = editable(tmp_path.resolve() / "site", mode=mode)
    result = ownership.inspect_installed([own])
    assert result["status"] == "PASS"
    assert result["checked_files"] == 0
    assert result["issues"] == []
    assert result["repair_commands"] == []
    assert result["editable_installs"] == ["futureagi"]
    assert (source / "__init__.py").read_bytes() == b"# editable source\n"


@pytest.mark.parametrize("empty_first", [False, True])
def test_each_ordinary_sdk_requires_its_own_runtime_record(tmp_path, empty_first):
    own = install(tmp_path.resolve() / "healthy")
    empty = install(tmp_path.resolve() / "empty", payload={"other.py": b"# not runtime\n"})
    distributions = [empty, own] if empty_first else [own, empty]
    result = ownership.inspect_installed(distributions)
    assert result["status"] == "FAIL"
    assert result["checked_files"] == 1
    assert {"kind": "empty-runtime-record", "distribution": "futureagi"} in result["issues"]
    manual_only(result, "futureagi")


def test_editable_removal_target_is_never_given_a_command(tmp_path):
    site = tmp_path.resolve() / "site"
    own = install(site)
    foreign, source = editable(site, "foreign-runtime", "1.0.0", "foreign")
    record = foreign._path / "RECORD"
    record.write_text(record.read_text() + "fi/cli/foreign.py,,\n")
    result = ownership.inspect_installed([own, foreign])
    manual_only(result, "foreign-runtime")
    assert (source / "__init__.py").read_bytes() == b"# editable source\n"
