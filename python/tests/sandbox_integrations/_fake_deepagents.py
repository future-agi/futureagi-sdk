"""A stand-in for the parts of Deep Agents the backend imports, so its tests run without the package.

The names, fields and signatures mirror ``deepagents==0.7.35`` (``libs/deepagents/deepagents/backends/
protocol.py`` and ``sandbox.py``): ``ExecuteResponse(output, exit_code=None, truncated=False)``, the two
file responses, the ``FileOperationError`` literal, ``execute_accepts_timeout`` (which checks
``"timeout" in sig.parameters``) and an abstract ``BaseSandbox`` whose subclasses implement
``execute``, ``id``, ``upload_files`` and ``download_files``.

:func:`install` puts the fake modules into ``sys.modules`` and makes sure the backend module is
imported afresh against them and dropped again when the test ends.
"""

from __future__ import annotations

import abc
import inspect
import sys
import types
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, Optional, Union

import fi.sandbox_integrations

ADAPTER = "fi.sandbox_integrations.deepagents"
ADAPTER_MODULES = (ADAPTER, ADAPTER + "._backend")
FAKE_MODULES = (
    "deepagents",
    "deepagents.backends",
    "deepagents.backends.protocol",
    "deepagents.backends.sandbox",
)

FileOperationError = Literal["file_not_found", "permission_denied", "is_directory", "invalid_path"]


@dataclass
class FileDownloadResponse:
    path: str
    content: Optional[bytes] = None
    error: Union[FileOperationError, str, None] = None


@dataclass
class FileUploadResponse:
    path: str
    error: Union[FileOperationError, str, None] = None


@dataclass
class ExecuteResponse:
    output: str
    exit_code: Optional[int] = None
    truncated: bool = False


class BackendProtocol(abc.ABC):  # noqa: B024 (no abstract methods, as upstream)
    pass


class SandboxBackendProtocol(BackendProtocol):
    @property
    def id(self) -> str:
        raise NotImplementedError

    def execute(self, command: str, *, timeout: Optional[int] = None) -> ExecuteResponse:
        raise NotImplementedError


@lru_cache(maxsize=128)
def execute_accepts_timeout(cls: type) -> bool:
    try:
        sig = inspect.signature(cls.execute)
    except (ValueError, TypeError):
        return False
    else:
        return "timeout" in sig.parameters


class BaseSandbox(SandboxBackendProtocol, abc.ABC):
    @abc.abstractmethod
    def execute(self, command: str, *, timeout: Optional[int] = None) -> ExecuteResponse:
        """Run a command."""

    @property
    @abc.abstractmethod
    def id(self) -> str:
        """The sandbox id."""

    @abc.abstractmethod
    def upload_files(self, files: list) -> list:
        """Upload files; per-file errors."""

    @abc.abstractmethod
    def download_files(self, paths: list) -> list:
        """Download files; per-file errors."""


def forget_on_teardown(monkeypatch, name: str) -> None:
    """Remove ``sys.modules[name]`` now and again when the test ends, whatever imported it since."""
    monkeypatch.setitem(sys.modules, name, None)
    monkeypatch.delitem(sys.modules, name)


def forget_adapter(monkeypatch) -> None:
    """Drop the backend module (and the package's attribute for it) now and at teardown."""
    for name in ADAPTER_MODULES:
        forget_on_teardown(monkeypatch, name)
    monkeypatch.setattr(fi.sandbox_integrations, "deepagents", None, raising=False)
    monkeypatch.delattr(fi.sandbox_integrations, "deepagents")


def install(monkeypatch) -> types.SimpleNamespace:
    """Put the fake Deep Agents modules in place and forget any earlier import of the backend.
    Returns the fake protocol names; import the backend after calling this."""
    forget_adapter(monkeypatch)
    modules = {name: types.ModuleType(name) for name in FAKE_MODULES}
    for name in ("deepagents", "deepagents.backends"):
        modules[name].__path__ = []
    protocol = modules["deepagents.backends.protocol"]
    for value in (
        ExecuteResponse,
        FileDownloadResponse,
        FileUploadResponse,
        BackendProtocol,
        SandboxBackendProtocol,
        execute_accepts_timeout,
    ):
        setattr(protocol, value.__name__, value)
    protocol.FileOperationError = FileOperationError
    sandbox = modules["deepagents.backends.sandbox"]
    sandbox.BaseSandbox = BaseSandbox
    sandbox.ExecuteResponse = ExecuteResponse
    sandbox.execute_accepts_timeout = execute_accepts_timeout
    modules["deepagents"].backends = modules["deepagents.backends"]
    modules["deepagents.backends"].protocol = protocol
    modules["deepagents.backends"].sandbox = sandbox
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    return types.SimpleNamespace(
        ExecuteResponse=ExecuteResponse,
        FileDownloadResponse=FileDownloadResponse,
        FileUploadResponse=FileUploadResponse,
        BaseSandbox=BaseSandbox,
        execute_accepts_timeout=execute_accepts_timeout,
    )
