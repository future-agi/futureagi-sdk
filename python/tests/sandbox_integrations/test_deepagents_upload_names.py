"""FutureAGISandbox.upload_files checks a file's whole path before it makes the file's folder: a name the
files API refuses (a backslash, a control character, a path over 4096 characters) under a subfolder such as
``/workspace/sub`` gets ``invalid_path`` without sending a request or creating a folder for that file.
Other files in the batch proceed. Deep Agents is faked; the sandbox API is the
frozen-OpenAPI mock. Fake credentials only."""

from __future__ import annotations

import importlib
from urllib.parse import unquote

import httpx
import pytest

from tests.platform._sandbox_mock import SBX, MockServer, api, example

from . import _fake_deepagents as fake

REFUSED = ("/workspace/sub/a\\b.txt", "/workspace/sub/deeper/a\x00b.txt", "/workspace/sub/" + "x" * 4097)


@pytest.fixture(name="adapter")
def adapter_fixture(monkeypatch):
    fake.install(monkeypatch)
    return importlib.import_module(fake.ADAPTER)


def make(adapter, server: MockServer):
    """A backend on a connected handle; the requests made to build it are forgotten."""
    body = example(server.spec, server.routes["sandboxes.settings.get"].schema)
    body["caps"]["exec"].update(maxTimeoutSeconds=900, defaultTimeoutSeconds=60)
    server.on("sandboxes.settings.get", lambda request: httpx.Response(200, json=body))
    backend = adapter.FutureAGISandbox(sandbox=api(server, "sync").connect(SBX))
    server.seen.clear()
    return backend


def target(seen) -> str:
    """``upload/<path>`` or ``folders/<path>`` of a file request."""
    return unquote(seen.request.url.raw_path.decode("ascii")).split(f"/{SBX}/", 1)[1]


@pytest.mark.parametrize("path", REFUSED, ids=["backslash", "nul", "over-4096-chars"])
def test_a_refused_name_under_a_subfolder_sends_nothing(adapter, path):
    server = MockServer()
    backend = make(adapter, server)
    assert backend.upload_files([(path, b"x")]) == [fake.FileUploadResponse(path=path, error="invalid_path")]
    assert server.seen == []  # no folder made for it, no upload


def test_the_other_files_go_after_a_refused_name(adapter):
    server = MockServer()
    backend = make(adapter, server)
    files = [("/workspace/sub/a\\b.txt", b"x"), ("/workspace/sub/ok.txt", b"ok")]
    assert [r.error for r in backend.upload_files(files)] == ["invalid_path", None]
    assert [target(seen) for seen in server.seen] == ["folders/sub", "upload/sub/ok.txt"]
