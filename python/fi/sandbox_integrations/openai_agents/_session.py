"""The Agents SDK session on one Future AGI sandbox: :class:`FutureAGISandboxSession`.

It implements the six calls the SDK's ``BaseSandboxSession`` leaves to a backend on the async sandbox
handle (:class:`fi.sandbox.AsyncSandbox`); the SDK builds its file tools, manifest setup and snapshots
on them:

- ``_exec_internal`` joins the argument list with ``shlex.join`` and runs it once in the workspace
  root. The exec API takes its working folder relative to ``/workspace`` and refuses an absolute
  one, so the root is sent that way (no working folder for ``/workspace`` itself, or before the
  root exists). How the command ended becomes the exit code the ``sandbox exec`` command uses
  (124 timed out, 128+N signal N, 130 cancelled, 1 could not start or no code), with one line
  saying so appended to stderr. A command whose outcome is unknown, or that the server failed after it started, raises the
  SDK's ``ExecTransportError`` (not retryable); it is never sent again.
- ``read`` / ``write`` use the sandbox files API, which reaches files under ``/workspace`` only.
  ``write`` makes the missing parent folders first.
- ``running`` reads the sandbox record: True while it is ``active``.
- ``persist_workspace`` / ``hydrate_workspace`` move the workspace as a tar stream with
  workspace-relative members, through a temporary ``/workspace/.fi-ws-<id>.tar`` that is removed
  afterwards. A stream above 64 MiB (the upload limit) is refused before anything is sent. A failed
  call can leave that file behind; files named ``.fi-ws-*.tar`` are never put into an archive.

Running a command or touching a file as another user is refused before any request (sandboxes run
every command as one fixed user). Nothing is retried, and a hibernated sandbox is not resumed here.
"""

from __future__ import annotations

import io
import logging
import math
import posixpath
import shlex
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, Union

from ._missing import missing_agents_sandbox

try:
    from agents.sandbox.errors import (
        ExecTransportError,
        WorkspaceArchiveReadError,
        WorkspaceArchiveWriteError,
        WorkspaceReadNotFoundError,
        WorkspaceStartError,
        WorkspaceWriteTypeError,
    )
    from agents.sandbox.session.base_sandbox_session import BaseSandboxSession
    from agents.sandbox.session.tar_workspace import shell_tar_exclude_args
    from agents.sandbox.types import ExecResult
    from agents.sandbox.util.tar_utils import UnsafeTarMemberError, validate_tar_bytes
except ImportError as exc:
    raise missing_agents_sandbox(exc) from exc

from fi.sandbox.errors import (
    CommandFailedError,
    CommandIncompleteError,
    ConfigurationError,
    ConflictError,
    NotFoundError,
    PayloadTooLargeError,
    SandboxError,
    SandboxHibernatedError,
)
from fi.sandbox_integrations._exit import ending_note, shell_exit_code

from ._options import WORKSPACE_ROOT, FutureAGISandboxSessionState

if TYPE_CHECKING:
    from agents.sandbox.types import User
    from fi.sandbox import AsyncSandbox, CommandResult

logger = logging.getLogger(__name__)

#: The largest file one upload takes (the hosted limit); a larger workspace stream is refused.
UPLOAD_LIMIT_BYTES = 64 * 1024 * 1024
#: The name every temporary workspace archive starts with; such files are never archived.
ARCHIVE_PREFIX = ".fi-ws-"
#: The time limit, in seconds, of the command that makes the workspace root at start.
SETUP_TIMEOUT_S = 60

_ARCHIVE_EXCLUDE = "--exclude=" + shlex.quote(f"./{ARCHIVE_PREFIX}*.tar")


def _user_refusal(user: Any) -> NotImplementedError:
    name = getattr(user, "name", user)
    return NotImplementedError(
        "Future AGI sandboxes run every command as one fixed user (uid 1000); acting as "
        f"user {name!r} is not supported"
    )


def files_path(path: Union[str, Path]) -> str:
    """An absolute sandbox path as the files API takes it: relative to ``/workspace`` (``""`` for
    ``/workspace`` itself). A path outside ``/workspace`` is refused."""
    text = posixpath.normpath(path.as_posix() if isinstance(path, Path) else str(path))
    if text == WORKSPACE_ROOT:
        return ""
    if not text.startswith(WORKSPACE_ROOT + "/"):
        raise NotImplementedError(
            f"{text}: the Future AGI sandbox files API reaches files under {WORKSPACE_ROOT} only"
        )
    return text[len(WORKSPACE_ROOT) + 1 :]


def _too_large(size: int) -> PayloadTooLargeError:
    error = PayloadTooLargeError(
        413,
        None,
        code="payload_too_large",
        message=(
            f"sandboxes.files.upload: the workspace archive is {size} bytes; one upload takes "
            f"at most {UPLOAD_LIMIT_BYTES} bytes (64 MiB), so nothing was sent"
        ),
        operation="sandboxes.files.upload",
    )
    error.limit_bytes, error.local = UPLOAD_LIMIT_BYTES, True
    return error


def _exec_result(result: CommandResult, limit: int) -> ExecResult:
    code = shell_exit_code(result)
    stderr = result.stderr
    note = ending_note(result, limit)
    if note is not None:
        stderr = f"{stderr}\n{note}" if stderr and not stderr.endswith("\n") else stderr + note
    return ExecResult(
        stdout=result.stdout.encode("utf-8", errors="replace"),
        stderr=stderr.encode("utf-8", errors="replace"),
        exit_code=code if code is not None else 1,
    )


def _transport_error(argv: List[str], error: SandboxError) -> ExecTransportError:
    incomplete = isinstance(error, CommandIncompleteError)
    context = {
        "reason": "exit_unknown" if incomplete else "server_failed",
        "provider_error": str(error),
        "exec_id": getattr(error, "exec_id", None),
    }
    message = (
        "the connection ended before the command's exit; whether it finished is unknown"
        if incomplete
        else "the sandbox failed after the command started"
    )
    return ExecTransportError(
        command=argv, context=context, cause=error, message=message, retryable=False
    )


class FutureAGISandboxSession(BaseSandboxSession):
    """One Future AGI sandbox as an Agents SDK session. :class:`FutureAGISandboxClient` builds it
    (and wraps it in the SDK's instrumented ``SandboxSession``); ``max_timeout_s`` is the
    workspace's exec maximum, read when the session was made."""

    state: FutureAGISandboxSessionState

    def __init__(
        self,
        *,
        state: FutureAGISandboxSessionState,
        sandbox: AsyncSandbox,
        max_timeout_s: int,
    ) -> None:
        self.state = state
        self._sandbox = sandbox
        self._max_timeout_s = max_timeout_s
        self._root_ready = state.workspace_root_ready
        self._ended = False

    @property
    def sandbox(self) -> AsyncSandbox:
        """The sandbox handle the session runs on."""
        return self._sandbox

    @property
    def sandbox_id(self) -> str:
        return self.state.sandbox_id

    @property
    def max_timeout_s(self) -> int:
        return self._max_timeout_s

    def _limit(self, timeout: Optional[float]) -> int:
        """Whole seconds for the sandbox: ``timeout`` rounded up and kept within 1 and the
        workspace maximum; None is the session's default (``exec_timeout_s``, else the maximum)."""
        if timeout is None:
            wanted = self.state.exec_timeout_s
            if wanted is None or wanted <= 0:
                return self._max_timeout_s
            return min(int(wanted), self._max_timeout_s)
        if not math.isfinite(timeout):
            return self._max_timeout_s
        return max(1, min(math.ceil(timeout), self._max_timeout_s))

    async def _exec_internal(
        self, *command: Union[str, Path], timeout: Optional[float] = None
    ) -> ExecResult:
        argv = [str(part) for part in command]
        if len(argv) >= 4 and argv[0] == "sudo" and argv[1] == "-u" and argv[3] == "--":
            raise _user_refusal(argv[2])
        limit = self._limit(timeout)
        cwd = (files_path(self.state.manifest.root) or None) if self._root_ready else None
        try:
            result = await self._sandbox.commands.run(
                shlex.join(argv), cwd=cwd, timeout_seconds=limit
            )
        except (CommandIncompleteError, CommandFailedError) as error:
            raise _transport_error(argv, error) from error
        return _exec_result(result, limit)

    async def read(self, path: Path, *, user: Union[str, User, None] = None) -> io.IOBase:
        if user is not None:
            raise _user_refusal(user)
        where = self.normalize_path(path)
        target = files_path(where)
        if not target:
            raise IsADirectoryError(f"{where} is a folder")
        try:
            data = await self._sandbox.files.download(target)
        except NotFoundError as error:
            raise WorkspaceReadNotFoundError(path=where, cause=error) from error
        return io.BytesIO(data)

    async def write(
        self, path: Path, data: io.IOBase, *, user: Union[str, User, None] = None
    ) -> None:
        if user is not None:
            raise _user_refusal(user)
        payload = data.read()
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        if not isinstance(payload, (bytes, bytearray)):
            raise WorkspaceWriteTypeError(path=Path(str(path)), actual_type=type(payload).__name__)
        where = self.normalize_path(path, for_write=True)
        target = files_path(where)
        if not target:
            raise IsADirectoryError(f"{where} is a folder")
        await self._make_dirs(posixpath.dirname(target))
        await self._sandbox.files.upload(target, bytes(payload))

    async def _make_dirs(self, folder: str) -> None:
        """Make sure ``folder`` (relative to ``/workspace``) exists. A folder that exists answers
        409 and counts as made; a 404 means a folder above it is missing, so the folders are then
        made from the top down."""
        if not folder:
            return
        try:
            await self._sandbox.files.make_dir(folder)
            return
        except SandboxHibernatedError:
            raise
        except ConflictError:
            return
        except NotFoundError:
            pass
        parts = folder.split("/")
        for depth in range(1, len(parts) + 1):
            try:
                await self._sandbox.files.make_dir("/".join(parts[:depth]))
            except SandboxHibernatedError:
                raise
            except ConflictError:
                continue

    async def running(self) -> bool:
        if not self._root_ready:
            return False
        try:
            await self._sandbox.refresh()
        except NotFoundError:
            return False
        return self._sandbox.state == "active"

    async def _prepare_backend_workspace(self) -> None:
        """Make the workspace root before the manifest or a snapshot is applied there (commands
        run in it, so it must exist first)."""
        if self._workspace_state_preserved_on_start() and self._root_ready:
            return
        root = self.state.manifest.root
        result = await self._sandbox.commands.run(
            f"mkdir -p -- {shlex.quote(root)}", timeout_seconds=self._limit(SETUP_TIMEOUT_S)
        )
        code = shell_exit_code(result)
        if code != 0:
            raise WorkspaceStartError(
                path=Path(root),
                context={"reason": "workspace_root_nonzero_exit", "exit_code": code,
                         "stderr": result.stderr},
            )
        self._root_ready = True

    def _mark_workspace_root_ready_from_probe(self) -> None:
        super()._mark_workspace_root_ready_from_probe()
        self._root_ready = True

    async def persist_workspace(self) -> io.IOBase:
        """The workspace as a tar stream: ``tar`` into a temporary file in ``/workspace``, then a
        download, then the file is removed."""
        root = self._workspace_root_path().as_posix()
        name = f"{ARCHIVE_PREFIX}{uuid.uuid4().hex}.tar"
        archive = f"{WORKSPACE_ROOT}/{name}"
        excludes = [*shell_tar_exclude_args(self._persist_workspace_skip_relpaths()), _ARCHIVE_EXCLUDE]
        command = (
            f"tar {' '.join(excludes)} -C {shlex.quote(root)} -cf {shlex.quote(archive)} ."
        )
        result = await self._sandbox.commands.run(command, timeout_seconds=self._limit(None))
        code = shell_exit_code(result)
        if code != 0:
            raise WorkspaceArchiveReadError(
                path=Path(root),
                context={"reason": "archive_nonzero_exit", "exit_code": code,
                         "stderr": result.stderr, "temporary_archive": archive},
                retryable=False,
            )
        data = await self._sandbox.files.download(name)
        await self._remove_archive(name)
        return io.BytesIO(data)

    async def hydrate_workspace(self, data: io.IOBase) -> None:
        """Unpack a tar stream into the workspace: an upload to a temporary file in
        ``/workspace``, ``tar -x`` into the root, then the file is removed."""
        root = self._workspace_root_path().as_posix()
        raw = data.read()
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        if not isinstance(raw, (bytes, bytearray)):
            raise WorkspaceWriteTypeError(path=Path(root), actual_type=type(raw).__name__)
        if len(raw) > UPLOAD_LIMIT_BYTES:
            raise _too_large(len(raw))
        try:
            validate_tar_bytes(bytes(raw), allow_external_symlink_targets=False)
        except UnsafeTarMemberError as error:
            raise WorkspaceArchiveWriteError(
                path=Path(root),
                context={"reason": "unsafe_or_invalid_tar", "member": error.member,
                         "detail": str(error)},
                cause=error,
            ) from error
        name = f"{ARCHIVE_PREFIX}{uuid.uuid4().hex}.tar"
        archive = f"{WORKSPACE_ROOT}/{name}"
        await self._sandbox.files.upload(name, bytes(raw))
        quoted = shlex.quote(root)
        result = await self._sandbox.commands.run(
            f"mkdir -p -- {quoted} && tar -C {quoted} -xf {shlex.quote(archive)}",
            timeout_seconds=self._limit(None),
        )
        await self._remove_archive(name)
        code = shell_exit_code(result)
        if code != 0:
            raise WorkspaceArchiveWriteError(
                path=Path(root),
                context={"reason": "hydrate_nonzero_exit", "exit_code": code,
                         "stderr": result.stderr},
            )
        self._root_ready = True

    async def _remove_archive(self, name: str) -> None:
        """Remove a temporary archive; a failure is logged, never raised (the data is fine)."""
        try:
            await self._sandbox.files.remove(name)
        except ConfigurationError:
            raise
        except SandboxError as error:
            logger.warning(
                "could not remove the temporary archive %s/%s from sandbox %s: %s",
                WORKSPACE_ROOT, name, self.sandbox_id, error,
            )

    async def _shutdown_backend(self) -> None:
        await self._end()

    async def _end(self) -> None:
        """Delete the sandbox (or hibernate it with ``hibernate_on_exit``) and close the connection
        pool this session's handle opened. Runs once; the SDK's shutdown and the client's
        ``delete`` both lead here. A sandbox that is already gone is not an error."""
        if self._ended:
            return
        self._ended = True
        try:
            if self.state.hibernate_on_exit:
                try:
                    await self._sandbox.hibernate()
                except NotFoundError:
                    pass
            else:
                await self._sandbox.delete()
        finally:
            await self._sandbox.aclose()


__all__ = [
    "ARCHIVE_PREFIX",
    "FutureAGISandboxSession",
    "SETUP_TIMEOUT_S",
    "UPLOAD_LIMIT_BYTES",
    "files_path",
]
