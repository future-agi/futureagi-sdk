"""A download that answers with an error status (sync and async) reads its error body only when the
body is not encoded, and then at most up to the error-body cap. The download asks for identity, so
it skips an encoded error body (gzip, br, a list, an unknown coding) without reading or
decompressing it. The error carries the status, its request ID and no server code. For an identity body,
the error includes the server code read within the cap. Fake credentials only."""

from __future__ import annotations

import asyncio
import gzip
import json

import httpx
import pytest
from fi._core.transport import MAX_ERROR_BODY
from fi.sandbox import NotFoundError, ValidationError

from ._sandbox_mock import MODES, SBX, Chunks, MockServer, api, resolve

ENVELOPE = json.dumps({"code": "not_found", "message": "fixture refusal"}).encode()


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


def refused(server, status, chunks, **headers):
    """Return ``status`` and a streamed body that the mock leaves unread."""
    stream = Counted(chunks)
    sent = {"content-type": "application/json", "x-request-id": "req-fixture", **headers}
    server.on("sandboxes.files.download", lambda request: httpx.Response(status, headers=sent, stream=stream))
    return stream


def download(server, mode):
    return asyncio.run(resolve(api(server, mode).files.download(SBX, "a.bin")))


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("encoding", ["gzip", "GZIP", "gzip, identity", "br", "x-unknown"])
def test_an_encoded_error_body_is_never_read(mode, encoding):
    # About 1 KiB as sent and 1 MiB once decoded, and valid JSON with the server's code when decoded.
    padded = gzip.compress(ENVELOPE + b" " * (1 << 20))
    server = MockServer()
    stream = refused(server, 404, [padded], **{"content-encoding": encoding})
    with pytest.raises(NotFoundError) as caught:
        download(server, mode)
    error = caught.value
    assert stream.read == 0
    assert error.status_code == 404 and error.code == "http_404"
    assert error.request_id == "req-fixture"
    assert [seen.name for seen in server.seen] == ["sandboxes.files.download"]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("encoding", [None, "identity", "Identity"])
def test_an_identity_error_body_gives_the_server_code(mode, encoding):
    server = MockServer()
    headers = {} if encoding is None else {"content-encoding": encoding}
    stream = refused(server, 404, [ENVELOPE], **headers)
    with pytest.raises(NotFoundError) as caught:
        download(server, mode)
    assert caught.value.code == "not_found" and stream.read == 1


@pytest.mark.parametrize("mode", MODES)
def test_an_identity_error_body_is_read_only_up_to_the_cap(mode):
    server = MockServer()
    half = b" " * (MAX_ERROR_BODY // 2)
    stream = refused(server, 400, [half] * 4)
    with pytest.raises(ValidationError) as caught:
        download(server, mode)
    assert caught.value.status_code == 400 and stream.read == 2  # the chunk that reached the cap
