"""Every status raises the same class on a core namespace and a
platform namespace; an undeclared 429 / 503 on a generated core call raises RateLimitError /
ServerError (never the generated client's UnexpectedStatus); connect errors and timeouts raise
APIConnectionError / APITimeoutError on both."""

from __future__ import annotations

import asyncio
import uuid

import httpx
import pytest

import fi.errors as errors
from fi import AsyncFutureAGIClient, FutureAGIClient
from fi._core.platform_async import AsyncPlatformCore
from fi._core.platform_base import PlatformCore
from fi._core.raw import Namespace
from fi._core.transport import PlatformShared
from tests.core._support import OPS, Recorder, respond

STATUS_CLASSES = [
    (400, errors.BadRequestError),
    (401, errors.AuthenticationError),
    (403, errors.PermissionDeniedError),
    (404, errors.NotFoundError),
    (409, errors.ConflictError),
    (413, errors.PayloadTooLargeError),
    (418, errors.FutureAGIAPIError),
    (422, errors.UnprocessableEntityError),
    (429, errors.RateLimitError),
    (500, errors.ServerError),
    (502, errors.ServerError),
    (503, errors.ServerError),
    (504, errors.ServerError),
]
QUEUE = str(uuid.uuid4())


class Capabilities(Namespace):
    """A minimal platform namespace, shaped like the real ones."""

    def get(self):
        return self._core.call("capabilities.get")


def _client(handler, **kw):
    client = FutureAGIClient(
        api_key="k-test-1234", secret_key="s-test-1234", base_url="http://api.test", retries=0, **kw
    )
    client.generated_client._httpx_args["transport"]._wrapped = httpx.MockTransport(handler)
    client.__dict__["_platform"] = PlatformCore(
        PlatformShared(client._resolve_platform_origin, retries=0, table=OPS, transport=httpx.MockTransport(handler))
    )
    return client


def _core_calls(client):
    return {
        "generated _request": lambda: client.annotation_queues.get(QUEUE),
        "generated _typed_result": lambda: client.datasets.versions.list(QUEUE),
        "raw _raw_request": lambda: client.users.current(),
        "platform": lambda: Capabilities(client._platform).get(),
    }


@pytest.mark.parametrize("status, cls", STATUS_CLASSES)
def test_every_structured_status_is_the_same_class_on_core_and_platform(status, cls):
    def handler(request):
        # Only Console resource errors use an EE envelope; preserve plain FA 404 coverage.
        body = ({"code": "not_found", "message": "nope"}
                if status == 404 and request.url.path.startswith("/omega/api/workspace/") else {"detail": "nope"})
        return respond(status, body, {"X-Request-Id": "req-7"})
    client = _client(handler)
    for path, call in _core_calls(client).items():
        with pytest.raises(errors.FutureAGIAPIError) as info:
            call()
        assert type(info.value) is cls, path
        assert info.value.status_code == status and info.value.request_id == "req-7", path
        assert isinstance(info.value, errors.SDKException)


@pytest.mark.parametrize("status, cls", [(429, errors.RateLimitError), (503, errors.ServerError)])
def test_an_undeclared_429_or_503_on_a_generated_call_is_typed(status, cls):
    # the spec declares neither for these operations: without the status mapping the generated client raised
    # UnexpectedStatus (a non-SDK exception) and the CLI printed a traceback
    client = _client(lambda request: respond(status, "<html>busy</html>", {"Retry-After": "7"}))
    for call in (lambda: client.annotation_queues.get(QUEUE), lambda: client.datasets.versions.list(QUEUE)):
        with pytest.raises(cls) as info:
            call()
        assert info.value.retry_after == 7.0


def test_platform_codes_pick_narrower_classes_and_redact_the_payload():
    answers = {
        "/omega/api/workspace/capabilities": respond(
            404, {"error": "product_not_admitted", "requestId": "g-1", "reason": "not enabled"}
        ),
    }
    client = _client(lambda request: answers[request.url.path])
    with pytest.raises(errors.ProductNotAvailableError) as info:
        Capabilities(client._platform).get()
    err = info.value
    assert isinstance(err, errors.NotFoundError) and err.code == "product_not_admitted" and err.request_id == "g-1"
    assert str(err).startswith("capabilities.get failed with status 404 (product_not_admitted): not enabled")
    assert err.to_dict()["error_code"] == "PRODUCT_NOT_AVAILABLE" and "payload" not in err.to_dict()


def test_reflected_secrets_never_reach_the_error():
    echo = {"code": "bad_request", "message": "bad key k-test-1234 / s-test-1234", "detail": {"token": "t-123456"}}
    client = _client(lambda request: respond(400, echo))
    with pytest.raises(errors.BadRequestError) as info:
        Capabilities(client._platform).get()
    text = str(info.value) + repr(info.value.payload)
    assert "k-test-1234" not in text and "s-test-1234" not in text and "t-123456" not in text


@pytest.mark.parametrize(
    "exc, cls, applied",
    [
        (httpx.ConnectError("refused"), errors.APIConnectionError, False),
        (httpx.ConnectTimeout("connect timed out"), errors.APITimeoutError, False),
        (httpx.ReadTimeout("read timed out"), errors.APITimeoutError, True),
        (httpx.ReadError("reset"), errors.APIConnectionError, True),
    ],
)
def test_no_response_is_api_connection_or_timeout_on_core_and_platform(exc, cls, applied):
    def boom(request):
        raise exc

    client = _client(boom)
    for path, call in _core_calls(client).items():
        with pytest.raises(cls) as info:
            call()
        assert isinstance(info.value, errors.TransportError), path
        assert info.value.possibly_applied is applied, path
        if path != "platform":
            assert isinstance(info.value, type(exc)), path  # still the httpx class it replaces
    with pytest.raises(type(exc)):
        client.annotation_queues.get(QUEUE)


def test_async_core_and_platform_raise_the_same_classes():
    async def go(status):
        client = AsyncFutureAGIClient(
            api_key="k-test-1234", secret_key="s-test-1234", base_url="http://api.test", retries=0
        )
        def handler(request):
            body = ({"code": "not_found", "message": "x"}
                    if status == 404 and request.url.path.startswith("/omega/api/workspace/") else {"detail": "x"})
            return respond(status, body)
        client.generated_client._httpx_args["transport"]._wrapped_async = httpx.MockTransport(handler)
        client.__dict__["_platform"] = AsyncPlatformCore(
            PlatformShared(
                client._resolve_platform_origin, retries=0, table=OPS, transport=httpx.MockTransport(handler)
            )
        )
        out = []
        for call in (lambda: client.request("GET", "/x"), lambda: client._platform.call("capabilities.get")):
            try:
                await call()
            except errors.FutureAGIAPIError as err:
                out.append(type(err))
        await client.aclose()
        return out

    for status, cls in STATUS_CLASSES:
        assert asyncio.run(go(status)) == [cls, cls], status


def test_redirects_are_never_followed_and_name_only_the_host():
    rec = Recorder(respond(302, None, {"Location": "https://evil.example:8443/steal?x=1"}))
    client = _client(rec)
    with pytest.raises(errors.UnexpectedRedirectError) as info:
        Capabilities(client._platform).get()
    assert info.value.target_host == "evil.example:8443" and "steal" not in str(info.value)
    assert len(rec.requests) == 1 and rec.requests[0].url.host == "127.0.0.1"


def test_an_unparsable_success_body_is_a_typed_error_made_once():
    rec = Recorder(respond(201, "not-json", {"content-type": "application/json"}))
    client = _client(rec)
    with pytest.raises(errors.FutureAGIAPIError) as info:
        client.datasets.versions.list(QUEUE)
    assert info.value.code == "invalid_json" and info.value.status_code == 201 and len(rec.requests) == 1
    assert isinstance(info.value, ValueError)  # the generated parse raised ValueError; that still catches it
