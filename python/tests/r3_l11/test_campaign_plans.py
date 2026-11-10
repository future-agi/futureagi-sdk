"""Local campaign export is a review document, not GitHub execution evidence."""

import json
from uuid import UUID

import httpx
import pytest
from fi.context.campaigns import CampaignClient, target_plan
from fi.context.lock import CONTEXT_LOCK, InstallationError, canonical_json, sha256
from fi.platform import Client
from test_materializer import apply, bundle, plan


@pytest.fixture
def project(tmp_path, monkeypatch):
    (tmp_path / "home").mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    root = tmp_path / "repo"
    root.mkdir()
    return root


def export(prepared, **kwargs):
    return target_plan(
        prepared,
        repository_id="100",
        base_commit="a" * 40,
        binding_revision=1,
        campaign_revision=kwargs.get("revision", 1),
    )


def test_cold_plan_binds_real_local_policy_without_leases_or_absolute_paths(project):
    local = b"Retain local policy without a trailing newline"
    (project / "AGENTS.md").write_bytes(local)
    prepared = plan(bundle(), project, adopt_local=True)
    result = export(prepared)
    root = next(row for row in result["changes"] if row["path"] == "AGENTS.md")
    assert root["ownership"] == "adopted"
    assert root["before_sha256"] == sha256(local)
    assert root["action"] == "replace"
    assert result["local_review_required"] is True
    assert result["previous_lock_digest"] is None
    assert "synthetic-lease" not in json.dumps(result)
    assert str(project) not in json.dumps(result)
    assert not (project / CONTEXT_LOCK).exists()
    assert (project / "AGENTS.md").read_bytes() == local
    expected = {
        key: value
        for key, value in result.items()
        if key not in {"plan_digest", "campaign_revision"}
    }
    assert result["plan_digest"] == "sha256:" + sha256(canonical_json(expected))
    # Campaign CAS advances while recording other targets; exact review does not.
    assert export(prepared, revision=40)["plan_digest"] == result["plan_digest"]


def test_modified_local_preimage_cannot_export_the_old_plan(project):
    (project / "AGENTS.md").write_bytes(b"Before")
    prepared = plan(bundle(), project, adopt_local=True)
    (project / "AGENTS.md").write_bytes(b"After")
    with pytest.raises(InstallationError, match="preimages"):
        export(prepared)


def test_new_unowned_native_file_blocks_campaign_export(project):
    prepared = plan(bundle(), project)
    unexpected = project / ".agents/skills/refunds/local.md"
    unexpected.parent.mkdir(parents=True)
    unexpected.write_bytes(b"Keep local skill instructions")
    with pytest.raises(InstallationError) as error:
        export(prepared)
    assert error.value.code == "unmanaged_collision"
    assert unexpected.read_bytes() == b"Keep local skill instructions"
    assert not (project / CONTEXT_LOCK).exists()


def test_update_and_reviewed_reverse_have_exact_previous_lock_digest(project):
    first = bundle(version=1)
    apply(plan(first, project))
    old_bytes = (project / CONTEXT_LOCK).read_bytes()
    second = plan(bundle(version=2), project, operation="update")
    assert export(second)["previous_lock_digest"] == "sha256:" + sha256(old_bytes)
    apply(second)
    current = (project / CONTEXT_LOCK).read_bytes()
    reverse = export(plan(first, project, operation="restore"))
    assert reverse["previous_lock_digest"] == "sha256:" + sha256(current)
    assert reverse["desired_version_id"] == first.identity.version_id
    assert (project / CONTEXT_LOCK).read_bytes() == current


def test_transport_uses_frozen_routes_and_original_idempotency_key():
    campaign_id, binding_id, key = (str(UUID(int=n)) for n in (1, 2, 3))
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"result": {"mode": "reconcile_only"}})

    with (
        httpx.Client(transport=httpx.MockTransport(handle)) as http,
        Client(
            api_key="synthetic",
            secret_key="synthetic",
            base_url="https://registry.example.invalid",
            http_client=http,
        ) as platform,
    ):
        client = CampaignClient(platform)
        result = client.claim(
            campaign_id,
            binding_id,
            plan_digest="sha256:" + "a" * 64,
            idempotency_key=key,
        )
        assert result["mode"] == "reconcile_only"
        assert len(seen) == 1
        assert (
            seen[0].url.path
            == f"/model-hub/skills/contexts/campaigns/{campaign_id}/targets/{binding_id}/claim/"
        )
        assert seen[0].headers["Idempotency-Key"] == key
        with pytest.raises(ValueError):
            client.change_status(
                campaign_id, action="../../enable", revision=1, reason="No"
            )
        with pytest.raises(ValueError):
            client.get("../other-scope")
        assert len(seen) == 1
