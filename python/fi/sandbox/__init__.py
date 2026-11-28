"""Remote sandboxes: isolated computers that run commands and keep files.

    from fi.sandbox import Sandbox

    with Sandbox.create(name="scratch") as sbx:
        result = sbx.commands.run("echo hello")
        print(result.exit_code, result.stdout)

``Sandbox`` is synchronous; ``AsyncSandbox`` has the same methods as coroutines
(``async with AsyncSandbox.create() as sbx``, or ``sbx = await AsyncSandbox.create()``).
``Sandbox.create`` / ``connect`` / ``list`` / ``settings`` read the environment only:
``OMEGA_BASE_URL`` (there is no default host), then ``FI_API_KEY`` + ``FI_SECRET_KEY`` (Future AGI cloud) or
``FUTUREAGI_OMEGA_API_KEY`` (self-managed Enterprise), not both, and ``FI_WORKSPACE_ID`` /
``FI_ORGANIZATION_ID`` as the scope. The key pair goes only to a Future AGI host (HTTPS in the
``futureagi.com`` zone) or to loopback unless ``FI_ALLOW_CUSTOM_PLATFORM_URL=1`` is set (the
command line's ``--allow-custom-base-url``). To pass keys, a base URL, a workspace or an organization in
code, build the client and use its generated layer, whose ``create`` / ``connect`` return the same
handle. The client has no default sandbox host either: give it the address::

    from fi import FutureAGIClient

    client = FutureAGIClient(
        api_key=..., secret_key=...,
        platform_base_url="https://<gateway-host>/omega/api", workspace_id="ws_1",
    )
    sbx = client.sandboxes.create(body={"name": "scratch"})

A self-managed Enterprise instance outside loopback needs the constructor-only
``FutureAGIClient(platform_token=..., platform_base_url=..., allow_custom_base_url=True)``.
Sandbox settings are read-only here; they are changed in the Console, from an owner's or admin's
signed-in session.

Run a command with its own binary-safe streams over the sandbox's channel (one WebSocket, standard
input and output as raw bytes, credit-based flow control both ways)::

    with sbx.commands.exec_stream(["sh", "-c", "cat; echo done >&2"]) as stream:
        stream.write(b"\x00 any bytes")
        stream.close_stdin()
        out = stream.read_stdout()
        exit_record = stream.wait()

``AsyncSandbox`` has the same methods as coroutines. The channel ends with a typed
``ChannelClosedError`` subclass when the server closes it (access revoked, sandbox gone, emergency
stop, hibernated, frozen, server stopping).

Errors are :mod:`fi.sandbox.errors` classes; each HTTP one is also its ``fi.errors`` status class.
"""

from typing import TYPE_CHECKING

from ._async_client import AsyncSandbox
from ._channel._async.stream import AsyncExecStream
from ._channel.protocol import ExecChunk
from ._client import Sandbox
from ._parts._async_client import (
    AsyncCommands,
    AsyncFiles,
    AsyncNetworkPolicy,
    AsyncSnapshots,
)
from ._parts._client import Commands, Files, NetworkPolicy, Snapshots
from ._resource import AsyncCommandStream, AsyncSandboxes, CommandStream, Sandboxes
from .errors import (
    AuthenticationError,
    CommandFailedError,
    CommandIncompleteError,
    ConfigurationError,
    ConflictError,
    ConnectionError,
    ConnectionTimeoutError,
    InsufficientStorageError,
    NotFoundError,
    PayloadTooLargeError,
    PermissionDeniedError,
    ProviderError,
    QuotaExceededError,
    RateLimitError,
    SandboxAPIError,
    SandboxError,
    SandboxHibernatedError,
    UnavailableError,
    ValidationError,
)
from .channel_errors import (
    ChannelAccessRevokedError,
    ChannelClosedError,
    ChannelEmergencyStopError,
    ChannelProtocolError,
    ChannelSandboxFrozenError,
    ChannelSandboxGoneError,
    ChannelSandboxHibernatedError,
    ChannelServerStoppingError,
    ChannelStreamEndedError,
)
from .frames import (
    ErrorFrame,
    ExecFrame,
    ExitFrame,
    StartedFrame,
    StderrFrame,
    StdoutFrame,
    UnknownFrame,
)
from .types import CommandResult, NetworkPolicyInfo, SandboxList

if TYPE_CHECKING:
    from ._channel._sync.stream import ExecStream

def __getattr__(name: str) -> object:
    # ``ExecStream`` loads the sync channel module, which checks the installed websockets at import;
    # it is loaded on first use so that importing ``fi.sandbox`` does not depend on that check.
    if name == "ExecStream":
        from ._channel._sync.stream import ExecStream

        return ExecStream
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Sandbox",
    "AsyncSandbox",
    "Sandboxes",
    "AsyncSandboxes",
    "Commands",
    "AsyncCommands",
    "Files",
    "AsyncFiles",
    "Snapshots",
    "AsyncSnapshots",
    "NetworkPolicy",
    "AsyncNetworkPolicy",
    "CommandStream",
    "AsyncCommandStream",
    "ExecStream",
    "AsyncExecStream",
    "ExecChunk",
    "CommandResult",
    "SandboxList",
    "NetworkPolicyInfo",
    "ExecFrame",
    "StartedFrame",
    "StdoutFrame",
    "StderrFrame",
    "ExitFrame",
    "ErrorFrame",
    "UnknownFrame",
    "SandboxError",
    "SandboxAPIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "SandboxHibernatedError",
    "QuotaExceededError",
    "ValidationError",
    "PayloadTooLargeError",
    "RateLimitError",
    "ProviderError",
    "UnavailableError",
    "InsufficientStorageError",
    "ConnectionError",
    "ConnectionTimeoutError",
    "CommandIncompleteError",
    "CommandFailedError",
    "ChannelClosedError",
    "ChannelAccessRevokedError",
    "ChannelSandboxGoneError",
    "ChannelEmergencyStopError",
    "ChannelSandboxHibernatedError",
    "ChannelSandboxFrozenError",
    "ChannelServerStoppingError",
    "ChannelProtocolError",
    "ChannelStreamEndedError",
    "ConfigurationError",
]
