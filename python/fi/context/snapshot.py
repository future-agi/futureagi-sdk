"""Immutable, bounded snapshots. Validation is independent of HTTP and runtime hosts.

A verified snapshot proves bytes, not current authorization or model delivery. It
contains no cache and never follows a moving selector to repair a failed read.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Mapping, Sequence
from uuid import UUID

MAX_FILES = 200
MAX_FILE_BYTES = 512 * 1024
MAX_BUNDLE_BYTES = 2 * 1024 * 1024
CHUNK_BYTES = 32768
PAGE_SIZE = 25


class SnapshotIntegrityError(ValueError):
    """The response does not describe one complete, valid immutable snapshot."""


class ResolutionExpiredError(RuntimeError):
    """Discard staged reads and explicitly resolve/replan; never splice leases."""


def _object(value: object) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise SnapshotIntegrityError("Expected a JSON object")
    return value


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise SnapshotIntegrityError(f"Invalid {name}")
    return value


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise SnapshotIntegrityError(f"Invalid {name}")
    return value


def _uuid(value: object, name: str) -> str:
    text = _string(value, name)
    try:
        if str(UUID(text)) != text:
            raise ValueError
    except ValueError:
        raise SnapshotIntegrityError(f"Invalid {name}") from None
    return text


def _hash(value: object, *, digest: bool = False) -> str:
    pattern = r"sha256:[0-9a-f]{64}" if digest else r"[0-9a-f]{64}"
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise SnapshotIntegrityError("Invalid SHA-256 identity")
    return value


def validate_path(value: object) -> str:
    path = _string(value, "file path")
    parts = path.split("/")
    if (
        len(path) > 255
        or len(parts) > 8
        or "\\" in path
        or any(
            ord(char) < 32 or ord(char) == 127 or 0xD800 <= ord(char) <= 0xDFFF
            for char in path
        )
        or any(part in ("", ".", "..") or part.endswith((" ", ".")) for part in parts)
        or ":" in path
    ):
        raise SnapshotIntegrityError("Unsafe snapshot path")
    return path


def _utf8(text: str) -> bytes:
    try:
        encoded = text.encode("utf-8")
    except UnicodeError:
        raise SnapshotIntegrityError("Invalid UTF-8 text") from None
    if any(ord(c) < 32 and c not in "\t\r\n" or ord(c) == 127 for c in text):
        raise SnapshotIntegrityError("Non-text snapshot content")
    return encoded


def _selector(value: object) -> Mapping[str, object]:
    result = _object(value)
    if set(result) == {"version"}:
        _integer(result["version"], "selector version", 1, 2**53 - 1)
    elif set(result) == {"label"}:
        if not re.fullmatch(
            r"[a-z0-9][a-z0-9-]{0,39}", _string(result["label"], "label")
        ):
            raise SnapshotIntegrityError("Invalid label")
    else:
        raise SnapshotIntegrityError("Expected exactly one selector")
    return MappingProxyType(dict(result))


@dataclass(frozen=True)
class SnapshotIdentity:
    kind: str
    resource_id: str
    name: str
    version: int
    version_id: str
    digest: str

    @classmethod
    def parse(cls, value: Mapping[str, object], kind: str) -> SnapshotIdentity:
        if kind not in ("agent_context", "skill"):
            raise SnapshotIntegrityError("Unsupported snapshot kind")
        name = _string(value.get("name"), "name")
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
            raise SnapshotIntegrityError("Invalid snapshot name")
        if value.get("kind") != kind:
            raise SnapshotIntegrityError("Manifest resource kind mismatch")
        root = "AGENTS.md" if kind == "agent_context" else "SKILL.md"
        descriptor = ".futureagi/context.json" if kind == "agent_context" else None
        if value.get("entrypoint") != root or value.get("descriptor_path") != descriptor:
            raise SnapshotIntegrityError("Invalid snapshot entrypoint")
        return cls(
            kind=kind,
            resource_id=_uuid(value.get("resource_id"), "resource ID"),
            name=name,
            version=_integer(value.get("version"), "version", 1, 2**53 - 1),
            version_id=_uuid(value.get("version_id"), "version ID"),
            digest=_hash(value.get("digest"), digest=True),
        )


@dataclass(frozen=True)
class ResolutionLease:
    resolution_id: str = field(repr=False)
    resolution_expires_at: datetime

    @classmethod
    def parse(cls, value: Mapping[str, object]) -> ResolutionLease:
        token = _string(value.get("resolution_id"), "resolution ID")
        if len(token) > 4096 or any(ord(c) <= 32 or ord(c) >= 127 for c in token):
            raise SnapshotIntegrityError("Invalid resolution ID")
        expiry = _string(value.get("resolution_expires_at"), "resolution expiry")
        try:
            parsed = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            if parsed.utcoffset() is None:
                raise ValueError
        except ValueError:
            raise SnapshotIntegrityError("Invalid resolution expiry") from None
        return cls(token, parsed)

    def require_live(self) -> None:
        if datetime.now(timezone.utc) >= self.resolution_expires_at:
            raise ResolutionExpiredError(
                "Resolution expired; explicitly resolve and replan"
            )


@dataclass(frozen=True)
class FileMetadata:
    path: str
    sha256: str
    size_bytes: int

    @classmethod
    def parse(cls, value: object) -> FileMetadata:
        item = _object(value)
        return cls(
            validate_path(item.get("path")),
            _hash(item.get("sha256")),
            _integer(item.get("size_bytes"), "file size", 0, MAX_FILE_BYTES),
        )


def manifest_digest(files: Sequence[FileMetadata]) -> str:
    # This is the existing backend algorithm, including JSON's ASCII escaping.
    pairs = sorted((item.path, item.sha256) for item in files)
    raw = json.dumps(pairs, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class SnapshotManifest:
    identity: SnapshotIdentity
    requested: Mapping[str, object]
    lease: ResolutionLease
    files: tuple[FileMetadata, ...]

    def file(self, path: str) -> FileMetadata:
        for item in self.files:
            if item.path == path:
                return item
        raise KeyError("Path is not in this immutable snapshot")


class ManifestCollector:
    """Reject sparse, repeated, mixed-identity and truncated manifest pages."""

    def __init__(self, first: object, *, kind: str) -> None:
        first = _object(first)
        self.identity = SnapshotIdentity.parse(first, kind)
        self.requested = _selector(first.get("requested"))
        self.lease = ResolutionLease.parse(first)
        self.count = _integer(first.get("file_count"), "file count", 1, MAX_FILES)
        self.files: list[FileMetadata] = []
        self.next_offset: int | None = 0
        self.add(first)

    def add(self, raw: object) -> None:
        page = _object(raw)
        if self.next_offset is None:
            raise SnapshotIntegrityError("Unexpected manifest continuation")
        if SnapshotIdentity.parse(page, self.identity.kind) != self.identity:
            raise SnapshotIntegrityError(
                "Manifest identity changed during continuation"
            )
        if _integer(page.get("file_count"), "file count", 1, MAX_FILES) != self.count:
            raise SnapshotIntegrityError("Manifest count changed during continuation")
        if (
            _integer(page.get("file_offset"), "file offset", 0, MAX_FILES)
            != self.next_offset
        ):
            raise SnapshotIntegrityError("Noncontiguous manifest page")
        # The exact-version endpoint can report requested={version:N}. It must
        # not replace the original requested selector retained from resolve.
        if "resolution_id" in page or "resolution_expires_at" in page:
            if ResolutionLease.parse(page) != self.lease:
                raise SnapshotIntegrityError(
                    "Resolution lease changed during continuation"
                )
        entries = page.get("files")
        if not isinstance(entries, list) or not 1 <= len(entries) <= PAGE_SIZE:
            raise SnapshotIntegrityError("Invalid manifest page length")
        self.files.extend(FileMetadata.parse(item) for item in entries)
        if len(self.files) > self.count:
            raise SnapshotIntegrityError("Manifest exceeds declared inventory")
        expected = len(self.files) if len(self.files) < self.count else None
        next_offset = page.get("next_file_offset")
        if next_offset is not None:
            _integer(next_offset, "next file offset", 1, MAX_FILES)
        if "next_file_offset" not in page or next_offset != expected:
            raise SnapshotIntegrityError("Incomplete or looping manifest continuation")
        self.next_offset = expected

    def finish(self) -> SnapshotManifest:
        if self.next_offset is not None or len(self.files) != self.count:
            raise SnapshotIntegrityError("Incomplete manifest")
        paths = [item.path.lower() for item in self.files]
        if len(set(paths)) != len(paths):
            raise SnapshotIntegrityError("Duplicate or case-colliding snapshot paths")
        path_set = set(paths)
        if any(
            "/".join(path.split("/")[:i]) in path_set
            for path in paths
            for i in range(1, len(path.split("/")))
        ):
            raise SnapshotIntegrityError("File/directory prefix collision")
        if sum(item.size_bytes for item in self.files) > MAX_BUNDLE_BYTES:
            raise SnapshotIntegrityError("Snapshot exceeds byte budget")
        root = "AGENTS.md" if self.identity.kind == "agent_context" else "SKILL.md"
        by_path = {item.path: item for item in self.files}
        if root not in by_path or by_path[root].size_bytes == 0:
            raise SnapshotIntegrityError("Snapshot root is missing or empty")
        if (
            self.identity.kind == "agent_context"
            and ".futureagi/context.json" not in by_path
        ):
            raise SnapshotIntegrityError("Context descriptor is missing")
        if manifest_digest(self.files) != self.identity.digest:
            raise SnapshotIntegrityError("Full manifest digest mismatch")
        self.lease.require_live()
        return SnapshotManifest(
            self.identity, self.requested, self.lease, tuple(self.files)
        )


class ChunkCollector:
    """Character offsets are Unicode code points, not UTF-8 bytes or UTF-16."""

    def __init__(self, manifest: SnapshotManifest, path: str) -> None:
        self.manifest = manifest
        self.file = manifest.file(path)
        self.offset = 0
        self.total_chars: int | None = None
        self.parts: list[str] = []
        self.received_bytes = 0
        self.eof = False

    def add(self, raw: object) -> None:
        item = _object(raw)
        if self.eof:
            raise SnapshotIntegrityError("Unexpected chunk after EOF")
        for key, expected in (
            ("path", self.file.path),
            ("sha256", self.file.sha256),
            ("size_bytes", self.file.size_bytes),
        ):
            if item.get(key) != expected:
                raise SnapshotIntegrityError(
                    "File identity changed during continuation"
                )
        if type(item.get("size_bytes")) is not int:
            raise SnapshotIntegrityError("Invalid file size")
        identity = self.manifest.identity
        identity_fields = (
            ("resource_id", identity.resource_id),
            ("version_id", identity.version_id),
            ("digest", identity.digest),
        )
        if any(item.get(key) != value for key, value in identity_fields):
            raise SnapshotIntegrityError("Chunk belongs to another snapshot")
        if (
            _integer(item.get("offset"), "chunk offset", 0, MAX_FILE_BYTES)
            != self.offset
        ):
            raise SnapshotIntegrityError("Noncontiguous chunk")
        total = _integer(
            item.get("total_chars"), "character count", 0, self.file.size_bytes
        )
        if self.total_chars is not None and self.total_chars != total:
            raise SnapshotIntegrityError("File character count changed")
        self.total_chars = total
        text = item.get("text")
        if not isinstance(text, str):
            raise SnapshotIntegrityError("Missing chunk text")
        encoded = _utf8(text)
        end = self.offset + len(text)
        if len(encoded) > CHUNK_BYTES or end > total:
            raise SnapshotIntegrityError("Chunk exceeds declared bounds")
        self.received_bytes += len(encoded)
        if self.received_bytes > self.file.size_bytes:
            raise SnapshotIntegrityError("File exceeds declared size")
        eof = item.get("eof")
        if type(eof) is not bool or eof != (end == total):
            raise SnapshotIntegrityError("Invalid EOF marker")
        if "next_offset" not in item or item["next_offset"] != (None if eof else end):
            raise SnapshotIntegrityError("Invalid chunk continuation")
        if not eof and (not text or type(item["next_offset"]) is not int):
            raise SnapshotIntegrityError("Chunk made no progress")
        # The server may shorten a chunk to bound the JSON-escaped envelope.
        # Contiguity, progress, total size and the final hash prove completeness.
        self.parts.append(text)
        self.offset = end
        self.eof = eof

    def finish(self) -> str:
        if not self.eof:
            raise SnapshotIntegrityError("Incomplete file")
        text = "".join(self.parts)
        if (
            self.received_bytes != self.file.size_bytes
            or hashlib.sha256(_utf8(text)).hexdigest() != self.file.sha256
        ):
            raise SnapshotIntegrityError("File checksum mismatch")
        self.manifest.lease.require_live()
        return text


@dataclass(frozen=True)
class VerifiedSnapshot:
    """Exact bytes for materialization; callers must reauthorize before reuse."""

    manifest: SnapshotManifest
    files: Mapping[str, str] = field(repr=False)

    def __post_init__(self) -> None:
        copied = dict(self.files)
        if manifest_digest(self.manifest.files) != self.manifest.identity.digest:
            raise SnapshotIntegrityError("Full manifest digest mismatch")
        if len(self.manifest.files) != len(copied) or not 1 <= len(copied) <= MAX_FILES:
            raise SnapshotIntegrityError("Verified snapshot inventory mismatch")
        if set(copied) != {item.path for item in self.manifest.files}:
            raise SnapshotIntegrityError("Verified snapshot inventory mismatch")
        for item in self.manifest.files:
            content = _utf8(copied[item.path])
            if (
                len(content) != item.size_bytes
                or hashlib.sha256(content).hexdigest() != item.sha256
            ):
                raise SnapshotIntegrityError("Verified snapshot checksum mismatch")
        if self.manifest.identity.kind == "agent_context":
            self._validate_descriptor(copied)
        object.__setattr__(self, "files", MappingProxyType(copied))

    @property
    def identity(self) -> SnapshotIdentity:
        return self.manifest.identity

    def _validate_descriptor(self, files: Mapping[str, str]) -> None:
        text = files[".futureagi/context.json"]
        try:
            descriptor = json.loads(text)
        except (ValueError, RecursionError):
            raise SnapshotIntegrityError("Invalid context descriptor") from None
        descriptor = _object(descriptor)
        canonical = json.dumps(
            dict(descriptor), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        if (
            canonical != text
            or descriptor.get("schema") != 1
            or type(descriptor.get("schema")) is not int
        ):
            raise SnapshotIntegrityError("Noncanonical context descriptor")
        if (
            descriptor.get("kind") != "agent_context"
            or descriptor.get("name") != self.identity.name
            or descriptor.get("entrypoint") != "AGENTS.md"
        ):
            raise SnapshotIntegrityError("Context descriptor identity mismatch")
        owned = descriptor.get("owned_paths")
        links = descriptor.get("links")
        if (
            not isinstance(owned, list)
            or not isinstance(links, list)
            or len(links) > 20
        ):
            raise SnapshotIntegrityError("Invalid descriptor inventory")
        if (
            not all(isinstance(path, str) for path in owned)
            or owned != sorted(set(owned))
            or "AGENTS.md" not in owned
        ):
            raise SnapshotIntegrityError("Invalid owned paths")
        covered = {".futureagi/context.json"}
        for path in owned:
            validate_path(path)
            if path.startswith(("skills/", ".futureagi/")) or path not in files:
                raise SnapshotIntegrityError("Invalid owned path")
            covered.add(path)
        mounts: list[str] = []
        child_ids: set[str] = set()
        for raw in links:
            link = _object(raw)
            mount = _string(link.get("mount"), "child mount")
            if not re.fullmatch(r"skills/[a-z0-9]+(?:-[a-z0-9]+)*/", mount):
                raise SnapshotIntegrityError("Invalid child mount")
            child_id = _uuid(link.get("skill_id"), "child ID")
            _uuid(link.get("version_id"), "child version ID")
            _integer(link.get("version"), "child version", 1, 2**53 - 1)
            _selector(link.get("requested"))
            if (
                child_id in child_ids
                or mount in mounts
                or mount + "SKILL.md" not in files
            ):
                raise SnapshotIntegrityError("Invalid linked skill inventory")
            child_ids.add(child_id)
            mounts.append(mount)
            child_files = tuple(
                FileMetadata(
                    path[len(mount) :],
                    hashlib.sha256(_utf8(content)).hexdigest(),
                    len(_utf8(content)),
                )
                for path, content in files.items()
                if path.startswith(mount)
            )
            if manifest_digest(child_files) != _hash(link.get("digest"), digest=True):
                raise SnapshotIntegrityError("Linked skill digest mismatch")
            covered.update(path for path in files if path.startswith(mount))
        if mounts != sorted(mounts) or covered != set(files):
            raise SnapshotIntegrityError("Descriptor does not cover the exact snapshot")
        if not files["AGENTS.md"].strip():
            raise SnapshotIntegrityError("Context root is empty")
