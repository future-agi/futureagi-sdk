"""Text-only native profiles fail closed before any project write.

All substitution samples are inert strings; no native host or shell is invoked.
"""
from __future__ import annotations

import json

import pytest
from fi.context import materialize
from fi.context.journal import parse_plan
from fi.context.lock import (
    InstallationError,
    SourceBundle,
    canonical_json,
    manifest_digest,
)
from fi.skills import installer
from test_materializer import bundle
from test_skills_cli import skill


@pytest.fixture
def project(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    root = tmp_path / "project"
    root.mkdir()
    return root


def with_skill_text(raw, linked):
    source = bundle() if linked else skill()
    files = dict(source.files)
    files["skills/refunds/SKILL.md" if linked else "SKILL.md"] = raw
    if linked:
        descriptor = json.loads(files[".futureagi/context.json"])
        descriptor["links"][0]["digest"] = manifest_digest(
            {p.removeprefix("skills/refunds/"): b for p, b in files.items() if p.startswith("skills/refunds/")}
        )
        files[".futureagi/context.json"] = canonical_json(descriptor)
    cls = SourceBundle if linked else installer.SkillBundle
    return cls(
        identity=source.identity.model_copy(update={"digest": manifest_digest(files)}),
        lease=source.lease,
        files=files,
    )


@pytest.mark.parametrize("linked", [False, True], ids=["standalone", "linked"])
@pytest.mark.parametrize("body", [
    b"Inline !`fixture-only` text.\n",
    b"!```\nfixture-only\n```\n",
    b"```markdown\n!`fixture-only`\n```\n",
    b"~~~text\n!`fixture-only`\n~~~\n",
])
def test_preview_rejects_shell_substitutions_in_complete_skill(project, linked, body):
    source = with_skill_text(b"---\nname: refunds\ndescription: Refund policy.\n---\n" + body, linked)
    plan = materialize.plan_install if linked else installer.plan_install_skill
    with pytest.raises(InstallationError, match="text-only") as failure:
        plan(source, project=project, profile="claude-code", allow_preview=True)
    assert failure.value.code == "runtime_incompatible"
    assert failure.value.exit_code == 7
    assert list(project.iterdir()) == []


@pytest.mark.parametrize("linked", [False, True], ids=["standalone", "linked"])
def test_old_skill_plan_is_revalidated_at_apply(project, monkeypatch, linked):
    source = with_skill_text(b"---\nname: refunds\ndescription: Refund policy.\n---\n!`fixture-only`\n", linked)
    module = materialize if linked else installer
    plan = materialize.plan_install if linked else installer.plan_install_skill
    apply = materialize.apply_plan if linked else installer.apply_skill_plan
    # Simulate an old SDK's plan, not installation or native execution.
    with monkeypatch.context() as previous:
        previous.setattr(module, "check_skill_content", lambda *_: None)
        prepared = plan(source, project=project, profile="claude-code", allow_preview=True)
    with pytest.raises(InstallationError, match="text-only"):
        apply(parse_plan(prepared.to_bytes()), authorize=lambda _: None, quiescent=True)
    assert not (project / ".claude").exists()
    assert not (project / ".futureagi-context.lock.json").exists()
    assert not (project / ".futureagi-skills.lock.json").exists()


@pytest.mark.parametrize("linked", [False, True], ids=["standalone", "linked"])
def test_plain_fenced_documentation_remains_installable(project, linked):
    raw = b"---\nname: refunds\ndescription: Refund policy.\n---\n```text\nApproved policy only.\n```\n"
    source = with_skill_text(raw, linked)
    plan = materialize.plan_install if linked else installer.plan_install_skill
    apply = materialize.apply_plan if linked else installer.apply_skill_plan
    prepared = plan(source, project=project, profile="claude-code", allow_preview=True)
    apply(prepared, authorize=lambda _: None, quiescent=True)
    assert (project / ".claude/skills/refunds/SKILL.md").read_bytes() == raw


@pytest.mark.parametrize("profile", ["codex", "claude-code"])
@pytest.mark.parametrize("existing", [False, True], ids=["absent", "unrelated-local-policy"])
@pytest.mark.parametrize("root", [
    b"Run `cat references/policy.md` before responding.\n",
    b"Read references/policy.md before responding.\n",
    b"Run `cat ./references/policy.md` before responding.\n",
    b'{"policy": "references/policy.md"}\n',
    b"Read references/policy%2Emd before responding.\n",
    b"```text\nreferences/policy.md\n```\n",
    b"[Approved](references/policy.md) but also read references/policy.md.\n",
])
def test_literal_relocation_blocks_plan_and_old_plan_apply(project, monkeypatch, profile, existing, root):
    local = project / "references/policy.md"
    if existing:
        local.parent.mkdir()
        local.write_bytes(b"Unrelated local policy")
    source = bundle(root=root, extra={"references/policy.md": b"Approved policy"})
    with pytest.raises(InstallationError, match="manual integration") as failure:
        materialize.plan_install(source, project=project, profile=profile, allow_preview=True)
    assert failure.value.code == "runtime_incompatible"
    # An old persisted plan must not bypass the corrected projection validator.
    with monkeypatch.context() as previous:
        previous.setattr(materialize, "project_entrypoint", lambda raw, *_: raw)
        prepared = materialize.plan_install(source, project=project, profile=profile, allow_preview=True)
    with pytest.raises(InstallationError, match="manual integration"):
        materialize.apply_plan(parse_plan(prepared.to_bytes()), authorize=lambda _: None, quiescent=True)
    assert not (project / "AGENTS.md").exists()
    assert not (project / ".futureagi-context.lock.json").exists()
    assert not (project / ".futureagi/context").exists()
    assert local.read_bytes() == b"Unrelated local policy" if existing else not local.exists()
