"""Installed-wheel assertions for plain, streamed, and mocked chat results."""
# pyright: reportUnnecessaryTypeIgnoreComment=error
from typing_extensions import assert_type
from fi.gateway import AgentCC, AsyncAgentCC, Stream, AsyncStream
from fi.gateway._streaming import StreamManager
from fi.gateway.types.chat.chat_completion import ChatCompletion


def sync(client: AgentCC, streaming: bool, mock: str | None) -> None:
    assert_type(client.chat.completions.create(model="test", messages=[]), ChatCompletion)
    assert_type(client.chat.completions.create(model="test", messages=[], stream=False), ChatCompletion)
    assert_type(client.chat.completions.create(model="test", messages=[], stream=True), Stream)
    assert_type(client.chat.completions.create(model="test", messages=[], stream=True, mock_response="ok"), StreamManager)
    assert_type(client.chat.completions.create(model="test", messages=[], stream=streaming, mock_response=mock), ChatCompletion | Stream | StreamManager)
    assert_type(client.chat.completions.create(model="test", messages=[], mock_response="ok"), ChatCompletion)
    client.chat.completions.create(model="test", messages=[], extra_headers=42)  # type: ignore
    client.chat.completions.create(model="test", messages=[], properties=42, stream=True)  # type: ignore
    client.chat.completions.create(model="test", messages=[], user_id=[], stream=True, mock_response="ok")  # type: ignore
    client.chat.completions.create(model="test", messages=[], extra_headers=42, stream=streaming)  # type: ignore
    client.chat.completions.create(model="test", messages=[], request_id=42)  # type: ignore
    client.chat.completions.create(model="test", messages=[], extra_body=42)  # type: ignore
    client.chat.completions.create(model="test", messages=[], mock_response=42)  # type: ignore


async def asynchronous(client: AsyncAgentCC, streaming: bool, mock: str | None) -> None:
    assert_type(await client.chat.completions.create(model="test", messages=[]), ChatCompletion)
    assert_type(await client.chat.completions.create(model="test", messages=[], stream=False), ChatCompletion)
    assert_type(await client.chat.completions.create(model="test", messages=[], stream=True), AsyncStream)
    # Frozen mock_response streaming returns the sync manager even for AsyncAgentCC.
    assert_type(await client.chat.completions.create(model="test", messages=[], stream=True, mock_response="ok"), StreamManager)
    assert_type(await client.chat.completions.create(model="test", messages=[], stream=streaming, mock_response=mock), ChatCompletion | AsyncStream | StreamManager)
    assert_type(await client.chat.completions.create(model="test", messages=[], mock_response="ok"), ChatCompletion)
    await client.chat.completions.create(model="test", messages=[], extra_headers=42)  # type: ignore
    await client.chat.completions.create(model="test", messages=[], properties=42, stream=True)  # type: ignore
    await client.chat.completions.create(model="test", messages=[], user_id=[], stream=True, mock_response="ok")  # type: ignore
    await client.chat.completions.create(model="test", messages=[], extra_headers=42, stream=streaming)  # type: ignore
    await client.chat.completions.create(model="test", messages=[], request_id=42)  # type: ignore
    await client.chat.completions.create(model="test", messages=[], extra_body=42)  # type: ignore
    await client.chat.completions.create(model="test", messages=[], mock_response=42)  # type: ignore


class CustomClient(AgentCC):
    pass


class CustomAsyncClient(AsyncAgentCC):
    pass


def copies(client: CustomClient, asynchronous: CustomAsyncClient) -> None:
    assert_type(client.with_options(), CustomClient)
    assert_type(asynchronous.with_options(), CustomAsyncClient)
