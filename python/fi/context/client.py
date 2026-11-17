"""Snapshot orchestration over the existing platform transport.

Routes come from the pinned F12 generated operations. Source protocols let leaf
consumption operations use the same verification engine without a second HTTP
implementation. Neither source nor snapshot retries a failed resolution.
"""

from __future__ import annotations

import functools
import inspect
import logging
import sys
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


_no_otel_logged = False


def _read_boundary(snapshot, path=None, *, trace=True, **kwargs):
    """Only public read boundaries call this; resolve/paging stay untraced."""
    global _no_otel_logged
    if not trace or not getattr(snapshot, "_tracing", True):
        return None
    if sys.modules.get("opentelemetry.trace") is None:
        from fi.telemetry._otel import mode
        if mode() != "off" and not _no_otel_logged:
            _no_otel_logged = True
            try:
                logging.getLogger("futureagi.telemetry").info(
                    "futureagi: no OpenTelemetry in this process"
                )
            except Exception:
                pass
        return None
    try:
        from fi.telemetry._hooks import Read
        return Read(snapshot, path, **kwargs)
    except Exception:
        return None


def _traced_read(function):
    """Capture completion only after checksum, lease and full-closure checks."""
    if inspect.iscoroutinefunction(function):
        @functools.wraps(function)
        async def async_read(self, *args, trace=True, **kwargs):
            path = args[0] if args else kwargs.get("path")
            boundary = _read_boundary(self, path, trace=trace)
            if boundary is None:
                return await function(self, *args, **kwargs)
            with boundary:
                result = await function(self, *args, **kwargs)
                boundary.success(result)
                return result
        return async_read
    @functools.wraps(function)
    def read(self, *args, trace=True, **kwargs):
        path = args[0] if args else kwargs.get("path")
        boundary = _read_boundary(self, path, trace=trace)
        if boundary is None:
            return function(self, *args, **kwargs)
        with boundary:
            result = function(self, *args, **kwargs)
            boundary.success(result)
            return result
    return read


@dataclass(frozen=True)
class ContextSnapshot:
    """Verified full inventory with lazy, authenticated, checksum-checked reads."""

    manifest: SnapshotManifest
    _source: SnapshotSource = field(repr=False)
    _tracing: bool = field(default=True, repr=False)
    _telemetry_binding_id: str | None = field(default=None, repr=False)
    _telemetry_session_id: str | None = field(default=None, repr=False)
    _telemetry_links: tuple | None = field(default=None, repr=False, compare=False)

    @property
    def identity(self) -> SnapshotIdentity:
        return self.manifest.identity

    @_traced_read
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

    @_traced_read
    def read_all(self) -> VerifiedSnapshot:
        files = {item.path: self.read_file(item.path, trace=False) for item in self.manifest.files}
        self.manifest.lease.require_live()
        return VerifiedSnapshot(self.manifest, files)


@dataclass(frozen=True)
class AsyncContextSnapshot:
    manifest: SnapshotManifest
    _source: AsyncSnapshotSource = field(repr=False)
    _tracing: bool = field(default=True, repr=False)
    _telemetry_binding_id: str | None = field(default=None, repr=False)
    _telemetry_session_id: str | None = field(default=None, repr=False)
    _telemetry_links: tuple | None = field(default=None, repr=False, compare=False)

    @property
    def identity(self) -> SnapshotIdentity:
        return self.manifest.identity

    @_traced_read
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

    @_traced_read
    async def read_all(self) -> VerifiedSnapshot:
        files = {
            item.path: await self.read_file(item.path, trace=False) for item in self.manifest.files
        }
        self.manifest.lease.require_live()
        return VerifiedSnapshot(self.manifest, files)


class SnapshotClient:
    """Shared engine for context and typed leaf-consumption sources."""

    def __init__(self, source: SnapshotSource, *, kind: str, tracing: bool = True) -> None:
        self._source = source
        self._kind = kind
        self._tracing = tracing

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
        return ContextSnapshot(collector.finish(), self._source, _tracing=self._tracing)


class AsyncSnapshotClient:
    def __init__(self, source: AsyncSnapshotSource, *, kind: str, tracing: bool = True) -> None:
        self._source = source
        self._kind = kind
        self._tracing = tracing

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
        return AsyncContextSnapshot(collector.finish(), self._source, _tracing=self._tracing)


class ContextClient(SnapshotClient):
    """Verified reads and live access checks using the caller-owned platform client."""

    def __init__(self, client: PlatformClient, *, tracing: bool = True) -> None:
        self._consumption = ConsumptionSource(client, kind="agent_context", tracing=tracing)
        super().__init__(self._consumption, kind="agent_context", tracing=tracing)

    def check_access(self, identity: SnapshotIdentity, lease: ResolutionLease) -> None:
        """Reauthorize exact bytes; does not renew a lease or report delivery."""
        self._consumption.check_access(identity, lease)


class AsyncContextClient(AsyncSnapshotClient):
    def __init__(self, client: PlatformAsyncClient, *, tracing: bool = True) -> None:
        self._consumption = AsyncConsumptionSource(client, kind="agent_context", tracing=tracing)
        super().__init__(self._consumption, kind="agent_context", tracing=tracing)

    async def check_access(
        self, identity: SnapshotIdentity, lease: ResolutionLease
    ) -> None:
        await self._consumption.check_access(identity, lease)
