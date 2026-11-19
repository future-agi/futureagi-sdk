"""Root clients load the generated platform contract without a fixture operation table."""

import asyncio

import httpx
import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.errors import NotFoundError, PlatformNotConfiguredError
from fi.generated.platform.policy import OPERATIONS

CAPABILITIES = "platform.capabilities.get"
OPTIONS = {
    "api_key": "k-test-1234",
    "secret_key": "s-test-1234",
    "base_url": "http://127.0.0.1:9",
    "workspace_id": "ws-test",
    "organization_id": "org-test",
    "retries": 0,
}


def recorder(status=200):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(status, json={"products": []}, headers={"x-request-id": "req-contract"})

    return requests, httpx.MockTransport(respond)


def assert_request(request):
    operation = OPERATIONS[CAPABILITIES]
    assert request.method == operation.method
    assert str(request.url) == "http://127.0.0.1:9/omega/api" + operation.path
    assert request.headers["x-api-key"] == OPTIONS["api_key"]
    assert request.headers["x-secret-key"] == OPTIONS["secret_key"]
    assert request.headers["x-workspace-id"] == OPTIONS["workspace_id"]
    assert request.headers["x-organization-id"] == OPTIONS["organization_id"]
    assert "idempotency-key" not in request.headers


def test_sync_client_and_copy_load_the_generated_contract():
    requests, transport = recorder()
    with FutureAGIClient(**OPTIONS) as client:
        client._platform.shared._recorder._inner = transport
        quick = client.with_options(timeout=0.5, retries=0)
        assert requests == []
        assert quick._platform.call(CAPABILITIES) == {"products": []}
        assert client._platform.call(CAPABILITIES) == {"products": []}
        assert quick._platform.shared is client._platform.shared
        assert client._platform.shared.table is OPERATIONS
        assert quick._platform.settings.timeout.read == 0.5
        assert client._platform.settings.timeout.read == 30.0
    assert len(requests) == 2
    for request in requests:
        assert_request(request)


def test_async_client_and_copy_load_the_generated_contract():
    async def run():
        requests, transport = recorder()
        async with AsyncFutureAGIClient(**OPTIONS) as client:
            client._platform.shared._recorder._inner_async = transport
            quick = client.with_options(timeout=0.5, retries=0)
            assert requests == []
            assert await quick._platform.call(CAPABILITIES) == {"products": []}
            assert await client._platform.call(CAPABILITIES) == {"products": []}
            assert quick._platform.shared is client._platform.shared
            assert client._platform.shared.table is OPERATIONS
            assert quick._platform.settings.timeout.read == 0.5
            assert client._platform.settings.timeout.read == 30.0
        assert len(requests) == 2
        for request in requests:
            assert_request(request)

    asyncio.run(run())


def test_generated_operation_maps_server_errors_and_refuses_unknown_names():
    requests, transport = recorder(404)
    with FutureAGIClient(**OPTIONS) as client:
        client._platform.shared._recorder._inner = transport
        with pytest.raises(NotFoundError):
            client._platform.call(CAPABILITIES)
        with pytest.raises(PlatformNotConfiguredError):
            client._platform.call("not.an.operation")
    assert len(requests) == 1
