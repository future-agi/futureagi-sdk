"""A Deep Agents sandbox backend on a Future AGI sandbox: :class:`FutureAGISandbox`.

Deep Agents builds every file tool (``ls``, ``read_file``, ``write_file``, ``edit_file``, ``delete``,
``glob``, ``grep``) on three calls, ``execute``, ``upload_files`` and ``download_files``, and its
``BaseSandbox`` runs ``python3`` inside the sandbox for several of them. This module implements those
three calls on the sandbox handle (:class:`fi.sandbox.Sandbox`) and nothing else:

- ``execute`` never raises for how a command ended. The exit code is the one the ``sandbox exec``
  command uses (124 timed out, 128+N signal N, 130 cancelled, 1 could not start), and a failure of
  the call itself comes back as output with exit code 1, or None when whether the command finished
  is unknown.
- ``upload_files`` and ``download_files`` report a failure per file and go on with the others.
  They use the sandbox's files API, whose paths are relative to ``/workspace``, so they reach
  files under ``/workspace`` only; a path elsewhere gets ``permission_denied`` without a request.
- Nothing is retried and nothing resumes a hibernated sandbox. A setup problem
  (:class:`fi.sandbox.ConfigurationError`) is raised, never turned into a result.

Building the backend reads the workspace's exec time limit (unless ``max_timeout=`` gives it) and
checks that ``python3`` is on the sandbox's PATH, refusing a sandbox without it.
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 11):
    raise ImportError(
        "fi.sandbox_integrations.deepagents needs Python 3.11+ (Deep Agents requires it)"
    )

from fi.errors import MissingExtraError

try:
    from deepagents.backends.protocol import (
        ExecuteResponse,
        FileDownloadResponse,
        FileUploadResponse,
    )
    from deepagents.backends.sandbox import BaseSandbox
except ImportError as exc:
    raise MissingExtraError(cause=exc, extra="sandbox-deepagents", module="deepagents") from exc

import inspect
import posixpath
from typing import TYPE_CHECKING, Any, Final, List, Mapping, Optional, Tuple

from fi.sandbox.errors import (
    CommandFailedError,
    CommandIncompleteError,
    ConfigurationError,
    ConflictError,
    NotFoundError,
    PayloadTooLargeError,
    PermissionDeniedError,
    SandboxError,
    SandboxHibernatedError,
    ValidationError,
)
from fi.sandbox_integrations._exit import ending_note, shell_exit_code

if TYPE_CHECKING:
    from fi.sandbox import Sandbox

#: Where commands run unless ``workdir=`` says otherwise: the sandbox's writable folder.
DEFAULT_WORKDIR: Final = "/workspace"
#: The time limit for a command when ``execute`` gets none (the E2B and Daytona backends' default),
#: lowered to the workspace's exec maximum when that is smaller.
DEFAULT_TIMEOUT_S: Final = 30 * 60
#: The folder the files API's paths are relative to; uploads and downloads reach only this folder.
FILES_ROOT: Final = "/workspace"
#: The time limit for the ``python3`` check made when the backend is built.
CHECK_TIMEOUT_S: Final = 30

_INCOMPLETE: Final = (
    "Error: the connection ended before the command finished; whether it finished is unknown"
)
#: What a 400 or 409 on a file says when the sandbox may not write there.
_NOT_WRITABLE_REASONS: Final = frozenset(
    {"read_only", "readonly", "not_writable", "permission_denied", "eacces", "eperm", "erofs"}
)
_NOT_WRITABLE_TEXT: Final = ("read-only", "can't write", "cannot write")


class FutureAGISandbox(BaseSandbox):
    """A Deep Agents backend whose tools run in a Future AGI sandbox.

    ``sandbox`` is a handle you created or connected (``Sandbox.create(...)``,
    ``client.sandboxes.connect(id)``); you keep its lifecycle. ``workdir`` is the folder commands run
    in. ``timeout`` is the default time limit in seconds; 0, or anything above the workspace's exec
    maximum, means that maximum (sandboxes have no unlimited run). ``max_timeout`` is that maximum
    in seconds when you know it (``caps.exec.maxTimeoutSeconds`` of the workspace's sandbox
    settings); without it the backend reads the settings.

    Building it makes up to two requests: it reads the workspace's sandbox settings for the exec
    maximum (not when ``max_timeout`` is given), and runs ``command -v python3`` in ``workdir``. It
    raises ``ConfigurationError`` (code ``python3_missing``) when the sandbox has no ``python3``,
    and any error of those two calls as the handle raised it (a hibernated sandbox included: resume
    it first)."""

    def __init__(
        self,
        *,
        sandbox: Sandbox,
        workdir: str = DEFAULT_WORKDIR,
        timeout: Optional[int] = None,
        max_timeout: Optional[int] = None,
    ) -> None:
        if inspect.iscoroutinefunction(getattr(sandbox.commands, "run", None)):
            raise TypeError(
                "FutureAGISandbox needs a sync fi.sandbox.Sandbox; an AsyncSandbox is not "
                "supported yet (Deep Agents runs the sync backend in worker threads for async agents)"
            )
        self._sandbox = sandbox
        self._workdir = workdir
        self._max_timeout = _exec_maximum(sandbox) if max_timeout is None else _given(max_timeout)
        self._timeout = self._limit(DEFAULT_TIMEOUT_S if timeout is None else timeout)
        _require_python3(sandbox, workdir, self._limit(CHECK_TIMEOUT_S))

    @property
    def id(self) -> str:
        return self._sandbox.id

    @property
    def sandbox(self) -> Sandbox:
        """The sandbox handle the backend runs on."""
        return self._sandbox

    @property
    def workdir(self) -> str:
        return self._workdir

    @property
    def timeout(self) -> int:
        """The time limit, in seconds, of a command run without one."""
        return self._timeout

    @property
    def max_timeout(self) -> int:
        """The workspace's exec maximum, in seconds: ``max_timeout=``, or read when the backend was
        built."""
        return self._max_timeout

    def _limit(self, seconds: int) -> int:
        if seconds <= 0 or seconds > self._max_timeout:
            return self._max_timeout
        return int(seconds)

    def execute(self, command: str, *, timeout: Optional[int] = None) -> ExecuteResponse:
        """Run ``command`` in ``workdir`` with a shell, once. ``timeout`` is in seconds: None uses the
        backend's default, 0 and anything above the workspace's maximum use that maximum."""
        limit = self._timeout if timeout is None else self._limit(timeout)
        try:
            result = self._sandbox.commands.run(
                command, cwd=self._workdir, timeout_seconds=limit
            )
        except ConfigurationError:
            raise
        except SandboxHibernatedError:
            return ExecuteResponse(output=self._hibernated("running commands"), exit_code=1)
        except CommandIncompleteError as error:
            partial = _combine(error.stdout, error.stderr)
            return ExecuteResponse(output=_line(partial, _INCOMPLETE), exit_code=None)
        except CommandFailedError as error:
            partial = _combine(error.stdout, error.stderr)
            text = f"Error executing command (CommandFailedError): {error}"
            return ExecuteResponse(output=_line(partial, text), exit_code=1)
        except SandboxError as error:
            text = f"Error executing command ({type(error).__name__}): {_describe(error)}"
            return ExecuteResponse(output=text, exit_code=1)
        output = _line(_combine(result.stdout, result.stderr), ending_note(result, limit))
        return ExecuteResponse(
            output=output, exit_code=shell_exit_code(result), truncated=result.truncated
        )

    def upload_files(self, files: List[Tuple[str, bytes]]) -> List[FileUploadResponse]:
        """Upload each file once, in order, creating its folder first. A failure is reported
        on that file (``invalid_path``, ``file_not_found``, ``permission_denied``,
        ``is_directory``, ``file_too_large`` or ``"{code}: {message}"``) and the others still
        upload. Only paths under ``/workspace`` can be uploaded (the files API's root)."""
        return [FileUploadResponse(path=path, error=self._upload(path, data)) for path, data in files]

    def download_files(self, paths: List[str]) -> List[FileDownloadResponse]:
        """Download each file once, in order. A failure is reported on that path
        (``invalid_path``, ``file_not_found``, ``is_directory``, ``permission_denied`` or
        ``"{code}: {message}"``) and the others still download. Only paths under
        ``/workspace`` can be downloaded (the files API's root)."""
        return [self._download(path) for path in paths]

    def _upload(self, path: str, data: bytes) -> Optional[str]:
        where = _files_path(path)
        if where is None or where == ".":
            return _outside(path, where)
        try:
            self._make_parents(posixpath.dirname(where))
            self._sandbox.files.upload(where, bytes(data))
        except ConfigurationError as error:
            if error.code == "invalid_path_param":
                return "invalid_path"
            raise
        except SandboxError as error:
            return self._file_error(error)
        return None

    def _make_parents(self, folder: str) -> None:
        """Make sure ``folder`` (relative to ``/workspace``) exists. A folder that already exists
        answers 409 and counts as made; a 409 that means something else is left for the upload
        to report. A 404 means a folder above it is missing and nothing was created, so the
        folders are then made from the top down, each existing one answering 409 (``folder``
        itself is asked a second time)."""
        if not folder:
            return
        try:
            self._sandbox.files.make_dir(folder)
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
                self._sandbox.files.make_dir("/".join(parts[:depth]))
            except SandboxHibernatedError:
                raise
            except ConflictError:
                continue

    def _download(self, path: str) -> FileDownloadResponse:
        where = _files_path(path)
        if where is None or where == ".":
            return FileDownloadResponse(path=path, error=_outside(path, where))
        try:
            return FileDownloadResponse(path=path, content=self._sandbox.files.download(where))
        except ConfigurationError as error:
            if error.code == "invalid_path_param":
                return FileDownloadResponse(path=path, error="invalid_path")
            raise
        except SandboxError as error:
            failure = self._file_error(error)
            if failure == "invalid_path" and self._is_folder(where):
                failure = "is_directory"
            return FileDownloadResponse(path=path, error=failure)

    def _is_folder(self, where: str) -> bool:
        """One listing of the parent folder, for a refusal that does not say the path is a
        folder: True when it holds a folder of that name."""
        parent, name = posixpath.split(where)
        try:
            entries = self._sandbox.files.list(parent or ".")
        except ConfigurationError:
            raise
        except SandboxError:
            return False
        return any(
            isinstance(entry, Mapping) and entry.get("name") == name and entry.get("directory") is True
            for entry in entries
        )

    def _file_error(self, error: SandboxError) -> str:
        reasons = _reasons(error)
        if isinstance(error, SandboxHibernatedError):
            return self._hibernated("using its files")
        if isinstance(error, NotFoundError):
            return "file_not_found"
        if isinstance(error, PermissionDeniedError):
            return "permission_denied"
        if isinstance(error, PayloadTooLargeError):
            return "file_too_large"
        if isinstance(error, (ValidationError, ConflictError)):
            text = str(error).lower()
            if reasons & _NOT_WRITABLE_REASONS or any(t in text for t in _NOT_WRITABLE_TEXT):
                return "permission_denied"
        if isinstance(error, ValidationError):
            return "is_directory" if "wrong_type" in reasons else "invalid_path"
        return _describe(error)

    def _hibernated(self, doing: str) -> str:
        return (
            f"Error: sandbox {self.id} is hibernated; resume it (sbx.resume()) before {doing}"
        )


def _exec_maximum(sandbox: Sandbox) -> int:
    """The workspace's exec time limit (``caps.exec.maxTimeoutSeconds`` of its sandbox settings);
    an operator sets it, so it is read, never assumed. It is read with the handle's own client and
    credentials: ``Sandbox.settings()`` would read them from the environment instead."""
    # TODO: call a public per-handle accessor for the workspace's sandbox settings once the
    # Python SDK has one; until then this reads the handle's private Sandboxes resource, and
    # ``max_timeout=`` avoids the read altogether.
    raw: Any = sandbox._sandboxes.settings.get()
    caps = raw.get("caps") if isinstance(raw, Mapping) else None
    limits = caps.get("exec") if isinstance(caps, Mapping) else None
    value = limits.get("maxTimeoutSeconds") if isinstance(limits, Mapping) else None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfigurationError(
            "sandboxes.settings.get: the settings carry no caps.exec.maxTimeoutSeconds, so the "
            "exec time limit is unknown",
            code="missing_exec_limit",
            operation="sandboxes.settings.get",
        )
    return value


def _given(max_timeout: Any) -> int:
    """``max_timeout=`` as given: a whole number of seconds, 1 or more."""
    if isinstance(max_timeout, bool) or not isinstance(max_timeout, int) or max_timeout < 1:
        raise ValueError(
            f"max_timeout must be the workspace's exec maximum in whole seconds (1 or more), "
            f"not {max_timeout!r}"
        )
    return max_timeout


def _require_python3(sandbox: Sandbox, workdir: str, limit: int) -> None:
    result = sandbox.commands.run("command -v python3", cwd=workdir, timeout_seconds=limit)
    if shell_exit_code(result) == 0:
        return
    note = ending_note(result, limit)
    why = f"the check for python3 did not finish ({note})" if note else "python3 is not on its PATH"
    raise ConfigurationError(
        f"sandbox {sandbox.id} cannot back a Deep Agents agent: {why}. Deep Agents runs python3 "
        "inside the sandbox for ls, read_file, edit_file and glob; every catalog template ships "
        "it, so create the sandbox from a template or from an image that has python3.",
        code="python3_missing",
        operation="sandboxes.commands.run",
    )


def _files_path(path: str) -> Optional[str]:
    """``path`` as the files API takes it: relative to ``/workspace`` (``"."`` for the folder
    itself). None for a relative path or one outside ``/workspace``."""
    if not path.startswith("/"):
        return None
    full = posixpath.normpath(path)
    if full == FILES_ROOT:
        return "."
    if full.startswith(FILES_ROOT + "/"):
        return full[len(FILES_ROOT) + 1 :]
    return None


def _outside(path: str, where: Optional[str]) -> str:
    """The error for a path the files API cannot reach."""
    if where == ".":
        return "is_directory"
    if not path.startswith("/"):
        return "invalid_path"
    return "permission_denied"


def _combine(stdout: str, stderr: str) -> str:
    """stdout, then stderr tagged so the model can tell the two apart."""
    output = stdout or ""
    if stderr:
        output += f"\n<stderr>{stderr}</stderr>"
    return output


def _line(output: str, note: Optional[str]) -> str:
    """``note`` on its own line after ``output``."""
    if not note:
        return output
    if not output:
        return note
    return output + ("" if output.endswith("\n") else "\n") + note


def _reasons(error: SandboxError) -> frozenset:
    found = {error.code}
    if isinstance(error.detail, Mapping):
        found.add(error.detail.get("reason"))
        found.add(error.detail.get("code"))
    return frozenset(str(item).lower() for item in found if isinstance(item, str))


def _describe(error: SandboxError) -> str:
    text = str(error)
    code = error.code or error.get_error_code()
    return text if text.startswith(f"{code}:") else f"{code}: {text}"


__all__ = [
    "CHECK_TIMEOUT_S",
    "DEFAULT_TIMEOUT_S",
    "DEFAULT_WORKDIR",
    "FILES_ROOT",
    "FutureAGISandbox",
]
