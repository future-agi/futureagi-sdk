"""Verified leaf reads through the isolated F12 consumption facade."""

from __future__ import annotations

from fi.context.client import (
    AsyncSnapshotClient,
    AsyncSnapshotSource,
    SnapshotClient,
    SnapshotSource,
)
from fi.context.snapshot import ResolutionLease, SnapshotIdentity
from fi.context.source import AsyncConsumptionSource, ConsumptionSource
from fi.platform import AsyncClient, Client


class SkillsClient(SnapshotClient):
    def __init__(self, source: Client | SnapshotSource) -> None:
        self._consumption = (
            ConsumptionSource(source, kind="skill")
            if isinstance(source, Client)
            else None
        )
        super().__init__(self._consumption or source, kind="skill")

    def check_access(self, identity: SnapshotIdentity, lease: ResolutionLease) -> None:
        if self._consumption is None:
            raise TypeError(
                "A custom SnapshotSource must supply its own live authorizer"
            )
        self._consumption.check_access(identity, lease)


class AsyncSkillsClient(AsyncSnapshotClient):
    def __init__(self, source: AsyncClient | AsyncSnapshotSource) -> None:
        self._consumption = (
            AsyncConsumptionSource(source, kind="skill")
            if isinstance(source, AsyncClient)
            else None
        )
        super().__init__(self._consumption or source, kind="skill")

    async def check_access(
        self, identity: SnapshotIdentity, lease: ResolutionLease
    ) -> None:
        if self._consumption is None:
            raise TypeError(
                "A custom SnapshotSource must supply its own live authorizer"
            )
        await self._consumption.check_access(identity, lease)
