"""``chat.completions.stream()`` and ``client.session()`` are annotated with what they return.

agentcc 1.0 annotated both ``-> Any``. The annotations name the classes, imported for
real so runtime introspection resolves them as type checkers do; the installed-wheel
mypy and pyright run on scripts/gateway/typing_fixture.py shows what users see. Here:
the annotation text, that it resolves to the class actually returned, and that the
module names are those classes.
"""

from __future__ import annotations

import inspect
import typing

import httpx

from fi.gateway import AgentCC, AsyncAgentCC, SessionContext
from fi.gateway._streaming import AsyncStreamManager, StreamManager
from fi.gateway.resources.chat.completions import AsyncChatCompletions, ChatCompletions

GW = "http://127.0.0.1:8090"
SSE = b'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[]}\n\ndata: [DONE]\n\n'
NS = {
    "StreamManager": StreamManager,
    "AsyncStreamManager": AsyncStreamManager,
    "SessionContext": SessionContext,
}


def _hint(fn: typing.Any) -> typing.Any:
    return typing.get_type_hints(fn, globalns={**vars(inspect.getmodule(fn)), **NS})[
        "return"
    ]


def test_the_annotations_name_the_returned_classes() -> None:
    assert (
        inspect.signature(ChatCompletions.stream).return_annotation == "StreamManager"
    )
    assert (
        inspect.signature(AsyncChatCompletions.stream).return_annotation
        == "AsyncStreamManager"
    )
    for cls in (AgentCC, AsyncAgentCC):
        assert inspect.signature(cls.session).return_annotation == "SessionContext"
    assert _hint(ChatCompletions.stream) is StreamManager
    assert _hint(AsyncChatCompletions.stream) is AsyncStreamManager
    assert _hint(AgentCC.session) is SessionContext


def test_what_they_return_matches_the_annotation() -> None:
    client = AgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.Client(
            transport=httpx.MockTransport(
                lambda r: httpx.Response(
                    200, headers={"content-type": "text/event-stream"}, content=SSE
                )
            )
        ),
    )
    assert isinstance(client.session(name="s"), SessionContext)
    with client.chat.completions.stream(model="m", messages=[]) as manager:
        assert isinstance(manager, StreamManager)


async def test_the_async_ones_too() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=SSE
        )

    client = AsyncAgentCC(
        api_key="k",
        base_url=GW,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    assert isinstance(client.session(name="s"), SessionContext)
    async with await client.chat.completions.stream(model="m", messages=[]) as m:
        assert isinstance(m, AsyncStreamManager)


def test_create_results_and_copies_are_annotated_with_what_they_return() -> None:
    """agentcc 1.0 annotated create() ``-> ChatCompletion | Any`` and with_options() with
    the base class. create() now names its three results (a completion, a stream, and the
    stream manager mock_response streams return, the sync one for both clients), and
    with_options() returns the class it is called on, so a subclass's copy is that
    subclass."""
    from fi.gateway._streaming import AsyncStream, Stream
    from fi.gateway.types.chat.chat_completion import ChatCompletion

    assert (
        inspect.signature(ChatCompletions.create).return_annotation
        == "ChatCompletion | _Stream | StreamManager"
    )
    assert (
        inspect.signature(AsyncChatCompletions.create).return_annotation
        == "ChatCompletion | _AsyncStream | _StreamManager"
    )
    hints = typing.get_type_hints(ChatCompletions.create)
    assert hints["return"] == ChatCompletion | Stream | StreamManager
    hints = typing.get_type_hints(AsyncChatCompletions.create)
    assert hints["return"] == ChatCompletion | AsyncStream | StreamManager
    for cls in (AgentCC, AsyncAgentCC):
        assert inspect.signature(cls.with_options).return_annotation == "_Self"

        class Custom(cls):  # type: ignore[valid-type, misc]
            pass

        copy = Custom(api_key="k", base_url=GW).with_options(timeout=1)
        assert type(copy) is Custom


def test_the_annotation_names_are_the_classes_at_run_time() -> None:
    """The names are real imports, so runtime introspection resolves them too
    (test_gw_runtime_type_hints.py sweeps every public annotation)."""
    import fi.gateway._client as sync_client
    import fi.gateway.resources.chat.completions as completions

    assert vars(sync_client)["SessionContext"] is SessionContext
    assert vars(completions)["StreamManager"] is StreamManager
