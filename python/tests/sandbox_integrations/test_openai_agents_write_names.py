"""FutureAGISandboxSession.write checks the file's whole path before it makes the file's parent folders: a
name the files API refuses (a backslash, a control character, a path over 4096 characters) under a
subfolder such as ``/workspace/sub`` raises ``ConfigurationError`` (``invalid_path``) with no request at all,
so the write creates neither the folder nor the file. The Agents SDK is faked; the sandbox API is the
frozen-OpenAPI mock. Fake credentials only."""

from __future__ import annotations

import importlib
import io
from pathlib import Path

import pytest

from fi.sandbox import AsyncSandbox, ConfigurationError
from tests.platform._sandbox_mock import SBX, MockServer, api, run

from . import _fake_openai_agents as fake

REFUSED = ("/workspace/sub/a\\b.txt", "/workspace/sub/deeper/a\x00b.txt", "/workspace/sub/" + "x" * 4097)


@pytest.fixture(name="adapter")
def adapter_fixture(monkeypatch):
    fake.install(monkeypatch)
    return importlib.import_module(fake.ADAPTER)


def make(adapter, server):
    """A session on a handle that made no request (its record says ``active``)."""
    sbx = AsyncSandbox(api(server, "async"), {"id": SBX, "state": "active"})
    state = adapter.FutureAGISandboxSessionState(
        manifest=fake.Manifest(), snapshot=fake.NoopSnapshot(id="snap"), sandbox_id=SBX,
        workspace_root_ready=True)
    return adapter.FutureAGISandboxSession(state=state, sandbox=sbx, max_timeout_s=900)


@pytest.mark.parametrize("path", REFUSED, ids=["backslash", "nul", "over-4096-chars"])
def test_a_refused_name_under_a_subfolder_sends_nothing(adapter, path):
    server = MockServer()
    session = make(adapter, server)
    with pytest.raises(ConfigurationError) as info:
        run(session.write(Path(path), io.BytesIO(b"x")))
    assert info.value.code == "invalid_path" and info.value.operation == "sandboxes.files.upload"
    assert server.seen == []  # no folder made for it, no upload


def test_a_good_name_makes_its_folder_then_uploads(adapter):
    server = MockServer()
    session = make(adapter, server)
    run(session.write(Path("/workspace/sub/ok.txt"), io.BytesIO(b"ok")))
    assert [seen.name for seen in server.seen] == ["sandboxes.files.makeDir", "sandboxes.files.upload"]
