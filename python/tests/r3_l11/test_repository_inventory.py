"""Repository inventory reads real local files, never hooks or configured tools."""

import json
import os
from pathlib import Path

import pytest
from fi.context import __main__ as cli
from fi.context.doctor import doctor
from fi.context.lock import InstallationError, canonical_json, sha256
from fi.context.repositories import inventory_repositories


def test_forty_selected_targets_keep_unavailable_and_real_no_lock_policy(tmp_path):
    selected = []
    for index in range(40):
        project = tmp_path / f"repo-{index}"
        selected.append({"repository_id": str(index + 1), "project": str(project)})
        if index == 39:
            continue
        project.mkdir()
        (project / "AGENTS.md").write_bytes(b"Keep my local instructions exactly.\n")
        (project / "CLAUDE.local.md").write_text("Private local precedence\n")
        (project / "nested").mkdir()
        (project / "nested/AGENTS.override.md").write_text("Nested scope\n")
        (project / ".git/hooks").mkdir(parents=True)
        (project / ".git/hooks/post-checkout").write_text(
            "#!/bin/sh\ntouch HOOK_EXECUTED\n"
        )
    result = inventory_repositories(selected)
    assert result["target_count"] == 40
    assert {row["repository_id"] for row in result["targets"]} == {
        str(i + 1) for i in range(40)
    }
    unavailable = [row for row in result["targets"] if row["state"] == "unavailable"]
    assert [row["repository_id"] for row in unavailable] == ["40"]
    for row in result["targets"]:
        if row["state"] == "unavailable":
            continue
        assert row["ownership"] == "not_authorized"
        observation = row["observation"]
        assert observation["lock_sha256"] is None
        assert observation["verification"]["code"] == "lock_missing"
        assert observation["inventory_complete"] is True
        assert {r["path"] for r in observation["findings"] if "path" in r} == {
            "AGENTS.md",
            "CLAUDE.local.md",
            "nested/AGENTS.override.md",
        }
        project = Path(selected[int(row["repository_id"]) - 1]["project"])
        assert not (project / "HOOK_EXECUTED").exists()
        assert not (project / ".futureagi-context.lock.json").exists()
    assert str(tmp_path) not in json.dumps(result)
    assert "Keep my local instructions" not in json.dumps(result)
    digest = result.pop("inventory_digest")
    assert digest == "sha256:" + sha256(canonical_json(result))


def test_instruction_edit_changes_inventory_digest(tmp_path):
    (tmp_path / "AGENTS.md").write_text("First local policy")
    selection = [{"repository_id": "1", "project": str(tmp_path)}]
    before = inventory_repositories(selection)
    (tmp_path / "AGENTS.md").write_text("Changed local policy")
    assert (
        inventory_repositories(selection)["inventory_digest"]
        != before["inventory_digest"]
    )


@pytest.mark.parametrize("kind", ["directory", "instruction", "broken"])
def test_symlink_is_not_followed_or_silently_omitted(tmp_path, kind):
    project = tmp_path / "repo"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "AGENTS.md").write_text("Must not read outside selection")
    link = project / ("nested" if kind == "directory" else "AGENTS.md")
    link.symlink_to(
        outside
        if kind == "directory"
        else outside / ("AGENTS.md" if kind == "instruction" else "missing")
    )
    observed = doctor(project=project)
    assert observed["inventory_complete"] is False
    assert any(row["code"] == "inventory_incomplete" for row in observed["findings"])
    assert not any("sha256" in row for row in observed["findings"])


def test_unreadable_directory_is_not_a_complete_inventory(tmp_path, monkeypatch):
    (tmp_path / "nested").mkdir()
    original = os.open

    def denied(path, *args, **kwargs):
        if path == "nested":
            raise PermissionError("private path must not leak")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", denied)
    observed = doctor(project=tmp_path)
    assert observed["inventory_complete"] is False
    assert "private path" not in json.dumps(observed)


def test_cli_preserves_unavailable_target_and_returns_nonzero(tmp_path, capsys):
    selection = tmp_path / "selected.json"
    selection.write_text(
        json.dumps([{"repository_id": "1", "project": str(tmp_path / "missing")}])
    )
    assert cli.main(["inventory", "--repositories", str(selection)]) == 6
    observed = json.loads(capsys.readouterr().out)
    assert observed["target_count"] == 1
    assert observed["targets"][0]["state"] == "unavailable"


@pytest.mark.parametrize(
    "selection",
    [
        [],
        [{"repository_id": "1", "project": "relative"}],
        [
            {"repository_id": "1", "project": "/a"},
            {"repository_id": "1", "project": "/b"},
        ],
        [{"repository_id": "1", "project": "/a", "command": "not allowed"}],
    ],
)
def test_invalid_selection_has_no_partial_inventory(selection):
    with pytest.raises(InstallationError, match="Select|Supply|numeric"):
        inventory_repositories(selection)
