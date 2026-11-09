"""Final F12 wire conformance at the real shared HTTP transport boundary."""

import json
from datetime import datetime, timezone

import httpx
import pytest
from fi.context import AsyncContextClient, ContextClient, SnapshotIntegrityError
from fi.context.__main__ import main as context_main
from fi.platform import AsyncClient, Client, ContextAuth, RequestOptions
from fi.skills import AsyncSkillsClient, SkillsClient
from fi.skills.__main__ import main as skills_main
from test_snapshots import LEASE, RESOURCE, VERSION, Fixture


class WireFixture(Fixture):
    def __init__(self, kind):
        super().__init__(kind=kind)
        self.prefix = "/model-hub/skills/" + (
            "contexts/" if kind == "agent_context" else "consumption/"
        )
        self.resource_id = RESOURCE
        self.version = 7
        self.version_id = VERSION
        self.requested = {"label": "production"}
        self.access_override = None
        self.chunk_limit = 6000  # escaped JSON can require chunks below max_bytes
        self.files["references/escaped.md"] = '\t"\\雪😀\n' * 14000
        if kind == "skill":
            self.files["SKILL.md"] = (
                "---\nname: fixture\ndescription: Use when checking synthetic policy.\n---\n"
                + "Policy.\n" * 20000
            )
        else:
            descriptor = json.loads(self.files[".futureagi/context.json"])
            descriptor["owned_paths"] = sorted(
                [*descriptor["owned_paths"], "references/escaped.md"]
            )
            self.files[".futureagi/context.json"] = json.dumps(
                descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        self.rehash()

    def page(self, offset=0):
        value = super().page(offset)
        value.update(
            resource_id=self.resource_id,
            version=self.version,
            version_id=self.version_id,
            requested=self.requested,
            description="Synthetic policy",
            created_at="2026-11-01T00:00:00Z",
        )
        for item in value["files"]:
            item["origin"] = {
                "kind": "owned",
                "skill_id": None,
                "version_id": None,
                "source_path": None,
            }
        return value

    def handle(self, request):
        self.requests.append(request)
        assert request.headers["authorization"] == "Context synthetic-credential"
        assert (
            "x-api-key" not in request.headers and "x-secret-key" not in request.headers
        )
        if self.denied:
            return httpx.Response(
                403, json={"status": False, "code": "context_credential_revoked"}
            )
        if request.url.path == self.prefix + "resolve/":
            self.resolve_count += 1
            self.requested = (
                {"version": int(request.url.params["version"])}
                if "version" in request.url.params
                else {"label": request.url.params.get("label", "production")}
            )
            result = self.page()
        else:
            assert request.headers["x-context-resolution"] == LEASE
            immutable = f"{self.prefix}{self.resource_id}/versions/{self.version}/"
            assert request.url.path.startswith(immutable)
            if request.url.path.endswith("manifest/"):
                result = self.page(int(request.url.params["file_offset"]))
            elif request.url.path.endswith("access-check/"):
                assert request.method == "POST" and json.loads(request.content) == {}
                result = self.access_override or {
                    "allowed": True,
                    "version_id": self.version_id,
                    "digest": self.digest,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }
            else:
                assert request.url.path.endswith("files/")
                path = request.url.params["path"]
                offset = int(request.url.params["offset"])
                result = self.chunk(path, offset)
                text = (
                    result["text"]
                    .encode()[: self.chunk_limit]
                    .decode("utf-8", errors="ignore")
                )
                end = offset + len(text)
                eof = end == result["total_chars"]
                result.update(
                    text=text,
                    eof=eof,
                    next_offset=None if eof else end,
                    resource_id=self.resource_id,
                    version_id=self.version_id,
                )
        return httpx.Response(200, json={"status": True, "result": result})


def platform(fixture, asynchronous=False, **kwargs):
    cls = AsyncClient if asynchronous else Client
    http = httpx.AsyncClient if asynchronous else httpx.Client
    return cls(
        auth=ContextAuth("synthetic-credential"),
        base_url="https://fixture.invalid",
        http_client=http(transport=httpx.MockTransport(fixture.handle)),
        max_retries=0,
        **kwargs,
    )


@pytest.mark.parametrize("kind", ["skill", "agent_context"])
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.asyncio
async def test_generated_consumption_complete_bytes_and_access(
    kind, asynchronous, monkeypatch
):
    monkeypatch.setenv("FI_API_KEY", "stale-broad")
    monkeypatch.setenv("FI_SECRET_KEY", "stale-broad")
    fixture = WireFixture(kind)
    client = platform(fixture, asynchronous)
    if asynchronous:
        async with client:
            wrapper = (AsyncSkillsClient if kind == "skill" else AsyncContextClient)(
                client
            )
            snapshot = await wrapper.resolve("fixture")
            verified = await snapshot.read_all()
            await wrapper.check_access(snapshot.identity, snapshot.manifest.lease)
    else:
        with client:
            wrapper = (SkillsClient if kind == "skill" else ContextClient)(client)
            snapshot = wrapper.resolve("fixture")
            verified = snapshot.read_all()
            wrapper.check_access(snapshot.identity, snapshot.manifest.lease)
    assert dict(verified.files) == fixture.files
    assert fixture.resolve_count == 1
    assert len(snapshot.manifest.files) > 25
    assert len(fixture.files["references/escaped.md"].encode()) > 100 * 1024
    assert all(
        request.url.path.startswith(fixture.prefix) for request in fixture.requests
    )


@pytest.mark.parametrize("kind", ["skill", "agent_context"])
@pytest.mark.parametrize("field", ["resource_id", "version_id", "digest"])
def test_chunk_requires_all_f12_identity_fields(kind, field):
    from fi.context.snapshot import ChunkCollector, ManifestCollector

    fixture = WireFixture(kind)
    collector = ManifestCollector(fixture.page(), kind=kind)
    collector.add(fixture.page(25))
    manifest = collector.finish()
    value = fixture.chunk("empty.txt", 0)
    value.pop(field)
    with pytest.raises(SnapshotIntegrityError):
        ChunkCollector(manifest, "empty.txt").add(value)


@pytest.mark.parametrize("kind", ["skill", "agent_context"])
def test_no_old_identity_alias_or_wrong_kind(kind):
    from fi.context.snapshot import ManifestCollector

    fixture = WireFixture(kind)
    for mutate in (
        lambda value: value.update(
            kind="skill" if kind == "agent_context" else "agent_context"
        ),
        lambda value: value.update(context_id=value.pop("resource_id")),
        lambda value: value.update(skill_id=value.pop("resource_id")),
    ):
        value = fixture.page()
        mutate(value)
        with pytest.raises(SnapshotIntegrityError):
            ManifestCollector(value, kind=kind)


@pytest.mark.parametrize("kind", ["skill", "agent_context"])
def test_public_generated_methods_encode_path_query_and_lease(kind):
    fixture = WireFixture(kind)
    with platform(fixture, strict_responses=True) as client:
        resource = (
            client.contexts if kind == "agent_context" else client.skill_consumption
        )
        resolved = resource.resolve(name="fixture", version=7)
        assert resolved.resource_id == RESOURCE and resolved.kind == kind
        page = resource.manifest(RESOURCE, 7, resolution_id=LEASE, file_offset=25)
        assert page.file_offset == 25
        chunk = resource.read_file(
            RESOURCE, 7, path="empty.txt", offset=0, resolution_id=LEASE
        )
        assert chunk.text == "" and chunk.resource_id == RESOURCE
        assert resource.check_access(RESOURCE, 7, resolution_id=LEASE).allowed is True
        before = len(fixture.requests)
        with pytest.raises(ValueError):
            resource.manifest(
                RESOURCE,
                7,
                resolution_id=LEASE,
                options=RequestOptions(resolution_id="other"),
            )
        assert len(fixture.requests) == before


def test_leaf_cli_complete_online_loop_and_revoked_apply(tmp_path, monkeypatch, capsys):
    fixture = WireFixture("skill")
    project = tmp_path / "project"
    project.mkdir()
    for key, value in {
        "FI_CONTEXT_ORIGIN": "https://fixture.invalid",
        "FI_CONTEXT_CREDENTIAL": "synthetic-credential",
        "FI_CONTEXT_ORGANIZATION_ID": RESOURCE,
        "FI_CONTEXT_WORKSPACE_ID": RESOURCE,
        "FI_API_KEY": "stale",
        "FI_SECRET_KEY": "stale",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(
        "fi.context.__main__.Client",
        lambda **kwargs: Client(
            **kwargs,
            max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(fixture.handle)),
        ),
    )
    plan = tmp_path / "plan.json"
    assert (
        skills_main(
            [
                "plan",
                "--name",
                "fixture",
                "--client",
                "codex",
                "--project",
                str(project),
                "--plan",
                str(plan),
                "--allow-preview",
            ]
        )
        == 0
    )
    assert "synthetic-credential" not in plan.read_text()
    fixture.denied = True
    assert skills_main(["apply", "--plan", str(plan), "--quiescent"]) == 3
    assert list(project.iterdir()) == []
    fixture.denied = False
    assert skills_main(["apply", "--plan", str(plan), "--quiescent"]) == 0
    assert skills_main(["verify", "--project", str(project)]) == 0
    lock = tmp_path / "retained.json"
    lock.write_bytes((project / ".futureagi-skills.lock.json").read_bytes())
    assert (
        skills_main(
            ["update", "--project", str(project), "--name", "fixture", "--check"]
        )
        == 0
    )
    assert (
        skills_main(
            [
                "update",
                "--project",
                str(project),
                "--name",
                "fixture",
                "--plan",
                str(tmp_path / "update.json"),
                "--allow-preview",
            ]
        )
        == 0
    )
    assert (
        skills_main(
            [
                "restore",
                "--project",
                str(project),
                "--name",
                "fixture",
                "--lock",
                str(lock),
                "--plan",
                str(tmp_path / "restore.json"),
                "--allow-preview",
            ]
        )
        == 0
    )
    assert (
        skills_main(["apply", "--plan", str(tmp_path / "restore.json"), "--quiescent"])
        == 0
    )
    installed = project / ".agents/skills/fixture/SKILL.md"
    installed.write_text("Local retained edits")
    remove = tmp_path / "remove.json"
    assert (
        skills_main(
            [
                "remove",
                "--project",
                str(project),
                "--name",
                "fixture",
                "--plan",
                str(remove),
            ]
        )
        == 0
    )
    assert skills_main(["apply", "--plan", str(remove), "--quiescent"]) == 0
    assert installed.read_text() == "Local retained edits"
    assert "synthetic-credential" not in capsys.readouterr().out


@pytest.mark.parametrize("kind", ["skill", "agent_context"])
@pytest.mark.parametrize("lease_change, expected", [("expiry", 6), ("expired", 3)])
def test_cli_apply_refuses_substituted_or_expired_leases(
    kind, lease_change, expected, tmp_path, monkeypatch, capsys
):
    from datetime import timedelta

    fixture = WireFixture(kind)
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    for name, value in {
        "FI_CONTEXT_ORIGIN": "https://fixture.invalid",
        "FI_CONTEXT_CREDENTIAL": "synthetic-credential",
        "FI_CONTEXT_ORGANIZATION_ID": RESOURCE,
        "FI_CONTEXT_WORKSPACE_ID": RESOURCE,
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        "fi.context.__main__.Client",
        lambda **kwargs: Client(
            **kwargs,
            max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(fixture.handle)),
        ),
    )
    main = skills_main if kind == "skill" else context_main
    plan = tmp_path / "plan.json"
    assert (
        main(
            [
                "plan",
                "--name",
                "fixture",
                "--client",
                "codex",
                "--project",
                str(project),
                "--plan",
                str(plan),
                "--allow-preview",
            ]
        )
        == 0
    )
    if lease_change == "expiry":
        fixture.expiry = (
            datetime.now(timezone.utc) + timedelta(minutes=12)
        ).isoformat()
    else:

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.now(tz) + timedelta(minutes=20)

        monkeypatch.setattr("fi.context.snapshot.datetime", Clock)
    assert main(["apply", "--plan", str(plan), "--quiescent"]) == expected
    assert list(project.iterdir()) == []
    assert fixture.resolve_count == 1
    assert "synthetic-credential" not in capsys.readouterr().out


def test_context_cli_uses_complete_generated_manifest_for_apply_and_update(
    tmp_path, monkeypatch, capsys
):
    fixture = WireFixture("agent_context")
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    for name, value in {
        "FI_CONTEXT_ORIGIN": "https://fixture.invalid",
        "FI_CONTEXT_CREDENTIAL": "synthetic-credential",
        "FI_CONTEXT_ORGANIZATION_ID": RESOURCE,
        "FI_CONTEXT_WORKSPACE_ID": RESOURCE,
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        "fi.context.__main__.Client",
        lambda **kwargs: Client(
            **kwargs,
            max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(fixture.handle)),
        ),
    )
    plan = tmp_path / "plan.json"
    assert (
        context_main(
            [
                "plan",
                "--name",
                "fixture",
                "--version",
                "7",
                "--client",
                "codex",
                "--project",
                str(project),
                "--out",
                str(plan),
                "--allow-preview",
            ]
        )
        == 0
    )
    assert context_main(["apply", "--plan", str(plan), "--quiescent"]) == 0
    lock = project / ".futureagi-context.lock.json"
    assert context_main(["verify", "--lock", str(lock)]) == 0
    assert context_main(["update", "--lock", str(lock), "--check"]) == 0
    fixture.resource_id = "55555555-5555-4555-8555-555555555555"
    # Resolve refuses the identity before any candidate replaces the checked-in lock.
    before = lock.read_bytes()
    assert context_main(["update", "--lock", str(lock), "--check"]) == 6
    assert lock.read_bytes() == before
    assert "synthetic-credential" not in capsys.readouterr().out


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.asyncio
async def test_generated_credential_issuance_replay_preserves_one_time_secret_and_operation(
    asynchronous,
):
    from fi.platform import ApiKeyAuth

    seen = []
    metadata = {
        "id": RESOURCE,
        "purpose": "consume",
        "grants": [
            {
                "kind": "skill",
                "resource_id": RESOURCE,
                "labels": ["production"],
                "version_ids": [],
            }
        ],
        "binding_ids": [],
        "expires_at": "2026-12-01T00:00:00Z",
        "revoked_at": None,
        "created_at": "2026-11-01T00:00:00Z",
        "last_used_at": None,
    }

    def handle(request):
        seen.append(request)
        assert request.url.path == "/model-hub/skills/contexts/credentials/"
        assert request.headers["idempotency-key"] == RESOURCE
        assert request.headers["x-api-key"] == "synthetic-user-key"
        assert "authorization" not in request.headers
        assert json.loads(request.content) == {
            key: metadata[key]
            for key in ("purpose", "grants", "binding_ids", "expires_at")
        }
        return httpx.Response(
            201 if len(seen) == 1 else 200,
            json={
                "status": True,
                "result": {
                    "id": RESOURCE,
                    "secret": "synthetic-once" if len(seen) == 1 else None,
                    "secret_available": len(seen) == 1,
                    "metadata": metadata,
                },
            },
        )

    cls, http_cls = (
        (AsyncClient, httpx.AsyncClient) if asynchronous else (Client, httpx.Client)
    )
    client = cls(
        auth=ApiKeyAuth("synthetic-user-key", "synthetic-user-secret"),
        base_url="https://fixture.invalid",
        strict_responses=True,
        http_client=http_cls(transport=httpx.MockTransport(handle)),
    )
    results = []
    for _ in range(2):
        call = client.context_credentials.issue(
            **{
                key: metadata[key]
                for key in ("purpose", "grants", "binding_ids", "expires_at")
            },
            idempotency_key=RESOURCE,
        )
        results.append(await call if asynchronous else call)
    assert results[0].secret == "synthetic-once" and results[0].secret_available is True
    assert results[1].secret is None and results[1].secret_available is False
    assert results[0].id == results[1].id == RESOURCE
    assert results[1].metadata.last_used_at is None
    if asynchronous:
        await client.aclose()
    else:
        client.close()
