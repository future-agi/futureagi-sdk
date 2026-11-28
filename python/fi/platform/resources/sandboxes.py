"""`client.sandboxes`: the generated layer of the sandbox namespace, one method per contract operation.

Method names follow each operation's OpenAPI `x-sdk-operation` name, snake_case per dotted segment
(`get_info`, `network_policy.update`, `files.make_dir`, `activity.list`, `commands.run`). The
classes are written async-first in `fi.sandbox._resource` (`scripts/platform/unasync.py` writes
the sync twin) and run on the platform executor (`fi._core.platform_base`) with the generated
operation table, not on this package's catalog transport, so they are not entries of
`Resources`. `FutureAGIClient.sandboxes` and `AsyncFutureAGIClient.sandboxes` construct them; the
`Sandbox` / `AsyncSandbox` handles (`fi.sandbox`) sit on top.
"""

from __future__ import annotations

from fi.sandbox._resource import (
    AsyncCommandStream,
    AsyncSandboxActivity,
    AsyncSandboxCommands,
    AsyncSandboxes,
    AsyncSandboxFiles,
    AsyncSandboxNetworkPolicy,
    AsyncSandboxSettings,
    AsyncSandboxSnapshots,
    CommandStream,
    SandboxActivity,
    SandboxCommands,
    Sandboxes,
    SandboxFiles,
    SandboxNetworkPolicy,
    SandboxSettings,
    SandboxSnapshots,
)

__all__ = [
    "Sandboxes",
    "SandboxSettings",
    "SandboxFiles",
    "SandboxSnapshots",
    "SandboxNetworkPolicy",
    "SandboxActivity",
    "SandboxCommands",
    "CommandStream",
    "AsyncSandboxes",
    "AsyncSandboxSettings",
    "AsyncSandboxFiles",
    "AsyncSandboxSnapshots",
    "AsyncSandboxNetworkPolicy",
    "AsyncSandboxActivity",
    "AsyncSandboxCommands",
    "AsyncCommandStream",
]
