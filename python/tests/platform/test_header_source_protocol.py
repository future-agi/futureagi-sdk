"""The extra-header source the platform executor takes (``HeaderSource``) declares every method the
executor calls on it, ``for_url`` and ``without_scope``, with the client's own class's
``without_scope`` signature, so a source written to the protocol alone works: its headers go out,
and the executor hands it the scope header names to drop. No network; made-up header values."""

from __future__ import annotations

import inspect

import pytest
from fi._core.platform_async import AsyncPlatformCore
from fi._core.platform_base import SCOPE_HEADERS, PlatformCore
from fi._core.transport import HeaderSource, PlatformShared
from fi._extra_headers import ExtraHeaders
from fi.sandbox import AsyncSandboxes, Sandboxes
from fi.sandbox._connection import OriginRule

from ._sandbox_mock import MODES, MockServer, origin, resolve, run


class ProtocolOnly:
    """A header source with exactly the protocol's methods and nothing else."""

    __slots__ = ("dropped",)

    def __init__(self) -> None:
        self.dropped: list[set[str]] = []

    def for_url(self, url):
        return {"X-Team": "made-up-team", "X-Workspace-Id": "ws_made_up"}

    def without_scope(self, headers, names):
        self.dropped.append(set(names))
        return {name: value for name, value in headers.items() if name.lower() not in names}


def test_the_protocol_declares_every_method_the_executor_calls():
    declared = {name for name in vars(HeaderSource) if not name.startswith("_")}
    assert declared == {"for_url", "without_scope"}
    assert {name for name in vars(ProtocolOnly) if not name.startswith("_")} == declared | {"dropped"}


def test_without_scope_has_the_client_class_signature():
    declared = inspect.signature(HeaderSource.without_scope)
    assert str(declared) == str(inspect.signature(ExtraHeaders.without_scope))
    assert list(declared.parameters) == ["self", "headers", "names"]


@pytest.mark.parametrize("mode", MODES)
def test_a_source_written_to_the_protocol_works_through_the_executor(mode):
    server, source = MockServer(), ProtocolOnly()
    found = origin("keys")
    shared = PlatformShared(lambda: found, transport=server.transport(), retries=0,
                            sleep=lambda _s: None, backoff_base_s=0.0, extra_headers=source)
    rule = OriginRule(allow_custom_base_url=True)
    sandboxes = (AsyncSandboxes(AsyncPlatformCore(shared), rule=rule) if mode == "async"
                 else Sandboxes(PlatformCore(shared), rule=rule))
    run(resolve(sandboxes.list()))
    sent = server.last.request.headers
    assert server.last.name == "sandboxes.list"
    assert sent["x-team"] == "made-up-team" and "x-workspace-id" not in sent
    assert source.dropped == [set(SCOPE_HEADERS)]
