import inspect

import httpx
import pytest

from fi.errors import ServerError

pytestmark = pytest.mark.asyncio


async def test_root_registers_all_resources_on_one_transport(resources):
    root = resources.root
    assert root.annotation_labels is root.scores.labels
    for name in ("prompts", "knowledge_bases", "scores", "annotation_labels"):
        namespace = getattr(root, name)
        assert namespace._client is root.generated_client
        assert await resources.call(namespace.list) == {"ok": True}
    assert len(resources.requests) == 4


async def test_with_options_rebinds_resources_and_inherits_configuration(resources):
    root = resources.root
    clone = root.with_options(timeout=2, retries=0)
    assert clone.annotation_labels is clone.scores.labels
    for name in ("prompts", "knowledge_bases", "scores", "annotation_labels"):
        namespace = getattr(clone, name)
        assert namespace is not getattr(root, name)
        assert namespace._client is clone.generated_client
        await resources.call(namespace.list)
    assert all(req.extensions["timeout"]["read"] == 2 for req in resources.requests)
    if hasattr(clone, "aclose"):
        await clone.aclose()
    else:
        clone.close()
    assert await resources.call(root.prompts.list) == {"ok": True}


async def test_create_never_retries_a_server_failure(resources):
    root = resources.root.with_options(retries=2)
    resources.replies.append(httpx.Response(503, json={"detail": "unavailable"}))
    with pytest.raises(ServerError):
        await resources.call(root.prompts.create, {"name": "hello", "prompt_config": [{"messages": []}]})
    assert len(resources.requests) == 1
    if hasattr(root, "aclose"):
        await root.aclose()
    else:
        root.close()


async def test_sync_async_public_method_parity(resources):
    from fi.prompts import AsyncPromptsClient, PromptsClient
    from fi.knowledge_bases import AsyncKnowledgeBasesClient, KnowledgeBasesClient
    from fi.scores import AsyncScoresClient, ScoresClient

    def public_methods(cls):
        return {name for name, value in inspect.getmembers(cls, callable) if not name.startswith("_")}

    for sync, asynchronous in [(PromptsClient, AsyncPromptsClient), (KnowledgeBasesClient, AsyncKnowledgeBasesClient), (ScoresClient, AsyncScoresClient)]:
        assert public_methods(sync) == public_methods(asynchronous)
