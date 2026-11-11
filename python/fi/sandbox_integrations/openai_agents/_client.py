"""The Agents SDK sandbox client for Future AGI sandboxes: :class:`FutureAGISandboxClient`.

Pass it to ``SandboxRunConfig(client=...)``. It creates a sandbox per session, reattaches a resumed
session to its sandbox (resuming it once if it is hibernated, or creating a replacement that the SDK
fills from the session's snapshot when it is gone), and deletes or hibernates the sandbox at the end.

Without ``client=`` it reads the environment, like :class:`fi.sandbox.AsyncSandbox`: ``OMEGA_BASE_URL``
and ``FI_API_KEY`` + ``FI_SECRET_KEY`` (hosted) or ``FUTUREAGI_OMEGA_API_KEY`` (self-hosted EE). With
``client=AsyncFutureAGIClient(...)`` it uses that client's ``sandboxes``. A setup problem raises
:class:`fi.sandbox.ConfigurationError`; nothing is retried.
"""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath
from typing import Any, Dict, Mapping, Optional

from ._missing import missing_agents_sandbox

try:
    from agents.sandbox.entries import Dir, File, LocalDir, LocalFile
    from agents.sandbox.manifest import Manifest
    from agents.sandbox.session.sandbox_client import BaseSandboxClient
    from agents.sandbox.snapshot import resolve_snapshot
except ImportError as exc:
    raise missing_agents_sandbox(exc) from exc

from fi.sandbox import AsyncSandbox
from fi.sandbox.errors import ConfigurationError, NotFoundError, SandboxError

from ._options import WORKSPACE_ROOT, FutureAGISandboxClientOptions, FutureAGISandboxSessionState
from ._session import FutureAGISandboxSession

#: The manifest entries this client materializes: plain files and folders.
SUPPORTED_ENTRIES = (Dir, File, LocalDir, LocalFile)


def check_manifest(manifest: Any) -> None:
    """Refuse, before anything is created, what a Future AGI sandbox cannot do: a workspace root
    outside ``/workspace``, users and groups, environment variables, mounts, git repositories and
    any other entry type than files and folders, and entries owned by a user or group."""
    root = PurePosixPath(manifest.root)
    if root != PurePosixPath(WORKSPACE_ROOT) and PurePosixPath(WORKSPACE_ROOT) not in root.parents:
        raise NotImplementedError(
            f"manifest root {manifest.root!r}: the workspace root must be {WORKSPACE_ROOT} or a "
            f"folder inside it (the sandbox files API reaches {WORKSPACE_ROOT} only)"
        )
    if manifest.users or manifest.groups:
        raise NotImplementedError(
            "manifest users and groups are not supported: Future AGI sandboxes run every command "
            "as one fixed user (uid 1000)"
        )
    if manifest.environment.value:
        raise NotImplementedError(
            "manifest environment variables are not supported: this client sends no environment "
            "with a command"
        )
    for rel, entry in manifest.iter_entries():
        if not isinstance(entry, SUPPORTED_ENTRIES):
            raise NotImplementedError(
                f"manifest entry {rel.as_posix()!r} of type {entry.type!r} is not supported: "
                "only files and folders (File, Dir, LocalFile, LocalDir); mounts and git "
                "repositories are not"
            )
        if entry.group is not None:
            raise NotImplementedError(
                f"manifest entry {rel.as_posix()!r} names an owner: users and groups are not supported"
            )


def exec_maximum(settings: Any) -> int:
    """The workspace's exec time limit, ``caps.exec.maxTimeoutSeconds`` of its sandbox settings (an
    operator sets it, so it is read, never assumed)."""
    caps = settings.get("caps") if isinstance(settings, Mapping) else None
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


def _create_body(source: Any) -> Dict[str, Any]:
    fields = {
        "name": source.name,
        "template": source.template,
        "size": source.size,
        "image": source.image,
        "idleTtlSeconds": source.idle_ttl_seconds,
    }
    return {key: value for key, value in fields.items() if value is not None}


class FutureAGISandboxClient(BaseSandboxClient[FutureAGISandboxClientOptions]):
    """Runs Agents SDK sandbox sessions in Future AGI sandboxes. ``client`` is an
    ``AsyncFutureAGIClient`` (anything with ``sandboxes``); without one the environment is read.
    ``instrumentation`` and ``dependencies`` are the SDK's own, passed to every session."""

    backend_id = "futureagi"
    supports_default_options = True

    def __init__(
        self,
        *,
        client: Any = None,
        instrumentation: Any = None,
        dependencies: Any = None,
    ) -> None:
        self._client = client
        self._instrumentation = instrumentation
        self._dependencies = dependencies

    async def _settings(self) -> Any:
        if self._client is not None:
            return await self._client.sandboxes.settings.get()
        return await AsyncSandbox.settings()

    async def _new_sandbox(self, body: Dict[str, Any]) -> AsyncSandbox:
        if self._client is not None:
            return await self._client.sandboxes.create(body=body)
        return await AsyncSandbox.create(
            name=body.get("name"),
            template=body.get("template"),
            size=body.get("size"),
            image=body.get("image"),
            idle_ttl_seconds=body.get("idleTtlSeconds"),
        )

    async def _connect(self, sandbox_id: str) -> AsyncSandbox:
        if self._client is not None:
            return await self._client.sandboxes.connect(sandbox_id)
        return await AsyncSandbox.connect(sandbox_id)

    def _wrap(self, inner: FutureAGISandboxSession) -> Any:
        return self._wrap_session(inner, instrumentation=self._instrumentation)

    async def create(
        self,
        *,
        snapshot: Any = None,
        manifest: Any = None,
        options: Optional[FutureAGISandboxClientOptions] = None,
    ) -> Any:
        """Create a sandbox and return its session (not started; the SDK starts it). The
        workspace's sandbox settings are read first, so a refusal there creates nothing."""
        options = options if options is not None else FutureAGISandboxClientOptions()
        if not isinstance(options, FutureAGISandboxClientOptions):
            raise TypeError("FutureAGISandboxClient.create expects FutureAGISandboxClientOptions")
        if manifest is None:
            manifest = Manifest(root=options.workdir)
        elif options.workdir not in (WORKSPACE_ROOT, manifest.root):
            raise ValueError(
                f"options.workdir {options.workdir!r} and manifest.root {manifest.root!r} differ; "
                "set the workspace root in one place"
            )
        check_manifest(manifest)
        self._validate_manifest_for_create(manifest)
        maximum = exec_maximum(await self._settings())
        sandbox = await self._new_sandbox(_create_body(options))
        session_id = uuid.uuid4()
        state = FutureAGISandboxSessionState(
            session_id=session_id,
            manifest=manifest,
            snapshot=resolve_snapshot(snapshot, str(session_id)),
            sandbox_id=sandbox.id,
            name=options.name,
            template=options.template,
            size=options.size,
            image=options.image,
            idle_ttl_seconds=options.idle_ttl_seconds,
            exec_timeout_s=options.exec_timeout_s,
            hibernate_on_exit=options.hibernate_on_exit,
        )
        inner = FutureAGISandboxSession(state=state, sandbox=sandbox, max_timeout_s=maximum)
        return self._wrap(inner)

    async def resume(self, state: Any) -> Any:
        """Reattach to the sandbox in ``state``. A hibernated one is resumed (once; this is the
        only call that resumes a sandbox). One that is gone is replaced by a new sandbox made
        with the same options, which the SDK fills from ``state.snapshot`` when it starts. A
        sandbox that needs recovery is refused rather than left behind."""
        if not isinstance(state, FutureAGISandboxSessionState):
            raise TypeError("FutureAGISandboxClient.resume expects a FutureAGISandboxSessionState")
        state.assert_path_grants_rebound()
        if state.exposed_ports:
            raise NotImplementedError("exposed ports are not supported by Future AGI sandboxes")
        check_manifest(state.manifest)
        maximum = exec_maximum(await self._settings())
        sandbox: Optional[AsyncSandbox]
        try:
            sandbox = await self._connect(state.sandbox_id)
        except NotFoundError:
            sandbox = None
        hibernated = False
        if sandbox is not None and sandbox.state == "destroyed":
            await sandbox.aclose()
            sandbox = None
        elif sandbox is not None and sandbox.state == "hibernated":
            await sandbox.resume()
            hibernated = True
        elif sandbox is not None and sandbox.state != "active":
            found = sandbox.state
            await sandbox.aclose()
            raise SandboxError(
                f"sandbox {state.sandbox_id} is {found}; it cannot be resumed. Delete it "
                "(fi.sandbox) and run again from the session's snapshot",
                code="sandbox_not_resumable",
            )
        reconnected = sandbox is not None
        if sandbox is None:
            sandbox = await self._new_sandbox(_create_body(state))
            state.sandbox_id = sandbox.id
            state.workspace_root_ready = False
        inner = FutureAGISandboxSession(state=state, sandbox=sandbox, max_timeout_s=maximum)
        inner._set_start_state_preserved(reconnected, system=reconnected and not hibernated)
        return self._wrap(inner)

    async def delete(self, session: Any) -> Any:
        """Delete the session's sandbox, or hibernate it with ``hibernate_on_exit`` (once: the
        session's shutdown may have done it already). A sandbox already gone is not an error."""
        inner = getattr(session, "_inner", session)
        if not isinstance(inner, FutureAGISandboxSession):
            raise TypeError("FutureAGISandboxClient.delete expects a FutureAGISandboxSession")
        await inner._end()
        return session

    def deserialize_session_state(self, payload: Dict[str, object]) -> FutureAGISandboxSessionState:
        return self._deserialize_session_state_payload(payload, FutureAGISandboxSessionState)


__all__ = ["FutureAGISandboxClient", "SUPPORTED_ENTRIES", "check_manifest", "exec_maximum"]
