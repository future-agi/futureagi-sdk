"""Snapshot orchestration over the existing platform transport.

Routes come from the pinned F12 generated operations. Source protocols let leaf
consumption operations use the same verification engine without a second HTTP
implementation. Neither source nor snapshot retries a failed resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from fi.platform import AsyncClient as PlatformAsyncClient
from fi.platform import Client as PlatformClient
from fi.platform import RequestOptions

from .snapshot import (
    ChunkCollector,
    ManifestCollector,
    ResolutionLease,
    SnapshotIdentity,
    SnapshotIntegrityError,
    SnapshotManifest,
    VerifiedSnapshot,
    _selector,
)
from .source import AsyncConsumptionSource, ConsumptionSource


class SnapshotSource(Protocol):
    """Adapter to generated operations; forward every supplied RequestOptions.

    Implementations must keep the platform client's credential/scope fixed and
    use identity.resource_id/version for continuation, never name or label.
    Results are unwrapped wire JSON, validated by the snapshot engine.
    """

    def resolve(self, *, name: str, selector: dict[str, object]) -> object: ...
    def manifest(
        self, identity: SnapshotIdentity, *, offset: int, options: RequestOptions
    ) -> object: ...
    def chunk(
        self,
        identity: SnapshotIdentity,
        *,
        path: str,
        offset: int,
        options: RequestOptions,
    ) -> object: ...


class AsyncSnapshotSource(Protocol):
    async def resolve(self, *, name: str, selector: dict[str, object]) -> object: ...
    async def manifest(
        self, identity: SnapshotIdentity, *, offset: int, options: RequestOptions
    ) -> object: ...
    async def chunk(
        self,
        identity: SnapshotIdentity,
        *,
        path: str,
        offset: int,
        options: RequestOptions,
    ) -> object: ...


def _requested(label: str | None, version: int | None) -> dict[str, object]:
    if label is not None and version is not None:
        raise ValueError("Specify label or version, not both")
    selector: dict[str, object] = (
        {"version": version}
        if version is not None
        else {"label": label if label is not None else "production"}
    )
    return dict(_selector(selector))


def _check_requested(
    collector: ManifestCollector, name: str, selector: dict[str, object]
) -> None:
    if collector.identity.name != name or collector.requested != selector:
        raise SnapshotIntegrityError(
            "Resolve response does not match requested selector"
        )
    if "version" in selector and collector.identity.version != selector["version"]:
        raise SnapshotIntegrityError("Resolve returned another version")


def _options(manifest: SnapshotManifest) -> RequestOptions:
    manifest.lease.require_live()
    return RequestOptions(resolution_id=manifest.lease.resolution_id)


@dataclass(frozen=True)
class ContextSnapshot:
    """Verified full inventory with lazy, authenticated, checksum-checked reads."""

    manifest: SnapshotManifest
    _source: SnapshotSource = field(repr=False)

    @property
    def identity(self) -> SnapshotIdentity:
        return self.manifest.identity

    def read_file(self, path: str) -> str:
        chunks = ChunkCollector(self.manifest, path)
        while not chunks.eof:
            chunks.add(
                self._source.chunk(
                    self.identity,
                    path=path,
                    offset=chunks.offset,
                    options=_options(self.manifest),
                )
            )
        return chunks.finish()

    def read_all(self) -> VerifiedSnapshot:
        files = {item.path: self.read_file(item.path) for item in self.manifest.files}
        self.manifest.lease.require_live()
        return VerifiedSnapshot(self.manifest, files)


@dataclass(frozen=True)
class AsyncContextSnapshot:
    manifest: SnapshotManifest
    _source: AsyncSnapshotSource = field(repr=False)

    @property
    def identity(self) -> SnapshotIdentity:
        return self.manifest.identity

    async def read_file(self, path: str) -> str:
        chunks = ChunkCollector(self.manifest, path)
        while not chunks.eof:
            chunks.add(
                await self._source.chunk(
                    self.identity,
                    path=path,
                    offset=chunks.offset,
                    options=_options(self.manifest),
                )
            )
        return chunks.finish()

    async def read_all(self) -> VerifiedSnapshot:
        files = {
            item.path: await self.read_file(item.path) for item in self.manifest.files
        }
        self.manifest.lease.require_live()
        return VerifiedSnapshot(self.manifest, files)


class SnapshotClient:
    """Shared engine for context and typed leaf-consumption sources."""

    def __init__(self, source: SnapshotSource, *, kind: str) -> None:
        self._source = source
        self._kind = kind

    def resolve(
        self, name: str, *, label: str | None = None, version: int | None = None
    ) -> ContextSnapshot:
        selector = _requested(label, version)
        collector = ManifestCollector(
            self._source.resolve(name=name, selector=selector), kind=self._kind
        )
        _check_requested(collector, name, selector)
        while collector.next_offset is not None:
            collector.lease.require_live()
            collector.add(
                self._source.manifest(
                    collector.identity,
                    offset=collector.next_offset,
                    options=RequestOptions(resolution_id=collector.lease.resolution_id),
                )
            )
        return ContextSnapshot(collector.finish(), self._source)


class AsyncSnapshotClient:
    def __init__(self, source: AsyncSnapshotSource, *, kind: str) -> None:
        self._source = source
        self._kind = kind

    async def resolve(
        self, name: str, *, label: str | None = None, version: int | None = None
    ) -> AsyncContextSnapshot:
        selector = _requested(label, version)
        collector = ManifestCollector(
            await self._source.resolve(name=name, selector=selector), kind=self._kind
        )
        _check_requested(collector, name, selector)
        while collector.next_offset is not None:
            collector.lease.require_live()
            collector.add(
                await self._source.manifest(
                    collector.identity,
                    offset=collector.next_offset,
                    options=RequestOptions(resolution_id=collector.lease.resolution_id),
                )
            )
        return AsyncContextSnapshot(collector.finish(), self._source)


class ContextClient(SnapshotClient):
    """Verified reads and live access checks using the caller-owned platform client."""

    def __init__(self, client: PlatformClient) -> None:
        self._consumption = ConsumptionSource(client, kind="agent_context")
        super().__init__(self._consumption, kind="agent_context")

    def check_access(self, identity: SnapshotIdentity, lease: ResolutionLease) -> None:
        """Reauthorize exact bytes; does not renew a lease or report delivery."""
        self._consumption.check_access(identity, lease)


class AsyncContextClient(AsyncSnapshotClient):
    def __init__(self, client: PlatformAsyncClient) -> None:
        self._consumption = AsyncConsumptionSource(client, kind="agent_context")
        super().__init__(self._consumption, kind="agent_context")

    async def check_access(
        self, identity: SnapshotIdentity, lease: ResolutionLease
    ) -> None:
        await self._consumption.check_access(identity, lease)
