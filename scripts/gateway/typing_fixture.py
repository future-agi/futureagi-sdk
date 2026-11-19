"""Typing proof fixture: what mypy and pyright see of fi.gateway from an installed wheel.

``reveal_type`` under mypy and pyright against the installed wheel; if either reports
``Any`` for these, fi.gateway's types do not reach users (PEP 561 reads the ``py.typed``
marker of the top-level package, ``fi``), and ``python/fi/py.typed`` is needed as well.
Run outside the source tree, in a venv holding only the wheel and the checker:

    mypy --strict typing_fixture.py      pyright typing_fixture.py

Expected (each line's revealed type contains):
    AgentCC -> "type[fi.gateway._client.AgentCC]"
    current_cost -> "float"
    error -> "fi.gateway._exceptions.AgentCCError"
    kwargs -> "dict[str, Any]" / "dict[builtins.str, Any]"
    metadata -> "AgentCCMetadata"
    client.chat -> "Chat"; async_client.chat.completions -> "AsyncChatCompletions"
    completion -> "ChatCompletion" (the 1.0 annotation, ``ChatCompletion | Any``)
    client.session(...) -> "SessionContext"; async_client.session(...) -> "SessionContext"
    client.chat.completions.stream(...) -> "StreamManager"
    async_client.chat.completions.stream -> "... -> Coroutine[Any, Any, AsyncStreamManager]";
        the awaited call -> "AsyncStreamManager"
    the StreamManager's and the AsyncStreamManager's events -> "StreamEvent";
    the session's Session -> "Session"

Both checkers exit 0 on this file: the reveals are notes, not errors.

agentcc 1.0 typed every client resource property, ``session()`` and
``chat.completions.stream()`` as ``Any``; the clients now give type checkers each one's
class.
"""

from __future__ import annotations

from fi.gateway import (
    AgentCC,
    AgentCCError,
    AgentCCMetadata,
    AsyncAgentCC,
    openai_kwargs,
)

client = AgentCC(api_key="gw-key", base_url="http://127.0.0.1:8090")
async_client = AsyncAgentCC(api_key="k", base_url="http://x")
reveal_type(AgentCC)  # noqa: F821
reveal_type(client.current_cost)  # noqa: F821
reveal_type(AgentCCError("x"))  # noqa: F821
reveal_type(openai_kwargs(api_key="k", base_url="http://127.0.0.1:8090"))  # noqa: F821
reveal_type(AgentCCMetadata.from_headers({}))  # noqa: F821
reveal_type(client.chat)  # noqa: F821
reveal_type(async_client.chat.completions)  # noqa: F821
reveal_type(client.chat.completions.create(model="m", messages=[]))  # noqa: F821
reveal_type(client.session(name="checkout"))  # noqa: F821
reveal_type(async_client.session(name="checkout"))  # noqa: F821
manager = client.chat.completions.stream(model="m", messages=[])
reveal_type(manager)  # noqa: F821
for event in manager:
    reveal_type(event)  # noqa: F821
with client.session(name="checkout") as session:
    reveal_type(session)  # noqa: F821


async def consume_async_stream() -> None:
    # The method, not a call: reveal_type(<coroutine>) is itself an unused coroutine,
    # which mypy --strict reports as an error.
    reveal_type(async_client.chat.completions.stream)  # noqa: F821
    async_manager = await async_client.chat.completions.stream(model="m", messages=[])
    reveal_type(async_manager)  # noqa: F821
    async for async_event in async_manager:
        reveal_type(async_event)  # noqa: F821
