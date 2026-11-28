"""Two tenants building the generated ``AuthenticatedClient`` at the same time each send only their own token: a
headers dict the caller passes to both, or one the clients share through ``attrs.evolve`` (``with_headers``,
``with_cookies``, ``with_timeout`` or ``evolve(client, token=..., base_url=...)``), stays exactly as the caller passed
it, and the token of one tenant is not carried to the other tenant's host. Each tenant has its own plain-http loopback
listener that the client sends to direct; the tokens are made at runtime, one per tenant, and every listener counts the
bytes of the other tenant's token it receives. The transport's SSL context build is slowed so the clients of both
tenants are built inside the same window, the way a busy process builds them."""

from __future__ import annotations

import asyncio
import os
import secrets
import threading
import time
from typing import Any, Callable, Iterator
from unittest import mock

import attrs
import httpx
import httpx._transports.default as httpx_default_transport
import pytest

from fi.generated.openapi_client import AuthenticatedClient
from tests.core._plaintext_oracle import PROXY_NAMES, Sink

THREADS = 8
ITERATIONS = 6
BUILD_DELAY = 0.01  # seconds added to each transport's SSL context build


@pytest.fixture()
def tenant_sinks() -> Iterator[dict[str, Sink]]:
    made = {"A": Sink(), "B": Sink()}
    yield made
    for each in made.values():
        each.close()


@pytest.fixture()
def slow_ssl_context(monkeypatch: pytest.MonkeyPatch) -> None:
    real = httpx_default_transport.create_ssl_context

    def slowed(*args: Any, **kwargs: Any) -> Any:
        time.sleep(BUILD_DELAY)
        return real(*args, **kwargs)

    monkeypatch.setattr(httpx_default_transport, "create_ssl_context", slowed)


@pytest.fixture()
def direct_env() -> Iterator[None]:
    clean = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, clean, clear=True):
        yield


def _tokens() -> dict[str, str]:
    return {"A": "tenanta" + secrets.token_hex(16), "B": "tenantb" + secrets.token_hex(16)}


def _url(sink: Sink) -> str:
    return f"http://127.0.0.1:{sink.port}"


def _foreign(sinks: dict[str, Sink], tokens: dict[str, str]) -> dict[str, dict[str, int]]:
    """Per tenant sink: the connections that carried the other tenant's token and the bytes of that token received."""
    seen = {}
    for tenant, other in (("A", "B"), ("B", "A")):
        marker = tokens[other].encode()
        chunks = sinks[tenant].chunks
        seen[tenant] = {
            "foreign_conns": sum(1 for chunk in chunks if marker in chunk),
            "foreign_bytes": sum(chunk.count(marker) for chunk in chunks) * len(marker),
        }
    return seen


def _own_requests(sinks: dict[str, Sink], tokens: dict[str, str]) -> dict[str, int]:
    return {tenant: sum(1 for chunk in sinks[tenant].chunks if tokens[tenant].encode() in chunk) for tenant in sinks}


def _send_sync(client: AuthenticatedClient) -> None:
    built = client.get_httpx_client()
    try:
        built.get("/probe/")
    finally:
        built.close()


def _send_async(clients: list[AuthenticatedClient], barrier: threading.Barrier | None = None) -> None:
    async def one(client: AuthenticatedClient) -> None:
        built = client.get_async_httpx_client()
        try:
            await built.get("/probe/")
        finally:
            await built.aclose()

    async def run() -> None:
        if barrier is not None:
            barrier.wait(timeout=60)  # inside the running loop, so every thread's tasks start together
        await asyncio.gather(*(one(client) for client in clients))

    asyncio.run(run())


def _race(clients: list[AuthenticatedClient], builder: str) -> list[BaseException]:
    """One thread per client, released together: a sync thread builds and sends with ``get_httpx_client``, an async
    thread runs an event loop whose task builds and sends with ``get_async_httpx_client``."""
    barrier = threading.Barrier(len(clients))
    errors: list[BaseException] = []

    def work(client: AuthenticatedClient) -> None:
        try:
            if builder == "sync":
                barrier.wait(timeout=60)
                _send_sync(client)
            else:
                _send_async([client], barrier)
        except BaseException as exc:  # reported by the test
            errors.append(exc)

    threads = [threading.Thread(target=work, args=(client,)) for client in clients]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=120)
    return errors


def _run(
    sinks: dict[str, Sink], tokens: dict[str, str], builder: str, make: Callable[[], tuple[list[AuthenticatedClient], list[tuple[dict, dict]]]]
) -> dict[str, Any]:
    for each in sinks.values():
        each.reset()
    errors: list[BaseException] = []
    altered: list[tuple[dict, dict]] = []
    sent = 0
    for _ in range(ITERATIONS):
        clients, passed = make()
        sent += len(clients)
        errors += _race(clients, builder)
        altered += [(as_passed, now_held) for as_passed, now_held in passed if now_held != as_passed]
    return {
        "foreign": _foreign(sinks, tokens),
        "callers_dicts_altered": len(altered),
        "errors": [repr(exc) for exc in errors],
        "own_requests": sum(_own_requests(sinks, tokens).values()) == sent,
    }


EXPECTED = {
    "foreign": {tenant: {"foreign_conns": 0, "foreign_bytes": 0} for tenant in ("A", "B")},
    "callers_dicts_altered": 0,
    "errors": [],
    "own_requests": True,
}


@pytest.mark.parametrize("builder", ["sync", "async"])
def test_tenants_sharing_a_callers_headers_dict_send_only_their_own_token(
    builder, tenant_sinks, slow_ssl_context, direct_env
):
    tokens = _tokens()

    def make():
        common = {"X-Common": "shared-value"}
        snapshot = dict(common)
        clients = [
            AuthenticatedClient(base_url=_url(tenant_sinks[tenant]), token=tokens[tenant], headers=common, timeout=httpx.Timeout(30))
            for tenant in ("A", "B") * (THREADS // 2)
        ]
        return clients, [(snapshot, common)]

    observed = _run(tenant_sinks, tokens, builder, make)
    assert observed == EXPECTED


@pytest.mark.parametrize("builder", ["sync", "async"])
def test_tenants_derived_through_evolve_send_only_their_own_token(builder, tenant_sinks, slow_ssl_context, direct_env):
    tokens = _tokens()

    def make():
        given = {"X-Common": "shared-value"}
        snapshot = dict(given)
        a = AuthenticatedClient(base_url=_url(tenant_sinks["A"]), token=tokens["A"], headers=given, timeout=httpx.Timeout(30))
        b = attrs.evolve(a, token=tokens["B"], base_url=_url(tenant_sinks["B"]))
        clients = [
            a,
            b,
            a.with_cookies({"session": "a"}),
            b.with_cookies({"session": "b"}),
            a.with_timeout(httpx.Timeout(31)),
            b.with_timeout(httpx.Timeout(31)),
            a.with_headers({"X-Extra": "a"}),
            b.with_headers({"X-Extra": "b"}),
        ]
        return clients, [(snapshot, given)]

    observed = _run(tenant_sinks, tokens, builder, make)
    assert observed == EXPECTED


@pytest.mark.parametrize("builder", ["sync", "async"])
@pytest.mark.parametrize("sharing", ["callers_dict", "evolve"])
def test_a_tenant_built_after_another_on_shared_headers_sends_only_its_own_token(
    sharing, builder, tenant_sinks, direct_env
):
    """Built one after the other, the second tenant's client carries no header the first tenant's build wrote."""
    tokens = _tokens()
    for each in tenant_sinks.values():
        each.reset()
    given = {"X-Common": "shared-value"}
    snapshot = dict(given)
    a = AuthenticatedClient(base_url=_url(tenant_sinks["A"]), token=tokens["A"], headers=given, timeout=httpx.Timeout(30))
    if sharing == "callers_dict":
        b = AuthenticatedClient(
            base_url=_url(tenant_sinks["B"]), token=tokens["B"], headers=given, auth_header_name="X-Api-Key",
            timeout=httpx.Timeout(30),
        )
    else:
        b = attrs.evolve(a, token=tokens["B"], base_url=_url(tenant_sinks["B"]), auth_header_name="X-Api-Key")
    if builder == "sync":
        _send_sync(a)
        _send_sync(b)
    else:
        _send_async([a])
        _send_async([b])
    observed = {"foreign": _foreign(tenant_sinks, tokens), "callers_dict": given}
    assert observed == {"foreign": EXPECTED["foreign"], "callers_dict": snapshot}
    assert _own_requests(tenant_sinks, tokens) == {"A": 1, "B": 1}
