"""Run with an installed wheel or sdist, outside the source checkout."""
import asyncio
import contextlib
import importlib
from importlib import metadata
import io
import socket


def refuse(*args, **kwargs):
    raise AssertionError("Consumer absence checks must not use the network")


socket.socket.connect = refuse
socket.getaddrinfo = refuse

import fi
from fi import AsyncFutureAGIClient, FutureAGIClient
from fi._cli.main import main

assert metadata.version("futureagi") == "0.7.0"
for name in ("deployments", "Deployment", "AsyncDeployment", "Deployments", "AsyncDeployments"):
    assert not hasattr(fi, name), name
    assert name not in fi.__all__, name
try:
    importlib.import_module("fi.deployments")
except ModuleNotFoundError as error:
    assert error.name == "fi.deployments", error
else:
    raise AssertionError("fi.deployments is importable")

with FutureAGIClient(base_url="http://127.0.0.1:9") as client:
    with client.with_options(retries=0) as copy:
        assert not hasattr(client, "deployments")
        assert not hasattr(copy, "deployments")


async def check_async():
    async with AsyncFutureAGIClient(base_url="http://127.0.0.1:9") as client:
        async with client.with_options(retries=0) as copy:
            assert not hasattr(client, "deployments")
            assert not hasattr(copy, "deployments")


asyncio.run(check_async())
assert not any(ep.name == "deployments" for ep in metadata.entry_points(group="futureagi.cli"))
output = io.StringIO()
with contextlib.redirect_stdout(output):
    assert main(["--help"]) == 0
assert "deployments" not in output.getvalue().lower()
error = io.StringIO()
with contextlib.redirect_stderr(error):
    assert main(["deployments", "list"]) == 2
assert "invalid choice" in error.getvalue()
print("Installed Python deployment absence: PASS (sync, async, copies, imports, CLI)")
