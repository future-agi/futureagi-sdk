"""Public-wrapper mutations must affect the same operation-contract runner."""
import asyncio

import httpx
import pytest
from fi.errors import BadRequestError

from ._contract_runtime import Runtime, resolve, success
from .test_operation_contracts import check_wire

PROMPT = {"id": "core:prompts.get", "adapter": "core", "name": "prompts.get",
          "method": "GET", "path": "/model-hub/prompt-templates/{id}/",
          "path_params": ["id"], "content_type": None, "stream": None,
          "idempotent": False, "retry": "http-idempotent",
          "py_operation": "model_hub_prompt_templates_read"}


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("mutation", ["missing", "misroute"])
def test_public_prompt_mutations_fail_the_operation_gate(mode, mutation):
    async def run():
        requests = []
        subject = Runtime(PROMPT, mode, lambda request: requests.append(request) or success(PROMPT))
        if mutation == "missing":
            subject.client.prompts.get = None
        else:
            subject.client.prompts.get = subject.client.prompts.delete
        try:
            if mutation == "missing":
                with pytest.raises((TypeError, AttributeError), match="get|callable"):
                    await resolve(subject.call())
                assert requests == []
            else:
                await resolve(subject.call())
                assert len(requests) == 1
                with pytest.raises(AssertionError):
                    check_wire(PROMPT, requests[0])
        finally:
            await subject.close()
    asyncio.run(run())


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_public_prompt_unwraps_and_maps_http_success_refusal(mode):
    async def run():
        payload = [{"status": True, "result": {"marker": "kept"}}]
        subject = Runtime(PROMPT, mode, lambda _: httpx.Response(200, json=payload[0],
            headers={"X-Request-Id": "contract-envelope"}))
        try:
            assert await resolve(subject.call()) == {"marker": "kept"}
            payload[0] = {"status": False, "code": "invalid", "result": "refused"}
            with pytest.raises(BadRequestError) as caught:
                await resolve(subject.call())
            assert caught.value.request_id == "contract-envelope"
        finally:
            await subject.close()
    asyncio.run(run())
