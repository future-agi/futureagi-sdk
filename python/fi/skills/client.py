"""Leaf snapshot engine, with a required generated consumption source.

No legacy /skills/ route is used for isolated Context credentials. The frozen
leaf facade's generated operations must implement SnapshotSource; no backend
route suffixes are guessed here. This is not yet a packaged REST quickstart.
"""

from fi.context.client import (
    AsyncSnapshotClient,
    AsyncSnapshotSource,
    SnapshotClient,
    SnapshotSource,
)


class SkillsClient(SnapshotClient):
    def __init__(self, source: SnapshotSource) -> None:
        super().__init__(source, kind="skill")


class AsyncSkillsClient(AsyncSnapshotClient):
    def __init__(self, source: AsyncSnapshotSource) -> None:
        super().__init__(source, kind="skill")
