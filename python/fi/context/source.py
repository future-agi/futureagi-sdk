"""F12 consumption operations on the shared transport, without model coercion.

Snapshot validation must inspect the original JSON types (bool is not a version
number). Generated Operation records own URLs/envelopes; no fallback route,
HTTP implementation, cache or lease renewal lives here.
"""

from __future__ import annotations

from fi.platform import AsyncClient, Client, RequestOptions
from fi.platform import _operations as operations

from .snapshot import (
    CHUNK_BYTES,
    PAGE_SIZE,
    ResolutionLease,
    SnapshotIdentity,
    SnapshotIntegrityError,
)


def _operations(kind: str):
    if kind == "agent_context":
        return (
            operations.OP_CONTEXTS_RESOLVE,
            operations.OP_CONTEXTS_MANIFEST,
            operations.OP_CONTEXTS_READ_FILE,
            operations.OP_CONTEXTS_CHECK_ACCESS,
        )
    if kind == "skill":
        return (
            operations.OP_SKILL_CONSUMPTION_RESOLVE,
            operations.OP_SKILL_CONSUMPTION_MANIFEST,
            operations.OP_SKILL_CONSUMPTION_READ_FILE,
            operations.OP_SKILL_CONSUMPTION_CHECK_ACCESS,
        )
    raise ValueError("Unsupported consumption kind")


def _path(identity: SnapshotIdentity, kind: str) -> dict[str, object]:
    if identity.kind != kind:
        raise SnapshotIntegrityError("Consumption resource kind mismatch")
    return {"resource_id": identity.resource_id, "number": identity.version}


def validate_access(result: object, identity: SnapshotIdentity) -> None:
    if not isinstance(result, dict) or (
        result.get("allowed") is not True
        or result.get("version_id") != identity.version_id
        or result.get("digest") != identity.digest
    ):
        raise SnapshotIntegrityError("Access check did not authorize this snapshot")


class ConsumptionSource:
    def __init__(self, client: Client, *, kind: str) -> None:
        self.client = client
        self.kind = kind
        self.operations = _operations(kind)

    def resolve(self, *, name: str, selector: dict[str, object]) -> object:
        return self.client._transport.call(
            self.operations[0], query={"name": name, **selector}
        )

    def manifest(
        self, identity: SnapshotIdentity, *, offset: int, options: RequestOptions
    ) -> object:
        return self.client._transport.call(
            self.operations[1],
            path=_path(identity, self.kind),
            query={"file_offset": offset, "file_limit": PAGE_SIZE},
            options=options,
        )

    def chunk(
        self,
        identity: SnapshotIdentity,
        *,
        path: str,
        offset: int,
        options: RequestOptions,
    ) -> object:
        return self.client._transport.call(
            self.operations[2],
            path=_path(identity, self.kind),
            query={"path": path, "offset": offset, "max_bytes": CHUNK_BYTES},
            options=options,
        )

    def check_access(self, identity: SnapshotIdentity, lease: ResolutionLease) -> None:
        lease.require_live()
        result = self.client._transport.call(
            self.operations[3],
            path=_path(identity, self.kind),
            body={},
            options=RequestOptions(resolution_id=lease.resolution_id),
        )
        validate_access(result, identity)
        lease.require_live()


class AsyncConsumptionSource:
    def __init__(self, client: AsyncClient, *, kind: str) -> None:
        self.client = client
        self.kind = kind
        self.operations = _operations(kind)

    async def resolve(self, *, name: str, selector: dict[str, object]) -> object:
        return await self.client._transport.acall(
            self.operations[0], query={"name": name, **selector}
        )

    async def manifest(
        self, identity: SnapshotIdentity, *, offset: int, options: RequestOptions
    ) -> object:
        return await self.client._transport.acall(
            self.operations[1],
            path=_path(identity, self.kind),
            query={"file_offset": offset, "file_limit": PAGE_SIZE},
            options=options,
        )

    async def chunk(
        self,
        identity: SnapshotIdentity,
        *,
        path: str,
        offset: int,
        options: RequestOptions,
    ) -> object:
        return await self.client._transport.acall(
            self.operations[2],
            path=_path(identity, self.kind),
            query={"path": path, "offset": offset, "max_bytes": CHUNK_BYTES},
            options=options,
        )

    async def check_access(
        self, identity: SnapshotIdentity, lease: ResolutionLease
    ) -> None:
        lease.require_live()
        result = await self.client._transport.acall(
            self.operations[3],
            path=_path(identity, self.kind),
            body={},
            options=RequestOptions(resolution_id=lease.resolution_id),
        )
        validate_access(result, identity)
        lease.require_live()
