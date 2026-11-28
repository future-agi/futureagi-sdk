"""Caller request hooks on the httpx client a generated client builds, and the drop of its credentials off origin.

The generated ``AuthenticatedClient`` and ``Client`` run a request hook of their own that removes the token header,
``Authorization``, ``Cookie``, ``X-Api-Key`` and ``X-Secret-Key`` from a request to an origin other than
``base_url``'s. A caller that gives request hooks through ``httpx_args`` ``event_hooks``, or appends to
``event_hooks["request"]`` of the built httpx client, keeps that drop: origin B, reached by a 302 from origin A, reads no
byte of the marker. Assigning a new ``event_hooks`` mapping on the built httpx client replaces the SDK's hook, and B
reads the marker; the 0.9.0 CHANGELOG states this next to ``set_httpx_client`` with the two ways to keep the drop.

Both origins are loopback listeners on 127.0.0.1; the marker is made per test with ``secrets.token_hex``.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any, Iterator
from unittest import mock

import pytest

from fi.errors import FutureAGIError
from fi.generated.openapi_client import AuthenticatedClient, Client
from tests.core._plaintext_oracle import PROXY_NAMES
from tests.core.test_generated_client_redirect_origin import Listener

CHANGELOG = Path(__file__).resolve().parents[2] / "CHANGELOG.md"
KINDS = ["authenticated", "client"]
WAYS = ["httpx_args_event_hooks", "appended_request_hook"]


@pytest.fixture()
def direct_env() -> Iterator[None]:
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, clean, clear=True):
        yield


@pytest.fixture()
def origins() -> Iterator[tuple[Listener, Listener]]:
    target = Listener()
    origin = Listener(location=f"{target.origin}/landed")
    yield origin, target
    origin.close()
    target.close()


def _make(kind: str, origin: Listener, marker: str, httpx_args: dict[str, Any]) -> Any:
    if kind == "authenticated":
        return AuthenticatedClient(
            base_url=origin.origin, token=marker, prefix="", auth_header_name="X-Api-Key",
            follow_redirects=True, timeout=30.0, httpx_args=httpx_args,
        )
    return Client(
        base_url=origin.origin, headers={"X-Api-Key": marker}, follow_redirects=True, timeout=30.0,
        httpx_args=httpx_args,
    )


def _marker_bytes(listener: Listener, marker: str) -> int:
    return sum(raw.count(marker.encode()) for _, raw in listener.requests) * len(marker)


def _send(client: Any, way: str, seen: list[str]) -> None:
    def caller_hook(request: Any) -> None:
        seen.append(str(request.url))

    built = client.get_httpx_client()
    if way == "appended_request_hook":
        built.event_hooks["request"].append(caller_hook)
    elif way == "assigned_event_hooks":
        built.event_hooks = {"request": [caller_hook], "response": []}
    try:
        built.get("/start")
    except FutureAGIError:
        pass


async def _send_async(client: Any, way: str, seen: list[str]) -> None:
    async def caller_hook(request: Any) -> None:
        seen.append(str(request.url))

    built = client.get_async_httpx_client()
    if way == "appended_request_hook":
        built.event_hooks["request"].append(caller_hook)
    elif way == "assigned_event_hooks":
        built.event_hooks = {"request": [caller_hook], "response": []}
    try:
        await built.get("/start")
    except FutureAGIError:
        pass


def _hooks_for(way: str, seen: list[str], is_async: bool) -> dict[str, Any]:
    if way != "httpx_args_event_hooks":
        return {}
    if is_async:
        async def caller_hook(request: Any) -> None:
            seen.append(str(request.url))
    else:
        def caller_hook(request: Any) -> None:
            seen.append(str(request.url))
    return {"event_hooks": {"request": [caller_hook]}}


@pytest.mark.parametrize("way", WAYS)
@pytest.mark.parametrize("kind", KINDS)
def test_caller_request_hooks_keep_the_off_origin_drop(direct_env, origins, kind, way):
    origin, target = origins
    marker, seen = secrets.token_hex(20), []
    with _make(kind, origin, marker, _hooks_for(way, seen, False)) as client:
        _send(client, way, seen)
    assert marker.encode() in origin.requests[0][1]
    assert [path for path, _ in target.requests] == ["/landed"]
    assert len(seen) == 2, seen
    assert _marker_bytes(target, marker) == 0


@pytest.mark.anyio
@pytest.mark.parametrize("way", WAYS)
@pytest.mark.parametrize("kind", KINDS)
async def test_async_caller_request_hooks_keep_the_off_origin_drop(direct_env, origins, kind, way):
    origin, target = origins
    marker, seen = secrets.token_hex(20), []
    async with _make(kind, origin, marker, _hooks_for(way, seen, True)) as client:
        await _send_async(client, way, seen)
    assert marker.encode() in origin.requests[0][1]
    assert [path for path, _ in target.requests] == ["/landed"]
    assert len(seen) == 2, seen
    assert _marker_bytes(target, marker) == 0


@pytest.mark.parametrize("kind", KINDS)
def test_assigned_event_hooks_replace_the_drop_as_the_changelog_states(direct_env, origins, kind):
    origin, target = origins
    marker, seen = secrets.token_hex(20), []
    with _make(kind, origin, marker, {}) as client:
        _send(client, "assigned_event_hooks", seen)
    assert _marker_bytes(target, marker) == len(marker)
    changelog = CHANGELOG.read_text(encoding="utf-8")
    _, heading, section = changelog.partition("\n## 0.9.0\n")
    assert heading, "Missing 0.9.0 changelog section"
    text = " ".join(section.split("\n## ", 1)[0].split())
    assert (
        "Assigning `event_hooks` on the httpx client either generated client builds (for example"
        " `client.get_httpx_client().event_hooks = {...}`) also removes this drop; to keep it, give request hooks"
        " through `httpx_args` `event_hooks` (they run before the drop), or append to `event_hooks[\"request\"]`"
        " (an appended hook runs after the drop, so use that form for a hook that reads the request and adds no"
        " header)."
    ) in text
