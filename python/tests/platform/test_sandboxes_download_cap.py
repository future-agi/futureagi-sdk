"""Downloads are capped (sync and async): by default at the 64 MiB upload limit, and by
``max_bytes=`` on ``sbx.files.download`` / ``download_to`` to raise or lower it. A declared
``Content-Length`` over the limit is refused before a byte is read; a body that grows past it is
refused as it arrives; the error names the limit and the keyword; ``download_to`` leaves no partial
or temporary file; the command line's ``cp`` keeps the default. Fake credentials only."""

from __future__ import annotations

import asyncio
import inspect

import httpx
import pytest
from fi._core.request import BODY_LIMITS
from fi.sandbox import AsyncSandbox, ConfigurationError, PayloadTooLargeError, Sandbox

from ._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    run,
    server_fixture,
)
from ._sandbox_mock import MODES, SBX, Chunks, MockServer, api, resolve

LIMIT = BODY_LIMITS["bundle"]


class Counted(Chunks):
    """A body that records how many chunks were read."""

    def __init__(self, chunks):
        super().__init__(chunks)
        self.read = 0

    def __iter__(self):
        for chunk in self.chunks:
            self.read += 1
            yield chunk

    async def __aiter__(self):
        for chunk in self.chunks:
            self.read += 1
            yield chunk


def handle(server, mode):
    cls = AsyncSandbox if mode == "async" else Sandbox
    return cls(api(server, mode), {"id": SBX, "state": "active"})


def body(chunks, length=None):
    stream = Counted(chunks)
    headers = {"content-type": "application/octet-stream"}
    if length is not None:
        headers["content-length"] = str(length)
    return stream, (lambda request: httpx.Response(200, headers=headers, stream=stream))


@pytest.mark.parametrize("mode", MODES)
def test_the_default_limit_is_the_upload_limit(mode):
    cls = AsyncSandbox if mode == "async" else Sandbox
    files = cls(api(MockServer(), mode), {"id": SBX}).files
    for method in (files.download, files.download_to):
        assert inspect.signature(method).parameters["max_bytes"].default == LIMIT == 64 * 1024 * 1024


@pytest.mark.parametrize("mode", MODES)
def test_a_declared_length_over_the_default_is_refused_before_reading(mode):
    server = MockServer()
    stream, answer = body([b"x"], length=LIMIT + 1)
    server.on("sandboxes.files.download", answer)
    sbx = handle(server, mode)
    for call in (lambda: sbx.files.download("big.bin"), lambda: api(server, mode).files.download(SBX, "big.bin")):
        with pytest.raises(PayloadTooLargeError) as caught:
            asyncio.run(resolve(call()))
        error = caught.value
        assert error.limit_bytes == LIMIT and error.local is True and error.code == "download_too_large"
        assert str(LIMIT) in str(error) and "max_bytes" in str(error)
    assert stream.read == 0


@pytest.mark.parametrize("mode", MODES)
def test_a_body_that_grows_past_max_bytes_is_refused_as_it_arrives(mode):
    server = MockServer()
    stream, answer = body([b"abcd", b"efgh", b"ijkl"])
    server.on("sandboxes.files.download", answer)
    with pytest.raises(PayloadTooLargeError) as caught:
        asyncio.run(resolve(handle(server, mode).files.download("a.bin", max_bytes=6)))
    assert caught.value.limit_bytes == 6 and "6 bytes" in str(caught.value)
    assert stream.read == 2  # the chunk that crossed the limit; never the one after it


@pytest.mark.parametrize("mode", MODES)
def test_max_bytes_raises_or_lowers_the_limit(mode):
    server = MockServer()
    server.on("sandboxes.files.download", lambda request: httpx.Response(200, content=b"0123456789"))
    files = handle(server, mode).files
    assert asyncio.run(resolve(files.download("a.bin", max_bytes=10))) == b"0123456789"
    with pytest.raises(PayloadTooLargeError):
        asyncio.run(resolve(files.download("a.bin", max_bytes=9)))
    assert asyncio.run(resolve(files.download("a.bin", max_bytes=LIMIT * 2))) == b"0123456789"


@pytest.mark.parametrize("mode", MODES)
def test_download_to_over_the_limit_leaves_no_file(mode, tmp_path):
    server = MockServer()
    stream, answer = body([b"abcd", b"efgh"])
    server.on("sandboxes.files.download", answer)
    target = tmp_path / "out.bin"
    with pytest.raises(PayloadTooLargeError):
        asyncio.run(resolve(handle(server, mode).files.download_to("a.bin", target, max_bytes=5)))
    assert list(tmp_path.iterdir()) == [] and stream.read == 2
    target.write_bytes(b"kept")
    server.on("sandboxes.files.download", body([b"x"], length=LIMIT + 1)[1])
    with pytest.raises(PayloadTooLargeError):
        asyncio.run(resolve(handle(server, mode).files.download_to("a.bin", target)))
    assert target.read_bytes() == b"kept" and [p.name for p in tmp_path.iterdir()] == ["out.bin"]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("value", [0, -1, True, "10", 1.5])
def test_a_bad_max_bytes_is_refused_before_anything_is_sent(mode, value, tmp_path):
    server = MockServer()
    files = handle(server, mode).files
    for call in (lambda: files.download("a.bin", max_bytes=value),
                 lambda: files.download_to("a.bin", tmp_path / "a.bin", max_bytes=value)):
        with pytest.raises(ConfigurationError, match="max_bytes"):
            asyncio.run(resolve(call()))
    assert server.seen == [] and list(tmp_path.iterdir()) == []


def test_cp_keeps_the_default_limit_and_leaves_no_partial_file(server, capsys, tmp_path):
    server.on("sandboxes.files.download", body([b"x"], length=LIMIT + 1)[1])
    assert run("cp", f"{SBX}:big.bin", str(tmp_path)) == 1
    err = capsys.readouterr().err
    assert err.startswith("download_too_large: ") and str(LIMIT) in err
    assert list(tmp_path.iterdir()) == []
