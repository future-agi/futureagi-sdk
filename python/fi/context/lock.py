"""Canonical context locks and bounded, untrusted installation inputs.

The lock is a byte-verification receipt, not authorization or runtime evidence.
Resolution credentials/leases belong only to the private installation plan.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from typing import Literal, Mapping
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CONTEXT_LOCK = ".futureagi-context.lock.json"
SKILLS_LOCK = ".futureagi-skills.lock.json"
MAX_FILE_BYTES = 512 * 1024
MAX_BUNDLE_BYTES = 2 * 1024 * 1024
MAX_DOCUMENT_BYTES = 16 * 1024 * 1024
HASH = re.compile(r"[a-f0-9]{64}\Z")
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


class InstallationError(Exception):
    """A safe diagnostic and the stable CLI exit category."""

    def __init__(self, code: str, message: str, exit_code: int = 5):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def manifest_digest(files: Mapping[str, bytes]) -> str:
    # Preserve v1's JSON encoding, including ASCII escaping of non-ASCII paths.
    pairs = [[path, sha256(content)] for path, content in sorted(files.items())]
    return "sha256:" + sha256(
        json.dumps(pairs, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    )


def collision_key(path: str) -> str:
    return unicodedata.normalize("NFC", path).casefold()


def validate_path(path: str, *, source: bool = False) -> str:
    limit, depth = (255, 8) if source else (1024, 16)
    if not isinstance(path, str) or not path or len(path) > limit:
        raise InstallationError(
            "path_invalid", "A path is empty or exceeds the path limit.", 6
        )
    parts = path.split("/")
    if len(parts) > depth or any(
        part in ("", ".", "..")
        or part[-1:] in (" ", ".")
        or any(ord(c) < 32 or ord(c) == 127 or c in "\\:" for c in part)
        for part in parts
    ):
        raise InstallationError(
            "path_invalid", "Paths must be safe relative POSIX paths.", 6
        )
    # Refuse names with platform-dependent filesystem meaning, even on Linux.
    reserved = {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{i}" for i in range(1, 10)),
        *(f"lpt{i}" for i in range(1, 10)),
    }
    if any(part.split(".")[0].casefold() in reserved for part in parts):
        raise InstallationError(
            "path_invalid", "A path uses a reserved device name.", 6
        )
    return path


def validate_paths(paths: list[str], *, source: bool = False) -> None:
    seen: set[str] = set()
    for path in paths:
        key = collision_key(validate_path(path, source=source))
        if key in seen:
            raise InstallationError(
                "path_collision", "Duplicate or case/Unicode-colliding paths.", 6
            )
        seen.add(key)
    for path in seen:
        if any(
            "/".join(path.split("/")[:i]) in seen
            for i in range(1, len(path.split("/")))
        ):
            raise InstallationError(
                "path_collision", "A file is also used as a directory.", 6
            )


def hash_value(value: str) -> str:
    if not HASH.fullmatch(value):
        raise ValueError("Expected a lowercase SHA-256 value")
    return value


def digest_value(value: str) -> str:
    if not value.startswith("sha256:"):
        raise ValueError("Expected a sha256: digest")
    hash_value(value[7:])
    return value


def uuid_value(value: str) -> str:
    if str(UUID(value)) != value:
        raise ValueError("Expected a canonical UUID")
    return value


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Selector(FrozenModel):
    label: str | None = None
    version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def exclusive(self) -> Selector:
        if (self.label is None) == (self.version is None):
            raise ValueError("Supply exactly one label or version")
        if self.label is not None and not re.fullmatch(
            r"[a-z0-9][a-z0-9-]{0,39}", self.label
        ):
            raise ValueError("Invalid label")
        return self

    def wire(self) -> dict[str, str | int]:
        if self.label is not None:
            return {"label": self.label}
        if self.version is None:
            raise ValueError("Selector is missing")
        return {"version": self.version}


class FileMeta(FrozenModel):
    path: str
    sha256: str
    size_bytes: int = Field(ge=0, le=MAX_FILE_BYTES)

    _hash = field_validator("sha256")(hash_value)

    @field_validator("path")
    @classmethod
    def path_valid(cls, value: str) -> str:
        return validate_path(value, source=True)


class ResourceIdentity(FrozenModel):
    origin: str
    organization_id: str
    workspace_id: str
    name: str
    requested: Selector
    version: int = Field(ge=1)
    version_id: str
    digest: str

    _ids = field_validator("organization_id", "workspace_id", "version_id")(uuid_value)
    _digest = field_validator("digest")(digest_value)

    @field_validator("origin")
    @classmethod
    def origin_valid(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in ("https", "http")
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Origin must be an HTTP(S) base URL without credentials/query/fragment"
            )
        if any(ord(c) < 32 for c in value):
            raise ValueError("Invalid origin")
        return value.rstrip("/")

    @field_validator("name")
    @classmethod
    def name_valid(cls, value: str) -> str:
        if len(value) > 64 or not NAME.fullmatch(value):
            raise ValueError("Invalid resource name")
        return value


class Identity(ResourceIdentity):
    context_id: str
    _context = field_validator("context_id")(uuid_value)


class SkillIdentity(ResourceIdentity):
    skill_id: str
    _skill = field_validator("skill_id")(uuid_value)


class MaterializedFile(FrozenModel):
    destination: str
    sha256: str
    source_path: str
    source_sha256: str
    ownership: Literal["managed", "adopted"]
    transformation: Literal["copy", "entrypoint", "import"]

    _hashes = field_validator("sha256", "source_sha256")(hash_value)

    @field_validator("destination")
    @classmethod
    def destination_valid(cls, value: str) -> str:
        return validate_path(value)

    @field_validator("source_path")
    @classmethod
    def source_valid(cls, value: str) -> str:
        return validate_path(value, source=True)


class Materialization(FrozenModel):
    profile: Literal["codex", "claude-code"]
    profile_version: Literal["1"]
    materialization_digest: str
    files: list[MaterializedFile] = Field(max_length=405)
    managed_entrypoint_base_sha256: str
    local_segment_sha256: str

    _digest = field_validator("materialization_digest")(digest_value)
    _hashes = field_validator("managed_entrypoint_base_sha256", "local_segment_sha256")(
        hash_value
    )


class ContextLock(Identity):
    schema_version: Literal[1] = Field(default=1, alias="schema")
    descriptor_sha256: str
    files: list[FileMeta] = Field(min_length=2, max_length=200)
    materialization: Materialization

    _descriptor = field_validator("descriptor_sha256")(hash_value)

    @model_validator(mode="after")
    def complete(self) -> ContextLock:
        validate_paths([f.path for f in self.files], source=True)
        validate_paths([f.destination for f in self.materialization.files])
        inventory = {f.path: f for f in self.files}
        if "AGENTS.md" not in inventory or ".futureagi/context.json" not in inventory:
            raise ValueError("Context entrypoint/descriptor missing")
        if inventory[".futureagi/context.json"].sha256 != self.descriptor_sha256:
            raise ValueError("Descriptor hash mismatch")
        if sum(f.size_bytes for f in self.files) > MAX_BUNDLE_BYTES:
            raise ValueError("Context exceeds the complete-tree limit")
        pairs = [[f.path, f.sha256] for f in sorted(self.files, key=lambda f: f.path)]
        digest = "sha256:" + sha256(json.dumps(pairs, separators=(",", ":")).encode())
        if digest != self.digest:
            raise ValueError("Manifest digest mismatch")
        if (
            materialization_digest(self.digest, self.materialization)
            != self.materialization.materialization_digest
        ):
            raise ValueError("Materialization digest mismatch")
        for output in self.materialization.files:
            if (
                output.source_path not in inventory
                or inventory[output.source_path].sha256 != output.source_sha256
            ):
                raise ValueError("Materialization references a different source")
        return self

    def to_bytes(self) -> bytes:
        value = self.model_dump(by_alias=True)
        value["requested"] = self.requested.wire()
        return canonical_json(value)


def materialization_digest(source_digest: str, materialization: Materialization) -> str:
    return "sha256:" + sha256(
        canonical_json(
            {
                "profile": materialization.profile,
                "profile_version": materialization.profile_version,
                "source_digest": source_digest,
                "files": [
                    f.model_dump()
                    for f in sorted(materialization.files, key=lambda f: f.destination)
                ],
                "managed_entrypoint_base_sha256": materialization.managed_entrypoint_base_sha256,
                "local_segment_sha256": materialization.local_segment_sha256,
            }
        )
    )


class Lease(FrozenModel):
    resolution_id: str = Field(min_length=1, max_length=4096, repr=False)
    resolution_expires_at: str

    def require_live(self) -> None:
        try:
            expiry = datetime.fromisoformat(
                self.resolution_expires_at.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise InstallationError(
                "lease_invalid", "Resolution expiry is invalid.", 6
            ) from exc
        if expiry.tzinfo is None or expiry <= datetime.now(timezone.utc):
            raise InstallationError(
                "resolution_expired",
                "Resolution expired; discard this plan and resolve/replan. No pages will be spliced.",
                3,
            )


class SourceBundle(FrozenModel):
    """L10 bridge: complete verified bytes plus the exact resolve identity and lease.

    This input is reverified here, not treated as trusted merely because it came
    from another SDK layer. No cache or independent HTTP implementation lives here.
    """

    identity: Identity
    lease: Lease
    files: dict[str, bytes]

    @model_validator(mode="after")
    def verified(self) -> SourceBundle:
        validate_paths(list(self.files), source=True)
        if (
            not 2 <= len(self.files) <= 200
            or sum(map(len, self.files.values())) > MAX_BUNDLE_BYTES
        ):
            raise ValueError("Invalid complete context size")
        for content in self.files.values():
            if len(content) > MAX_FILE_BYTES:
                raise ValueError("File exceeds byte limit")
            text = content.decode("utf-8")
            if any(ord(c) < 32 and c not in "\t\n\r" for c in text) or "\x7f" in text:
                raise ValueError("Context files must be UTF-8 text")
        if manifest_digest(self.files) != self.identity.digest:
            raise ValueError("Complete context digest mismatch")
        if (
            not self.files.get("AGENTS.md", b"").strip()
            or ".futureagi/context.json" not in self.files
        ):
            raise ValueError("Context root or descriptor missing")
        return self


def parse_lock(raw: bytes) -> ContextLock:
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise InstallationError("lock_invalid", "Lock exceeds its size limit.", 6)
    try:
        return ContextLock.model_validate(json.loads(raw))
    except (ValueError, TypeError) as exc:
        raise InstallationError(
            "lock_invalid", "Invalid context lock; no files were changed.", 6
        ) from exc
