"""Published file edits preserve JSON and multipart selection on every send path."""
import inspect
import json
from email.parser import BytesParser
from email.policy import default

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._base_client import RequestOptions
from fi.gateway.callbacks.base import CallbackHandler

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("path", ["parsed", "raw", "stream"])
@pytest.mark.parametrize("change", ["untouched", "empty", "clear", "replace_empty", "replace_none", "replace_file", "insert_file", "retry_clear"])
async def test_send_path_encoding_published_contract(async_mode, redact, path, change):
    sent, called, descriptors = [], [], []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            descriptors.append(request)
            if change in {"empty", "clear", "replace_empty", "replace_none", "retry_clear"}:
                request.files = {}
            if change in {"clear", "retry_clear"}:
                request.files["file"] = ("first.dat", b"first")
                if change == "clear":
                    request.files.clear()
            if change == "replace_none":
                request.files = None
            if change == "replace_file":
                request.files = {"file": ("new.dat", b"replaced")}
            if change == "insert_file":
                if request.files is None:
                    request.files = {}
                request.files["file"] = ("new.dat", b"replaced")
            called.append("start")

        def on_retry(self, request, error, attempt, delay):
            descriptors.append(request)
            if request.files is not None:
                request.files.clear()
            called.append("retry")

        def on_request_end(self, request, response):
            descriptors.append(request)
            called.append("end")

    def serve(request):
        sent.append(request)
        if change == "retry_clear" and len(sent) == 1 and path != "stream":
            return httpx.Response(500, headers={"retry-after": "0"}, json={"error": {"message": "offline"}})
        if path == "stream":
            return httpx.Response(200, headers={"content-type": "text/event-stream"}, text="data: [DONE]\n\n")
        if path == "raw":
            return httpx.Response(200, content=b"result")
        return httpx.Response(200, json={"id": "reply", "object": "chat.completion", "created": 0, "model": "test", "choices": []})

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-wire-sdk", base_url="https://gateway.example.test", http_client=http,
        callbacks=[Edit()], redact_messages=redact, max_retries=1 if change == "retry_clear" else 0,
    )
    try:
        if path == "raw":
            await resolve(client.audio.speech.create(model="test", input="speak", voice="alloy"))
        else:
            result = await resolve(client.chat.completions.create(model="test", messages=[], stream=path == "stream"))
            if path == "stream":
                if async_mode:
                    async for _ in result:
                        pass
                else:
                    list(result)
        assert called[0] == "start" and called[-1] == "end"
        assert all(item is descriptors[0] for item in descriptors)
        for index, request in enumerate(sent):
            # Published streaming always uses JSON, regardless of descriptor.files.
            expect_files = not redact and path != "stream" and (
                change in {"replace_file", "insert_file"} or (change == "retry_clear" and index == 0)
            )
            if expect_files:
                assert request.headers["content-type"].startswith("multipart/form-data;")
                message = BytesParser(policy=default).parsebytes(
                    b"Content-Type: " + request.headers["content-type"].encode() + b"\r\n\r\n" + request.content
                )
                parts = {p.get_param("name", header="content-disposition"): p.get_payload(decode=True) for p in message.iter_parts()}
                assert parts["file"] == (b"first" if change == "retry_clear" and index == 0 else b"replaced")
                assert parts["model"] == b"test"
            else:
                assert request.headers["content-type"] == "application/json"
                assert json.loads(request.content)["model"] == "test"
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("endpoint", ["transcriptions", "translations", "files"])
@pytest.mark.parametrize("change", ["clear", "replace_empty", "replace_none", "replace_file", "clear_then_insert"])
async def test_upload_resource_encoding_published_contract(async_mode, redact, endpoint, change):
    seen, called = [], []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            if change in {"clear", "clear_then_insert"}:
                request.files.clear()
                if change == "clear_then_insert":
                    request.files["file"] = ("replacement.dat", b"new-data")
            elif change == "replace_empty":
                request.files = {}
            elif change == "replace_none":
                request.files = None
            else:
                request.files = {"file": ("replacement.dat", b"new-data")}
            called.append(True)

    def serve(request):
        seen.append(request)
        return httpx.Response(200, json={"text": "ok"} if endpoint != "files" else {
            "id": "file-test", "object": "file", "bytes": 3, "created_at": 0,
            "filename": "input.dat", "purpose": "assistants",
        })

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-upload-sdk", base_url="https://gateway.example.test", http_client=http,
        callbacks=[Edit()], redact_messages=redact, max_retries=0,
    )
    try:
        if endpoint == "files":
            await resolve(client.files.create(file=("input.dat", b"old"), purpose="assistants"))
        else:
            await resolve(getattr(client.audio, endpoint).create(file=("input.dat", b"old"), model="test", prompt="prompt"))
        assert called == [True]
        expected_json = change == "clear" or (not redact and change in {"replace_empty", "replace_none"})
        if expected_json:
            assert seen[0].headers["content-type"] == "application/json"
            assert json.loads(seen[0].content) == ({"purpose": "assistants"} if endpoint == "files" else {"model": "test", "prompt": "prompt"})
        else:
            assert seen[0].headers["content-type"].startswith("multipart/form-data;")
            expected = b"new-data" if change == "clear_then_insert" or (change == "replace_file" and not redact) else b"old"
            assert expected in seen[0].content
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("async_mode", [False, True])
async def test_explicit_form_stream_still_uses_multipart(async_mode):
    seen = []

    def serve(request):
        seen.append(request)
        return httpx.Response(200, text="data: [DONE]\n\n")

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key="synthetic-sdk-key", base_url="https://gateway.example.test", http_client=http,
    )
    try:
        options = RequestOptions("POST", "/v1/test", form={"model": "test"}, files={"file": ("input.dat", b"sample")})
        response = await resolve(client._get_base_client()._stream_request(options))
        await resolve(response.aclose() if async_mode else response.close())
        assert seen[0].headers["content-type"].startswith("multipart/form-data;")
        assert b"sample" in seen[0].content and b"test" in seen[0].content
    finally:
        await resolve(http.aclose() if async_mode else http.close())
