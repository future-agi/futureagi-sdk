"""FutureAGISandbox.upload_files / download_files over the frozen-OpenAPI mock, with Deep Agents faked:
input order kept, the folder made before the upload (top down when a folder above is missing), paths
mapped onto the files API's root (``/workspace``), a refusal mapped per file while the other files
still go, a folder found by its refusal or by one listing, and nothing sent for a path the API cannot
reach. Fake credentials only."""

from __future__ import annotations

import importlib
from urllib.parse import unquote

import httpx
import pytest

from tests.platform._sandbox_mock import SBX, MockServer, api, error, example

from . import _fake_deepagents as fake

NOT_WRITABLE = "its folder is read-only or the sandbox can't write there"


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


def target(request: httpx.Request) -> str:
    """``upload/<path>``, ``folders/<path>`` or ``download/<path>`` of a file request."""
    return unquote(request.url.raw_path.decode("ascii")).split(f"/{SBX}/", 1)[1]


def sent(server: MockServer) -> list:
    return [target(seen.request) for seen in server.seen]


def test_upload_keeps_order_and_makes_parent_first(adapter):
    server = MockServer()
    backend = make(adapter, server)
    asked: list = []

    def folders(request):
        asked.append(target(request))
        if asked.count(target(request)) > 1:
            return error(409, "conflict", detail={"reason": "exists"})
        return httpx.Response(201, json=example(server.spec, server.routes["sandboxes.files.makeDir"].schema))

    server.on("sandboxes.files.makeDir", folders)
    files = [("/workspace/b.txt", b"B"), ("/workspace/sub/a.txt", b"A"), ("/workspace/sub/c.txt", b"C")]
    responses = backend.upload_files(files)
    assert responses == [fake.FileUploadResponse(path=path) for path, _ in files]
    assert sent(server) == [
        "upload/b.txt",
        "folders/sub", "upload/sub/a.txt",
        "folders/sub", "upload/sub/c.txt",  # 409 "exists" counts as made
    ]
    uploads = [seen.body for seen in server.seen if seen.name == "sandboxes.files.upload"]
    assert uploads == [b"B", b"A", b"C"]


def test_upload_creates_missing_folders_top_down(adapter):
    server = MockServer()
    backend = make(adapter, server)
    asked: list = []

    def folders(request):
        asked.append(target(request))
        if asked == ["folders/x/y"]:
            return error(404, "not_found")
        return httpx.Response(201, json=example(server.spec, server.routes["sandboxes.files.makeDir"].schema))

    server.on("sandboxes.files.makeDir", folders)
    assert backend.upload_files([("/workspace/x/y/z.txt", b"z")]) == [
        fake.FileUploadResponse(path="/workspace/x/y/z.txt")]
    assert sent(server) == ["folders/x/y", "folders/x", "folders/x/y", "upload/x/y/z.txt"]


def test_upload_relative_path_is_invalid_path_without_request(adapter):
    server = MockServer()
    backend = make(adapter, server)
    responses = backend.upload_files([
        ("rel.txt", b"x"), ("/etc/passwd", b"x"), ("/workspace/../etc/x", b"x"), ("/workspace", b"x"),
    ])
    assert [r.error for r in responses] == ["invalid_path", "permission_denied", "permission_denied", "is_directory"]
    assert [r.path for r in responses] == ["rel.txt", "/etc/passwd", "/workspace/../etc/x", "/workspace"]
    assert server.seen == []


def test_upload_maps_403_404_400_413_per_file_and_continues(adapter):
    server = MockServer()
    backend = make(adapter, server)
    refusals = {
        "f403.txt": lambda: error(403, "forbidden"),
        "f404.txt": lambda: error(404, "not_found"),
        "f400.txt": lambda: error(400, "validation_failed"),
        "f413.txt": lambda: error(413, "too_large", detail={"maxBytes": 1}),
        "ro400.txt": lambda: error(400, "validation_failed", message=NOT_WRITABLE),
        "ro409.txt": lambda: error(409, "read_only"),
        "busy.txt": lambda: error(409, "conflict", detail={"state": "hibernated"}),
    }

    def upload(request):
        name = target(request).rsplit("/", 1)[-1]
        if name in refusals:
            return refusals[name]()
        return httpx.Response(200, json=example(server.spec, server.routes["sandboxes.files.upload"].schema))

    server.on("sandboxes.files.upload", upload)
    names = ["ok1.txt", *refusals, "ok2.txt"]
    responses = backend.upload_files([(f"/workspace/{name}", name.encode()) for name in names])
    assert [r.path for r in responses] == [f"/workspace/{name}" for name in names]
    assert [r.error for r in responses[:-2]] == [
        None, "permission_denied", "file_not_found", "invalid_path", "file_too_large",
        "permission_denied", "permission_denied",
    ]
    assert "hibernated" in responses[-2].error and "resume" in responses[-2].error
    assert responses[-1].error is None
    assert sent(server) == [f"upload/{name}" for name in names]  # one request each, none retried


def test_upload_folder_refusal_is_that_files_error(adapter):
    server = MockServer()
    backend = make(adapter, server)
    server.on("sandboxes.files.makeDir", lambda request: error(403, "forbidden"))
    responses = backend.upload_files([("/workspace/locked/a.txt", b"a"), ("/workspace/b.txt", b"b")])
    assert [r.error for r in responses] == ["permission_denied", None]
    assert sent(server) == ["folders/locked", "upload/b.txt"]


def test_download_returns_bytes(adapter):
    server = MockServer()
    backend = make(adapter, server)
    blobs = {"download/data/a.bin": b"\x00bin\xff", "download/b.txt": b"text"}
    server.on("sandboxes.files.download", lambda request: httpx.Response(200, content=blobs[target(request)]))
    responses = backend.download_files(["/workspace/data/a.bin", "/workspace/b.txt"])
    assert responses == [
        fake.FileDownloadResponse(path="/workspace/data/a.bin", content=b"\x00bin\xff"),
        fake.FileDownloadResponse(path="/workspace/b.txt", content=b"text"),
    ]
    assert sent(server) == ["download/data/a.bin", "download/b.txt"]


def test_download_404_is_file_not_found(adapter):
    server = MockServer()
    backend = make(adapter, server)
    server.on("sandboxes.files.download", lambda request: error(404, "not_found"))
    responses = backend.download_files(["/workspace/gone.txt"])
    assert responses == [fake.FileDownloadResponse(path="/workspace/gone.txt", error="file_not_found")]
    assert [seen.name for seen in server.seen] == ["sandboxes.files.download"]  # no probe


def listing(*entries):
    body = {"schemaVersion": "omega-workspace-sandboxes/v1", "path": ".", "entries": list(entries)}
    return lambda request: httpx.Response(200, json=body)


def test_download_directory_probe_gives_is_directory(adapter):
    server = MockServer()
    backend = make(adapter, server)
    server.on("sandboxes.files.download", lambda request: error(400, "validation_failed"))
    server.on("sandboxes.files.list", listing(
        {"name": "src", "size": 0, "mode": "755", "directory": True},
        {"name": "notes.txt", "size": 3, "mode": "644", "directory": False},
    ))
    responses = backend.download_files(["/workspace/src", "/workspace/notes.txt"])
    assert [r.error for r in responses] == ["is_directory", "invalid_path"]
    assert [seen.name for seen in server.seen] == [
        "sandboxes.files.download", "sandboxes.files.list"] * 2
    assert server.seen[1].request.url.params["path"] == "."


def test_download_wrong_type_is_directory_without_probe(adapter):
    server = MockServer()
    backend = make(adapter, server)
    server.on("sandboxes.files.download",
              lambda request: error(400, "validation_failed", detail={"reason": "wrong_type"}))
    responses = backend.download_files(["/workspace/src/pkg", "/workspace"])
    assert [r.error for r in responses] == ["is_directory", "is_directory"]
    assert sent(server) == ["download/src/pkg"]  # /workspace itself is known without a request


def test_download_permission_refusal(adapter):
    server = MockServer()
    backend = make(adapter, server)
    server.on("sandboxes.files.download", lambda request: error(403, "forbidden"))
    assert backend.download_files(["/workspace/secret.txt"])[0].error == "permission_denied"


def test_download_relative_path_is_invalid_path(adapter):
    server = MockServer()
    backend = make(adapter, server)
    responses = backend.download_files(["rel.txt", "/etc/hosts", "/workspace/ok.txt"])
    assert [r.error for r in responses] == ["invalid_path", "permission_denied", None]
    assert responses[2].content == b"file-bytes"
    assert sent(server) == ["download/ok.txt"]
