"""The sandbox senders that do not go through the generated call path refuse a 3xx answer from their own origin: the
file download (whole, to a local file, and streamed), the command stream and the file upload and write. One loopback
server answers every request with a 302 to a path on the same origin and counts the planted marker bytes of each request;
a sender passes when the server saw exactly one request, none for the redirect target, and the caller got
``KeyedRedirectRefusedError``."""

from __future__ import annotations

import asyncio

import pytest

import fi
from fi import AsyncFutureAGIClient, FutureAGIClient

from .test_same_origin_redirect_per_sender import MARKER_KEY, MARKER_SECRET, Redirector, origin  # noqa: F401

RECORD = {"sandbox": {"id": "sbx-1", "name": "n", "status": "running"}}


def _client(url: str) -> FutureAGIClient:
    return FutureAGIClient(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=url, retries=0, platform_base_url=url + "/omega/api")


def _async_client(url: str) -> AsyncFutureAGIClient:
    return AsyncFutureAGIClient(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=url, retries=0, platform_base_url=url + "/omega/api")


def test_the_file_download_refuses_a_same_origin_redirect(origin):  # noqa: F811
    client = _client(origin.url)
    with pytest.raises(fi.KeyedRedirectRefusedError):
        client.sandboxes.files.download("sbx-1", "a.txt")
    origin.assert_refused_after_one_request()


def test_the_handle_download_refuses_a_same_origin_redirect(origin):  # noqa: F811
    sbx = _client(origin.url).sandboxes._handle(RECORD, "t")
    with pytest.raises(fi.KeyedRedirectRefusedError):
        sbx.files.download("a.txt")
    origin.assert_refused_after_one_request()


def test_the_handle_download_to_refuses_a_same_origin_redirect_and_leaves_no_file(origin, tmp_path):  # noqa: F811
    sbx = _client(origin.url).sandboxes._handle(RECORD, "t")
    with pytest.raises(fi.KeyedRedirectRefusedError):
        sbx.files.download_to("a.txt", tmp_path / "out.bin")
    assert list(tmp_path.iterdir()) == []
    origin.assert_refused_after_one_request()


def test_the_streamed_download_refuses_a_same_origin_redirect(origin):  # noqa: F811
    client = _client(origin.url)
    with pytest.raises(fi.KeyedRedirectRefusedError):
        for _ in client.sandboxes.files._stream("sbx-1", "a.txt", None):
            pass
    origin.assert_refused_after_one_request()


def test_the_async_file_download_refuses_a_same_origin_redirect(origin):  # noqa: F811
    async def go():
        async with _async_client(origin.url) as client:
            return await client.sandboxes.files.download("sbx-1", "a.txt")

    with pytest.raises(fi.KeyedRedirectRefusedError):
        asyncio.run(go())
    origin.assert_refused_after_one_request()


def test_the_async_streamed_download_refuses_a_same_origin_redirect(origin):  # noqa: F811
    async def go():
        async with _async_client(origin.url) as client:
            async for _ in client.sandboxes.files._stream("sbx-1", "a.txt", None):
                pass

    with pytest.raises(fi.KeyedRedirectRefusedError):
        asyncio.run(go())
    origin.assert_refused_after_one_request()


def test_the_command_stream_refuses_a_same_origin_redirect(origin):  # noqa: F811
    sbx = _client(origin.url).sandboxes._handle(RECORD, "t")
    with pytest.raises(fi.KeyedRedirectRefusedError):
        with sbx.commands.stream("echo hi") as stream:
            for _ in stream:
                pass
    origin.assert_refused_after_one_request()


def test_the_command_run_refuses_a_same_origin_redirect(origin):  # noqa: F811
    sbx = _client(origin.url).sandboxes._handle(RECORD, "t")
    with pytest.raises(fi.KeyedRedirectRefusedError):
        sbx.commands.run("echo hi")
    origin.assert_refused_after_one_request()


def test_the_async_command_stream_refuses_a_same_origin_redirect(origin):  # noqa: F811
    async def go():
        async with _async_client(origin.url) as client:
            sbx = client.sandboxes._handle(RECORD, "t")
            async with sbx.commands.stream("echo hi") as stream:
                async for _ in stream:
                    pass

    with pytest.raises(fi.KeyedRedirectRefusedError):
        asyncio.run(go())
    origin.assert_refused_after_one_request()


def test_the_file_upload_refuses_a_same_origin_redirect(origin):  # noqa: F811
    sbx = _client(origin.url).sandboxes._handle(RECORD, "t")
    with pytest.raises(fi.KeyedRedirectRefusedError):
        sbx.files.upload("a.txt", b"payload")
    origin.assert_refused_after_one_request()


def test_the_file_write_refuses_a_same_origin_redirect(origin):  # noqa: F811
    sbx = _client(origin.url).sandboxes._handle(RECORD, "t")
    with pytest.raises(fi.KeyedRedirectRefusedError):
        sbx.files.write("a.txt", "payload")
    origin.assert_refused_after_one_request()
