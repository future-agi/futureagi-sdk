"""The sandbox tools an MCP server offers, with no MCP import: plain coroutines over ``AsyncSandboxes``.

:class:`SandboxTools` holds one ``client.sandboxes`` (async), a handle per sandbox id it has used, and the
ids it created (``created``), which :meth:`SandboxTools.cleanup` deletes when the server stops. Every
method returns a JSON-ready ``dict``. A refusal, or a sandbox error, is raised as :class:`SandboxToolError`
whose text is ``code: message`` plus what to do next; the key never appears in it (the handle's errors
are scrubbed, and nothing here reads a credential). :meth:`SandboxTools.cleanup` sends its deletes
together, since a client gives a stopping server only a short grace period.

No method re-sends anything: not create, exec, write or delete. Reads add no retry of their own either.
Cancelling the coroutine of a running ``sandbox_exec`` leaves the command's stream, which cancels the
command. Pinned mode (``pinned=ID``) serves one sandbox: the file and exec tools default to it and refuse
any other id, and listing, creating and deleting are refused.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import posixpath
import re
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Set, Tuple

from fi.errors import FutureAGIError

if TYPE_CHECKING:
    from fi.sandbox import AsyncSandbox, AsyncSandboxes

DEFAULT_MAX_OUTPUT_CHARS = 20_000
#: A sandbox name is 1 to 120 bytes of printable UTF-8 text.
MAX_NAME_BYTES = 120
#: The shortest time limit the API takes, in seconds.
MIN_TIMEOUT_SECONDS = 1
#: The command a message suggests for things only a person can do (the console script's name today).
CLI = "futureagi-py sandbox"
#: The sandbox's writable folder; a command's folder is given relative to it.
WORKSPACE = "/workspace"

_CAPS_FIELDS = ("maxActiveSandboxes", "defaultTemplate", "defaultSize", "idleTtlSeconds")
_EXEC_CAPS = ("defaultTimeoutSeconds", "maxTimeoutSeconds", "maxOutputBytes")


class SandboxToolError(Exception):
    """A tool call that did not work: ``code: message`` and the next step, safe to show a model."""

    def __init__(self, text: str, *, code: str) -> None:
        super().__init__(text)
        self.code = code


def _refuse(code: str, message: str) -> SandboxToolError:
    return SandboxToolError(f"{code}: {message}", code=code)


def _code(error: BaseException) -> str:
    """The error's code; a refused files path outside ``/workspace`` is ``outside_workspace`` (any
    other refused path stays ``invalid_path``)."""
    code = getattr(error, "code", None)
    if code == "invalid_path" and _reason(error) == "outside_workspace":
        return "outside_workspace"
    if isinstance(code, str) and code:
        return code
    get = getattr(error, "get_error_code", None)
    return get().lower() if callable(get) else type(error).__name__


def _said(error: BaseException) -> str:
    """The server's words without the SDK's ``<operation> failed with status N (code):`` prefix."""
    text = str(error)
    found = re.match(r"[\w.]+ failed with status (\d+) \([^)]*\)(?:: )?", text)
    if found:
        text = text[found.end():] or f"refused with status {found.group(1)}"
    return text.rstrip(". ")


def _reason(error: BaseException) -> Optional[str]:
    detail = getattr(error, "detail", None)
    reason = detail.get("reason") if isinstance(detail, Mapping) else None
    return reason if isinstance(reason, str) else None


def _next_step(error: BaseException, code: str, tool: str, sandbox_id: Optional[str]) -> str:
    from fi import sandbox as sb

    if code == "outside_workspace":
        return (". The file tools reach only /workspace: for a file elsewhere, run a command with "
                "sandbox_exec (for example cat /tmp/notes.txt)")
    if code == "invalid_path":  # the message names what is wrong with the path; no next step
        return ""
    if isinstance(error, sb.ConfigurationError):
        return (". This is a setup problem of the server, so trying again will not help: fix its "
                "environment (OMEGA_BASE_URL and the credentials) and restart it")
    if isinstance(error, sb.QuotaExceededError):
        return (". The workspace is at its limit of active sandboxes: delete a sandbox you no longer "
                "need (sandbox_list shows them) or ask an admin to raise the limit")
    if isinstance(error, sb.SandboxHibernatedError):
        where = sandbox_id or "SANDBOX_ID"
        return (f". The sandbox is hibernated and nothing here resumes it: ask the user to run "
                f"{CLI} resume {where}, then try again")
    if isinstance(error, sb.ConnectionError) and tool == "sandbox_create":
        return (". Whether the sandbox was created is unknown: call sandbox_list before creating "
                "another (a sandbox made this way is not deleted when the server stops)")
    if isinstance(error, sb.CommandIncompleteError):
        return (". It was not run again: look at the sandbox's files (sandbox_list_files) before "
                "running it again")
    if isinstance(error, sb.RateLimitError):
        wait = error.retry_after_seconds
        return f". Try again in {wait:g} s" if wait is not None else ". Try again shortly"
    if isinstance(error, sb.ValidationError) and "wrong_type" in (code, _reason(error)):
        if tool == "sandbox_read_file":
            return ". The path is a folder, not a file: use sandbox_list_files to see what is in it"
        return ". The path is not the kind this tool expects (a file or a folder)"
    if isinstance(error, sb.NotFoundError):
        if tool in ("sandbox_read_file", "sandbox_write_file", "sandbox_list_files"):
            return ". Check the path (sandbox_list_files) and the sandbox id (sandbox_list)"
        return ". No such sandbox in this workspace: sandbox_list shows yours"
    if isinstance(error, sb.InsufficientStorageError):
        return ". Free some space: delete files or sandboxes you no longer need"
    return ""


def describe(error: BaseException, *, tool: str, sandbox_id: Optional[str] = None) -> SandboxToolError:
    """The tool error for a sandbox error: ``code: message`` and one next step."""
    code = _code(error)
    return SandboxToolError(f"{code}: {_said(error)}{_next_step(error, code, tool, sandbox_id)}", code=code)


def _clip(text: str, limit: int) -> Tuple[str, bool]:
    """The last ``limit`` characters, after a line that says how many came before them."""
    if len(text) <= limit:
        return text, False
    dropped = len(text) - limit
    return f"[... {dropped} earlier characters dropped ...]\n" + text[-limit:], True


def _trim_caps(caps: Any) -> Dict[str, Any]:
    """The workspace limits a model needs to choose a template, a size and a time limit."""
    caps = caps if isinstance(caps, dict) else {}
    out: Dict[str, Any] = {key: caps[key] for key in _CAPS_FIELDS if key in caps}
    for key in ("templates", "sizes"):
        items = caps.get(key)
        if isinstance(items, list):
            out[key] = [
                {field: item[field] for field in ("id", "name", "available") if field in item}
                for item in items if isinstance(item, dict)
            ]
    exec_caps = caps.get("exec")
    if isinstance(exec_caps, dict):
        out["exec"] = {key: exec_caps[key] for key in _EXEC_CAPS if key in exec_caps}
    return out


def _whole_number(value: Any) -> Optional[int]:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _exec_cwd(cwd: Optional[str]) -> Optional[str]:
    """A command's folder as the exec API takes it: relative to ``/workspace``, None for ``/workspace``
    itself (or no folder). The API refuses an absolute folder, so ``/workspace/src`` is sent as ``src``.
    A folder outside ``/workspace``, or one that leaves it through ``..``, is refused before any request."""
    if cwd is None:
        return None
    joined = cwd if cwd.startswith("/") else f"{WORKSPACE}/{cwd}"
    full = posixpath.normpath("/" + joined.lstrip("/"))
    if full == WORKSPACE:
        return None
    if full.startswith(WORKSPACE + "/"):
        return full[len(WORKSPACE) + 1:]
    raise _refuse("invalid_cwd", f"cwd {cwd!r} is outside {WORKSPACE}: commands run in {WORKSPACE} or a "
                                 f"folder under it. Give cwd relative to {WORKSPACE} (for example src), or "
                                 "change folder inside the command (cd /tmp && ...)")


class SandboxTools:
    """The sandbox tools, over ``client.sandboxes`` (async). ``created`` holds the ids this object
    created and has not deleted; ``cleanup_failures`` the ``(id, text)`` of each delete that
    :meth:`cleanup` could not do."""

    def __init__(
        self,
        sandboxes: AsyncSandboxes,
        *,
        pinned: Optional[str] = None,
        max_output_chars: int = DEFAULT_MAX_OUTPUT_CHARS,
    ) -> None:
        if _whole_number(max_output_chars) is None or max_output_chars < 1:
            raise ValueError("max_output_chars must be a whole number above 0")
        self._api = sandboxes
        self.pinned = pinned or None
        self.max_output_chars = max_output_chars
        self.created: Set[str] = set()
        self.cleanup_failures: List[Tuple[str, str]] = []
        self._handles: Dict[str, AsyncSandbox] = {}
        self._caps: Optional[Dict[str, Any]] = None

    # -- which sandbox ------------------------------------------------------------------------

    def _unpinned(self, tool: str) -> None:
        if self.pinned is not None:
            raise _refuse("pinned", f"this server serves only sandbox {self.pinned}, so {tool} is "
                                    "not offered")

    def _target(self, sandbox_id: Optional[str]) -> str:
        if self.pinned is not None:
            if sandbox_id and sandbox_id != self.pinned:
                raise _refuse("pinned", f"this server serves only sandbox {self.pinned}; it does not "
                                        f"use {sandbox_id}. Leave sandbox_id out")
            return self.pinned
        if not sandbox_id:
            raise _refuse("missing_sandbox_id", "give sandbox_id: sandbox_create makes a sandbox and "
                                                "sandbox_list shows yours")
        return sandbox_id

    async def _sandbox(self, sandbox_id: str) -> AsyncSandbox:
        handle = self._handles.get(sandbox_id)
        if handle is None:
            handle = await self._api.connect(sandbox_id)
            self._handles[sandbox_id] = handle
        return handle

    async def _exec_limit(self) -> Optional[int]:
        """The workspace's longest exec time limit (``caps.exec.maxTimeoutSeconds``), read once."""
        if self._caps is None:
            raw = await self._api.list()
            self._caps = dict(raw.get("caps") or {})
        exec_caps = self._caps.get("exec")
        limit = _whole_number(exec_caps.get("maxTimeoutSeconds")) if isinstance(exec_caps, dict) else None
        return limit if limit is not None and limit >= MIN_TIMEOUT_SECONDS else None

    # -- the tools ----------------------------------------------------------------------------

    async def sandbox_list(self) -> Dict[str, Any]:
        """The workspace's sandboxes and its sandbox limits."""
        self._unpinned("sandbox_list")
        try:
            raw = await self._api.list()
        except FutureAGIError as error:
            raise _wrapped(error, "sandbox_list") from error
        self._caps = dict(raw.get("caps") or {})
        rows = [
            {key: row.get(key) for key in ("id", "name", "state", "template", "size", "lastActivityAt")}
            for row in raw.get("sandboxes") or [] if isinstance(row, dict)
        ]
        return {"sandboxes": rows, "caps": _trim_caps(self._caps)}

    async def sandbox_create(
        self,
        name: Optional[str] = None,
        template: Optional[str] = None,
        size: Optional[str] = None,
        idle_ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a sandbox; its id joins ``created``."""
        self._unpinned("sandbox_create")
        if name is not None:
            if not name.strip() or not name.isprintable():
                raise _refuse("invalid_name", "a sandbox name is printable text and not blank")
            if len(name.encode("utf-8")) > MAX_NAME_BYTES:
                raise _refuse("invalid_name", f"a sandbox name is at most {MAX_NAME_BYTES} bytes of "
                                              "UTF-8 text; use a shorter one")
        fields = {"name": name, "template": template, "size": size, "idleTtlSeconds": idle_ttl_seconds}
        body = {key: value for key, value in fields.items() if value is not None}
        try:
            sbx = await self._api.create(body=body)
        except FutureAGIError as error:
            raise _wrapped(error, "sandbox_create") from error
        self.created.add(sbx.id)
        self._handles[sbx.id] = sbx
        info = sbx.info
        return {"id": sbx.id, **{key: info.get(key) for key in ("name", "state", "template", "size")}}

    async def sandbox_exec(
        self,
        command: str,
        sandbox_id: Optional[str] = None,
        cwd: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run ``command`` to its end; the whole exit record, with each output's last characters.
        ``cwd`` is relative to ``/workspace``; an absolute folder under it is sent in that form."""
        target = self._target(sandbox_id)
        folder = _exec_cwd(cwd)
        try:
            if timeout_seconds is not None:
                timeout_seconds = max(MIN_TIMEOUT_SECONDS, int(timeout_seconds))
                limit = await self._exec_limit()
                if limit is not None:
                    timeout_seconds = min(timeout_seconds, limit)
            sbx = await self._sandbox(target)
            result = await sbx.commands.run(command, cwd=folder, timeout_seconds=timeout_seconds)
        except FutureAGIError as error:
            raise _wrapped(error, "sandbox_exec", target) from error
        stdout, stdout_clipped = _clip(result.stdout, self.max_output_chars)
        stderr, stderr_clipped = _clip(result.stderr, self.max_output_chars)
        return {
            "exit_code": result.exit_code,
            "signal": result.signal,
            "timed_out": result.timed_out,
            "cancelled": result.cancelled,
            "truncated": result.truncated,
            "duration_ms": result.duration_ms,
            "error": result.error,
            "exec_id": result.exec_id,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_clipped": stdout_clipped,
            "stderr_clipped": stderr_clipped,
        }

    async def sandbox_read_file(
        self, path: str, sandbox_id: Optional[str] = None, max_bytes: Optional[int] = None
    ) -> Dict[str, Any]:
        """A file: UTF-8 text as it is, anything else as base64; ``truncated`` when cut at the limit.
        ``path`` is relative to ``/workspace``; an absolute path under it is sent in that form. A
        path outside it is refused before any request with ``outside_workspace``, and one with a
        ``.`` or ``..`` segment (never folded), a backslash or a control character with
        ``invalid_path``."""
        from fi.sandbox._wire import files_path

        target = self._target(sandbox_id)
        try:
            where = files_path(path, "sandboxes.files.read")
            await self._sandbox(target)
            raw = await self._api.files.read(target, where, max_bytes=max_bytes)
        except FutureAGIError as error:
            raise _wrapped(error, "sandbox_read_file", target) from error
        file = raw.get("file") or {}
        return {
            "path": file.get("path", path),
            "encoding": file.get("encoding", "utf8"),
            "content": file.get("content", ""),
            "bytes": file.get("bytes"),
            "truncated": bool(file.get("truncated")),
        }

    async def sandbox_write_file(
        self, path: str, content: str, sandbox_id: Optional[str] = None, encoding: str = "utf8"
    ) -> Dict[str, Any]:
        """Write a file (missing folders are created by the write itself). ``path`` follows
        :meth:`sandbox_read_file`'s rule."""
        from fi.sandbox._wire import files_path

        target = self._target(sandbox_id)
        data: Any = content
        if encoding == "base64":
            try:
                data = base64.b64decode(content, validate=True)
            except (binascii.Error, ValueError):
                raise _refuse("invalid_content", "content is not valid base64") from None
        elif encoding != "utf8":
            raise _refuse("invalid_encoding", "encoding is utf8 (text) or base64 (any bytes)")
        try:
            files_path(path, "sandboxes.files.write")  # a refused path costs no request
            sbx = await self._sandbox(target)
            raw = await sbx.files.write(path, data)
        except FutureAGIError as error:
            raise _wrapped(error, "sandbox_write_file", target) from error
        file = raw.get("file") or {}
        size = file.get("bytes")
        if size is None:
            size = len(data) if isinstance(data, bytes) else len(content.encode("utf-8"))
        return {"path": file.get("path", path), "bytes": size}

    async def sandbox_list_files(self, path: str = ".", sandbox_id: Optional[str] = None) -> Dict[str, Any]:
        """The entries of one folder (relative paths start at ``/workspace``, the sandbox's files;
        ``"."`` is that folder itself)."""
        from fi.sandbox._wire import files_path

        target = self._target(sandbox_id)
        try:
            files_path(path, "sandboxes.files.list", root=True)  # a refused path costs no request
            sbx = await self._sandbox(target)
            entries = await sbx.files.list(path)
        except FutureAGIError as error:
            raise _wrapped(error, "sandbox_list_files", target) from error
        rows = [
            {"name": entry.get("name"), "size": entry.get("size"),
             "directory": bool(entry.get("directory")), "mode": entry.get("mode")}
            for entry in entries if isinstance(entry, dict)
        ]
        return {"path": path, "entries": rows}

    async def sandbox_delete(self, sandbox_id: str) -> Dict[str, Any]:
        """Delete a sandbox and its files; one that is already gone is not an error."""
        self._unpinned("sandbox_delete")
        if not sandbox_id:
            raise _refuse("missing_sandbox_id", "give the sandbox_id to delete (sandbox_list shows yours)")
        try:
            record = await self._delete(sandbox_id)
        except FutureAGIError as error:
            raise _wrapped(error, "sandbox_delete", sandbox_id) from error
        return {"id": sandbox_id, "state": record.get("state", "destroyed")}

    async def _delete(self, sandbox_id: str) -> Dict[str, Any]:
        """Delete without reading first (the handle treats a 404 as already deleted)."""
        from fi.sandbox import AsyncSandbox

        handle = self._handles.get(sandbox_id) or AsyncSandbox(self._api, {"id": sandbox_id})
        record = await handle.delete()
        self._handles.pop(sandbox_id, None)
        self.created.discard(sandbox_id)
        return record

    async def cleanup(self) -> List[str]:
        """Delete every sandbox in ``created``, all at once; returns the ids deleted, in id order. A
        failed delete is kept in ``cleanup_failures`` as ``(id, "code: message")`` and does not stop
        the others."""
        ids = sorted(self.created)
        failures = await asyncio.gather(*(self._cleanup_one(sandbox_id) for sandbox_id in ids))
        deleted: List[str] = []
        for sandbox_id, failure in zip(ids, failures):
            if failure is None:
                deleted.append(sandbox_id)
            else:
                self.cleanup_failures.append((sandbox_id, failure))
        return deleted

    async def _cleanup_one(self, sandbox_id: str) -> Optional[str]:
        """Delete one created sandbox; ``None`` when done, else the text of what went wrong."""
        try:
            await self._delete(sandbox_id)
        except Exception as error:
            failure = _wrapped(error, "sandbox_delete", sandbox_id)
            return str(failure) if isinstance(failure, SandboxToolError) else f"{type(error).__name__}: {error}"
        return None


def _wrapped(error: Exception, tool: str, sandbox_id: Optional[str] = None) -> Exception:
    """A sandbox error as a :class:`SandboxToolError`; anything else unchanged (a bug, not a refusal)."""
    if isinstance(error, SandboxToolError):
        return error
    if isinstance(error, FutureAGIError):
        return describe(error, tool=tool, sandbox_id=sandbox_id)
    return error


__all__ = ["DEFAULT_MAX_OUTPUT_CHARS", "MAX_NAME_BYTES", "SandboxToolError", "SandboxTools", "describe"]
