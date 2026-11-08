"""Replacement metadata and per-key session headers from 0.7.0."""

import json
from contextlib import nullcontext

import pytest

from fi.gateway._constants import NOT_GIVEN
from fi.gateway._session import Session

from ._published_helpers import call_resource, client_for, clear_platform_keys

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_published_session_headers():
    session = Session(session_id="session", name="named", path="/step",
                      metadata={"count": 2, "object": {"k": "v"}, "null": None})
    assert session.to_headers() == {
        "x-agentcc-session-id": "session", "x-agentcc-session-name": "named",
        "x-agentcc-session-path": "/step", "x-agentcc-metadata-count": "2",
        "x-agentcc-metadata-object": "{'k': 'v'}", "x-agentcc-metadata-null": "None",
    }


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("alias", [False, True])
@pytest.mark.parametrize("with_session", [False, True])
async def test_published_replacement_across_resources_and_copies(async_mode, alias, with_session):
    resources = ("chat", "stream", "completions", "responses", "files", "transcriptions", "translations", "speech")
    async with client_for(async_mode, alias=alias, metadata={"client": "kept"}) as (parent, seen):
        client = parent.with_options()
        context = client.session(session_id="session", metadata={"session": "separate"}) if with_session else nullcontext()
        with context:
            for resource in resources:
                for metadata in (NOT_GIVEN, {}, {"request": "only"}, '{"raw":"string"}'):
                    await call_resource(client, resource, request_metadata=metadata)
                    expected = {"client": "kept"} if metadata is NOT_GIVEN else metadata
                    actual = seen[-1].headers["x-agentcc-metadata"]
                    assert actual == expected if isinstance(expected, str) else json.loads(actual) == expected
                    if with_session:
                        assert seen[-1].headers["x-agentcc-metadata-session"] == "separate"
                        assert seen[-1].headers["x-agentcc-session-id"] == "session"
                await call_resource(client, resource, request_metadata={},
                    extra_headers={"x-agentcc-metadata": '{"explicit":"wins"}'})
                assert seen[-1].headers.get_list("x-agentcc-metadata") == ['{"explicit":"wins"}']
                # A differently spelled raw header was sent as its own header line.
                await call_resource(client, resource, request_metadata={},
                    extra_headers={"X-AgentCC-Metadata": '{"explicit":"line"}'})
                assert seen[-1].headers.get_list("x-agentcc-metadata") == ["{}", '{"explicit":"line"}']


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("alias", [False, True])
async def test_merge_mode_is_explicit_and_survives_copies_and_sessions(async_mode, alias):
    async with client_for(async_mode, alias=alias, metadata={"client": 1}, metadata_mode="merge") as (parent, seen):
        client = parent.with_options(metadata={"copy": 1})
        with client.session(metadata={"session": 2}):
            for resource in ("chat", "stream", "completions", "responses", "files", "transcriptions", "translations", "speech"):
                await call_resource(client, resource, request_metadata={})
                assert json.loads(seen[-1].headers["x-agentcc-metadata"]) == {"copy": 1, "session": 2}
                assert "x-agentcc-metadata-session" not in seen[-1].headers
                await call_resource(client, resource, request_metadata={"request": 3})
                assert json.loads(seen[-1].headers["x-agentcc-metadata"]) == {"copy": 1, "session": 2, "request": 3}
                await call_resource(client, resource, request_metadata={},
                                    extra_headers={"x-agentcc-metadata": '{"raw":4}'})
                assert seen[-1].headers.get_list("x-agentcc-metadata") == ['{"raw":4}']


def test_session_header_merge_is_opt_in_without_changing_request_parameters():
    from types import SimpleNamespace
    from fi.gateway._agentcc_params import merge_session_headers

    session = Session(session_id="session", metadata={"session": 1})
    client = SimpleNamespace(_active_session=session, _metadata={"client": 2})
    params = {"request_metadata": {}}
    headers = merge_session_headers(client, {}, params)
    assert params == {"request_metadata": {}}
    assert headers == {"x-agentcc-session-id": "session", "x-agentcc-metadata-session": "1"}
    assert Session(session_id="session", metadata={"session": 1}, metadata_mode="merge").to_headers() == {
        "x-agentcc-session-id": "session", "x-agentcc-metadata": '{"session":1}'}
