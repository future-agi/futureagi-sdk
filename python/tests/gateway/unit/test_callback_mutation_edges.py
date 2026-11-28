"""Boundary cases for shared callback containers and caller-owned records."""

import json

import pytest

from fi.gateway.callbacks.base import CallbackHandler

from .test_published_callback_mutations import client_for, offline, resolve

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings("ignore::DeprecationWarning")]


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("operation", ["insert", "delete", "slice", "replace", "equal_reverse"])
async def test_list_edits_keep_credentials_with_their_records(async_mode, redact, operation):
    calls = []
    captured = []
    first = {"name": "same" if operation == "equal_reverse" else "first", "password": "first-placeholder"}
    second = {"name": "same" if operation == "equal_reverse" else "second", "password": "second-placeholder"}
    added = {"name": "added"}
    expected = {
        "insert": [added, first, second],
        "delete": [second],
        "slice": [second, added, first],
        "replace": [added, second],
        "equal_reverse": [second, first],
    }[operation]

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            calls.append(True)
            records = request.body["metadata"]["records"]
            captured.extend(record["password"] for record in records)
            if operation == "insert":
                records.insert(0, {"name": "added"})
            elif operation == "delete":
                del records[0]
            elif operation == "slice":
                records[:] = [records[1], {"name": "added"}, records[0]]
            elif operation == "replace":
                records[0] = {"name": "added"}
            else:
                records.reverse()

    async with client_for(async_mode, Edit(), redact=redact) as (client, seen):
        await resolve(client.chat.completions.create(
            model="test", messages=[], metadata={"records": [dict(first), dict(second)]}))
    assert calls == [True]
    assert captured == ["first-placeholder", "second-placeholder"]
    assert json.loads(seen[0].content)["metadata"]["records"] == expected


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("redact", [False, True])
@pytest.mark.parametrize("route", ["transcriptions", "translations"])
async def test_shared_header_file_edits_precede_descriptor_replacement(async_mode, redact, route):
    calls = []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            calls.append(request.headers["Authorization"])
            request.headers["X-Original"] = "mutated"
            request.headers["X-Added"] = "present"
            request.headers = {"X-Replaced": "replacement"}
            request.files["file"] = ("mutated.wav", b"mutated")
            request.files = {"file": ("replacement.wav", b"replacement")}

    async with client_for(async_mode, Edit(), redact=redact) as (client, seen):
        await resolve(getattr(client.audio, route).create(
            model="test", file=("original.wav", b"original"), prompt="private text",
            extra_headers={"X-Original": "original", "Authorization": "Bearer header-placeholder"}))
    assert calls == ["Bearer header-placeholder"]
    assert seen[0].headers["authorization"] == ("Bearer header-placeholder" if redact else "Bearer unit-key")
    if redact:
        assert seen[0].headers["x-original"] == "mutated"
        assert seen[0].headers["x-added"] == "present"
        assert "x-replaced" not in seen[0].headers
        assert b'filename="mutated.wav"' in seen[0].content
        assert b'filename="replacement.wav"' not in seen[0].content
    else:
        assert "x-original" not in seen[0].headers
        assert "x-added" not in seen[0].headers
        assert seen[0].headers["x-replaced"] == "replacement"
        assert b'filename="replacement.wav"' in seen[0].content


@pytest.mark.parametrize("async_mode", [False, True])
async def test_redacted_copied_fields_and_replaced_nested_fields_stay_detached(async_mode):
    calls = []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            message = request.body["messages"][0]
            function = message["tool_calls"][0]["function"]
            legacy = message["function_call"]
            calls.append((message["content"], function["arguments"], message["annotations"]["password"]))
            message["role"] = "user"
            message["content"] = "replacement text"
            message["annotations"]["label"] = "shared edit"
            message["annotations"]["password"] = "[REDACTED]"
            message["annotations"] = {"label": "detached replacement"}
            function["name"] = "replacement name"
            function["arguments"] = "replacement arguments"
            function["schema"]["label"] = "shared edit"
            function["schema"] = {"label": "detached replacement"}
            legacy["schema"]["label"] = "shared edit"
            legacy["arguments"] = "replacement arguments"
            request.body["messages"].clear()
            request.body = {"messages": []}

    message = {
        "role": "assistant", "content": "private text",
        "annotations": {"label": "original", "password": "annotation-placeholder"},
        "tool_calls": [{"id": "call", "type": "function", "function": {
            "name": "tool", "arguments": "private arguments", "schema": {"label": "original"}}}],
        "function_call": {"name": "legacy", "arguments": "private arguments", "schema": {"label": "original"}},
    }
    async with client_for(async_mode, Edit()) as (client, seen):
        await resolve(client.chat.completions.create(model="test", messages=[message]))
    assert calls == [("[REDACTED]", "[REDACTED]", "annotation-placeholder")]
    wire = json.loads(seen[0].content)["messages"][0]
    assert wire["role"] == "assistant" and wire["content"] == "private text"
    assert wire["annotations"] == {"label": "shared edit", "password": "[REDACTED]"}
    assert wire["tool_calls"][0]["function"] == {
        "name": "tool", "arguments": "private arguments", "schema": {"label": "shared edit"}}
    assert wire["function_call"] == {
        "name": "legacy", "arguments": "private arguments", "schema": {"label": "shared edit"}}


@pytest.mark.parametrize("async_mode", [False, True])
async def test_live_record_identity_survives_multiple_hooks(async_mode):
    from .test_callback_live_semantics import client_for as live_client

    record = {"name": "before", "password": "synthetic-caller"}
    rows = [record, record]
    observed = []
    descriptors = []

    class Edit(CallbackHandler):
        def on_request_start(self, request):
            descriptors.append(request)
            visible = request.body["metadata"]["records"]
            visible.reverse()
            visible[0]["name"] = "edited"
            record["added"] = "caller update"
            observed.append(visible is rows and visible[0] is visible[1] is record)

        def on_request_end(self, request, response):
            descriptors.append(request)
            visible = request.body["metadata"]["records"]
            observed.append(visible[1]["added"] == "caller update")
            visible.insert(0, {"name": "new"})

    async with live_client(async_mode, [Edit()], True) as (client, seen):
        await resolve(client.chat.completions.create(model="test", messages=[], metadata={"records": rows}))
    assert observed == [True, True]
    assert descriptors[0] is descriptors[1]
    assert rows == [{"name": "new"}, record, record]
    assert record == {"name": "edited", "password": "synthetic-caller", "added": "caller update"}
