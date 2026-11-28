"""The generated ``AuthenticatedClient`` B sends only its own token when a caller gives it the headers of another
tenant's client A, whatever the copy and whatever the way the headers reach B.

A sends its token under its own token header and also carries a ``Cookie`` and an ``X-Secret-Key`` header. The caller
copies A's headers into B as ``dict(a.get_httpx_client().headers)``, as the ``httpx.Headers`` object itself, as
``dict(...headers.raw)`` (bytes names), or by hand with text or bytes names in upper, lower or swapped letter case,
for token header names that match between A and B and for names that differ (A's ``X-Api-Key`` into B's
``Authorization`` and others). The headers reach B through the constructor, ``with_headers`` on an unbuilt B,
``with_headers`` on a B whose httpx client is built (that same httpx client sends), the client ``with_headers``
returns from a built B, and ``attrs.evolve``. B's host, a plain-http loopback listener the client sends to direct,
receives no byte of A's marker and B's own token once in each request, sync and async. The markers are made in the
test, a distinct one per tenant.
"""

from __future__ import annotations

import asyncio
import os
import secrets
from typing import Any, Callable, Iterator
from unittest import mock

import attrs
import httpx
import pytest

from fi.generated.openapi_client import AuthenticatedClient
from tests.core._plaintext_oracle import PROXY_NAMES, Sink

# (A's token header, A's prefix, B's token header, B's prefix)
NAME_PAIRS = [
    ("Authorization", "Bearer", "Authorization", "Bearer"),
    ("X-Api-Key", "", "Authorization", "Bearer"),
    ("Authorization", "Bearer", "X-Api-Key", ""),
    ("X-Api-Key", "", "X-Api-Key", ""),
    ("X-Fi-Token", "", "X-Fi-Token", ""),
    ("Authorization", "Bearer", "X-Fi-Token", ""),
    ("X-Api-Key", "", "X-Fi-Token", ""),
]


def _hand(pairs: list[tuple[str, str]], name: Callable[[str], Any], value: Callable[[str], Any]) -> dict[Any, Any]:
    return {name(each): value(text) for each, text in pairs}


# How the caller copies A's headers: from A's built httpx client, or by hand from A's header names and values.
COPIES: dict[str, Callable[[httpx.Headers, list[tuple[str, str]]], Any]] = {
    "client_dict": lambda built, pairs: dict(built),
    "client_headers_object": lambda built, pairs: built,
    "client_raw_bytes": lambda built, pairs: dict(built.raw),
    "text_upper": lambda built, pairs: _hand(pairs, str.upper, str),
    "text_lower": lambda built, pairs: _hand(pairs, str.lower, str),
    "text_swapped_case": lambda built, pairs: _hand(pairs, str.swapcase, str),
    "bytes_names": lambda built, pairs: _hand(pairs, str.encode, str),
    "bytes_upper_names_and_values": lambda built, pairs: _hand(pairs, lambda n: n.upper().encode(), str.encode),
}
PATHS = ["constructor", "unbuilt_with_headers", "built_with_headers_same_client", "built_with_headers_derived", "evolve"]


@pytest.fixture()
def sinks() -> Iterator[dict[str, Sink]]:
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


def _build(client: AuthenticatedClient, builder: str) -> Any:
    return client.get_httpx_client() if builder == "sync" else client.get_async_httpx_client()


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


def _b_client(path: str, base: dict[str, Any], given: Any, builder: str) -> AuthenticatedClient:
    if path == "constructor":
        return AuthenticatedClient(**base, headers=given)
    plain = AuthenticatedClient(**base)
    if path == "unbuilt_with_headers":
        return plain.with_headers(given)
    _build(plain, builder)
    if path == "built_with_headers_same_client":
        plain.with_headers(given)
        return plain
    if path == "built_with_headers_derived":
        return plain.with_headers(given)
    return attrs.evolve(plain, headers=given)


@pytest.mark.parametrize("builder", ["sync", "async"])
@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("copy", list(COPIES))
@pytest.mark.parametrize("a_name,a_prefix,b_name,b_prefix", NAME_PAIRS)
def test_headers_copied_from_another_tenant_carry_none_of_its_credentials(
    a_name, a_prefix, b_name, b_prefix, copy, path, builder, sinks, direct_env
):
    marker_a = "mk" + "-A-" + secrets.token_hex(8)
    marker_b = "mk" + "-B-" + secrets.token_hex(8)
    a_headers = [("X-Common", "shared-value"), ("Cookie", "sid=" + marker_a + "c"), ("X-Secret-Key", marker_a + "s")]
    a = AuthenticatedClient(
        base_url=_url(sinks["A"]), token=marker_a + "t", prefix=a_prefix, auth_header_name=a_name,
        headers=dict(a_headers), timeout=httpx.Timeout(30),
    )
    a_built = _build(a, builder).headers
    a_token = (a_prefix + " " if a_prefix else "") + marker_a + "t"
    given = COPIES[copy](a_built, [*a_headers, (a_name, a_token)])
    base = {
        "base_url": _url(sinks["B"]), "token": marker_b, "prefix": b_prefix, "auth_header_name": b_name,
        "timeout": httpx.Timeout(30),
    }
    b = _b_client(path, base, given, builder)
    _send(b, builder)

    b_chunks = sinks["B"].chunks
    b_lines = [line.lower() for chunk in b_chunks for line in chunk.split(b"\r\n")]
    observed = {
        "a_marker_bytes_at_b": sum(chunk.count(marker_a.encode()) for chunk in b_chunks) * len(marker_a),
        "b_token_per_request": [chunk.count(marker_b.encode()) for chunk in b_chunks],
        "b_token_header_lines": sum(1 for line in b_lines if line.startswith(b_name.lower().encode() + b":")),
        "common_header_lines": sum(1 for line in b_lines if line.startswith(b"x-common:")),
    }
    assert observed == {
        "a_marker_bytes_at_b": 0,
        "b_token_per_request": [1],
        "b_token_header_lines": 1,
        "common_header_lines": 1,
    }
