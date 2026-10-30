"""Tests for SDK-level batch/parallel completion utilities."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from fi.gateway._client import AsyncAgentCC, AgentCC
from fi.gateway.types.chat.chat_completion import ChatCompletion

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_URL = "https://batch.test"


def _make_sync_client() -> AgentCC:
    return AgentCC(api_key="sk-test", base_url=BASE_URL)


def _make_async_client() -> AsyncAgentCC:
    return AsyncAgentCC(api_key="sk-test", base_url=BASE_URL)


def _chat_response(*, model: str = "gpt-4o", content: str = "Hello!") -> dict:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1700000000,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
    }


# ---------------------------------------------------------------------------
# batch_completion tests
# ---------------------------------------------------------------------------


class TestBatchCompletion:
    @respx.mock
    def test_batch_completion_basic(self) -> None:
        """3 prompts produce 3 results."""
        from fi.gateway._batch import batch_completion

        route = respx.post(f"{BASE_URL}/v1/chat/completions").respond(
            200, json=_chat_response()
        )
        client = _make_sync_client()
        messages_list = [
            [{"role": "user", "content": f"Prompt {i}"}] for i in range(3)
        ]
        results = batch_completion(client, "gpt-4o", messages_list)
        assert len(results) == 3
        assert route.call_count == 3
        for r in results:
            assert isinstance(r, ChatCompletion)
            assert r.choices[0].message.content == "Hello!"

    @respx.mock
    def test_batch_completion_preserves_order(self) -> None:
        """Results match input order even though futures may complete out of order."""
        from fi.gateway._batch import batch_completion

        call_count = 0

        def _side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            body = json.loads(request.content)
            user_msg = body["messages"][0]["content"]
            call_count += 1
            return httpx.Response(
                200,
                json=_chat_response(content=f"Reply to {user_msg}"),
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=_side_effect)
        client = _make_sync_client()
        messages_list = [
            [{"role": "user", "content": f"Prompt-{i}"}] for i in range(5)
        ]
        results = batch_completion(client, "gpt-4o", messages_list)
        for i, r in enumerate(results):
            assert isinstance(r, ChatCompletion)
            assert r.choices[0].message.content == f"Reply to Prompt-{i}"

    def test_batch_completion_empty_list(self) -> None:
        """Empty messages_list returns empty list without any HTTP calls."""
        from fi.gateway._batch import batch_completion

        client = _make_sync_client()
        results = batch_completion(client, "gpt-4o", [])
        assert results == []

    @respx.mock
    def test_batch_completion_single_item(self) -> None:
        from fi.gateway._batch import batch_completion

        respx.post(f"{BASE_URL}/v1/chat/completions").respond(
            200, json=_chat_response()
        )
        client = _make_sync_client()
        results = batch_completion(
            client, "gpt-4o", [[{"role": "user", "content": "Solo"}]]
        )
        assert len(results) == 1
        assert isinstance(results[0], ChatCompletion)

    @respx.mock
    def test_batch_completion_return_exceptions_true(self) -> None:
        """When return_exceptions=True, failed requests appear as exceptions in list."""
        from fi.gateway._batch import batch_completion

        call_idx = 0

        def _side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_idx
            current = call_idx
            call_idx += 1
            body = json.loads(request.content)
            user_msg = body["messages"][0]["content"]
            if "fail" in user_msg:
                return httpx.Response(
                    500, json={"error": {"message": "server error"}}
                )
            return httpx.Response(200, json=_chat_response(content=f"ok-{current}"))

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=_side_effect)
        client = _make_sync_client()
        messages_list = [
            [{"role": "user", "content": "good-0"}],
            [{"role": "user", "content": "fail-1"}],
            [{"role": "user", "content": "good-2"}],
        ]
        results = batch_completion(
            client, "gpt-4o", messages_list, return_exceptions=True
        )
        assert len(results) == 3
        assert isinstance(results[0], ChatCompletion)
        assert isinstance(results[1], Exception)
        assert isinstance(results[2], ChatCompletion)

    @respx.mock
    def test_batch_completion_return_exceptions_false_raises(self) -> None:
        """When return_exceptions=False (default), first failure raises immediately."""
        from fi.gateway._batch import batch_completion
        from fi.gateway._exceptions import InternalServerError

        respx.post(f"{BASE_URL}/v1/chat/completions").respond(
            500, json={"error": {"message": "server error"}}
        )
        client = _make_sync_client()
        messages_list = [
            [{"role": "user", "content": f"Prompt-{i}"}] for i in range(3)
        ]
        with pytest.raises(InternalServerError):
            batch_completion(client, "gpt-4o", messages_list)

    @respx.mock
    def test_batch_completion_passes_kwargs(self) -> None:
        """Extra kwargs are forwarded to each create() call."""
        from fi.gateway._batch import batch_completion

        route = respx.post(f"{BASE_URL}/v1/chat/completions").respond(
            200, json=_chat_response()
        )
        client = _make_sync_client()
        messages_list = [[{"role": "user", "content": "Hi"}]]
        batch_completion(
            client, "gpt-4o", messages_list, temperature=0.5, max_tokens=100
        )
        body = json.loads(route.calls[0].request.content)
        assert body["temperature"] == 0.5
        assert body["max_tokens"] == 100


# ---------------------------------------------------------------------------
# abatch_completion tests
# ---------------------------------------------------------------------------


class TestAbatchCompletion:
    @respx.mock
    @pytest.mark.anyio
    async def test_abatch_completion_basic(self) -> None:
        from fi.gateway._batch import abatch_completion

        respx.post(f"{BASE_URL}/v1/chat/completions").respond(
            200, json=_chat_response()
        )
        client = _make_async_client()
        messages_list = [
            [{"role": "user", "content": f"Prompt {i}"}] for i in range(3)
        ]
        results = await abatch_completion(client, "gpt-4o", messages_list)
        assert len(results) == 3
        for r in results:
            assert isinstance(r, ChatCompletion)

    @respx.mock
    @pytest.mark.anyio
    async def test_abatch_completion_preserves_order(self) -> None:
        from fi.gateway._batch import abatch_completion

        def _side_effect(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            user_msg = body["messages"][0]["content"]
            return httpx.Response(
                200, json=_chat_response(content=f"Reply to {user_msg}")
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=_side_effect)
        client = _make_async_client()
        messages_list = [
            [{"role": "user", "content": f"Prompt-{i}"}] for i in range(4)
        ]
        results = await abatch_completion(client, "gpt-4o", messages_list)
        for i, r in enumerate(results):
            assert isinstance(r, ChatCompletion)
            assert r.choices[0].message.content == f"Reply to Prompt-{i}"

    @respx.mock
    @pytest.mark.anyio
    async def test_abatch_completion_return_exceptions(self) -> None:
        from fi.gateway._batch import abatch_completion

        def _side_effect(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            user_msg = body["messages"][0]["content"]
            if "fail" in user_msg:
                return httpx.Response(
                    500, json={"error": {"message": "server error"}}
                )
            return httpx.Response(200, json=_chat_response())

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=_side_effect)
        client = _make_async_client()
        messages_list = [
            [{"role": "user", "content": "good"}],
            [{"role": "user", "content": "fail"}],
            [{"role": "user", "content": "good"}],
        ]
        results = await abatch_completion(
            client, "gpt-4o", messages_list, return_exceptions=True
        )
        assert len(results) == 3
        assert isinstance(results[0], ChatCompletion)
        assert isinstance(results[1], Exception)
        assert isinstance(results[2], ChatCompletion)


# ---------------------------------------------------------------------------
# batch_completion_models tests
# ---------------------------------------------------------------------------


class TestBatchCompletionModels:
    @respx.mock
    def test_batch_completion_models_returns_first(self) -> None:
        """Mock 3 models; verify we get exactly one ChatCompletion result."""
        from fi.gateway._batch import batch_completion_models

        def _side_effect(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            return httpx.Response(
                200, json=_chat_response(model=body["model"])
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=_side_effect)
        client = _make_sync_client()
        result = batch_completion_models(
            client,
            models=["gpt-4o", "claude-3-opus", "gemini-pro"],
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert isinstance(result, ChatCompletion)
        # The model should be one of the three
        assert result.model in {"gpt-4o", "claude-3-opus", "gemini-pro"}

    @respx.mock
    def test_batch_completion_models_all_fail(self) -> None:
        """When all models fail, the last exception is raised."""
        from fi.gateway._batch import batch_completion_models
        from fi.gateway._exceptions import InternalServerError

        respx.post(f"{BASE_URL}/v1/chat/completions").respond(
            500, json={"error": {"message": "server error"}}
        )
        client = _make_sync_client()
        with pytest.raises(InternalServerError):
            batch_completion_models(
                client,
                models=["bad-a", "bad-b"],
                messages=[{"role": "user", "content": "Hi"}],
            )


# ---------------------------------------------------------------------------
# batch_completion_models_all tests
# ---------------------------------------------------------------------------


class TestBatchCompletionModelsAll:
    @respx.mock
    def test_batch_completion_models_all_basic(self) -> None:
        """3 models produce 3 results."""
        from fi.gateway._batch import batch_completion_models_all

        def _side_effect(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            return httpx.Response(
                200, json=_chat_response(model=body["model"])
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=_side_effect)
        client = _make_sync_client()
        results = batch_completion_models_all(
            client,
            models=["gpt-4o", "claude-3-opus", "gemini-pro"],
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert len(results) == 3
        # Verify ordering matches input models list
        for i, model_name in enumerate(["gpt-4o", "claude-3-opus", "gemini-pro"]):
            assert isinstance(results[i], ChatCompletion)
            assert results[i].model == model_name

    @respx.mock
    def test_batch_completion_models_all_return_exceptions(self) -> None:
        from fi.gateway._batch import batch_completion_models_all

        def _side_effect(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            if body["model"] == "bad-model":
                return httpx.Response(
                    500, json={"error": {"message": "server error"}}
                )
            return httpx.Response(
                200, json=_chat_response(model=body["model"])
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=_side_effect)
        client = _make_sync_client()
        results = batch_completion_models_all(
            client,
            models=["gpt-4o", "bad-model", "gemini-pro"],
            messages=[{"role": "user", "content": "Hi"}],
            return_exceptions=True,
        )
        assert len(results) == 3
        assert isinstance(results[0], ChatCompletion)
        assert isinstance(results[1], Exception)
        assert isinstance(results[2], ChatCompletion)


# ---------------------------------------------------------------------------
# Async model variants
# ---------------------------------------------------------------------------


class TestAbatchCompletionModels:
    @respx.mock
    @pytest.mark.anyio
    async def test_abatch_completion_models_returns_first(self) -> None:
        from fi.gateway._batch import abatch_completion_models

        def _side_effect(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            return httpx.Response(
                200, json=_chat_response(model=body["model"])
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=_side_effect)
        client = _make_async_client()
        result = await abatch_completion_models(
            client,
            models=["gpt-4o", "claude-3-opus"],
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert isinstance(result, ChatCompletion)
        assert result.model in {"gpt-4o", "claude-3-opus"}

    @respx.mock
    @pytest.mark.anyio
    async def test_abatch_completion_models_all_fail(self) -> None:
        from fi.gateway._batch import abatch_completion_models
        from fi.gateway._exceptions import InternalServerError

        respx.post(f"{BASE_URL}/v1/chat/completions").respond(
            500, json={"error": {"message": "server error"}}
        )
        client = _make_async_client()
        with pytest.raises(InternalServerError):
            await abatch_completion_models(
                client,
                models=["bad-a", "bad-b"],
                messages=[{"role": "user", "content": "Hi"}],
            )


class TestAbatchCompletionModelsAll:
    @respx.mock
    @pytest.mark.anyio
    async def test_abatch_completion_models_all_basic(self) -> None:
        from fi.gateway._batch import abatch_completion_models_all

        def _side_effect(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            return httpx.Response(
                200, json=_chat_response(model=body["model"])
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=_side_effect)
        client = _make_async_client()
        results = await abatch_completion_models_all(
            client,
            models=["gpt-4o", "claude-3-opus"],
            messages=[{"role": "user", "content": "Hi"}],
        )
        assert len(results) == 2
        assert isinstance(results[0], ChatCompletion)
        assert results[0].model == "gpt-4o"
        assert isinstance(results[1], ChatCompletion)
        assert results[1].model == "claude-3-opus"


# ---------------------------------------------------------------------------
# Lazy import tests
# ---------------------------------------------------------------------------


class TestLazyImports:
    def test_batch_completion_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.batch_completion)

    def test_abatch_completion_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.abatch_completion)

    def test_batch_completion_models_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.batch_completion_models)

    def test_abatch_completion_models_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.abatch_completion_models)

    def test_batch_completion_models_all_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.batch_completion_models_all)

    def test_abatch_completion_models_all_importable(self) -> None:
        import fi.gateway as agentcc

        assert callable(agentcc.abatch_completion_models_all)

    def test_from_import(self) -> None:
        from fi.gateway import batch_completion

        assert callable(batch_completion)

    def test_from_import_async(self) -> None:
        from fi.gateway import abatch_completion

        assert callable(abatch_completion)
