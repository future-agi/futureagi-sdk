"""Run with an isolated Python interpreter after installing the candidate wheel."""
import asyncio
import socket


def refuse(*args, **kwargs):
    raise AssertionError("Sandbox consumer checks must not use the network")


socket.socket.connect = refuse
socket.getaddrinfo = refuse

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.generated.platform.policy import OPERATIONS
from fi.sandbox import AsyncSandbox, AsyncSandboxes, CommandResult, Sandbox, SandboxError, Sandboxes

NAMES = ("list", "create", "connect", "get_info", "update", "kill", "hibernate", "resume",
         "settings.get", "network_policy.get", "network_policy.update", "files.list", "files.read",
         "files.write", "files.remove", "files.download", "files.upload", "files.rename",
         "files.make_dir", "snapshots.list", "snapshots.create", "snapshots.restore",
         "activity.list", "commands.run", "commands.cancel")

assert sum(name.startswith("sandboxes.") for name in OPERATIONS) == 24
assert "sandboxes.settings.update" not in OPERATIONS
assert issubclass(SandboxError, Exception) and Sandbox.create and AsyncSandbox.create
assert {"exit_code", "signal", "timed_out", "cancelled", "error"} <= set(CommandResult.__dataclass_fields__)
for cls, namespace in ((FutureAGIClient, Sandboxes), (AsyncFutureAGIClient, AsyncSandboxes)):
    client = cls(api_key="test-key", secret_key="test-secret", base_url="http://127.0.0.1:9",
                 allow_custom_base_url=False)
    try:
        for view in (client, client.with_options(retries=0)):
            assert isinstance(view.sandboxes, namespace)
            for name in NAMES:
                target = view.sandboxes
                for part in name.split("."):
                    target = getattr(target, part)
                assert callable(target), name
            assert not hasattr(view.sandboxes.settings, "update")
    finally:
        if isinstance(client, AsyncFutureAGIClient):
            asyncio.run(client.aclose())
        else:
            client.close()
print("Installed wheel: sandbox imports, accessors and the 24 generated names present")
