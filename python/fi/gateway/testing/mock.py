"""MockAgentCC and an HTTP-mapped client that never falls through to the network."""

from __future__ import annotations

from typing import Any

from fi.gateway._exceptions import AgentCCError
from fi.gateway.testing.fixtures import make_agentcc_metadata, make_completion
from fi.gateway.types.chat.chat_completion import ChatCompletion


class _MockChatCompletions:
    def __init__(self) -> None:
        self._responses: list[ChatCompletion | Exception] = []
        self._calls: list[dict[str, Any]] = []
        self._index = 0

    def respond_with(self, response: ChatCompletion | Exception) -> None:
        self._responses.append(response)

    def create(self, **kwargs: Any) -> ChatCompletion:
        self._calls.append(kwargs)
        if not self._responses:
            return make_completion(agentcc=make_agentcc_metadata())
        idx = min(self._index, len(self._responses) - 1)
        self._index += 1
        resp = self._responses[idx]
        if isinstance(resp, Exception):
            raise resp
        return resp

    @property
    def calls(self) -> list[dict[str, Any]]:
        return self._calls


class _MockChat:
    def __init__(self) -> None:
        self._completions = _MockChatCompletions()

    @property
    def completions(self) -> _MockChatCompletions:
        return self._completions


class MockAgentCC:
    """In-memory chat completion fake."""

    def __init__(self) -> None:
        self._chat = _MockChat()

    @property
    def chat(self) -> _MockChat:
        return self._chat

    def close(self) -> None:
        pass

    def __enter__(self) -> MockAgentCC:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def mock_completion(
    content: str = "Hello!", model: str = "gpt-4o", provider: str = "openai",
    cost: float | None = None, cache_status: str | None = None, **kwargs: Any,
) -> ChatCompletion:
    agentcc = make_agentcc_metadata(provider=provider, cost=cost, cache_status=cache_status)
    return make_completion(content=content, model=model, agentcc=agentcc, **kwargs)


def mock_error(status_code: int = 500, message: str = "Internal error", code: str | None = None) -> AgentCCError:
    from fi.gateway._exceptions import _STATUS_CODE_MAP, APIStatusError

    cls = _STATUS_CODE_MAP.get(status_code, APIStatusError)
    return cls(status_code=status_code, message=message, type="error", code=code, param=None, response=None, body=None, request_id=None)


def create_mock_client(
    responses: dict[str, Any] | None = None,
    api_key: str = "sk-test-mock", base_url: str = "https://mock.agentcc.test",
) -> Any:
    """Create a real client using only MockTransport; unmapped paths return 404.

    The _mock_responses mapping remains live and values may be callables.
    """
    import httpx
    from fi.gateway._client import AgentCC

    mapping: dict[str, Any] = dict(responses or {})

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path in mapping:
            body = mapping[path]
            return httpx.Response(200, json=body() if callable(body) else body)
        return httpx.Response(404, json={"error": {
            "message": f"create_mock_client has no response for {request.method} {path}",
            "type": "mock_not_found",
        }})

    client = AgentCC(
        api_key=api_key, base_url=base_url,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)), max_retries=0,
    )
    client._mock_responses = mapping
    return client
