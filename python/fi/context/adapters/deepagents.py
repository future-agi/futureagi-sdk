"""Read-only Deep Agents 0.4.11 context mount, not a session/job executor.

Use the real memory source `/fi_context/AGENTS.md` and skills parent
`/fi_context/skills/`. Keep the application's writable backend as default.
The caller supplies live authorization from its exact server-issued session.
Model-boundary checks, checkpoint ownership and delivery receipts must also be
wired by that application's qualified adapter; backend fetches prove none of them.
"""

from __future__ import annotations

from importlib.metadata import version
from typing import Callable

from deepagents.backends import BackendProtocol, CompositeBackend, StateBackend
from deepagents.backends.protocol import (
    EditResult,
    FileDownloadResponse,
    FileUploadResponse,
    WriteResult,
)
from deepagents.backends.utils import create_file_data
from langchain.tools import ToolRuntime

from fi.context.snapshot import (
    ResolutionLease,
    SnapshotIdentity,
    VerifiedSnapshot,
    validate_path,
)

MOUNT = "/fi_context/"
MEMORY_SOURCE = MOUNT + "AGENTS.md"
SKILLS_SOURCE = MOUNT + "skills/"
QUALIFIED_BACKEND_VERSION = "0.4.11"
Authorize = Callable[[SnapshotIdentity, ResolutionLease], None]


class ReadOnlyContextBackend(BackendProtocol):
    """A verified generation, with no mutation route and no mutable label lookup."""

    def __init__(self, snapshot: VerifiedSnapshot, *, authorize: Authorize) -> None:
        if version("deepagents") != QUALIFIED_BACKEND_VERSION:
            raise RuntimeError(
                "This backend requires the qualified Deep Agents 0.4.11 protocol"
            )
        if snapshot.identity.kind != "agent_context":
            raise ValueError("The standing-instruction mount requires an agent context")
        self._snapshot = snapshot
        self._authorize = authorize
        runtime = ToolRuntime(
            state={
                "files": {
                    f"/{path}": create_file_data(
                        text, created_at="1980-01-01T00:00:00Z"
                    )
                    for path, text in snapshot.files.items()
                }
            },
            context=None,
            config={},
            stream_writer=lambda _: None,
            tool_call_id=None,
            store=None,
        )
        self._reader = StateBackend(runtime)

    def _check(self) -> None:
        lease = self._snapshot.manifest.lease
        lease.require_live()
        self._authorize(self._snapshot.identity, lease)
        lease.require_live()

    @staticmethod
    def _path(path: str, *, directory: bool = False) -> str:
        if not isinstance(path, str) or not path.startswith("/"):
            raise ValueError("The backend requires an absolute virtual path")
        relative = path[1:]
        if directory:
            relative = relative.rstrip("/")
        if relative:
            validate_path(relative)
        elif not directory:
            raise ValueError("A file path is required")
        return path

    def ls_info(self, path: str) -> list[dict]:
        self._check()
        return self._reader.ls_info(self._path(path, directory=True))

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        self._check()
        if (
            type(offset) is not int
            or type(limit) is not int
            or offset < 0
            or not 1 <= limit <= 2000
        ):
            raise ValueError("Invalid line range")
        # This is the host's line-numbered/truncated view, not a full-file receipt.
        return self._reader.read(self._path(file_path), offset, limit)

    def grep_raw(
        self, pattern: str, path: str | None = None, glob: str | None = None
    ) -> list[dict] | str:
        self._check()
        return self._reader.grep_raw(
            pattern, self._path(path, directory=True) if path else None, glob
        )

    def glob_info(self, pattern: str, path: str = "/") -> list[dict]:
        self._check()
        return self._reader.glob_info(pattern, self._path(path, directory=True))

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        self._check()
        results = []
        for path in paths:
            relative = self._path(path)[1:]
            text = self._snapshot.files.get(relative)
            results.append(
                FileDownloadResponse(
                    path=path,
                    content=None if text is None else text.encode("utf-8"),
                    error="file_not_found" if text is None else None,
                )
            )
        return results

    def write(self, file_path: str, content: str) -> WriteResult:
        return WriteResult(error="Approved context is read-only")

    def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> EditResult:
        return EditResult(error="Approved context is read-only")

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        return [
            FileUploadResponse(path=path, error="permission_denied")
            for path, _ in files
        ]


def mount_context(
    snapshot: VerifiedSnapshot, *, default: BackendProtocol, authorize: Authorize
) -> CompositeBackend:
    """Only the context prefix is immutable; transient/private app state stays writable."""
    return CompositeBackend(
        default=default,
        routes={MOUNT: ReadOnlyContextBackend(snapshot, authorize=authorize)},
    )
