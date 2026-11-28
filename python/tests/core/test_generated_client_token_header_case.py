"""The generated ``AuthenticatedClient`` sends its own token once, under its own token header, whatever the case of a
header of the same name in the caller's ``headers``.

httpx sends both of two header names that differ in case only. A caller that builds client B from the headers of
another client A (``dict(a.get_httpx_client().headers)``, whose names httpx lowercases) or that spells the token header
in another case would otherwise send A's token next to B's own to B's host. Each client has its own plain-http
loopback listener that the client sends to direct; the tokens are planted markers made in the test, and B's listener
counts the bytes of A's token it receives.
"""

from __future__ import annotations

import asyncio
import os
import secrets
from typing import Iterator
from unittest import mock

import httpx
import pytest

from fi.generated.openapi_client import AuthenticatedClient
from tests.core._plaintext_oracle import PROXY_NAMES, Sink

# (A's token header, B's token header, prefix of both): the caller copies A's headers into B.
HEADER_PAIRS = [
    ("Authorization", "Authorization", "Bearer"),
    ("X-Api-Key", "X-Api-Key", ""),
    ("X-Fi-Token", "X-Fi-Token", ""),
    ("Authorization", "X-Api-Key", ""),
]
SPELLINGS = ["copied", "upper", "swapcase"]


@pytest.fixture()
def pair_sinks() -> Iterator[dict[str, Sink]]:
    made = {"A": Sink(), "B": Sink()}
    yield made
    for each in made.values():
        each.close()


@pytest.fixture()
def direct_env() -> Iterator[None]:
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, clean, clear=True):
        yield


def _url(sink: Sink) -> str:
    return f"http://127.0.0.1:{sink.port}"


def _send(client: AuthenticatedClient, builder: str) -> None:
    if builder == "sync":
        built = client.get_httpx_client()
        try:
            built.get("/probe/")
        finally:
            built.close()
        return

    async def run() -> None:
        built = client.get_async_httpx_client()
        try:
            await built.get("/probe/")
        finally:
            await built.aclose()

    asyncio.run(run())


def _callers_headers(a: AuthenticatedClient, a_header: str, spelling: str, builder: str) -> dict[str, str]:
    """A's token header as the caller passes it to B: copied from A's built httpx client (lowercase names), or
    spelled in upper case or with each letter's case swapped."""
    built = a.get_httpx_client() if builder == "sync" else a.get_async_httpx_client()
    copied = dict(built.headers)
    if spelling == "copied":
        return copied
    value = copied[a_header.lower()]
    name = a_header.upper() if spelling == "upper" else a_header.swapcase()
    return {"X-Common": "shared-value", name: value}


@pytest.mark.parametrize("builder", ["sync", "async"])
@pytest.mark.parametrize("spelling", SPELLINGS)
@pytest.mark.parametrize("a_header,b_header,prefix", HEADER_PAIRS)
def test_client_built_from_another_clients_headers_sends_only_its_own_token(
    a_header, b_header, prefix, spelling, builder, pair_sinks, direct_env
):
    marker_a = "MARKERKEY-A-" + secrets.token_hex(16)
    marker_b = "MARKERKEY-B-" + secrets.token_hex(16)
    a = AuthenticatedClient(
        base_url=_url(pair_sinks["A"]), token=marker_a, prefix=prefix, auth_header_name=a_header,
        timeout=httpx.Timeout(30),
    )
    given = _callers_headers(a, a_header, spelling, builder)
    snapshot = dict(given)
    _send(a, builder)
    b = AuthenticatedClient(
        base_url=_url(pair_sinks["B"]), token=marker_b, prefix=prefix, auth_header_name=b_header, headers=given,
        timeout=httpx.Timeout(30),
    )
    _send(b, builder)

    b_chunks = pair_sinks["B"].chunks
    b_lines = [line.lower() for chunk in b_chunks for line in chunk.split(b"\r\n")]
    observed = {
        "a_marker_bytes_at_b": sum(chunk.count(marker_a.encode()) for chunk in b_chunks) * len(marker_a),
        "b_token_per_request": [chunk.count(marker_b.encode()) for chunk in b_chunks],
        "b_token_header_lines": sum(1 for line in b_lines if line.startswith(b_header.lower().encode() + b":")),
        "a_token_at_a": sum(chunk.count(marker_a.encode()) for chunk in pair_sinks["A"].chunks),
        "callers_dict": given,
    }
    assert observed == {
        "a_marker_bytes_at_b": 0,
        "b_token_per_request": [1],
        "b_token_header_lines": 1,
        "a_token_at_a": 1,
        "callers_dict": snapshot,
    }
