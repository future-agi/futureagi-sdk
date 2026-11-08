"""Option copies share management pools owned and closed by the original client."""
import asyncio

import httpx
import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.errors import BadRequestError


class ClosingMock(httpx.MockTransport):
    def __init__(self, handler):
        super().__init__(handler)
        self.close_calls = 0

    def close(self):
        self.close_calls += 1
        super().close()

    async def aclose(self):
        self.close_calls += 1
        await super().aclose()


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("warm", [False, True])
@pytest.mark.parametrize("status", [200, 400])
@pytest.mark.parametrize("context", [False, True])
def test_option_copy_management_pool_ownership(asynchronous, warm, status, context):
    async def run():
        cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
        parent = cls(api_key="api-fixture", secret_key="secret-fixture",
                     base_url="http://localhost:9012", retries=0)
        assert "_management" not in parent.__dict__
        if warm:
            parent._management
        copy = parent.with_options(timeout=7, retries=0)
        shared = copy._management.shared
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(status, json={"status": False, "result": {
                "error_code": "validation_failed", "message": "denied",
            }}, headers={"X-Request-Id": "trace-fixture-id", "Retry-After": "9"})

        mock = ClosingMock(handler)
        shared._recorder._inner = mock
        copies = [copy]

        async def close(client):
            if asynchronous:
                await client.aclose()
            else:
                client.close()

        async def request(client, *, raw=False):
            resource = client.gateway.config.with_raw_response if raw else client.gateway.config
            with pytest.raises(BadRequestError) as caught:
                result = resource.get_active()
                if asynchronous:
                    await result
            assert caught.value.request_id == "trace-fixture-id"
            assert caught.value.retry_after == 9

        try:
            # No management connection pool is allocated until a request is made.
            assert shared._http is None and shared._ahttp is None
            if context:
                if asynchronous:
                    await parent.__aenter__()
                else:
                    parent.__enter__()
            await request(copy, raw=True)
            assert len(calls) == 1
            assert calls[0].extensions["timeout"]["read"] == 7
            pool = shared._ahttp if asynchronous else shared._http
            assert pool is not None and not pool.is_closed
            await close(copy)
            assert not pool.is_closed and mock.close_calls == 0
            owner = parent.__dict__.get("_management")
            assert owner is not None and owner.shared is shared

            # Siblings and nested copies must not allocate independent pools, even
            # when the intermediate copy has already been closed.
            sibling = parent.with_options(timeout=11, retries=0)
            nested = copy.with_options(retries=0)
            copies.extend([sibling, nested])
            for client in (sibling, nested, parent):
                assert client._management.shared is shared
                await request(client)
                assert (shared._ahttp if asynchronous else shared._http) is pool
            assert len(calls) == 4
            assert calls[1].extensions["timeout"]["read"] == 11
            assert calls[2].extensions["timeout"]["read"] == 7
            assert calls[3].extensions["timeout"]["read"] == 30
            await close(sibling)
            assert not pool.is_closed and mock.close_calls == 0

            if context:
                if asynchronous:
                    await parent.__aexit__(None, None, None)
                else:
                    parent.__exit__(None, None, None)
            else:
                await close(parent)
            assert pool.is_closed
            assert mock.close_calls == 1
            await close(nested)
            await close(parent)
            assert mock.close_calls == 1
        finally:
            for client in copies:
                await close(client)
            await close(parent)
            # Also reclaim an unowned pool when running against the old behavior.
            if asynchronous:
                await shared.aclose()
            else:
                shared.close()

    asyncio.run(run())
