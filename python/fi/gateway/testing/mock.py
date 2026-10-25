"""MockAgentCC — drop-in test replacement for the AgentCC client."""

from __future__ import annotations

from typing import Any

from fi.gateway._exceptions import AgentCCError
from fi.gateway.testing.fixtures import make_completion, make_agentcc_metadata
from fi.gateway.types.chat.chat_completion import ChatCompletion


class _MockChatCompletions:
    """Mock chat completions that returns pre-configured responses."""

    def __init__(self) -> None:
        self._responses: list[ChatCompletion | Exception] = []
        self._calls: list[dict[str, Any]] = []
        self._index = 0

    def respond_with(self, response: ChatCompletion | Exception) -> None:
        """Register a response to return on the next create() call."""
        self._responses.append(response)

    def create(self, **kwargs: Any) -> ChatCompletion:
        """Return the next registered response."""
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
    """Mock chat namespace."""

    def __init__(self) -> None:
        self._completions = _MockChatCompletions()

    @property
    def completions(self) -> _MockChatCompletions:
        return self._completions


class MockAgentCC:
    """Drop-in test replacement for AgentCC.

    Usage::

        from fi.gateway.testing import MockAgentCC, mock_completion

        client = MockAgentCC()
        client.chat.completions.respond_with(mock_completion("Hello!"))
        result = client.chat.completions.create(model="gpt-4o", messages=[...])
        assert result.choices[0].message.content == "Hello!"
    """

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
    content: str = "Hello!",
    model: str = "gpt-4o",
    provider: str = "openai",
    cost: float | None = None,
    cache_status: str | None = None,
    **kwargs: Any,
) -> ChatCompletion:
    """Create a mock ChatCompletion with sensible defaults."""
    agentcc = make_agentcc_metadata(provider=provider, cost=cost, cache_status=cache_status)
    return make_completion(content=content, model=model, agentcc=agentcc, **kwargs)


def mock_error(status_code: int = 500, message: str = "Internal error", code: str | None = None) -> AgentCCError:
    """Create a mock API error."""
    from fi.gateway._exceptions import _STATUS_CODE_MAP, APIStatusError

    cls = _STATUS_CODE_MAP.get(status_code, APIStatusError)
    return cls(status_code=status_code, message=message, type="error", code=code, param=None, response=None, body=None, request_id=None)


def create_mock_client(
    responses: dict[str, Any] | None = None,
    api_key: str = "sk-test-mock",
    base_url: str = "https://mock.agentcc.test",
) -> Any:
    """Create a mock AgentCC client for testing.

    Args:
        responses: Dict mapping URL patterns to response data.
            Key is a URL path like "/v1/chat/completions".
            Value is a dict that will be returned as JSON.
        api_key: API key for the mock client.
        base_url: Base URL for the mock client.

    Returns:
        A AgentCC client instance configured for testing. The ``_mock_responses``
        attribute holds the response mapping that users can extend.

    Usage::

        from fi.gateway.testing import create_mock_client

        client = create_mock_client(responses={
            "/v1/chat/completions": {"id": "chatcmpl-test", ...}
        })
    """
    from fi.gateway._client import AgentCC

    client = AgentCC(api_key=api_key, base_url=base_url)
    client._mock_responses = responses or {}  # type: ignore[attr-defined]
    return client
