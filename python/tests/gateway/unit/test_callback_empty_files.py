"""Empty published upload maps choose JSON, even after live callback edits."""
import inspect
import json
from email.parser import BytesParser
from email.policy import default

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway.callbacks.base import CallbackHandler

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("operation", ["clear", "assign_empty", "assign_none"])
async def test_empty_upload_files_fall_back_to_json(async_mode, redact, operation):
    sent, completed = [], []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            if operation == "clear":
                request.files.clear()
            else:
                request.files = {} if operation == "assign_empty" else None
            completed.append(True)

    def serve(request):
        sent.append(request)
        return httpx.Response(200, json={"text": "ok"})

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key="synthetic-sdk-key",
        base_url="https://gateway.example.test", http_client=http, callbacks=[Edit()],
        redact_messages=redact, max_retries=0)
    try:
        await resolve(client.audio.transcriptions.create(model="test", file=("original.wav", b"original"), prompt="p"))
        assert completed == [True] and len(sent) == 1
        if redact and operation != "clear":
            data = b"Content-Type: " + sent[0].headers["content-type"].encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + sent[0].content
            parts = BytesParser(policy=default).parsebytes(data).iter_parts()
            files = {p.get_param("name", header="content-disposition"): (p.get_filename(), p.get_payload(decode=True)) for p in parts}
            assert files["file"] == ("original.wav", b"original")
        else:
            assert sent[0].headers["content-type"] == "application/json"
            assert json.loads(sent[0].content) == {"model": "test", "prompt": "p"}
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("files", [None, {}])
@pytest.mark.parametrize("normalized", [False, True])
def test_empty_file_encoding_is_consistent_across_request_builders(files, normalized):
    from fi.gateway._transport._base import RequestOptions, send_arguments
    from fi.gateway._transport._sync import SyncBaseClient

    body = {"model": "test", "nested": {"visible": True}}
    options = RequestOptions("POST", "/v1/test", files=files,
        body=None if normalized else body, form={"model": "test"} if normalized else None)
    transport = SyncBaseClient(api_key="synthetic-sdk-key", base_url="https://gateway.example.test")
    headers = {"Content-Type": "application/json"}
    args = send_arguments(options, headers)
    if normalized and files is not None:
        assert args == {"files": {}, "data": {"model": "test"}}
        assert "Content-Type" not in headers
        assert transport._request_arguments(options)[0]["data"] == options.form
        with pytest.raises(TypeError):
            transport._build_request(options)
    else:
        assert args == {"json": options.body} and headers["Content-Type"] == "application/json"
        raw = transport._build_request(options)
        # The released send passed ``json=``; inspection keeps its own encoder.
        sent = transport._request_arguments(options)[0]
        assert sent["json"] == options.body and "content" not in sent
        if not normalized:
            assert json.loads(raw.content) == body
