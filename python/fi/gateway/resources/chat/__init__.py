"""Chat resource — wraps completions sub-resource."""

from __future__ import annotations

from functools import cached_property
from typing import Any

from fi.gateway.resources.chat.completions import AsyncChatCompletions, ChatCompletions


class Chat:
    """Sync chat resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    @cached_property
    def completions(self) -> ChatCompletions:
        return ChatCompletions(self._client)


class AsyncChat:
    """Async chat resource."""

    def __init__(self, client: Any) -> None:
        self._client = client

    @cached_property
    def completions(self) -> AsyncChatCompletions:
        return AsyncChatCompletions(self._client)
