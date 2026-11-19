"""Per-request retry classes in fi._http: request.extensions["fi.retry"]."""

import asyncio

import httpx
import pytest

from fi._http import AsyncRetryingTransport, ClientRetryingTransport, RetryingTransport, request_retry_policy


def _sync(statuses, ext=None, method="POST", retries=3):
    calls, sleeps = [], []

    def handler(request):
        calls.append(request.method)
        return httpx.Response(statuses[min(len(calls) - 1, len(statuses) - 1)])

    transport = RetryingTransport(httpx.MockTransport(handler), retries=retries, sleep=sleeps.append)
    client = httpx.Client(transport=transport, base_url="http://api.test")
    kwargs = {"extensions": {"fi.retry": ext}} if ext is not None else {}
    response = client.request(method, "/x", json={"a": 1}, **kwargs)
    return response.status_code, len(calls), len(sleeps)


@pytest.mark.parametrize("status", [500, 502, 503, 504])
@pytest.mark.parametrize("cls", ["unsafe", "keyed-not-durable"])
def test_unsafe_and_non_durable_never_retry_a_5xx(cls, status):
    assert _sync([status, 200], cls) == (status, 1, 0)


@pytest.mark.parametrize("cls", ["unsafe", "keyed-not-durable", "keyed", "http-idempotent"])
def test_every_class_retries_429(cls):
    assert _sync([429, 200], cls) == (200, 2, 1)


@pytest.mark.parametrize("status", [502, 503, 504])
@pytest.mark.parametrize("cls", ["keyed", "http-idempotent"])
def test_keyed_and_idempotent_retry_gateway_errors_on_post(cls, status):
    assert _sync([status, 200], cls, method="POST") == (200, 2, 1)


def test_no_class_retries_a_5xx_only_on_idempotent_methods():
    # a 5xx on a POST may mean the request ran, so it is never repeated
    for status in (502, 503, 504):
        assert _sync([status, 200], method="POST") == (status, 1, 0)
        assert _sync([status, 200], method="PATCH") == (status, 1, 0)
        for method in ("GET", "PUT", "DELETE"):
            assert _sync([status, 200], method=method) == (200, 2, 1)
    assert _sync([429, 200], method="POST") == (200, 2, 1)  # 429: every method
    assert _sync([500, 200], method="GET") == (500, 1, 0)


def test_mapping_form_overrides_the_retry_count():
    assert _sync([429, 429, 429, 200], {"class": "unsafe", "retries": 1}) == (429, 2, 1)
    assert _sync([503, 200], {"retries": 0}, method="GET") == (503, 1, 0)
    assert _sync([503, 503, 200], {"retries": 1}, method="GET") == (503, 2, 1)  # count only, default rule


@pytest.mark.parametrize("bad", ["Unsafe", "idempotent", 3, {"class": "unsafe", "retries": -1}])
def test_unknown_class_is_an_error_not_a_silent_retry(bad):
    request = httpx.Request("POST", "http://api.test/x", extensions={"fi.retry": bad})
    with pytest.raises(ValueError):
        request_retry_policy(request)


def _error_then_201(error, cls=None, method="POST"):
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            raise error(request)
        return httpx.Response(201)

    transport = RetryingTransport(httpx.MockTransport(handler), retries=3, sleep=lambda s: None)
    kwargs = {"extensions": {"fi.retry": cls}} if cls else {}
    try:
        status = httpx.Client(transport=transport).request(method, "http://api.test/x", **kwargs).status_code
    except httpx.TransportError as exc:
        status = type(exc).__name__
    return status, len(calls)


REFUSED = lambda request: httpx.ConnectError("refused", request=request)  # noqa: E731
CONNECT_TIMEOUT = lambda request: httpx.ConnectTimeout("connect timed out", request=request)  # noqa: E731
RESET = lambda request: httpx.ReadError("connection reset", request=request)  # noqa: E731
CLOSED = lambda request: httpx.RemoteProtocolError("server closed the connection", request=request)  # noqa: E731
READ_TIMEOUT = lambda request: httpx.ReadTimeout("read timed out", request=request)  # noqa: E731


@pytest.mark.parametrize("cls", [None, "unsafe", "keyed-not-durable", "keyed", "http-idempotent"])
@pytest.mark.parametrize("error", [REFUSED, CONNECT_TIMEOUT], ids=["refused", "connect-timeout"])
def test_pre_send_errors_are_retried_in_every_class(cls, error):
    # S7: ConnectTimeout is pre-send too (TypeScript retries UND_ERR_CONNECT_TIMEOUT)
    assert _error_then_201(error, cls) == (201, 2)


@pytest.mark.parametrize("error", [RESET, CLOSED], ids=["reset", "closed"])
def test_a_network_error_after_sending_follows_the_class(error):
    # S7: the same table as TypeScript's shouldRetryNetworkError
    assert _error_then_201(error, "keyed") == (201, 2)
    assert _error_then_201(error, "http-idempotent") == (201, 2)
    assert _error_then_201(error, None, method="GET") == (201, 2)
    assert _error_then_201(error, None, method="POST")[1] == 1
    assert _error_then_201(error, "unsafe")[1] == 1
    assert _error_then_201(error, "keyed-not-durable", method="GET")[1] == 1


@pytest.mark.parametrize("cls", [None, "keyed", "http-idempotent"])
def test_a_read_timeout_is_never_retried(cls):
    assert _error_then_201(READ_TIMEOUT, cls, method="GET") == ("ReadTimeout", 1)


def test_async_transport_honours_the_class():
    async def go(cls, statuses):
        calls = []

        async def handler(request):
            calls.append(1)
            return httpx.Response(statuses[min(len(calls) - 1, len(statuses) - 1)])

        async def no_sleep(_):
            return None

        transport = AsyncRetryingTransport(httpx.MockTransport(handler), retries=3, sleep=no_sleep)
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.post("http://api.test/x", extensions={"fi.retry": cls})
        return response.status_code, len(calls)

    assert asyncio.run(go("unsafe", [503, 200])) == (503, 1)
    assert asyncio.run(go("keyed", [503, 200])) == (200, 2)


def test_client_transport_passes_the_class_to_both_sides():
    calls = []

    def handler(request):
        calls.append(request.method)
        return httpx.Response(503)

    mock = httpx.MockTransport(handler)
    transport = ClientRetryingTransport(retries=2, wrapped=mock, wrapped_async=mock, backoff_base_s=0)
    response = httpx.Client(transport=transport).get("http://api.test/x", extensions={"fi.retry": "unsafe"})
    assert (response.status_code, len(calls)) == (503, 1)
    calls.clear()
    assert httpx.Client(transport=transport).get("http://api.test/x").status_code == 503
    assert len(calls) == 3  # no class, GET: 503 retried twice

    async def go(ext):
        calls.clear()
        async with httpx.AsyncClient(transport=transport) as client:
            kwargs = {"extensions": {"fi.retry": ext}} if ext else {}
            response = await client.get("http://api.test/x", **kwargs)
        return response.status_code, len(calls)

    assert asyncio.run(go("unsafe")) == (503, 1)  # S7: the async side honours the class too
    assert asyncio.run(go(None)) == (503, 3)


def _clean_env(monkeypatch):
    for var in ("FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL", "FI_PLATFORM_BASE_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", "/nonexistent/futureagi-test-login.json")


def test_dataset_version_create_makes_one_attempt_on_a_503(monkeypatch):
    """DatasetVersionsClient says "Create makes one attempt"; a retried
    POST could create a second immutable snapshot. A GET on the same client is still retried."""
    from fi import FutureAGIClient
    from fi.errors import FutureAGIAPIError
    from fi.generated.openapi_client.models.dataset_version_create import DatasetVersionCreate

    _clean_env(monkeypatch)
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path))
        return httpx.Response(503, json={"detail": "busy"})

    client = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://api.test")
    transport = client.generated_client._httpx_args["transport"]
    transport._wrapped = httpx.MockTransport(handler)
    transport.backoff_base_s = 0
    dataset = "3f2c1d7e-0000-4000-8000-000000000001"
    with pytest.raises(FutureAGIAPIError) as info:
        client.datasets.versions.create(dataset, body=DatasetVersionCreate(items=[]))
    assert info.value.status_code == 503
    assert calls == [("POST", f"/model-hub/datasets/{dataset}/versions/")]
    calls.clear()
    with pytest.raises(FutureAGIAPIError):
        client.datasets.versions.list(dataset)
    assert [method for method, _ in calls] == ["GET"] * 4  # 1 + 3 retries


def test_async_client_post_makes_one_attempt_on_a_503(monkeypatch):
    from fi import AsyncFutureAGIClient
    from fi.errors import ServerError

    _clean_env(monkeypatch)
    calls = []

    def handler(request):
        calls.append(request.method)
        return httpx.Response(503, json={"detail": "busy"})

    client = AsyncFutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://api.test")
    transport = client.generated_client._httpx_args["transport"]
    transport._wrapped_async = httpx.MockTransport(handler)
    transport.backoff_base_s = 0

    async def go():
        try:
            await client.request("POST", "/x", body={"a": 1})
        finally:
            await client.aclose()

    with pytest.raises(ServerError):
        asyncio.run(go())
    assert calls == ["POST"]
