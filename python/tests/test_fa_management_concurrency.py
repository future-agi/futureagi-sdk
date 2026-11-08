"""Concurrent first use keeps management state owned by one parent client."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from unittest.mock import patch

import httpx
import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi._core import fa_registration
from fi.errors import BadRequestError

from tests.test_fa_management_lifecycle import ClosingMock


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("warm", [False, True])
@pytest.mark.parametrize("raw", [False, True])
@pytest.mark.parametrize("mode", ["success", "envelope", "http"])
@pytest.mark.parametrize("entry", ["copies", "mixed"])
def test_concurrent_management_first_use(asynchronous, warm, raw, mode, entry):
    async def run():
        cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
        parent = cls(api_key="api-fixture", secret_key="secret-fixture",
                     base_url="http://localhost:9012", retries=0)
        assert "_management" not in parent.__dict__
        if warm:
            parent._management
        start = threading.Barrier(2)
        overlap = threading.Event()
        made = []
        original = fa_registration.make_core

        def factory(client, **kwargs):
            assert client is parent
            core = original(client, **kwargs)
            made.append(core)
            if len(made) == 2:
                overlap.set()
            # Give a competing cold lookup a bounded opportunity to enter. The
            # initializer must not require a second factory call to make progress.
            overlap.wait(timeout=0.1)
            return core

        def first_use(index):
            start.wait(timeout=5)
            if entry == "mixed" and index == 0:
                parent.gateway
                return parent
            return parent.with_options(timeout=3 + index, retries=0)

        with patch.object(fa_registration, "make_core", side_effect=factory) as spy:
            with ThreadPoolExecutor(max_workers=2) as workers:
                clients = list(workers.map(first_use, (0, 1)))
            factory_calls = spy.call_count
            assert factory_calls == len(made)
            assert factory_calls == 0 if warm else factory_calls >= 1

        shared_states = {id(c._management.shared): c._management.shared
                         for c in [*clients, parent]}
        mocks = []
        failing = mode != "success"
        payload = ({"status": False, "result": {
            "error_code": "validation_failed", "message": "denied"}}
            if failing else {"status": True, "result": None})
        for shared in shared_states.values():
            calls = []

            def handler(request, calls=calls):
                calls.append(request)
                return httpx.Response(400 if mode == "http" else 200, json=payload,
                                      headers={"X-Request-Id": "trace-fixture-id"})

            mock = ClosingMock(handler)
            shared._recorder._inner = mock
            mocks.append((mock, calls))
            assert shared._http is None and shared._ahttp is None

        async def close(client):
            if asynchronous:
                await client.aclose()
            else:
                client.close()

        try:
            for client in [*clients, parent]:
                resource = client.gateway.config.with_raw_response if raw else client.gateway.config

                async def invoke():
                    result = resource.get_active()
                    return await result if asynchronous else result

                if failing:
                    with pytest.raises(BadRequestError) as caught:
                        await invoke()
                    assert caught.value.request_id == "trace-fixture-id"
                else:
                    result = await invoke()
                    assert (result.data if raw else result) is None
            assert sum(len(calls) for _, calls in mocks) == 3
            pools = [s._ahttp if asynchronous else s._http for s in shared_states.values()]
            assert all(pool is not None and not pool.is_closed for pool in pools)
            for client in clients:
                if client is not parent:
                    await close(client)
            assert all(not pool.is_closed for pool in pools)
            assert all(mock.close_calls == 0 for mock, _ in mocks)
            await close(parent)
            assert all(pool.is_closed for pool in pools)
            assert all(mock.close_calls == 1 for mock, _ in mocks)
            assert len(shared_states) == 1
            assert all(c._management.shared is parent._management.shared for c in clients)
            assert factory_calls == (0 if warm else 1)
            await close(parent)
            assert all(mock.close_calls == 1 for mock, _ in mocks)
        finally:
            for client in [*clients, parent]:
                await close(client)
            # Reclaim every state even when checking unsynchronized initialization.
            for shared in shared_states.values():
                if asynchronous:
                    await shared.aclose()
                else:
                    shared.close()

    asyncio.run(run())


@pytest.mark.parametrize("asynchronous", [False, True])
def test_management_initializers_on_distinct_parents_do_not_block(asynchronous):
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    parents = [cls(api_key="api-fixture", secret_key="secret-fixture",
                   base_url="http://localhost:9012", retries=0) for _ in range(2)]
    entered = threading.Barrier(2)
    original = fa_registration.make_core

    def factory(client, **kwargs):
        # cached_property on older Python serializes the descriptor itself. Test
        # the initializer directly there so the per-parent guard is independent
        # of that older implementation detail.
        entered.wait(timeout=5)
        return original(client, **kwargs)

    def initialize(client):
        return type(client)._management.func(client)

    try:
        with patch.object(fa_registration, "make_core", side_effect=factory) as spy:
            with ThreadPoolExecutor(max_workers=2) as workers:
                cores = list(workers.map(initialize, parents))
            assert spy.call_count == 2
        assert cores[0].shared is not cores[1].shared
        for core in cores:
            assert core.shared._http is None and core.shared._ahttp is None
            core.shared.close()
    finally:
        for parent in parents:
            if asynchronous:
                asyncio.run(parent.aclose())
            else:
                parent.close()


@pytest.mark.parametrize("asynchronous", [False, True])
def test_management_initialization_can_retry_after_factory_error(asynchronous):
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    parent = cls(api_key="api-fixture", secret_key="secret-fixture",
                 base_url="http://localhost:9012", retries=0)
    original = fa_registration.make_core
    try:
        with patch.object(fa_registration, "make_core", side_effect=ValueError("factory-fixture")) as spy:
            with pytest.raises(ValueError, match="factory-fixture"):
                parent._management
            assert spy.call_count == 1
        assert "_management" not in parent.__dict__
        with patch.object(fa_registration, "make_core", wraps=original) as spy:
            core = parent._management
            assert parent._management is core
            assert spy.call_count == 1
    finally:
        if asynchronous:
            asyncio.run(parent.aclose())
        else:
            parent.close()
