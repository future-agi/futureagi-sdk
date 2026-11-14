"""What the ``sandbox`` command-group tests share (test_sandbox_cli*.py): a self-hosted EE on
loopback with the frozen-OpenAPI mock as its transport, only this group loaded, and small
response helpers. Fake credentials only."""

from __future__ import annotations

import httpx
import pytest
from fi._cli import main as cli_main
from fi._cli import registry
from fi.sandbox import _connection

from ._sandbox_mock import EXEC as EXEC_ID
from ._sandbox_mock import (
    FAKE_KEY,
    FAKE_SECRET,
    FAKE_TOKEN,
    SBX,
    Chunks,
    MockServer,
    error,
    sse,
    stream_response,
)

LOCAL = "http://127.0.0.1:8787"
OTHER = "sbx_" + "c" * 24
ENV = ("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
       "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID", "FI_ALLOW_INSECURE_HTTP", "FI_BASE_URL",
       "FI_PLATFORM_BASE_URL", "FI_PLATFORM_TOKEN", "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_EXTRA_HEADERS")
SECRETS = (FAKE_KEY, FAKE_SECRET, FAKE_TOKEN)
STARTED = ("started", {"execId": EXEC_ID, "sandboxId": SBX})


class _EP:
    name = "sandbox"

    def load(self):
        import fi._cli.sandbox as module

        return module


@pytest.fixture(name="server")
def server_fixture(monkeypatch):
    """A self-hosted EE on loopback (Bearer), the mock as its transport, only this group loaded.
    Test modules import it as ``server_fixture`` and take ``server``."""
    mock = MockServer()
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OMEGA_BASE_URL", LOCAL)
    monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", FAKE_TOKEN)
    monkeypatch.setattr(_connection, "default_transport", mock.transport)
    monkeypatch.setattr(registry, "entry_points", lambda: [_EP()])
    return mock


def run(*argv: str) -> int:
    return cli_main.main(["sandbox", *argv])


def answer(*args, **kwargs):
    """A fresh response for every request (a response body is read once)."""
    return lambda request: httpx.Response(*args, **kwargs)


def refuse(*args, **kwargs):
    """A fresh error response for every request."""
    return lambda request: error(*args, **kwargs)


def record(state="active", ident=SBX, **extra):
    return {"schemaVersion": "omega-workspace-sandboxes/v1",
            "sandbox": {"id": ident, "state": state, "name": "n", **extra}}


def names(server):
    return [seen.name for seen in server.seen]


def no_secret(*texts):
    joined = "".join(texts)
    assert not any(secret in joined for secret in SECRETS)


def exec_body(*frames, chunks=None, fail=None):
    data = sse(STARTED, *frames)
    return lambda request: stream_response(Chunks(chunks(data) if chunks else [data], fail=fail))


def file_answer(content, encoding="utf8", truncated=False):
    return answer(200, json={"schemaVersion": "v1", "file": {
        "outcome": "ok", "path": "f", "encoding": encoding, "content": content, "bytes": 6, "truncated": truncated}})
