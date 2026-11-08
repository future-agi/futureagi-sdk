"""Synthetic transport-boundary conformance; no backend/provider credentials."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fi.context import (
    AsyncContextClient,
    ContextClient,
    ResolutionExpiredError,
    SnapshotIntegrityError,
)
from fi.context.snapshot import (
    ChunkCollector,
    ManifestCollector,
    VerifiedSnapshot,
    manifest_digest,
)
from fi.platform import AsyncClient, Client, ContextAuth
from fi.skills import AsyncSkillsClient, SkillsClient

RESOURCE = "11111111-1111-4111-8111-111111111111"
VERSION = "22222222-2222-4222-8222-222222222222"
PREFIX = "/model-hub/skills/contexts/"
LEASE = "synthetic-resolution-lease"


def digest(files):
    pairs = sorted(
        [path, hashlib.sha256(text.encode()).hexdigest()]
        for path, text in files.items()
    )
    return (
        "sha256:"
        + hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest()
    )


class Fixture:
    def __init__(self, *, kind="agent_context"):
        self.kind = kind
        self.files = {
            f"references/file-{i:02}.md": f"Reference {i}\n" for i in range(27)
        }
        self.files.update(
            {
                "references/😀é.txt": "unicode path\n",
                "references/\ue000.txt": "private use path\n",
                "empty.txt": "",
            }
        )
        root = "AGENTS.md" if kind == "agent_context" else "SKILL.md"
        self.files[root] = "Boundary é😀\n" * 11000
        if kind == "agent_context":
            child = {
                "SKILL.md": "---\nname: refund\ndescription: Use for refund requests.\n---\nRefund rules.\n",
                "references/policy.md": "Retain local rules.\n",
            }
            descriptor = {
                "schema": 1,
                "kind": kind,
                "name": "fixture",
                "description": "Synthetic fixture",
                "entrypoint": "AGENTS.md",
                "owned_paths": sorted(self.files),
                "links": [
                    {
                        "mount": "skills/refund/",
                        "skill_id": "33333333-3333-4333-8333-333333333333",
                        "version": 4,
                        "version_id": "44444444-4444-4444-8444-444444444444",
                        "digest": digest(child),
                        "requested": {"version": 4},
                    }
                ],
            }
            self.files.update(
                {"skills/refund/" + path: text for path, text in child.items()}
            )
            self.files[".futureagi/context.json"] = json.dumps(
                descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        self.rehash()
        self.requests = []
        self.resolve_count = 0
        self.denied = False
        self.mutate_page = None
        self.mutate_chunk = None
        self.expiry = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()

    def rehash(self):
        self.metadata = [
            {
                "path": path,
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "size_bytes": len(text.encode()),
            }
            for path, text in sorted(self.files.items())
        ]
        self.digest = digest(self.files)

    def page(self, offset=0):
        return {
            "context_id" if self.kind == "agent_context" else "skill_id": RESOURCE,
            "name": "fixture",
            "version": 7,
            "version_id": VERSION,
            "digest": self.digest,
            "requested": {"label": "production"},
            "entrypoint": "AGENTS.md",
            "descriptor_path": ".futureagi/context.json",
            "resolution_id": LEASE,
            "resolution_expires_at": self.expiry,
            "files": copy.deepcopy(self.metadata[offset : offset + 25]),
            "file_count": len(self.files),
            "file_offset": offset,
            "next_file_offset": offset + 25 if offset + 25 < len(self.files) else None,
        }

    def chunk(self, path, offset):
        content = self.files[path]
        end = offset
        size = 0
        while end < len(content) and size + len(content[end].encode()) <= 32768:
            size += len(content[end].encode())
            end += 1
        return {
            "path": path,
            "sha256": hashlib.sha256(content.encode()).hexdigest(),
            "size_bytes": len(content.encode()),
            "total_chars": len(content),
            "offset": offset,
            "next_offset": end if end < len(content) else None,
            "eof": end == len(content),
            "text": content[offset:end],
            "context_id": RESOURCE,
            "version_id": VERSION,
            "digest": self.digest,
        }

    def handle(self, request):
        self.requests.append(request)
        assert request.headers["authorization"] == "Context synthetic-credential"
        assert (
            "x-api-key" not in request.headers and "x-secret-key" not in request.headers
        )
        assert "x-workspace-id" not in request.headers
        assert request.url.host == "fixture.invalid"
        if self.denied:
            return httpx.Response(
                403,
                json={
                    "status": False,
                    "code": "context_credential_revoked",
                    "message": "Revoked",
                },
            )
        if request.url.path == PREFIX + "resolve/":
            self.resolve_count += 1
            assert self.resolve_count == 1, "A moving label must never be re-resolved"
            result = self.page()
            if self.mutate_page:
                self.mutate_page(result, 0)
        else:
            assert request.headers["x-context-resolution"] == LEASE
            immutable = f"{PREFIX}{RESOURCE}/versions/7/"
            assert request.url.path.startswith(immutable)
            assert "label" not in request.url.params
            if request.url.path == immutable + "manifest/":
                offset = int(request.url.params["file_offset"])
                result = self.page(offset)
                if self.mutate_page:
                    self.mutate_page(result, offset)
            else:
                assert request.url.path == immutable + "files/"
                result = self.chunk(
                    request.url.params["path"], int(request.url.params["offset"])
                )
                if self.mutate_chunk:
                    self.mutate_chunk(result)
        return httpx.Response(
            200,
            content=json.dumps({"status": True, "result": result}).encode(),
            headers={"Content-Type": "application/json"},
        )


def client(fixture):
    return Client(
        auth=ContextAuth("synthetic-credential"),
        base_url="https://fixture.invalid",
        http_client=httpx.Client(transport=httpx.MockTransport(fixture.handle)),
        max_retries=0,
    )


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.asyncio
async def test_complete_inventory_utf8_and_moved_label(monkeypatch, asynchronous):
    for key in ("FI_API_KEY", "FI_SECRET_KEY", "FI_WORKSPACE_ID"):
        monkeypatch.setenv(key, "stale-broad-value")
    fixture = Fixture()
    if asynchronous:
        async with AsyncClient(
            auth=ContextAuth("synthetic-credential"),
            base_url="https://fixture.invalid",
            http_client=httpx.AsyncClient(
                transport=httpx.MockTransport(fixture.handle)
            ),
        ) as platform:
            snapshot = await AsyncContextClient(platform).resolve("fixture")
            verified = await snapshot.read_all()
            assert await snapshot.read_file("empty.txt") == ""
    else:
        with client(fixture) as platform:
            snapshot = ContextClient(platform).resolve("fixture")
            verified = snapshot.read_all()
            assert snapshot.read_file("empty.txt") == ""
    assert dict(verified.files) == fixture.files
    assert snapshot.identity.version == 7
    assert snapshot.manifest.requested == {"label": "production"}
    assert len(snapshot.manifest.files) == 34
    assert manifest_digest(snapshot.manifest.files) == fixture.digest
    assert (
        fixture.digest
        == "sha256:567bb27c361daf3faf3368cc1afc6d83b7187eef6f6226fba318579efcad3bc4"
    )
    assert (
        len([r for r in fixture.requests if r.url.params.get("path") == "AGENTS.md"])
        > 4
    )
    assert fixture.resolve_count == 1
    with pytest.raises(TypeError):
        verified.files["AGENTS.md"] = "changed"
    with pytest.raises(FrozenInstanceError):
        snapshot.identity.version = 8
    with pytest.raises(TypeError):
        snapshot.manifest.requested["label"] = "latest"


@pytest.mark.parametrize(
    "key,value",
    [
        ("next_file_offset", None),
        ("next_file_offset", 0),
        ("file_count", 201),
        ("file_offset", 1),
        ("files", []),
        ("file_count", True),
        ("version", True),
        ("context_id", "../../escape"),
        ("resolution_id", "bad\nheader"),
        ("resolution_expires_at", "2026-01-01T00:00:00"),
        ("entrypoint", "SKILL.md"),
    ],
)
def test_bad_initial_manifest(key, value):
    fixture = Fixture()
    page = fixture.page()
    page[key] = value
    with pytest.raises(SnapshotIntegrityError):
        ManifestCollector(page, kind="agent_context").finish()


@pytest.mark.parametrize(
    "key,value",
    [
        ("version", 8),
        ("version_id", "55555555-5555-4555-8555-555555555555"),
        ("digest", "sha256:" + "0" * 64),
        ("resolution_id", "new-lease"),
        ("file_count", 35),
        ("file_offset", 0),
        ("next_file_offset", 25),
    ],
)
def test_mixed_continuations_fail(key, value):
    fixture = Fixture()
    fixture.mutate_page = lambda page, offset: (
        page.update({key: value}) if offset else None
    )
    with client(fixture) as platform, pytest.raises(SnapshotIntegrityError):
        ContextClient(platform).resolve("fixture")
    assert fixture.resolve_count == 1


@pytest.mark.parametrize(
    "path",
    [
        "../evil",
        "/absolute",
        "a\\b",
        "x/./y",
        "a//b",
        "a./b",
        "x\x00y",
        "C:/drive",
        "a/" * 8 + "b",
    ],
)
def test_unsafe_manifest_paths(path):
    fixture = Fixture()
    fixture.metadata[0]["path"] = path
    with pytest.raises(SnapshotIntegrityError):
        ManifestCollector(fixture.page(), kind="agent_context")


@pytest.mark.parametrize("path", ["agents.md", "references", "references/FILE-00.md"])
def test_case_and_prefix_collisions(path):
    fixture = Fixture()
    fixture.files[path] = "collision"
    fixture.rehash()
    with client(fixture) as platform, pytest.raises(SnapshotIntegrityError):
        ContextClient(platform).resolve("fixture")


@pytest.mark.parametrize(
    "key,value",
    [
        ("sha256", "0" * 64),
        ("path", "other.md"),
        ("offset", 1),
        ("version_id", "55555555-5555-4555-8555-555555555555"),
        ("total_chars", 0),
        ("eof", True),
        ("next_offset", 1),
        ("size_bytes", 2**30),
        ("text", "\ud800"),
        ("text", "\x00"),
    ],
)
def test_invalid_chunks_fail_without_reresolving(key, value):
    fixture = Fixture()
    fixture.mutate_chunk = lambda chunk: chunk.update({key: value})
    with client(fixture) as platform:
        snapshot = ContextClient(platform).resolve("fixture")
        with pytest.raises(SnapshotIntegrityError):
            snapshot.read_file("AGENTS.md")
    assert fixture.resolve_count == 1


def test_same_size_corruption_fails_hash():
    fixture = Fixture()
    fixture.mutate_chunk = lambda chunk: chunk.update(
        text=chunk["text"].replace("Boundary", "Changed!")
    )
    with client(fixture) as platform:
        snapshot = ContextClient(platform).resolve("fixture")
        with pytest.raises(SnapshotIntegrityError, match="checksum"):
            snapshot.read_file("AGENTS.md")


def test_missing_chunk_fields_and_zero_progress():
    fixture = Fixture()
    collector = ManifestCollector(fixture.page(), kind="agent_context")
    collector.add(fixture.page(25))
    manifest = collector.finish()
    for mutate in (
        lambda c: c.pop("next_offset"),
        lambda c: c.update(text="", next_offset=0, eof=False),
    ):
        chunk = fixture.chunk("AGENTS.md", 0)
        mutate(chunk)
        with pytest.raises(SnapshotIntegrityError):
            ChunkCollector(manifest, "AGENTS.md").add(chunk)


def test_reads_are_not_cache_authorization():
    fixture = Fixture()
    with client(fixture) as platform:
        snapshot = ContextClient(platform).resolve("fixture")
        assert snapshot.read_file("empty.txt") == ""
        fixture.denied = True
        from fi.platform import APIError

        with pytest.raises(APIError) as error:
            snapshot.read_file("empty.txt")
        assert error.value.status_code == 403
        assert (
            len(
                [r for r in fixture.requests if r.url.params.get("path") == "empty.txt"]
            )
            == 2
        )


@pytest.mark.parametrize("status", [304, 302, 403, 410])
def test_denials_and_redirects_never_become_content(status):
    fixture = Fixture()
    original = fixture.handle

    def handler(request):
        if request.url.path.endswith("files/"):
            return httpx.Response(
                status,
                headers={"Location": "https://other.invalid/leak"},
                json={"status": False, "message": "denied"},
            )
        return original(request)

    fixture.handle = handler
    with client(fixture) as platform:
        snapshot = ContextClient(platform).resolve("fixture")
        with pytest.raises(Exception):
            snapshot.read_file("AGENTS.md")
        assert fixture.resolve_count == 1


def test_expired_resolution_and_expiry_midread_fail_closed():
    fixture = Fixture()
    fixture.expiry = "2000-01-01T00:00:00+00:00"
    with client(fixture) as platform, pytest.raises(ResolutionExpiredError):
        ContextClient(platform).resolve("fixture")
    assert len(fixture.requests) == 1


def test_no_missing_path_request_or_selector_fallback():
    fixture = Fixture()
    with client(fixture) as platform:
        with pytest.raises(ValueError):
            ContextClient(platform).resolve("fixture", label="production", version=7)
        assert not fixture.requests
        snapshot = ContextClient(platform).resolve("fixture")
        count = len(fixture.requests)
        with pytest.raises(KeyError):
            snapshot.read_file("not-there")
        assert len(fixture.requests) == count


@pytest.mark.parametrize("mutation", ["root", "name", "canonical", "child", "coverage"])
def test_descriptor_integrity(mutation):
    fixture = Fixture()
    descriptor = json.loads(fixture.files[".futureagi/context.json"])
    if mutation == "root":
        fixture.files["AGENTS.md"] = " "
    elif mutation == "name":
        descriptor["name"] = "another"
    elif mutation == "child":
        descriptor["links"][0]["digest"] = "sha256:" + "0" * 64
    elif mutation == "coverage":
        descriptor["owned_paths"].remove("empty.txt")
    fixture.files[".futureagi/context.json"] = json.dumps(
        descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ) + ("\n" if mutation == "canonical" else "")
    fixture.rehash()
    with client(fixture) as platform:
        snapshot = ContextClient(platform).resolve("fixture")
        with pytest.raises(SnapshotIntegrityError):
            snapshot.read_all()


def test_verified_snapshot_defensively_copies_and_checks():
    fixture = Fixture()
    collector = ManifestCollector(fixture.page(), kind="agent_context")
    collector.add(fixture.page(25))
    manifest = collector.finish()
    verified = VerifiedSnapshot(manifest, fixture.files)
    fixture.files["AGENTS.md"] = "bad"
    assert verified.files["AGENTS.md"] != "bad"
    with pytest.raises(SnapshotIntegrityError):
        VerifiedSnapshot(manifest, fixture.files)


@pytest.mark.asyncio
async def test_leaf_sources_share_exact_verification_and_lease():
    fixture = Fixture(kind="skill")

    class Source:
        def resolve(self, *, name, selector):
            assert name == "fixture" and selector == {"label": "production"}
            return fixture.page()

        def manifest(self, identity, *, offset, options):
            assert identity.kind == "skill" and options.resolution_id == LEASE
            return fixture.page(offset)

        def chunk(self, identity, *, path, offset, options):
            assert identity.version_id == VERSION and options.resolution_id == LEASE
            return fixture.chunk(path, offset)

    source = Source()
    sync = SkillsClient(source).resolve("fixture").read_all()

    class AsyncSource:
        async def resolve(self, **kwargs):
            return source.resolve(**kwargs)

        async def manifest(self, identity, **kwargs):
            return source.manifest(identity, **kwargs)

        async def chunk(self, identity, **kwargs):
            return source.chunk(identity, **kwargs)

    snapshot = await AsyncSkillsClient(AsyncSource()).resolve("fixture")
    asynchronous = await snapshot.read_all()
    assert dict(sync.files) == dict(asynchronous.files) == fixture.files
    assert sync.identity.kind == "skill"


@pytest.mark.asyncio
async def test_async_expiry_midchunk_discards_staged_bytes(monkeypatch):
    import fi.context.snapshot as module

    fixture = Fixture()
    instant = datetime.now(timezone.utc)

    class Clock:
        @staticmethod
        def now(tz):
            return instant

        fromisoformat = datetime.fromisoformat

    monkeypatch.setattr(module, "datetime", Clock)

    def expire(chunk):
        nonlocal instant
        instant += timedelta(minutes=20)

    fixture.mutate_chunk = expire
    async with AsyncClient(
        auth=ContextAuth("synthetic-credential"),
        base_url="https://fixture.invalid",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(fixture.handle)),
    ) as platform:
        snapshot = await AsyncContextClient(platform).resolve("fixture")
        with pytest.raises(ResolutionExpiredError):
            await snapshot.read_file("AGENTS.md")
    assert len([r for r in fixture.requests if r.url.path.endswith("files/")]) == 1
    assert fixture.resolve_count == 1


@pytest.mark.asyncio
async def test_async_corruption_does_not_return_partial_bytes():
    fixture = Fixture()
    fixture.mutate_chunk = lambda chunk: chunk.update(
        text=chunk["text"].replace("Boundary", "Changed!")
    )
    async with AsyncClient(
        auth=ContextAuth("synthetic-credential"),
        base_url="https://fixture.invalid",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(fixture.handle)),
    ) as platform:
        snapshot = await AsyncContextClient(platform).resolve("fixture")
        with pytest.raises(SnapshotIntegrityError, match="checksum"):
            await snapshot.read_file("AGENTS.md")


@pytest.mark.parametrize(
    "case",
    [
        "over_file",
        "over_bundle",
        "missing_root",
        "missing_descriptor",
        "hash",
        "duplicate",
        "missing_offset",
    ],
)
def test_manifest_inventory_boundaries(case):
    fixture = Fixture()
    if case == "over_file":
        fixture.metadata[0]["size_bytes"] = 524289
    elif case == "over_bundle":
        for item in fixture.metadata:
            item["size_bytes"] = 524288
    elif case == "missing_root":
        fixture.files.pop("AGENTS.md")
        fixture.rehash()
    elif case == "missing_descriptor":
        fixture.files.pop(".futureagi/context.json")
        fixture.rehash()
    elif case == "hash":
        fixture.digest = "sha256:" + "0" * 64
    elif case == "duplicate":
        fixture.metadata[-1] = fixture.metadata[0]
    else:
        fixture.mutate_page = lambda page, offset: page.pop("next_file_offset")
    with client(fixture) as platform, pytest.raises(SnapshotIntegrityError):
        ContextClient(platform).resolve("fixture")


def test_exact_maximum_file_inventory_is_not_truncated():
    fixture = Fixture(kind="skill")
    fixture.files = {
        "SKILL.md": "root",
        **{f"references/{i}.txt": "" for i in range(199)},
    }
    fixture.rehash()
    collector = ManifestCollector(fixture.page(), kind="skill")
    while collector.next_offset is not None:
        collector.add(fixture.page(collector.next_offset))
    assert len(collector.finish().files) == 200


def test_surrogate_paths_and_forged_verified_manifest_fail():
    from dataclasses import replace

    from fi.context.snapshot import validate_path

    with pytest.raises(SnapshotIntegrityError):
        validate_path("invalid\ud800.txt")
    fixture = Fixture()
    collector = ManifestCollector(fixture.page(), kind="agent_context")
    collector.add(fixture.page(25))
    manifest = collector.finish()
    forged = replace(
        manifest, identity=replace(manifest.identity, digest="sha256:" + "0" * 64)
    )
    with pytest.raises(SnapshotIntegrityError, match="manifest digest"):
        VerifiedSnapshot(forged, fixture.files)


def test_leaf_chunks_reject_contradictory_identity():
    fixture = Fixture(kind="skill")
    collector = ManifestCollector(fixture.page(), kind="skill")
    collector.add(fixture.page(25))
    chunk = fixture.chunk("SKILL.md", 0)
    chunk["version_id"] = "55555555-5555-4555-8555-555555555555"
    with pytest.raises(SnapshotIntegrityError):
        ChunkCollector(collector.finish(), "SKILL.md").add(chunk)
