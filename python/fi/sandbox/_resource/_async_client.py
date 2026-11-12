"""``client.sandboxes`` (async): one method per sandbox operation, named by its ``x-omega-sdk``
(snake_case per dotted segment: ``get_info``, ``network_policy.update``, ``files.make_dir``,
``activity.list``, ``commands.run``). Sandbox settings are read-only here: they are changed in the
Console, from an owner's or admin's signed-in session.

Each method calls the platform executor by SDK name (the generated ``OPERATIONS`` table holds the
paths) and returns the server's JSON; ``create``, ``connect`` and ``snapshots.restore`` return an
``AsyncSandbox``, ``commands.run`` an ``AsyncCommandStream`` and ``files.download`` bytes. Nothing
that changes a sandbox is retried (``retries=0``); ``kill`` keeps the transport's retries, and a
404 on a retry counts as done. Every call first passes ``fi.sandbox._connection.OriginRule``.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, AsyncIterator, Optional, Union

import httpx

from fi._core.raw import AsyncNamespace
from fi._core.transport import MAX_ERROR_BODY
from fi.generated.platform import types as T

from .._connection import OriginRule, http_of, sandbox_core
from .._wire import NO_RETRY, DownloadBudget, UploadBody, etag, payload, sandbox_record
from ..errors import CORE_ERRORS, stream_failure, translate
from ._stream._async_client import AsyncCommandStream

if TYPE_CHECKING:
    from .._async_client import AsyncSandbox


class _Part(AsyncNamespace):
    def __init__(self, core: Any, *, rule: Optional[OriginRule] = None) -> None:
        super().__init__(sandbox_core(core))
        self._rule = rule or OriginRule()

    def _part(self, cls: Any) -> Any:
        return cls(self._core, rule=self._rule)

    def _refusal(self, name: str) -> Optional[BaseException]:
        """Why this call must not be sent (origin settings, plain HTTP, a foreign self-host)."""
        try:
            origin = self._core.shared.origin()
        except CORE_ERRORS as error:
            return translate(error, name, self._rule.setting)
        return self._rule.problem(origin)

    async def _call(self, name: str, **kw: Any) -> Any:
        failure = self._refusal(name)
        if failure is None:
            try:
                return await self._core.call(name, **kw)
            except CORE_ERRORS as error:
                failure = translate(error, name, self._rule.setting)
        raise failure  # outside the except block: the error chains nothing

    def _handle(self, raw: Any, operation: str) -> AsyncSandbox:
        from .._async_client import AsyncSandbox

        sandboxes = AsyncSandboxes(self._core, rule=self._rule)
        return AsyncSandbox(sandboxes, sandbox_record(raw, operation))


class AsyncSandboxSettings(_Part):
    """``client.sandboxes.settings``: the workspace's sandbox settings (read-only)."""

    async def get(self) -> T.GetWorkspaceSandboxSettingsResponse:
        """Templates, images, sizes, caps and the operator's limits. They are changed in
        the Console, from an owner's or admin's signed-in session; the SDK never
        changes them."""
        return await self._call("sandboxes.settings.get")


class AsyncSandboxFiles(_Part):
    """``client.sandboxes.files``: files and folders inside a sandbox."""

    async def list(
        self, sandbox_id: str, *, path: Optional[str] = None
    ) -> T.ListWorkspaceSandboxFilesResponse:
        """The entries of one folder (``path`` relative to the workspace, default its root)."""
        return await self._call(
            "sandboxes.files.list", path={"id": sandbox_id}, query={"path": path}
        )

    async def read(
        self, sandbox_id: str, path: str, *, max_bytes: Optional[int] = None
    ) -> T.ReadWorkspaceSandboxFileResponse:
        """A bounded read: ``file.content`` in ``file.encoding`` (utf8 or base64)."""
        return await self._call(
            "sandboxes.files.read",
            path={"id": sandbox_id, "path": path},
            query={"maxBytes": max_bytes},
        )

    async def write(
        self, sandbox_id: str, path: str, *, body: T.WriteWorkspaceSandboxFileRequest
    ) -> T.WriteWorkspaceSandboxFileResponse:
        """Write a small text or base64 file (audited). Sent once, never retried."""
        return await self._call(
            "sandboxes.files.write",
            path={"id": sandbox_id, "path": path},
            body=dict(body),
            retries=NO_RETRY,
        )

    async def remove(
        self, sandbox_id: str, path: str, *, recursive: Optional[bool] = None
    ) -> T.DeleteWorkspaceSandboxPathResponse:
        """Delete a file, or a folder with ``recursive=True``. Sent once, never retried."""
        return await self._call(
            "sandboxes.files.remove",
            path={"id": sandbox_id, "path": path},
            query={"recursive": recursive},
            retries=NO_RETRY,
        )

    async def download(self, sandbox_id: str, path: str) -> bytes:
        """A file's raw bytes, at most 64 MiB (a larger file raises ``PayloadTooLargeError``)."""
        return b"".join([chunk async for chunk in self._stream(sandbox_id, path, None)])

    async def upload(
        self, sandbox_id: str, path: str, *, body: UploadBody
    ) -> T.UploadWorkspaceSandboxFileResponse:
        """Upload raw bytes (bytes, str, a path or a binary file; at most 64 MiB, read into
        memory first). The folder must exist. Never retried."""
        return await self._call(
            "sandboxes.files.upload",
            path={"id": sandbox_id, "path": path},
            body=payload(body),
            retries=NO_RETRY,
        )

    async def rename(
        self, sandbox_id: str, *, body: T.MoveWorkspaceSandboxPathRequest
    ) -> T.MoveWorkspaceSandboxPathResponse:
        """Move or rename a file or folder (``{"from", "to"}``). Never retried."""
        return await self._call(
            "sandboxes.files.rename",
            path={"id": sandbox_id},
            body=dict(body),
            retries=NO_RETRY,
        )

    async def make_dir(
        self, sandbox_id: str, path: str
    ) -> T.CreateWorkspaceSandboxFolderResponse:
        """Create a folder (and its parents). Sent once, never retried."""
        return await self._call(
            "sandboxes.files.makeDir",
            path={"id": sandbox_id, "path": path},
            retries=NO_RETRY,
        )

    async def _stream(self, sandbox_id: str, path: str, max_bytes: Any) -> AsyncIterator[bytes]:
        """The file's bytes as they arrive, never more than ``max_bytes`` (None: 64 MiB; the
        executor has no binary call, so this sends the prepared request itself with the
        executor's own error mapping)."""
        name, core, setting = "sandboxes.files.download", self._core, self._rule.setting
        budget = DownloadBudget(max_bytes)
        failure = self._refusal(name)
        http = http_of(core)
        if failure is None:
            try:
                prep = core._prepare(
                    http,
                    name,
                    path={"id": sandbox_id, "path": path},
                    query=None,
                    body=None,
                    key=None,
                    headers=None,
                    timeout=None,
                    retries=None,
                    stream=False,
                    idle=None,
                )
            except CORE_ERRORS as error:
                failure = translate(error, name, setting)
        if failure is not None:
            raise failure
        prep.request.headers["Accept"] = "application/octet-stream"
        prep.request.headers["Accept-Encoding"] = "identity"  # an encoded answer is refused unread
        try:
            response = await http.send(
                prep.request, stream=True, auth=None, follow_redirects=False
            )
        except httpx.TransportError as error:
            failure = translate(core._no_response(prep, error), name, setting)
        if failure is not None:
            raise failure
        try:
            if not response.is_success:
                failure = await self._refused(prep, response)
            else:
                core._meta(prep, response, 0)
                budget.start(response, core, name, prep.request)
                async for chunk in response.aiter_bytes():
                    yield budget.take(chunk)
        except httpx.HTTPError as error:
            raise stream_failure(name, error) from None
        finally:
            await response.aclose()
        if failure is not None:
            raise failure

    async def _refused(self, prep: Any, response: httpx.Response) -> BaseException:
        """The sandbox error for a download that answered with an error status."""
        core, chunks = self._core, []
        complete = not response.is_redirect
        if complete:
            async for chunk in response.aiter_bytes():
                chunks.append(chunk)
                if sum(len(c) for c in chunks) >= MAX_ERROR_BODY:
                    complete = False
                    break
        if response.is_redirect:
            failure: Any = core._redirect(prep, response)
        else:
            raw = b"".join(chunks)
            failure = core._status_error(prep, response, raw, complete=complete)
        return translate(failure, prep.op.name)


class AsyncSandboxSnapshots(_Part):
    """``client.sandboxes.snapshots``: file snapshots and restores."""

    async def list(self, sandbox_id: str) -> T.ListWorkspaceSandboxSnapshotsResponse:
        """The sandbox's snapshots."""
        return await self._call("sandboxes.snapshots.list", path={"id": sandbox_id})

    async def create(self, sandbox_id: str) -> T.SnapshotWorkspaceSandboxResponse:
        """Snapshot the sandbox's files. Sent once, never retried."""
        return await self._call(
            "sandboxes.snapshots.create", path={"id": sandbox_id}, retries=NO_RETRY
        )

    async def restore(
        self,
        sandbox_id: str,
        snapshot_id: str,
        *,
        body: Optional[T.RestoreWorkspaceSandboxSnapshotRequest] = None,
    ) -> AsyncSandbox:
        """A NEW sandbox from the snapshot; the source sandbox is unchanged. Never retried."""
        raw = await self._call(
            "sandboxes.snapshots.restore",
            path={"id": sandbox_id, "snapshotId": snapshot_id},
            body=dict(body or {}),
            retries=NO_RETRY,
        )
        return self._handle(raw, "sandboxes.snapshots.restore")


class AsyncSandboxNetworkPolicy(_Part):
    """``client.sandboxes.network_policy`` (on deployments whose sandboxes have network access)."""

    async def get(self, sandbox_id: str) -> T.GetWorkspaceSandboxNetworkPolicyResponse:
        """The desired and applied policy. The response's ``ETag`` header (read it with
        ``with_raw_response``) is the next ``if_match``."""
        return await self._call("sandboxes.networkPolicy.get", path={"id": sandbox_id})

    async def update(
        self,
        sandbox_id: str,
        *,
        body: T.PutWorkspaceSandboxNetworkPolicyRequest,
        if_match: Union[str, int],
    ) -> T.PutWorkspaceSandboxNetworkPolicyResponse:
        """Replace the whole policy, guarded by ``if_match`` (the ETag read last; an int is
        quoted for you). A stale one is a 412 ``ConflictError``
        (``network_policy_revision_mismatch``). Sent once, never retried."""
        return await self._call(
            "sandboxes.networkPolicy.update",
            path={"id": sandbox_id},
            body=dict(body),
            headers={"If-Match": etag(if_match)},
            retries=NO_RETRY,
        )


class AsyncSandboxActivity(_Part):
    """``client.sandboxes.activity``."""

    async def list(self, sandbox_id: str) -> T.ListWorkspaceSandboxActivityResponse:
        """The sandbox's audited activity, newest first."""
        return await self._call("sandboxes.activity.list", path={"id": sandbox_id})


class AsyncSandboxCommands(_Part):
    """``client.sandboxes.commands``: run a command (a stream of frames) and cancel one."""

    def run(
        self, sandbox_id: str, *, body: T.ExecInWorkspaceSandboxRequest
    ) -> AsyncCommandStream:
        """Run a command: its typed frames (``AsyncCommandStream``), sent when iterated. Never
        retried: another stream is another command."""
        return AsyncCommandStream(
            self._core, sandbox_id, body, self._refusal, self._rule.setting
        )

    async def cancel(
        self, sandbox_id: str, exec_id: str
    ) -> T.CancelWorkspaceSandboxExecResponse:
        """Cancel a running command by its ``exec_id``."""
        return await self._call(
            "sandboxes.commands.cancel", path={"id": sandbox_id, "execId": exec_id}
        )


class AsyncSandboxes(_Part):
    """``client.sandboxes`` (async): the generated layer under ``AsyncSandbox``."""

    @cached_property
    def settings(self) -> AsyncSandboxSettings:
        return self._part(AsyncSandboxSettings)

    @cached_property
    def files(self) -> AsyncSandboxFiles:
        return self._part(AsyncSandboxFiles)

    @cached_property
    def snapshots(self) -> AsyncSandboxSnapshots:
        return self._part(AsyncSandboxSnapshots)

    @cached_property
    def network_policy(self) -> AsyncSandboxNetworkPolicy:
        return self._part(AsyncSandboxNetworkPolicy)

    @cached_property
    def activity(self) -> AsyncSandboxActivity:
        return self._part(AsyncSandboxActivity)

    @cached_property
    def commands(self) -> AsyncSandboxCommands:
        return self._part(AsyncSandboxCommands)

    async def list(self) -> T.ListWorkspaceSandboxesResponse:
        """The workspace's sandboxes and its caps (one page)."""
        return await self._call("sandboxes.list")

    async def create(
        self, *, body: Optional[T.CreateWorkspaceSandboxRequest] = None
    ) -> AsyncSandbox:
        """Create a sandbox (every field optional) and return its handle. Never retried."""
        fields = dict(body or {})
        raw = await self._call("sandboxes.create", body=fields, retries=NO_RETRY)
        return self._handle(raw, "sandboxes.create")

    async def connect(self, sandbox_id: str) -> AsyncSandbox:
        """A handle on an existing sandbox (its ``info`` is the record just read)."""
        raw = await self.get_info(sandbox_id)
        return self._handle(raw, "sandboxes.getInfo")

    async def get_info(self, sandbox_id: str) -> T.GetWorkspaceSandboxResponse:
        """The sandbox's record (``connect`` returns a handle on it instead)."""
        return await self._call("sandboxes.getInfo", path={"id": sandbox_id})

    async def update(
        self, sandbox_id: str, *, body: T.UpdateWorkspaceSandboxRequest
    ) -> T.UpdateWorkspaceSandboxResponse:
        """Rename it or change its idle TTL."""
        path = {"id": sandbox_id}
        return await self._call("sandboxes.update", path=path, body=dict(body))

    async def kill(
        self,
        sandbox_id: str,
    ) -> Optional[T.DestroyWorkspaceSandboxResponse]:
        """Destroy the sandbox and its disk. None when a retry found it already gone."""
        return await self._call("sandboxes.kill", path={"id": sandbox_id})

    async def hibernate(self, sandbox_id: str) -> T.HibernateWorkspaceSandboxResponse:
        """Stop its container and keep its disk. Never retried."""
        return await self._call(
            "sandboxes.hibernate", path={"id": sandbox_id}, retries=NO_RETRY
        )

    async def resume(self, sandbox_id: str) -> T.ResumeWorkspaceSandboxResponse:
        """Start a hibernated sandbox again. Never retried."""
        path = {"id": sandbox_id}
        return await self._call("sandboxes.resume", path=path, retries=NO_RETRY)


__all__ = [
    "AsyncSandboxes",
    "AsyncSandboxSettings",
    "AsyncSandboxFiles",
    "AsyncSandboxSnapshots",
    "AsyncSandboxNetworkPolicy",
    "AsyncSandboxActivity",
    "AsyncSandboxCommands",
    "AsyncCommandStream",
]
