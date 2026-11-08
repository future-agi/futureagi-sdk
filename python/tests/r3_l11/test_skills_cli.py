from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest
from fi.context.__main__ import main as context_main
from fi.context.doctor import doctor
from fi.context.journal import SKILLS_OWNERSHIP, write_plan
from fi.context.lock import (
    SKILLS_LOCK,
    InstallationError,
    Lease,
    Selector,
    SkillIdentity,
    manifest_digest,
)
from fi.skills.__main__ import main as skills_main
from fi.skills.installer import (
    SkillBundle,
    apply_skill_plan,
    plan_install_skill,
    plan_remove_skill,
    verify_skills,
)


def skill(name="refunds", number=5, version=1):
    files = {
        "SKILL.md": f"---\nname: {name}\ndescription: Use for policy requests.\n---\nPolicy version {version}.\n".encode(),
        "references/policy.md": b"Supporting policy",
    }
    return SkillBundle(
        identity=SkillIdentity(
            origin="https://registry.example.invalid",
            organization_id=str(UUID(int=1)),
            workspace_id=str(UUID(int=2)),
            skill_id=str(UUID(int=number)),
            name=name,
            version=version,
            version_id=str(UUID(int=number * 100 + version)),
            digest=manifest_digest(files),
            requested=Selector(label="production"),
        ),
        lease=Lease(
            resolution_id="synthetic-leaf-lease",
            resolution_expires_at=(
                datetime.now(timezone.utc) + timedelta(minutes=10)
            ).isoformat(),
        ),
        files=files,
    )


@pytest.fixture
def project(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    path = tmp_path / "project"
    path.mkdir()
    return path


def planned(source, project, **kwargs):
    return plan_install_skill(
        source, project=project, profile="codex", allow_preview=True, **kwargs
    )


def apply(plan):
    apply_skill_plan(plan, authorize=lambda authorization: None, quiescent=True)


def test_standalone_cumulative_lock_install_update_restore_and_remove(project):
    apply(planned(skill(), project))
    first = (project / ".agents/skills/refunds/SKILL.md").read_bytes()
    apply(planned(skill("payments", 6), project))
    lock = json.loads((project / SKILLS_LOCK).read_bytes())
    assert set(lock) == {"schema", "origin", "skills", "skipped"}
    assert {item["name"] for item in lock["skills"]} == {"payments", "refunds"}
    assert set(lock["skills"][0]) == {
        "name",
        "version",
        "version_id",
        "digest",
        "label",
    }
    assert (project / ".agents/skills/refunds/SKILL.md").read_bytes() == first
    assert b"synthetic-leaf-lease" not in (project / SKILLS_LOCK).read_bytes()
    apply(planned(skill(version=2), project, operation="update"))
    assert verify_skills(project=project)["verified"]
    apply(planned(skill(version=1), project, operation="restore"))
    assert (project / ".agents/skills/refunds/SKILL.md").read_bytes() == first
    apply(plan_remove_skill(project=project, name="payments"))
    assert (
        json.loads((project / SKILLS_LOCK).read_bytes())["skills"][0]["name"]
        == "refunds"
    )
    apply(plan_remove_skill(project=project, name="refunds"))
    assert not (project / SKILLS_LOCK).exists()
    assert not (project / SKILLS_OWNERSHIP).exists()


def test_cumulative_changed_ownership_invalidates_an_older_plan(project):
    one = planned(skill(), project)
    two = planned(skill("payments", 6), project)
    apply(one)
    with pytest.raises(InstallationError) as exc:
        apply(two)
    assert exc.value.code == "stale_plan"
    assert not (project / ".agents/skills/payments/SKILL.md").exists()


@pytest.mark.parametrize("state", ["dirty", "missing", "unowned"])
def test_skill_update_preserves_local_exceptions(project, state):
    apply(planned(skill(), project))
    path = project / ".agents/skills/refunds/references/policy.md"
    if state == "dirty":
        path.write_bytes(b"User edit")
    elif state == "missing":
        path.unlink()
    else:
        (path.parent / "unowned.md").write_bytes(b"Unowned")
    with pytest.raises(InstallationError):
        planned(skill(version=2), project)
    if state == "dirty":
        apply(plan_remove_skill(project=project, name="refunds"))
        assert path.read_bytes() == b"User edit"


def test_same_name_new_identity_is_not_adopted(project):
    apply(planned(skill(), project))
    with pytest.raises(InstallationError) as exc:
        planned(skill(number=7), project)
    assert exc.value.code == "identity_collision"


def test_legacy_download_lock_is_not_assumed_ownership(project):
    (project / SKILLS_LOCK).write_text(
        '{"schema":1,"origin":"https://registry.example.invalid","skills":[],"skipped":[]}'
    )
    with pytest.raises(InstallationError) as exc:
        planned(skill(), project)
    assert exc.value.code == "ownership_missing"


def test_unowned_extra_native_file_fails_byte_verifier(project):
    apply(planned(skill(), project))
    path = project / ".agents/skills/refunds/extra.md"
    path.write_bytes(b"Untracked")
    outcome = verify_skills(project=project)
    assert not outcome["verified"]
    assert outcome["differences"] == [
        {"path": ".agents/skills/refunds/extra.md", "state": "unexpected"}
    ]
    removal = plan_remove_skill(project=project, name="refunds")
    assert ".agents/skills/refunds/extra.md" in removal.preserved
    apply(removal)
    assert path.read_bytes() == b"Untracked"


def test_skills_cli_verifies_without_credentials_and_removes_via_private_plan(
    project, tmp_path, capsys
):
    apply(planned(skill(), project))
    assert skills_main(["verify", "--project", str(project)]) == 0
    assert json.loads(capsys.readouterr().out)["authorization"] == "not_checked"
    output = tmp_path / "removal.json"
    assert (
        skills_main(
            [
                "remove",
                "--project",
                str(project),
                "--name",
                "refunds",
                "--plan",
                str(output),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert output.stat().st_mode & 0o777 == 0o600
    assert skills_main(["apply", "--plan", str(output), "--quiescent"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "removed"


def test_cli_leaf_application_fails_closed_when_contract_source_not_integrated(
    project, tmp_path, capsys
):
    prepared = planned(skill(), project)
    path = tmp_path / "plan.json"
    write_plan(path, prepared)
    assert skills_main(["apply", "--plan", str(path), "--quiescent"]) == 3
    assert (
        json.loads(capsys.readouterr().out)["error"]["code"]
        == "leaf_contract_unavailable"
    )
    assert list(project.iterdir()) == []


def test_context_cli_configuration_ignores_broad_api_environment(
    project, monkeypatch, capsys
):
    for name in [
        "FI_CONTEXT_ORIGIN",
        "FI_CONTEXT_CREDENTIAL",
        "FI_CONTEXT_ORGANIZATION_ID",
        "FI_CONTEXT_WORKSPACE_ID",
    ]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_API_KEY", "synthetic-ambient-key")
    monkeypatch.setenv("FI_SECRET_KEY", "synthetic-ambient-secret")
    assert (
        context_main(
            [
                "plan",
                "--name",
                "policy",
                "--client",
                "codex",
                "--project",
                str(project),
                "--out",
                str(project / "plan.json"),
            ]
        )
        == 3
    )
    output = capsys.readouterr().out
    assert "configuration_required" in output
    assert "synthetic-ambient" not in output


def test_doctor_is_read_only_and_distinguishes_additional_context(project):
    (project / "AGENTS.override.md").write_bytes(b"Local override")
    nested = project / "subproject"
    nested.mkdir()
    (nested / "AGENTS.md").write_bytes(b"Additional context")
    result = doctor(project=project)
    assert result["native_qualification"] == "not_qualified"
    assert result["delivery"] == "not_observed"
    assert {f["path"] for f in result["findings"] if "path" in f} == {
        "AGENTS.override.md",
        "subproject/AGENTS.md",
    }
    assert not (Path.home() / ".local").exists()


def test_action_uses_isolated_pinned_sdk_without_project_hooks():
    import yaml

    path = (
        Path(__file__).resolve().parents[3]
        / ".github/actions/context-verify/action.yml"
    )
    action = yaml.safe_load(path.read_text())
    script = action["runs"]["steps"][0]["run"]
    assert '"$FI_VERIFY_PYTHON" -I -' in script
    assert "materialize.py" in script and "sha256" in script
    assert "pip install" not in script
    assert "subprocess" not in script
    assert 'main(["verify"' in script
