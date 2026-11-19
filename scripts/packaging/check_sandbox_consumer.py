"""Run with an isolated Python interpreter after installing the candidate wheel."""
import asyncio
import importlib
import socket
import subprocess
import sys


def refuse(*args, **kwargs):
    raise AssertionError("Sandbox absence checks must not use the network")


socket.socket.connect = refuse
socket.getaddrinfo = refuse

import fi
from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.generated.platform.policy import OPERATIONS

assert not any(name.startswith("sandboxes.") for name in OPERATIONS)
for name in ("Sandbox", "AsyncSandbox", "SandboxesClient", "AsyncSandboxesClient"):
    assert not hasattr(fi, name), name
for name in ("fi.sandboxes", "fi.sandboxes.types", "fi.sandboxes._cli"):
    try:
        importlib.import_module(name)
    except ModuleNotFoundError as exc:
        assert exc.name == "fi.sandboxes", exc
    else:
        raise AssertionError(f"{name} is importable")
for cls in (FutureAGIClient, AsyncFutureAGIClient):
    client = cls(api_key="test-key", secret_key="test-secret", base_url="http://127.0.0.1:9")
    try:
        assert not hasattr(client, "sandboxes")
        assert not hasattr(client.with_options(retries=0), "sandboxes")
    finally:
        if isinstance(client, AsyncFutureAGIClient):
            asyncio.run(client.aclose())
        else:
            client.close()
for args, code in ((["--help"], 0), (["sandboxes", "--help"], 2)):
    result = subprocess.run([sys.executable, "-I", "-m", "fi._cli.main", *args], capture_output=True, text=True, timeout=30)
    assert result.returncode == code, result.stderr
    if code == 0:
        assert "sandboxes" not in result.stdout.lower()
    else:
        assert "invalid choice" in result.stderr
print("Installed wheel: sandbox imports, accessors and CLI absent")
