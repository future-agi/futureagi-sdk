"""A stand-in for the parts of the OpenAI Agents SDK sandbox package the client imports, so its tests run
without ``openai-agents`` 0.24 (CI installs 0.4.2, which has no ``agents.sandbox``).

The module names, class names and signatures mirror ``openai-agents==0.24.0`` (``src/agents/sandbox``):
the pydantic ``BaseSandboxClientOptions`` and ``SandboxSessionState`` that register a subclass by its
``type`` default, ``BaseSandboxClient`` with ``_wrap_session`` (recorded here), ``BaseSandboxSession``
with its six abstract methods and the helpers the client calls, ``ExecResult``, the manifest and its
entry types, ``resolve_snapshot``, ``shell_tar_exclude_args`` and ``validate_tar_bytes``.

:func:`install` puts the fake modules into ``sys.modules`` and makes sure the client is imported afresh
against them and dropped again when the test ends.
"""

from __future__ import annotations

import abc
import io
import posixpath
import shlex
import sys
import tarfile
import types
import uuid
from pathlib import Path, PurePosixPath
from typing import Any, ClassVar, Dict, Generic, List, Optional, Tuple, TypeVar

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, field_validator

import fi.sandbox_integrations

ADAPTER = "fi.sandbox_integrations.openai_agents"
ADAPTER_MODULES = (ADAPTER, ADAPTER + "._client", ADAPTER + "._session", ADAPTER + "._options")
PACKAGES = ("agents.sandbox", "agents.sandbox.session", "agents.sandbox.util")
LEAVES = (
    "agents.sandbox.entries",
    "agents.sandbox.errors",
    "agents.sandbox.manifest",
    "agents.sandbox.snapshot",
    "agents.sandbox.types",
    "agents.sandbox.session.base_sandbox_session",
    "agents.sandbox.session.sandbox_client",
    "agents.sandbox.session.sandbox_session_state",
    "agents.sandbox.session.tar_workspace",
    "agents.sandbox.util.tar_utils",
)


def _register(base: Any, cls: Any) -> None:
    field = cls.model_fields.get("type")
    default = field.default if field is not None else None
    if not isinstance(default, str) or not default:
        raise TypeError(f"{cls.__name__} must define a non-empty string default for `type`")
    existing = base._subclass_registry.get(default)
    if existing is not None and (existing.__module__, existing.__qualname__) != (cls.__module__, cls.__qualname__):
        raise TypeError(f"type `{default}` is already registered by {existing.__name__}")
    if existing is None:  # a re-import of the same class keeps the first one, as upstream does
        base._subclass_registry[default] = cls


class User(BaseModel):
    name: str


class Group(BaseModel):
    name: str
    users: List[User] = Field(default_factory=list)


class ExecResult:
    def __init__(self, *, stdout: bytes, stderr: bytes, exit_code: int) -> None:
        self.stdout, self.stderr, self.exit_code = stdout, stderr, exit_code

    def ok(self) -> bool:
        return self.exit_code == 0


class SandboxError(Exception):
    def __init__(self, *, message: str, context: Optional[dict] = None, cause: Any = None,
                 retryable: Optional[bool] = None) -> None:
        super().__init__(message)
        self.message, self.context, self.cause, self.retryable = message, dict(context or {}), cause, retryable


class ExecTransportError(SandboxError):
    def __init__(self, *, command: Any, context: Optional[dict] = None, cause: Any = None,
                 message: Optional[str] = None, retryable: Optional[bool] = None) -> None:
        super().__init__(message=message or "exec transport error", context=context, cause=cause, retryable=retryable)
        self.command = tuple(str(c) for c in command)


class _PathError(SandboxError):
    def __init__(self, *, path: Path, context: Optional[dict] = None, cause: Any = None,
                 retryable: Optional[bool] = None, message: Optional[str] = None) -> None:
        super().__init__(message=message or f"{type(self).__name__}: {path}",
                         context={"path": str(path), **(context or {})}, cause=cause, retryable=retryable)


class WorkspaceArchiveReadError(_PathError):
    pass


class WorkspaceArchiveWriteError(_PathError):
    pass


class WorkspaceStartError(_PathError):
    pass


class WorkspaceReadNotFoundError(_PathError):
    def __init__(self, *, path: Path, context: Optional[dict] = None, cause: Any = None) -> None:
        super().__init__(path=path, context=context, cause=cause, retryable=False)


class WorkspaceWriteTypeError(_PathError):
    def __init__(self, *, path: Path, actual_type: str, context: Optional[dict] = None, cause: Any = None) -> None:
        super().__init__(path=path, context={"actual_type": actual_type, **(context or {})}, cause=cause)


class BaseEntry(BaseModel):
    type: str
    group: Optional[Any] = None
    _subclass_registry: ClassVar[Dict[str, Any]] = {}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        _register(BaseEntry, cls)

    @classmethod
    def parse(cls, value: Any) -> "BaseEntry":
        return value if isinstance(value, BaseEntry) else cls._subclass_registry[value["type"]].model_validate(value)


class Dir(BaseEntry):
    type: str = "dir"
    children: Dict[str, SerializeAsAny[BaseEntry]] = Field(default_factory=dict)


class File(BaseEntry):
    type: str = "file"
    content: bytes = b""


class LocalFile(BaseEntry):
    type: str = "local_file"
    src: Path = Path("x")


class LocalDir(BaseEntry):
    type: str = "local_dir"
    src: Optional[Path] = None


class GitRepo(BaseEntry):
    type: str = "git_repo"
    repo: str = "org/repo"


class S3Mount(BaseEntry):
    type: str = "s3_mount"
    bucket: str = "bucket"


class Environment(BaseModel):
    value: Dict[str, Any] = Field(default_factory=dict)


class Manifest(BaseModel):
    root: str = "/workspace"
    entries: Dict[str, SerializeAsAny[BaseEntry]] = Field(default_factory=dict)
    environment: Environment = Field(default_factory=Environment)
    users: List[User] = Field(default_factory=list)
    groups: List[Group] = Field(default_factory=list)
    extra_path_grants: Tuple[Any, ...] = ()

    @field_validator("entries", mode="before")
    @classmethod
    def _parse_entries(cls, value: Any) -> Any:
        return {str(k): BaseEntry.parse(v) for k, v in (value or {}).items()}

    def iter_entries(self):
        stack = [(Path(k), v) for k, v in reversed(list(self.entries.items()))]
        while stack:
            rel, entry = stack.pop()
            yield rel, entry
            if isinstance(entry, Dir):
                stack.extend((rel / k, v) for k, v in reversed(list(entry.children.items())))


class SnapshotBase(BaseModel):
    type: str = "noop"
    id: str = "snapshot"


class NoopSnapshot(SnapshotBase):
    type: str = "noop"


def resolve_snapshot(spec: Any, snapshot_id: str) -> SnapshotBase:
    return spec if isinstance(spec, SnapshotBase) else NoopSnapshot(id=snapshot_id)


class BaseSandboxClientOptions(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)
    type: str
    _subclass_registry: ClassVar[Dict[str, Any]] = {}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        _register(BaseSandboxClientOptions, cls)


class SandboxSessionState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    type: str
    session_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    snapshot: SerializeAsAny[SnapshotBase]
    manifest: Manifest
    exposed_ports: Tuple[int, ...] = ()
    workspace_root_ready: bool = False
    _subclass_registry: ClassVar[Dict[str, Any]] = {}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        _register(SandboxSessionState, cls)

    @field_validator("snapshot", mode="before")
    @classmethod
    def _coerce_snapshot(cls, value: Any) -> Any:
        return NoopSnapshot.model_validate(value) if isinstance(value, dict) else value

    def assert_path_grants_rebound(self) -> None:
        return None


class BaseSandboxSession(abc.ABC):
    state: SandboxSessionState
    _start_workspace_state_preserved: bool = False
    _start_system_state_preserved: bool = False
    _skip_paths: Optional[set] = None

    @abc.abstractmethod
    async def _exec_internal(self, *command: Any, timeout: Optional[float] = None) -> ExecResult: ...

    @abc.abstractmethod
    async def read(self, path: Path, *, user: Any = None) -> io.IOBase: ...

    @abc.abstractmethod
    async def write(self, path: Path, data: io.IOBase, *, user: Any = None) -> None: ...

    @abc.abstractmethod
    async def running(self) -> bool: ...

    @abc.abstractmethod
    async def persist_workspace(self) -> io.IOBase: ...

    @abc.abstractmethod
    async def hydrate_workspace(self, data: io.IOBase) -> None: ...

    async def exec(self, *command: Any, timeout: Optional[float] = None, shell: Any = True, user: Any = None) -> ExecResult:
        argv = [str(c) for c in command]
        if shell:
            argv = ["sh", "-lc", argv[0] if len(argv) == 1 else shlex.join(argv)]
        if user:
            argv = ["sudo", "-u", getattr(user, "name", user), "--", *argv]
        return await self._exec_internal(*argv, timeout=timeout)

    def normalize_path(self, path: Any, *, for_write: bool = False) -> Path:
        root = PurePosixPath(self.state.manifest.root)
        full = PurePosixPath(posixpath.normpath(str(root / PurePosixPath(str(path)))))
        if full != root and root not in full.parents:
            raise ValueError(f"{path} escapes the workspace root")
        return Path(str(full))

    def _workspace_root_path(self) -> Path:
        return Path(self.state.manifest.root)

    def register_persist_workspace_skip_path(self, path: Any) -> Path:
        self._skip_paths = {*(self._skip_paths or ()), Path(str(path))}
        return Path(str(path))

    def _persist_workspace_skip_relpaths(self) -> set:
        return set(self._skip_paths or ())

    def _set_start_state_preserved(self, workspace: bool, *, system: Optional[bool] = None) -> None:
        self._start_workspace_state_preserved = workspace
        self._start_system_state_preserved = workspace if system is None else system

    def _workspace_state_preserved_on_start(self) -> bool:
        return self._start_workspace_state_preserved

    def _mark_workspace_root_ready_from_probe(self) -> None:
        self.state.workspace_root_ready = True

    async def _prepare_backend_workspace(self) -> None:
        return None

    async def _shutdown_backend(self) -> None:
        return None

    async def shutdown(self) -> None:
        await self._shutdown_backend()


class SandboxSession:
    def __init__(self, inner: BaseSandboxSession, *, instrumentation: Any = None) -> None:
        self._inner, self.instrumentation = inner, instrumentation

    @property
    def state(self) -> SandboxSessionState:
        return self._inner.state


ClientOptionsT = TypeVar("ClientOptionsT")


class BaseSandboxClient(abc.ABC, Generic[ClientOptionsT]):
    backend_id: str
    supports_default_options: bool = False
    #: Every inner session ``_wrap_session`` was given, across clients (cleared by :func:`install`).
    wrapped: ClassVar[List[Any]] = []

    def _wrap_session(self, inner: BaseSandboxSession, *, instrumentation: Any = None) -> SandboxSession:
        BaseSandboxClient.wrapped.append(inner)
        return SandboxSession(inner, instrumentation=instrumentation)

    def _validate_manifest_for_create(self, manifest: Manifest) -> Manifest:
        return manifest

    @abc.abstractmethod
    async def create(self, *, snapshot: Any = None, manifest: Any = None, options: Any) -> SandboxSession: ...

    @abc.abstractmethod
    async def delete(self, session: SandboxSession) -> SandboxSession: ...

    @abc.abstractmethod
    async def resume(self, state: SandboxSessionState) -> SandboxSession: ...

    def serialize_session_state(self, state: SandboxSessionState) -> Dict[str, object]:
        return state.model_dump(mode="json")

    @staticmethod
    def _deserialize_session_state_payload(payload: Any, state_class: Any) -> SandboxSessionState:
        return state_class.model_validate(payload)

    @abc.abstractmethod
    def deserialize_session_state(self, payload: Dict[str, object]) -> SandboxSessionState: ...


def shell_tar_exclude_args(skip_relpaths: Any) -> List[str]:
    out = []
    for rel in sorted(skip_relpaths, key=lambda p: p.as_posix()):
        text = rel.as_posix().lstrip("/")
        if text and text not in {".", "/"}:
            out.append(f"--exclude={shlex.quote(f'./{text}')}")
    return out


class UnsafeTarMemberError(ValueError):
    def __init__(self, *, member: str, reason: str) -> None:
        super().__init__(f"unsafe tar member {member!r}: {reason}")
        self.member, self.reason = member, reason


def validate_tar_bytes(raw: bytes, *, allow_external_symlink_targets: bool = True, **_: Any) -> None:
    try:
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            members = archive.getmembers()
    except tarfile.TarError as error:
        raise UnsafeTarMemberError(member="<archive>", reason=str(error)) from error
    for member in members:
        if member.name.startswith("/") or ".." in PurePosixPath(member.name).parts:
            raise UnsafeTarMemberError(member=member.name, reason="outside the workspace")


def forget_on_teardown(monkeypatch, name: str) -> None:
    """Remove ``sys.modules[name]`` now and again when the test ends, whatever imported it since."""
    monkeypatch.setitem(sys.modules, name, None)
    monkeypatch.delitem(sys.modules, name)


def forget_adapter(monkeypatch) -> None:
    """Drop the client modules (and the package's attribute for them) now and at teardown."""
    for name in ADAPTER_MODULES:
        forget_on_teardown(monkeypatch, name)
    monkeypatch.setattr(fi.sandbox_integrations, "openai_agents", None, raising=False)
    monkeypatch.delattr(fi.sandbox_integrations, "openai_agents")


_CONTENTS = {
    "agents.sandbox.entries": (BaseEntry, Dir, File, LocalFile, LocalDir, GitRepo, S3Mount),
    "agents.sandbox.errors": (SandboxError, ExecTransportError, WorkspaceArchiveReadError,
                              WorkspaceArchiveWriteError, WorkspaceReadNotFoundError,
                              WorkspaceStartError, WorkspaceWriteTypeError),
    "agents.sandbox.manifest": (Manifest, Environment),
    "agents.sandbox.snapshot": (SnapshotBase, NoopSnapshot, resolve_snapshot),
    "agents.sandbox.types": (ExecResult, User, Group),
    "agents.sandbox.session.base_sandbox_session": (BaseSandboxSession,),
    "agents.sandbox.session.sandbox_client": (BaseSandboxClient, BaseSandboxClientOptions, SandboxSession),
    "agents.sandbox.session.sandbox_session_state": (SandboxSessionState,),
    "agents.sandbox.session.tar_workspace": (shell_tar_exclude_args,),
    "agents.sandbox.util.tar_utils": (UnsafeTarMemberError, validate_tar_bytes),
}


def install(monkeypatch) -> types.ModuleType:
    """Put the fake sandbox modules in place (a bare ``agents`` package too, unless one is already
    imported) and forget any earlier import of the client. Returns this module; import the client
    after calling it."""
    forget_adapter(monkeypatch)
    BaseSandboxClient.wrapped.clear()
    if "agents" not in sys.modules:
        top = types.ModuleType("agents")
        top.__path__ = []
        monkeypatch.setitem(sys.modules, "agents", top)
    modules = {name: types.ModuleType(name) for name in PACKAGES + LEAVES}
    for name in PACKAGES:
        modules[name].__path__ = []
    for name, values in _CONTENTS.items():
        for value in values:
            setattr(modules[name], value.__name__, value)
    for name, module in modules.items():
        parent, _, leaf = name.rpartition(".")
        if parent in modules:
            setattr(modules[parent], leaf, module)
        monkeypatch.setitem(sys.modules, name, module)
    return sys.modules[__name__]
