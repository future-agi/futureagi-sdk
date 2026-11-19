"""Editable source mappings are explicit diagnostics, not wheel integrity certificates."""
from __future__ import annotations

import base64
import csv
import hashlib
import io
from importlib import metadata
import json
from pathlib import Path

import pytest

from fi._core import namespace_ownership as ownership


def editable(tmp_path, mode="pth", editable_flag=True):
    project = tmp_path / "project"
    source = project / "src"
    (source / "fi/_core").mkdir(parents=True)
    (source / "fi/__init__.py").write_text("# editable source\n")
    (source / "fi/_core/namespace_ownership.py").write_text("# source marker\n")
    site = tmp_path / "site"
    info = site / "futureagi-0.7.0.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text("Metadata-Version: 2.1\nName: futureagi\nVersion: 0.7.0\n")
    (info / "direct_url.json").write_text(json.dumps({"url": project.as_uri(), "dir_info": {"editable": editable_flag}}))
    if mode in {"pth", "poetry"}:
        (site / "futureagi.pth").write_text(str(source) + "\n")
    else:
        module = "__editable___futureagi_finder"
        (site / "__editable__.futureagi.pth").write_text(f"import {module}; {module}.install()\n")
        (site / (module + ".py")).write_text(f"MAPPING = {{'fi': {str(source / 'fi')!r}}}\ndef install():\n    raise RuntimeError('must not execute')\n")
    record = io.StringIO()
    writer = csv.writer(record)
    for file in sorted(site.rglob("*")):
        if file.is_file():
            data = file.read_bytes()
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            name = str(file) if mode == "poetry" else file.relative_to(site).as_posix()
            writer.writerow((name, "sha256=" + digest, str(len(data))))
    writer.writerow(("futureagi-0.7.0.dist-info/RECORD", "", ""))
    (info / "RECORD").write_text(record.getvalue())
    return metadata.PathDistribution(info), source, site, info


def doctor(monkeypatch, capsys, dist):
    from fi._cli import main, registry
    monkeypatch.setattr(registry, "entry_points", lambda: [])
    monkeypatch.setattr(ownership.metadata, "distributions", lambda: [dist])
    code = main.main(["doctor", "--offline", "--json"])
    return code, json.loads(capsys.readouterr().out)


@pytest.mark.parametrize("mode", ["pth", "finder", "poetry"])
def test_valid_editable_mapping_is_reported_not_certified_as_a_wheel(tmp_path, monkeypatch, capsys, mode):
    dist, _, _, _ = editable(tmp_path, mode)
    result = ownership.inspect_installed([dist])
    assert result["status"] == "PASS"
    assert result["checked_files"] == 0
    assert result["editable_installs"] == ["futureagi"]
    assert result["issues"] == []
    code, output = doctor(monkeypatch, capsys, dist)
    assert code == 0
    assert "editable development install" in json.dumps(output)


@pytest.mark.parametrize("damage", ["empty", "missing", "malformed", "runtime-missing"])
def test_noneditable_empty_or_damaged_record_still_exits_three(tmp_path, monkeypatch, capsys, damage):
    dist, _, _, info = editable(tmp_path, editable_flag=False)
    record = info / "RECORD"
    if damage == "missing":
        record.unlink()
    elif damage == "malformed":
        record.write_text("fi/__init__.py,only-two-fields\n")
    elif damage == "runtime-missing":
        record.write_text("fi/__init__.py,sha256=missing,10\n")
    else:
        record.write_text("")
    assert doctor(monkeypatch, capsys, dist)[0] == 3


@pytest.mark.parametrize("damage", ["missing-pth", "wrong-root", "missing-package", "bad-url", "false-flag", "bad-finder", "empty-record", "unrecorded-pth", "changed-pth"])
def test_editable_flag_alone_never_bypasses_mapping_validation(tmp_path, monkeypatch, capsys, damage):
    dist, source, site, info = editable(tmp_path, "finder" if damage == "bad-finder" else "pth")
    if damage == "missing-pth":
        (site / "futureagi.pth").unlink()
    elif damage == "wrong-root":
        data = json.loads((info / "direct_url.json").read_text())
        other = tmp_path / "other"
        other.mkdir()
        data["url"] = other.as_uri()
        (info / "direct_url.json").write_text(json.dumps(data))
    elif damage == "missing-package":
        (source / "fi/__init__.py").unlink()
    elif damage == "bad-url":
        (info / "direct_url.json").write_text(json.dumps({"url": "https://example.org/source", "dir_info": {"editable": True}}))
    elif damage == "false-flag":
        (info / "direct_url.json").write_text(json.dumps({"url": source.parent.as_uri(), "dir_info": {"editable": "true"}}))
    elif damage == "bad-finder":
        (site / "__editable___futureagi_finder.py").write_text("MAPPING = compute_mapping()\n")
    elif damage == "empty-record":
        (info / "RECORD").write_text("")
    elif damage == "unrecorded-pth":
        text = (info / "RECORD").read_text()
        (info / "RECORD").write_text("\n".join(line for line in text.splitlines() if not line.startswith("futureagi.pth,")))
    else:
        (site / "futureagi.pth").write_text(str(source) + "\nimport arbitrary_code\n")
    assert doctor(monkeypatch, capsys, dist)[0] == 3


def test_editable_install_does_not_hide_legacy_distribution(tmp_path):
    dist, _, _, _ = editable(tmp_path)
    legacy = type("Legacy", (), {"metadata": {"Name": "ai-evaluation"}, "version": "1.1.0", "entry_points": [], "read_text": lambda *_: ""})()
    result = ownership.inspect_installed([dist, legacy])
    assert result["status"] == "FAIL"
    assert any(issue["kind"] == "unsupported-distribution" for issue in result["issues"])


def test_valid_editable_cannot_mask_another_empty_sdk_record(tmp_path):
    dist, _, _, _ = editable(tmp_path / "editable")
    damaged, _, _, info = editable(tmp_path / "damaged", editable_flag=False)
    (info / "RECORD").write_text("")
    result = ownership.inspect_installed([dist, damaged])
    assert result["status"] == "FAIL"
    assert any(issue["kind"] == "empty-runtime-record" for issue in result["issues"])
