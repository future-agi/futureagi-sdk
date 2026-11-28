"""The ``AsyncSandbox`` handle: one remote sandbox, backed by ``client.sandboxes`` (async).

    async with AsyncSandbox.create(name="scratch") as sbx:
        result = await sbx.commands.run("echo hello")
        print(result.exit_code, result.stdout)

``AsyncSandbox.create`` / ``connect`` / ``list`` / ``settings`` read the environment only
(``fi.sandbox._connection``). To pass keys, a base URL, a workspace or an organization in code,
build ``AsyncFutureAGIClient(...)`` and call ``client.sandboxes.create(...)`` /
``client.sandboxes.connect(id)``, which return this same handle.

Every method calls the generated layer (``fi.sandbox._resource``); none re-implements the wire.
Nothing that changes a sandbox is retried. The SDK does not resume a hibernated sandbox; the server may.
"""

from __future__ import annotations

import warnings
from typing import Any, Awaitable, Dict, List, Mapping, Optional

from . import _wire
from ._connection import ENVIRONMENT_RULE, AsyncSandboxConnection
from ._parts._async_client import (
    AsyncCommands,
    AsyncFiles,
    AsyncNetworkPolicy,
    AsyncSnapshots,
)
from ._resource._async_client import AsyncSandboxes
from ._wire import present, sandbox_record
from .errors import NotFoundError
from .types import SandboxList


def _default() -> AsyncSandboxes:
    """``client.sandboxes`` over a connection built from the environment alone."""
    core = AsyncSandboxConnection().core()
    return AsyncSandboxes(core, rule=ENVIRONMENT_RULE)


async def _owned(pending: Awaitable[AsyncSandbox]) -> AsyncSandbox:
    """The handle ``create`` / ``connect`` made; it closes the connection pool it opened."""
    sandbox = await pending
    sandbox._owns_pool = True
    return sandbox


class AsyncSandbox:
    """One remote sandbox: an isolated computer that runs commands and keeps files.

    ``info`` is the record last read; ``refresh()`` reads it again. Use ``async with`` to
    delete the sandbox on exit."""

    def __init__(
        self,
        sandboxes: AsyncSandboxes,
        info: Mapping[str, Any],
        *,
        owns_pool: bool = False,
    ) -> None:
        self._sandboxes = sandboxes
        self._info: Dict[str, Any] = dict(info)
        self._owns_pool = owns_pool
        self.commands = AsyncCommands(self)
        self.files = AsyncFiles(self)
        self.snapshots = AsyncSnapshots(self)
        self.network_policy = AsyncNetworkPolicy(self)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id!r}, state={self.state!r})"

    @property
    def id(self) -> str:
        return str(self._info["id"])

    @property
    def info(self) -> Dict[str, Any]:
        """The sandbox record last read (``id``, ``name``, ``state``, ``limits``...)."""
        return self._info

    @property
    def state(self) -> Optional[str]:
        return self._info.get("state")

    @classmethod
    def create(
        cls,
        *,
        name: Optional[str] = None,
        template: Optional[str] = None,
        size: Optional[str] = None,
        image: Optional[str] = None,
        environment_id: Optional[str] = None,
        limits: Optional[Mapping[str, Any]] = None,
        network: Optional[str] = None,
        network_policy: Optional[Mapping[str, Any]] = None,
        idle_ttl_seconds: Optional[int] = None,
    ) -> Awaitable[AsyncSandbox]:
        """Create a sandbox with the environment's settings (every field optional: a bare
        create uses the deployment's defaults). Not retried. Used directly in
        ``async with``, it deletes the sandbox on exit."""
        body = present(
            name=name,
            template=template,
            size=size,
            image=image,
            environmentId=environment_id,
            limits=dict(limits) if limits is not None else None,
            network=network,
            networkPolicy=dict(network_policy) if network_policy is not None else None,
            idleTtlSeconds=idle_ttl_seconds,
        )
        return _wire.awaitable_handle(_owned(_default().create(body=body)))

    @classmethod
    def connect(cls, sandbox_id: str) -> Awaitable[AsyncSandbox]:
        """A handle on an existing sandbox, with the environment's settings. Used directly
        in ``async with``, it deletes the sandbox on exit."""
        return _wire.awaitable_handle(_owned(_default().connect(sandbox_id)))

    @classmethod
    async def list(cls) -> SandboxList:
        """The workspace's sandboxes (one handle each) and its caps. The connection is
        closed once the list is read; a handle reopens it on its first call, and closing
        that handle closes it again."""
        api = _default()
        try:
            raw = await api.list()
        finally:
            await api._core.shared.aclose()
        records = raw.get("sandboxes", [])
        handles = [cls(api, record, owns_pool=True) for record in records]
        return SandboxList(handles, dict(raw.get("caps", {})), dict(raw))

    @classmethod
    async def settings(cls) -> Dict[str, Any]:
        """The workspace's sandbox settings, caps, templates and sizes (read-only). Sandbox
        settings are changed in the Console, from an owner's or admin's signed-in session;
        no API key changes them."""
        api = _default()
        try:
            return await api.settings.get()
        finally:
            await api._core.shared.aclose()

    def _adopt(self, raw: Any) -> Dict[str, Any]:
        record = raw.get("sandbox") if isinstance(raw, Mapping) else None
        if isinstance(record, Mapping):
            self._info = dict(record)
        return self._info

    async def refresh(self) -> Dict[str, Any]:
        """Read the record again; ``info`` becomes it."""
        raw = await self._sandboxes.get_info(self.id)
        self._info = dict(sandbox_record(raw, "sandboxes.getInfo"))
        return self._info

    async def update(
        self, *, name: Optional[str] = None, idle_ttl_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Rename it or change its idle TTL; returns the updated record."""
        body = present(name=name, idleTtlSeconds=idle_ttl_seconds)
        return self._adopt(await self._sandboxes.update(self.id, body=body))

    async def hibernate(self) -> Dict[str, Any]:
        """Stop its container and keep its disk; returns the updated record."""
        return self._adopt(await self._sandboxes.hibernate(self.id))

    async def resume(self) -> Dict[str, Any]:
        """Start it again after ``hibernate()``; returns the updated record."""
        return self._adopt(await self._sandboxes.resume(self.id))

    async def activity(self) -> List[Dict[str, Any]]:
        """Its audited activity entries, newest first."""
        raw = await self._sandboxes.activity.list(self.id)
        return list(raw.get("activity", []))

    async def delete(self) -> Dict[str, Any]:
        """Destroy it and its disk; returns the final record (state ``destroyed``). Safe to
        repeat: a sandbox that is already gone is not an error here."""
        try:
            raw = await self._sandboxes.kill(self.id)
        except NotFoundError:
            raw = None
        if raw is None:
            self._info = {**self._info, "state": "destroyed"}
            return self._info
        return self._adopt(raw)

    async def aclose(self) -> None:
        """Close the connection pool this handle opened (``create`` / ``connect`` /
        ``list``, or a restore from one of them). A handle that shares it reopens it when
        next used."""
        if self._owns_pool:
            await self._sandboxes._core.shared.aclose()

    async def __aenter__(self) -> AsyncSandbox:
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Delete on exit. If the body raised, its exception is the one that propagates (a
        failed delete is added to it as a note, or a ``RuntimeWarning`` before Python 3.11);
        otherwise a failed delete raises."""
        try:
            await self.delete()
        except Exception as failure:
            if exc is None:
                raise
            note = f"deleting sandbox {self.id} on exit failed: {failure}"
            if hasattr(exc, "add_note"):
                exc.add_note(note)
            else:
                warnings.warn(note, RuntimeWarning, stacklevel=2)
        finally:
            await self.aclose()


__all__ = [
    "AsyncSandbox",
    "AsyncCommands",
    "AsyncFiles",
    "AsyncSnapshots",
    "AsyncNetworkPolicy",
]
